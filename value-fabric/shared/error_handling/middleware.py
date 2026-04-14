"""Middleware for request correlation ID handling."""

import re
import uuid
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Maximum length for request ID to prevent header size attacks
MAX_REQUEST_ID_LENGTH = 64

# Regex for valid request ID characters (alphanumeric, hyphen, underscore)
VALID_REQUEST_ID_PATTERN = re.compile(r'^[a-zA-Z0-9\-_]+$')


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request correlation IDs to all requests.

    This middleware:
    1. Reads X-Request-ID from incoming request headers (if present)
    2. Generates a new UUID if no request ID is provided
    3. Stores the request ID in request state for access in handlers
    4. Adds X-Request-ID to all response headers
    5. Makes request ID available for logging correlation
    """

    def __init__(
        self,
        app,
        header_name: str = "X-Request-ID",
        generator: Callable[[], str] | None = None,
    ):
        """Initialize the middleware.

        Args:
            app: FastAPI application
            header_name: Header name for request ID (default: X-Request-ID)
            generator: Optional custom ID generator function
        """
        super().__init__(app)
        self.header_name = header_name
        self.generator = generator or self._default_generator

    @staticmethod
    def _default_generator() -> str:
        """Generate a default request ID."""
        return f"req_{uuid.uuid4().hex[:20]}"

    def _validate_request_id(self, request_id: str | None) -> str:
        """Validate and sanitize incoming request ID.
        
        Returns a safe request ID or generates a new one if invalid.
        """
        if not request_id:
            return self.generator()
        
        # Check length
        if len(request_id) > MAX_REQUEST_ID_LENGTH:
            request_id = request_id[:MAX_REQUEST_ID_LENGTH]
        
        # Check valid characters
        if not VALID_REQUEST_ID_PATTERN.match(request_id):
            # Invalid characters found, generate new ID
            return self.generator()
        
        return request_id

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add correlation ID."""
        # Get and validate request ID from header, or generate new one
        raw_request_id = request.headers.get(self.header_name)
        request_id = self._validate_request_id(raw_request_id)

        # Store in request state for access in route handlers
        request.state.trace_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers[self.header_name] = request_id

        return response


def get_request_id(request: Request) -> str:
    """Get the request ID from a request object.

    Usage in route handlers:
        @app.get("/example")
        async def example(request: Request):
            trace_id = get_request_id(request)
            return {"trace_id": trace_id}
    """
    # Try to get from request state (set by middleware)
    trace_id = getattr(request.state, "trace_id", None)
    if trace_id:
        return str(trace_id)

    # Fall back to header
    return request.headers.get("X-Request-ID", "unknown")
