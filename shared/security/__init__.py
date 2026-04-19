"""Shared security module for middleware and hardening."""

from .middleware import add_security_middleware
from .config import SecurityConfig

__all__ = [
    "add_security_middleware",
    "SecurityConfig",
]
