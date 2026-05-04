"""Exceptions for LLM safety module."""

from enum import Enum
from typing import Any


class LLMSafetyError(Exception):
    """Base exception for LLM safety violations."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class PromptInjectionError(LLMSafetyError):
    """Raised when prompt injection is detected.

    SECURITY: In fail-closed mode, this blocks the LLM request.
    """

    def __init__(
        self,
        message: str,
        severity: str,
        matched_patterns: list[str],
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details)
        self.severity = severity
        self.matched_patterns = matched_patterns


class PIIRedactionError(LLMSafetyError):
    """Raised when PII redaction fails or detects unredactable content."""

    def __init__(
        self,
        message: str,
        pii_types_found: list[str],
        redaction_count: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details)
        self.pii_types_found = pii_types_found
        self.redaction_count = redaction_count


class OutputValidationError(LLMSafetyError):
    """Raised when LLM output fails safety validation."""

    def __init__(
        self,
        message: str,
        validation_type: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details)
        self.validation_type = validation_type


class TokenLimitError(LLMSafetyError):
    """Raised when token limit is exceeded."""

    def __init__(
        self,
        message: str,
        estimated_tokens: int,
        max_tokens: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details)
        self.estimated_tokens = estimated_tokens
        self.max_tokens = max_tokens
