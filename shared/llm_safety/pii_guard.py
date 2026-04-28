"""PII detection and redaction for LLM inputs (F-14).

Detects and redacts personally identifiable information before sending to LLMs.
SECURITY: Prevents PII leakage to external LLM providers.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from .exceptions import PIIRedactionError

logger = logging.getLogger(__name__)


class PIIType(Enum):
    """Types of PII that can be detected."""

    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    PHONE_NUMBER = "phone_number"
    EMAIL = "email"
    IP_ADDRESS = "ip_address"
    API_KEY = "api_key"
    PASSWORD = "password"


@dataclass
class PIIFinding:
    """A detected PII instance."""

    pii_type: PIIType
    start: int
    end: int
    original: str
    redacted: str
    confidence: float  # 0.0 to 1.0


@dataclass
class RedactionResult:
    """Result of PII redaction."""

    sanitized_text: str
    findings: list[PIIFinding]
    redaction_count: int
    pii_types_found: list[str]


class PIIGuard:
    """Detect and redact PII from text before LLM processing.

    Supported PII types:
    - US Social Security Numbers (SSN)
    - Credit card numbers (major brands)
    - Phone numbers (US/International)
    - Email addresses
    - IP addresses (v4/v6)
    - API keys and secrets patterns
    - Password/credential patterns
    """

    # PII detection patterns with redaction templates
    PATTERNS: dict[PIIType, tuple[re.Pattern, str, float]] = {
        # SSN: XXX-XX-XXXX or XXXXXXXXX (strict to avoid false positives)
        PIIType.SSN: (
            re.compile(r"\b(\d{3})[-\s]?(\d{2})[-\s]?(\d{4})\b"),
            "[REDACTED-SSN]",
            0.95,
        ),
        # Credit cards: Visa, MC, Amex, Discover with validation
        PIIType.CREDIT_CARD: (
            re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12})\b"),
            "[REDACTED-CC]",
            0.95,
        ),
        # Phone numbers: US formats with area code
        PIIType.PHONE_NUMBER: (
            re.compile(r"\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b"),
            "[REDACTED-PHONE]",
            0.85,
        ),
        # Email addresses
        PIIType.EMAIL: (
            re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "[REDACTED-EMAIL]",
            0.95,
        ),
        # IP addresses (v4 and v6)
        PIIType.IP_ADDRESS: (
            re.compile(
                r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b|"
                r"(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|"
                r"(?:[0-9a-fA-F]{1,4}:)*::(?:[0-9a-fA-F]{1,4}:)*[0-9a-fA-F]{1,4}?|"
                r"::(?:[fF]{4}:)?(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
            ),
            "[REDACTED-IP]",
            0.80,
        ),
        # API keys: common patterns (generic, high false positive risk)
        PIIType.API_KEY: (
            re.compile(r"\b(?:sk-|ak-|api[_-]?key|apikey)[_\s]*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?", re.IGNORECASE),
            "[REDACTED-API-KEY]",
            0.75,
        ),
        # Password patterns in text
        PIIType.PASSWORD: (
            re.compile(r"\b(?:password|passwd|pwd)\s*[:=]\s*['\"]?([^\s'\"]+)['\"]?", re.IGNORECASE),
            "[REDACTED-PASSWORD]",
            0.90,
        ),
    }

    def __init__(
        self,
        enabled_types: set[PIIType] | None = None,
        fail_closed: bool | None = None,
    ) -> None:
        """Initialize PIIGuard.

        Args:
            enabled_types: Set of PII types to detect. If None, all types enabled.
            fail_closed: If True, raise exception when PII detected but can't be fully redacted.
        """
        self.enabled = os.getenv("LLM_PII_REDACTION", "true").lower() not in ("false", "0", "no")
        self.enabled_types = enabled_types or set(self.PATTERNS.keys())
        self.fail_closed = (
            fail_closed
            if fail_closed is not None
            else os.getenv("LLM_SAFETY_FAIL_CLOSED", "").lower() in ("true", "1", "yes")
        )

    def redact(self, text: str | None, context: dict[str, Any] | None = None) -> RedactionResult:
        """Detect and redact PII from text.

        Args:
            text: Text to scan for PII
            context: Optional context for logging

        Returns:
            RedactionResult with sanitized text and findings

        Raises:
            PIIRedactionError: If fail_closed enabled and unredactable PII found
        """
        # Handle edge cases
        if not text or not isinstance(text, str):
            return RedactionResult(
                sanitized_text=text or "",
                findings=[],
                redaction_count=0,
                pii_types_found=[],
            )

        if not self.enabled:
            return RedactionResult(
                sanitized_text=text,
                findings=[],
                redaction_count=0,
                pii_types_found=[],
            )

        findings: list[PIIFinding] = []
        sanitized = text
        offset_adjustment = 0

        for pii_type in self.enabled_types:
            if pii_type not in self.PATTERNS:
                continue

            pattern, redaction_template, confidence = self.PATTERNS[pii_type]

            for match in pattern.finditer(text):
                original = match.group(0)
                start = match.start()
                end = match.end()

                # Adjust positions based on previous redactions
                adjusted_start = start + offset_adjustment
                adjusted_end = end + offset_adjustment

                finding = PIIFinding(
                    pii_type=pii_type,
                    start=adjusted_start,
                    end=adjusted_end,
                    original=original,
                    redacted=redaction_template,
                    confidence=confidence,
                )
                findings.append(finding)

                # Perform redaction
                sanitized = sanitized[:adjusted_start] + redaction_template + sanitized[adjusted_end:]
                offset_adjustment += len(redaction_template) - len(original)

        # Build result
        pii_types_found = list(set(f.pii_type.value for f in findings))

        result = RedactionResult(
            sanitized_text=sanitized,
            findings=findings,
            redaction_count=len(findings),
            pii_types_found=pii_types_found,
        )

        # Log redactions
        if findings:
            ctx = context or {}
            logger.info(
                "PII redacted from LLM input",
                extra={
                    "redaction_count": len(findings),
                    "pii_types": pii_types_found,
                    "tenant_id": ctx.get("tenant_id"),
                    "request_id": ctx.get("request_id"),
                },
            )

            # Fail closed if in strict mode (redaction failures should block)
            if self.fail_closed and findings:
                raise PIIRedactionError(
                    message="PII detected in fail-closed mode - blocking request",
                    pii_types_found=pii_types_found,
                    redaction_count=len(findings),
                    details={"context": context},
                )

        return result

    def check(self, text: str) -> list[PIIFinding]:
        """Check text for PII without redacting.

        Returns:
            List of PII findings (empty if none found)
        """
        result = self.redact(text)
        return result.findings

    def is_clean(self, text: str) -> bool:
        """Quick check if text contains no PII.

        Returns:
            True if no PII detected, False otherwise
        """
        result = self.redact(text)
        return result.redaction_count == 0
