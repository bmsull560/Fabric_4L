"""Domain exception hierarchy for Layer 1 Ingestion Service.

Provides explicit exception classes for all failure modes that were
previously handled with bare or silent except blocks (M-02 remediation).
"""


class Layer1Exception(Exception):
    """Base exception for all Layer 1 ingestion errors."""

    def __init__(self, message: str, *, component: str = "layer1", error_code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.component = component
        self.error_code = error_code or self.__class__.__name__


class XBRLParseError(Layer1Exception):
    """Raised when XBRL parsing fails in a way that produces incorrect or incomplete data."""

    def __init__(
        self,
        message: str,
        *,
        concept: str | None = None,
        value_preview: str | None = None,
        context_ref: str | None = None,
        component: str = "xbrl_parser",
        error_code: str = "XBRL_PARSE_ERROR",
    ) -> None:
        super().__init__(message, component=component, error_code=error_code)
        self.concept = concept
        self.value_preview = value_preview
        self.context_ref = context_ref


class ConfigurationError(Layer1Exception):
    """Raised when service configuration is invalid or missing."""

    def __init__(
        self,
        message: str,
        *,
        component: str = "config",
        error_code: str = "CONFIGURATION_ERROR",
    ) -> None:
        super().__init__(message, component=component, error_code=error_code)
