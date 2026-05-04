"""Shared error handling module for all Value Fabric layers."""

from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    ValidationError,
    ValueFabricException,
)
from .handlers import register_exception_handlers
from .middleware import get_request_id, RequestIDMiddleware
from .models import ErrorCode, ErrorResponse

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "ErrorCode",
    "ErrorResponse",
    "get_request_id",
    "NotFoundError",
    "RateLimitError",
    "register_exception_handlers",
    "RequestIDMiddleware",
    "ServiceUnavailableError",
    "ValidationError",
    "ValueFabricException",
]
