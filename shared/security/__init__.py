"""Shared security module for middleware and hardening."""

from .middleware import (
    add_security_middleware,
    SecurityValidator,
    SQL_INJECTION_PATTERNS,
    XSS_PATTERNS,
)
from .config import SecurityConfig

__all__ = [
    "add_security_middleware",
    "SecurityConfig",
    "SecurityValidator",
    "SQL_INJECTION_PATTERNS",
    "XSS_PATTERNS",
]
