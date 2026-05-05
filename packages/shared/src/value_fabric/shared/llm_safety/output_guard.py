"""LLM output validation and safety checks (F-15).

Validates LLM responses for:
- Content safety (toxicity patterns)
- Format validation for structured outputs
- Hallucination indicators
- Response completeness
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .exceptions import OutputValidationError

logger = logging.getLogger(__name__)


class ValidationType(Enum):
    """Types of output validation."""

    CONTENT_SAFETY = "content_safety"
    FORMAT_VALIDATION = "format_validation"
    JSON_SCHEMA = "json_schema"
    COMPLETENESS = "completeness"
    HALLUCINATION = "hallucination"


class ContentSafetyLevel(Enum):
    """Content safety classification."""

    SAFE = "safe"
    SUSPICIOUS = "suspicious"  # Worth reviewing but not blocking
    UNSAFE = "unsafe"  # Should block in fail-closed mode


@dataclass
class ValidationResult:
    """Result of output validation."""

    is_valid: bool
    validation_type: ValidationType
    safety_level: ContentSafetyLevel
    issues: list[str]
    confidence: float


def _is_production_like() -> bool:
    env = (os.getenv("ENVIRONMENT") or os.getenv("APP_ENV") or "").strip().lower()
    return env in {"production", "prod", "staging", "stage"}


class OutputGuard:
    """Validate and sanitize LLM outputs.

    Checks for:
    - Toxic/harmful content patterns
    - Refusal/uncertainty indicators
    - Format compliance for structured outputs
    - Incomplete responses

    Semantics:
    - Fail closed in production-like environments by default.
    - Explicit dev bypass requires LLM_SAFETY_DEV_BYPASS=true (loudly logged).
    - sanitize() is a no-op placeholder; in fail-closed mode it raises.
    """

    # Toxic/harmful content patterns (basic heuristic-based detection)
    TOXICITY_PATTERNS: list[tuple[re.Pattern, str, float]] = [
        # Hate speech indicators (basic patterns - production should use ML classifier)
        (re.compile(r"\b(hate|kill|die|murder|attack)\s+(?:all|every)\s+\w+\s+(?:people|group|race|religion|gender)", re.IGNORECASE), "hate_speech", 0.9),
        # Self-harm indicators
        (re.compile(r"\b(?:suicide|self[- ]?harm|kill myself|end my life)\b", re.IGNORECASE), "self_harm", 0.95),
        # Violence instructions
        (re.compile(r"\b(?:how to|steps to|guide for)\s+(?:make|build|create)\s+(?:bomb|weapon|explosive|poison)", re.IGNORECASE), "violence_instructions", 0.95),
    ]

    # Refusal/uncertainty indicators (not necessarily bad, but worth flagging)
    REFUSAL_PATTERNS: list[re.Pattern] = [
        re.compile(r"\b(i cannot|i can't|i'm unable|i am unable|i do not|i don't)\s+(?:provide|answer|help|assist)", re.IGNORECASE),
        re.compile(r"\b(as an ai|as a language model|i'm just an ai|i don't have)\b", re.IGNORECASE),
        re.compile(r"\b(i don't know|i'm not sure|i cannot determine|unclear|insufficient information)\b", re.IGNORECASE),
    ]

    # Hallucination indicators
    HALLUCINATION_PATTERNS: list[re.Pattern] = [
        re.compile(r"\b(i think|probably|maybe|likely|seems like|appears to be)\s+\w+\s+(?:is|was|has|had)", re.IGNORECASE),
        re.compile(r"\b(according to some sources|some people say|it's said that)\b", re.IGNORECASE),
    ]

    # Incomplete response indicators
    INCOMPLETE_PATTERNS: list[re.Pattern] = [
        re.compile(r"\.{3,}\s*$"),  # Ends with ellipsis
        re.compile(r"\[truncated\]|\[cut off\]|\[incomplete\]", re.IGNORECASE),
        re.compile(r"\(continued\s*(?:in\s+part|\s*\d+\))", re.IGNORECASE),
    ]

    def __init__(self, fail_closed: bool | None = None) -> None:
        """Initialize OutputGuard.

        Args:
            fail_closed: If True, raise exception on unsafe content.
        """
        self.enabled = os.getenv("LLM_OUTPUT_VALIDATION", "true").lower() not in ("false", "0", "no")

        if fail_closed is not None:
            self.fail_closed = fail_closed
        else:
            env_val = os.getenv("LLM_SAFETY_FAIL_CLOSED", "").strip().lower()
            if env_val in ("true", "1", "yes"):
                self.fail_closed = True
            elif env_val in ("false", "0", "no"):
                self.fail_closed = False
            else:
                # Default: fail closed in production-like environments
                self.fail_closed = _is_production_like()

        # Explicit dev bypass (loud)
        if os.getenv("LLM_SAFETY_DEV_BYPASS", "").lower() in ("true", "1", "yes"):
            if _is_production_like():
                logger.error(
                    "LLM_SAFETY_DEV_BYPASS is set but ignored in production-like environments."
                )
            else:
                logger.warning(
                    "SECURITY: LLM_SAFETY_DEV_BYPASS=true — output guard is BYPASSED. "
                    "This must never be used in production."
                )
                self.enabled = False
                self.fail_closed = False

    def validate(
        self,
        content: str,
        expected_format: str | None = None,
        json_schema: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """Validate LLM output content.

        Args:
            content: The LLM response content
            expected_format: Expected format type ("json", "text", "structured")
            json_schema: Optional JSON schema for validation
            context: Optional context for logging

        Returns:
            ValidationResult with validation details

        Raises:
            OutputValidationError: If fail_closed enabled and content unsafe
        """
        if not self.enabled:
            return ValidationResult(
                is_valid=True,
                validation_type=ValidationType.CONTENT_SAFETY,
                safety_level=ContentSafetyLevel.SAFE,
                issues=[],
                confidence=1.0,
            )

        issues: list[str] = []
        safety_level = ContentSafetyLevel.SAFE
        confidence = 1.0

        # Check content safety
        toxicity_score, toxic_issues = self._check_toxicity(content)
        if toxicity_score > 0.8:
            safety_level = ContentSafetyLevel.UNSAFE
            issues.extend(toxic_issues)
            confidence = toxicity_score
        elif toxicity_score > 0.5:
            safety_level = ContentSafetyLevel.SUSPICIOUS
            issues.extend(toxic_issues)

        # Check for refusals (log but don't block)
        refusal_issues = self._check_refusals(content)
        if refusal_issues:
            issues.extend(refusal_issues)
            logger.debug("Response contains refusal indicators", extra={"indicators": refusal_issues})

        # Check for incompleteness
        incomplete_issues = self._check_completeness(content)
        if incomplete_issues:
            issues.extend(incomplete_issues)

        # Validate JSON format if expected
        if expected_format == "json" or json_schema:
            format_issues = self._validate_json(content, json_schema)
            issues.extend(format_issues)

        # Determine overall validity
        is_valid = safety_level != ContentSafetyLevel.UNSAFE and not any(
            i.startswith("JSON validation") for i in issues
        )

        result = ValidationResult(
            is_valid=is_valid,
            validation_type=ValidationType.CONTENT_SAFETY,
            safety_level=safety_level,
            issues=issues,
            confidence=confidence,
        )

        # Log validation results
        if issues:
            ctx = context or {}
            logger.warning(
                "Output validation found issues",
                extra={
                    "safety_level": safety_level.value,
                    "issues": issues,
                    "tenant_id": ctx.get("tenant_id"),
                    "request_id": ctx.get("request_id"),
                },
            )

        # Fail closed on unsafe content
        if self.fail_closed and safety_level == ContentSafetyLevel.UNSAFE:
            raise OutputValidationError(
                message=f"Unsafe LLM output detected: {', '.join(issues[:3])}",
                validation_type=ValidationType.CONTENT_SAFETY.value,
                details={"safety_level": safety_level.value, "issues": issues},
            )

        return result

    def _check_toxicity(self, content: str) -> tuple[float, list[str]]:
        """Check content for toxicity patterns.

        Returns:
            Tuple of (toxicity_score, list_of_issues)
        """
        issues: list[str] = []
        max_score = 0.0

        for pattern, name, confidence in self.TOXICITY_PATTERNS:
            if pattern.search(content):
                issues.append(f"Detected: {name}")
                max_score = max(max_score, confidence)

        return max_score, issues

    def _check_refusals(self, content: str) -> list[str]:
        """Check for refusal/uncertainty indicators."""
        issues: list[str] = []
        for pattern in self.REFUSAL_PATTERNS:
            if pattern.search(content):
                issues.append("Refusal/uncertainty indicator detected")
                break
        return issues

    def _check_completeness(self, content: str) -> list[str]:
        """Check if response appears incomplete."""
        issues: list[str] = []
        for pattern in self.INCOMPLETE_PATTERNS:
            if pattern.search(content):
                issues.append("Response may be incomplete (truncated/unfinished)")
                break
        return issues

    def _validate_json(self, content: str, schema: dict[str, Any] | None = None) -> list[str]:
        """Validate JSON format and optional schema."""
        issues: list[str] = []

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return [f"JSON validation error: {e}"]

        # Basic schema validation (simplified - production should use jsonschema library)
        if schema and "required" in schema:
            for field in schema["required"]:
                if field not in data:
                    issues.append(f"Missing required field: {field}")

        return issues

    def sanitize(self, content: str) -> str:
        """Sanitize content by removing potentially harmful sections.

        In fail-closed mode this raises because a real sanitizer is not yet
        implemented. To bypass in development, set LLM_SAFETY_DEV_BYPASS=true
        (loudly logged). NEVER bypass in production.
        """
        if not self.enabled:
            return content

        if self.fail_closed:
            raise OutputValidationError(
                message=(
                    "Output sanitization is not implemented. "
                    "In fail-closed mode, content cannot be passed through un-sanitized."
                ),
                validation_type=ValidationType.CONTENT_SAFETY.value,
                details={"note": "Implement a real sanitizer or explicitly disable fail_closed"},
            )

        logger.warning(
            "sanitize() is a no-op placeholder. Implement real content filtering before production use."
        )
        return content
