"""Compatibility exports for structured Value Fabric error handling."""

from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    ValidationError,
    ValueFabricException,
)
from .models import ErrorCode, ErrorResponse

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "ErrorCode",
    "ErrorResponse",
    "NotFoundError",
    "RateLimitError",
    "ServiceUnavailableError",
    "ValidationError",
    "ValueFabricException",
]
