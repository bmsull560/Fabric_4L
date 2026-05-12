"""FastAPI exception handlers for standardized error responses."""

import logging
import os
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..observability.trace_context import ALL_TRACE_HEADERS, sanitize_trace_id
from ..testability import IDGenerator
from .exceptions import ValueFabricException
from .models import ErrorCode, ErrorResponse

logger = logging.getLogger(__name__)


def canonical_error_response_schema() -> dict[str, Any]:
    """Return the canonical API error schema used by every layer service."""
    return {
        "type": "object",
        "title": "ErrorResponse",
        "required": ["message", "code", "trace_id"],
        "additionalProperties": False,
        "properties": {
            "message": {
                "type": "string",
                "description": "Human-readable error message",
            },
            "code": {
                "type": "string",
                "minLength": 1,
                "description": "Machine-readable error code",
            },
            "trace_id": {
                "type": "string",
                "minLength": 1,
                "description": "Request trace ID for support correlation",
            },
            "details": {
                "anyOf": [
                    {"type": "object", "additionalProperties": True},
                    {"type": "null"},
                ],
                "description": "Optional sanitized error details",
            },
        },
    }


def install_error_response_openapi(app: FastAPI) -> None:
    """Ensure generated OpenAPI exposes the canonical error envelope.

    FastAPI defaults validation failures to ``HTTPValidationError`` with a
    ``detail`` array. Runtime handlers return ``ErrorResponse`` instead, so we
    publish ``HTTPValidationError`` as a deprecated alias to prevent generated
    clients from learning the wrong shape while old references are migrated.
    """

    if getattr(app.state, "_canonical_error_openapi_installed", False):
        return

    original_openapi = app.openapi

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        try:
            schema = original_openapi()
        except Exception:
            schema = get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=app.routes,
            )

        components = schema.setdefault("components", {})
        schemas = components.setdefault("schemas", {})
        error_schema = canonical_error_response_schema()
        schemas["ErrorResponse"] = error_schema
        schemas["HTTPValidationError"] = {
            **error_schema,
            "title": "HTTPValidationError",
            "description": (
                "Deprecated compatibility alias for ErrorResponse. "
                "Use ErrorResponse for new clients."
            ),
        }
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi
    app.state._canonical_error_openapi_installed = True


def is_production() -> bool:
    """Check if running in production environment.
    
    Checks multiple common environment variable names for compatibility
    across different layers and deployment configurations.
    """
    env = (
        os.getenv("ENVIRONMENT") 
        or os.getenv("ENV") 
        or os.getenv("APP_ENV")
        or "development"
    ).lower()
    return env in ("production", "prod", "staging", "stg")


def sanitize_error_details(details: dict[str, Any] | None) -> dict[str, Any] | None:
    """Sanitize error details for production responses.

    Removes potentially sensitive information like:
    - Stack traces
    - Internal paths
    - Database connection strings
    - Credentials
    """
    if details is None:
        return None

    sensitive_keys = {
        "password",
        "token",
        "secret",
        "key",
        "credential",
        "auth",
        "traceback",
        "stack_trace",
        "internal_path",
        "connection_string",
    }

    sanitized = {}
    for key, value in details.items():
        # Skip sensitive keys
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            continue

        # Truncate long values
        if isinstance(value, str) and len(value) > 1000:
            value = value[:1000] + "... [truncated]"

        sanitized[key] = value

    return sanitized if sanitized else None


def get_request_trace_id(
    request: Request,
    id_generator: IDGenerator | None = None,
) -> str:
    """Extract or generate trace ID from request.

    Args:
        request: The incoming request.
        id_generator: Optional injectable ID generator.  Defaults to UUID-based
            generation when ``None``.
    """
    # Try to get from request state (set by middleware)
    trace_id = getattr(request.state, "trace_id", None)
    if trace_id:
        return str(trace_id)

    # Try to get from header
    for header in ALL_TRACE_HEADERS:
        trace_id = request.headers.get(header)
        if trace_id:
            return sanitize_trace_id(trace_id, generator=(id_generator.generate if id_generator else None))

    # Generate new trace ID
    if id_generator is not None:
        return f"req_{id_generator.generate()[:16]}"
    return f"req_{uuid.uuid4().hex[:16]}"


def _sanitize_trace_id(
    trace_id: str,
    id_generator: IDGenerator | None = None,
) -> str:
    """Sanitize a trace ID from external sources.
    
    Prevents header injection attacks by:
    - Truncating to max length
    - Removing control characters
    - Allowing only alphanumeric, hyphen, underscore

    Args:
        trace_id: The raw trace ID string.
        id_generator: Optional injectable ID generator for fallback IDs.
    """
    return sanitize_trace_id(trace_id, generator=(id_generator.generate if id_generator else None))


async def value_fabric_exception_handler(
    request: Request, exc: ValueFabricException
) -> JSONResponse:
    """Handle ValueFabricException with standardized response."""
    trace_id = get_request_trace_id(request)

    # Sanitize details in production
    details = exc.details if not is_production() else sanitize_error_details(exc.details)

    error_response = ErrorResponse(
        code=exc.error_code,
        message=exc.message,
        trace_id=trace_id,
        details=details,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
        headers={"X-Request-ID": trace_id},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException with standardized response."""
    trace_id = get_request_trace_id(request)

    # Map HTTP status to error code
    code_map = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.AUTHENTICATION_ERROR,
        403: ErrorCode.AUTHORIZATION_ERROR,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }

    error_code = code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)

    # Extract detail message
    message = str(exc.detail)
    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", str(exc.detail))

    error_response = ErrorResponse(
        code=error_code,
        message=message,
        trace_id=trace_id,
        details=None,  # Don't expose HTTP exception details
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
        headers={"X-Request-ID": trace_id},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle FastAPI request validation errors."""
    trace_id = get_request_trace_id(request)

    # Format validation errors
    errors = []
    for error in exc.errors():
        error_info = {
            "field": ".".join(str(x) for x in error.get("loc", [])),
            "type": error.get("type"),
            "message": error.get("msg"),
        }
        errors.append(error_info)

    details = {"validation_errors": errors} if not is_production() else None

    # Single message summarizing the errors
    message = f"Request validation failed: {len(errors)} field(s) invalid"
    if errors and len(errors) == 1:
        message = f"Invalid value for field '{errors[0]['field']}'"

    error_response = ErrorResponse(
        code=ErrorCode.VALIDATION_ERROR,
        message=message,
        trace_id=trace_id,
        details=details,
    )

    return JSONResponse(
        status_code=422,
        content=error_response.model_dump(),
        headers={"X-Request-ID": trace_id},
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with sanitized response."""
    trace_id = get_request_trace_id(request)

    # Log the full exception for debugging
    logger.exception(f"Unhandled exception (trace_id={trace_id}): {exc}")

    # Always return sanitized message in production
    if is_production():
        message = "An unexpected error occurred. Please try again or contact support."
        details = None
    else:
        message = f"Internal error: {str(exc)}"
        details = {"exception_type": type(exc).__name__}

    error_response = ErrorResponse(
        code=ErrorCode.INTERNAL_ERROR,
        message=message,
        trace_id=trace_id,
        details=details,
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(),
        headers={"X-Request-ID": trace_id},
    )


async def starlette_http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle Starlette HTTP exceptions (internal FastAPI errors)."""
    trace_id = get_request_trace_id(request)
    
    # Map status codes similar to HTTPException handler
    code_map = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.AUTHENTICATION_ERROR,
        403: ErrorCode.AUTHORIZATION_ERROR,
        404: ErrorCode.NOT_FOUND,
        500: ErrorCode.INTERNAL_ERROR,
    }
    
    error_code = code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    
    error_response = ErrorResponse(
        code=error_code,
        message=str(exc.detail),
        trace_id=trace_id,
        details=None,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
        headers={"X-Request-ID": trace_id},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with a FastAPI application.

    Usage:
        from value_fabric.shared.error_handling import register_exception_handlers
        app = FastAPI()
        register_exception_handlers(app)
    """
    # Register specific exception handlers first
    app.add_exception_handler(ValueFabricException, value_fabric_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    # Catch-all must be last
    app.add_exception_handler(Exception, global_exception_handler)
    install_error_response_openapi(app)
