"""Compatibility exports for shared security middleware and validators."""

from .middleware import (
    SecurityConfig,
    SecurityMiddleware,
    SecurityValidator,
    add_security_middleware,
    SQL_INJECTION_PATTERNS,
    XSS_PATTERNS,
    NOSQL_INJECTION_PATTERNS,
)
from .config import (
    validate_production_safety,
    is_production_like_environment,
)
from .redaction import redact_credentials

__all__ = [
    "SecurityConfig",
    "SecurityMiddleware",
    "SecurityValidator",
    "add_security_middleware",
    "SQL_INJECTION_PATTERNS",
    "XSS_PATTERNS",
    "NOSQL_INJECTION_PATTERNS",
    "redact_credentials",
    "validate_production_safety",
    "is_production_like_environment",
]
