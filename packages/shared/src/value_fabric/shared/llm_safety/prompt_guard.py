"""Prompt injection detection and prevention (F-13).

Detects common prompt injection patterns and jailbreak attempts.
SECURITY: In fail-closed mode, blocks requests with detected injections.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .exceptions import PromptInjectionError

logger = logging.getLogger(__name__)


class InjectionSeverity(Enum):
    """Severity levels for detected prompt injections."""

    CRITICAL = "critical"  # Definite injection attempt, block immediately
    HIGH = "high"  # Strong indicators of injection
    MEDIUM = "medium"  # Suspicious patterns, review recommended
    LOW = "low"  # Minor concerns, log only


@dataclass
class InjectionCheckResult:
    """Result of prompt injection check."""

    is_injection: bool
    severity: InjectionSeverity
    matched_patterns: list[str]
    confidence: float  # 0.0 to 1.0


class PromptGuard:
    """Guard against prompt injection attacks.

    Detects patterns like:
    - Instruction override attempts ("ignore previous instructions")
    - System prompt extraction ("what is your system prompt")
    - Jailbreak patterns (DAN, Developer Mode, etc.)
    - Delimiter confusion attacks
    - Role confusion attempts
    """

    # CRITICAL: Definite injection patterns - always block in fail-closed mode
    CRITICAL_PATTERNS: list[tuple[re.Pattern, str]] = [
        # Instruction override
        (re.compile(r"ignore\s+(?:all\s+)?(?:previous|above|prior)\s+(?:instructions?|commands?|prompt)", re.IGNORECASE), "instruction_override"),
        (re.compile(r"disregard\s+(?:all\s+)?(?:previous|above|prior)\s+(?:instructions?|prompt)", re.IGNORECASE), "instruction_disregard"),
        (re.compile(r"forget\s+(?:all\s+)?(?:previous|prior)\s+(?:instructions?|prompt)", re.IGNORECASE), "instruction_forget"),
        # System prompt extraction
        (re.compile(r"(?:what|tell me|show me|repeat|print|output)\s+(?:your|the)\s+(?:system\s+)?prompt", re.IGNORECASE), "system_prompt_extraction"),
        (re.compile(r"(?:system|developer|instruction)\s*:\s*", re.IGNORECASE), "fake_system_marker"),
        # Jailbreak patterns
        (re.compile(r"\bDAN\b.*(?:mode|do anything now)", re.IGNORECASE), "dan_jailbreak"),
        (re.compile(r"developer\s*mode\s*(?:enabled?|on|activated)", re.IGNORECASE), "developer_mode_jailbreak"),
        (re.compile(r"(?:simulate|pretend|act as if)\s+(?:you are|you're|there are)\s+no\s+(?:restrictions?|limits?|constraints?)", re.IGNORECASE), "restriction_removal"),
        # Delimiter attacks
        (re.compile(r"```\s*(?:system|user|assistant)?\s*\n.*?ignore", re.IGNORECASE | re.DOTALL), "code_block_injection"),
        (re.compile(r'"""\s*(?:system|user)?\s*\n.*?ignore', re.IGNORECASE | re.DOTALL), "docstring_injection"),
    ]

    # HIGH: Strong indicators but may have false positives
    HIGH_PATTERNS: list[tuple[re.Pattern, str]] = [
        # Role confusion
        (re.compile(r"(?:from now on|going forward)\s*,?\s*(?:you are|you're|act as|become)\s+(?:an?\s+)?(?:unrestricted?|uncensored?|unfiltered)", re.IGNORECASE), "role_confusion"),
        # Obfuscation attempts
        (re.compile(r"i\s+will\s+tip\s+you\s+\$\d+.*if\s+you\s+(?:ignore|break|bypass)", re.IGNORECASE), "bribery_attempt"),
        (re.compile(r"(?:this\s+is\s+a\s+test|debugging|maintenance)\s+mode", re.IGNORECASE), "fake_maintenance"),
        # Context manipulation
        (re.compile(r"(?:user|human|person)\s*:\s*.*?\n\s*(?:assistant|ai|bot)\s*:\s*.*?\n\s*(?:user|human)?\s*:\s*ignore", re.IGNORECASE | re.DOTALL), "conversation_injection"),
    ]

    # MEDIUM: Suspicious but context-dependent
    MEDIUM_PATTERNS: list[tuple[re.Pattern, str]] = [
        (re.compile(r"\[system\s+override\]|\[admin\s+mode\]|\[debug\s+mode\]", re.IGNORECASE), "fake_mode_tags"),
        (re.compile(r"base64\s*:\s*[a-zA-Z0-9+/]{20,}={0,2}", re.IGNORECASE), "base64_obfuscation"),
        (re.compile(r"unicode\s*:\s*(?:U\+[0-9A-Fa-f]{4,}|\\u[0-9A-Fa-f]{4})", re.IGNORECASE), "unicode_obfuscation"),
    ]

    def __init__(self, fail_closed: bool | None = None) -> None:
        """Initialize PromptGuard.

        Args:
            fail_closed: If True, raise exception on injection detection.
                        If None, read from LLM_SAFETY_FAIL_CLOSED env var.
        """
        self.fail_closed = (
            fail_closed
            if fail_closed is not None
            else os.getenv("LLM_SAFETY_FAIL_CLOSED", "").lower() in ("true", "1", "yes")
        )
        self.enabled = os.getenv("LLM_PROMPT_INJECTION_CHECK", "true").lower() not in ("false", "0", "no")

    def check(self, text: str | None, context: dict[str, Any] | None = None) -> InjectionCheckResult:
        """Check text for prompt injection patterns.

        Args:
            text: Text to check (user input or prompt content)
            context: Optional context for logging (tenant_id, request_id, etc.)

        Returns:
            InjectionCheckResult with detection details

        Raises:
            PromptInjectionError: If fail_closed is enabled and injection detected
        """
        # Handle edge cases
        if not text or not isinstance(text, str):
            return InjectionCheckResult(
                is_injection=False,
                severity=InjectionSeverity.LOW,
                matched_patterns=[],
                confidence=0.0,
            )

        if not self.enabled:
            return InjectionCheckResult(is_injection=False, severity=InjectionSeverity.LOW, matched_patterns=[], confidence=0.0)

        matched_patterns: list[str] = []
        max_severity = InjectionSeverity.LOW
        confidence = 0.0

        # Check CRITICAL patterns
        for pattern, name in self.CRITICAL_PATTERNS:
            if pattern.search(text):
                matched_patterns.append(name)
                max_severity = InjectionSeverity.CRITICAL
                confidence = 1.0
                break  # Critical is maximum severity

        # Check HIGH patterns (only if no critical found)
        if max_severity != InjectionSeverity.CRITICAL:
            for pattern, name in self.HIGH_PATTERNS:
                if pattern.search(text):
                    matched_patterns.append(name)
                    max_severity = InjectionSeverity.HIGH
                    confidence = 0.85

        # Check MEDIUM patterns (only if no high/critical found)
        if max_severity == InjectionSeverity.LOW:
            for pattern, name in self.MEDIUM_PATTERNS:
                if pattern.search(text):
                    matched_patterns.append(name)
                    max_severity = InjectionSeverity.MEDIUM
                    confidence = 0.6

        is_injection = max_severity in (InjectionSeverity.CRITICAL, InjectionSeverity.HIGH)

        # Log detection
        if matched_patterns:
            ctx = context or {}
            logger.warning(
                "Prompt injection detected",
                extra={
                    "severity": max_severity.value,
                    "patterns": matched_patterns,
                    "confidence": confidence,
                    "tenant_id": ctx.get("tenant_id"),
                    "request_id": ctx.get("request_id"),
                },
            )

        # Fail closed if enabled and injection detected
        if self.fail_closed and is_injection:
            raise PromptInjectionError(
                message=f"Prompt injection detected: {max_severity.value} severity",
                severity=max_severity.value,
                matched_patterns=matched_patterns,
                details={"confidence": confidence, "context": context},
            )

        return InjectionCheckResult(
            is_injection=is_injection,
            severity=max_severity,
            matched_patterns=matched_patterns,
            confidence=confidence,
        )

    def sanitize(self, text: str, context: dict[str, Any] | None = None) -> tuple[str, InjectionCheckResult]:
        """Check text and return sanitized version.

        Unlike check(), this doesn't raise but returns the check result.
        Caller can decide whether to proceed based on severity.

        Returns:
            Tuple of (sanitized_text, check_result)
        """
        result = self.check(text, context)
        # Currently no transformation is applied, just detection
        # Future: Could redact specific injection payloads
        return text, result
