"""Governance middleware for request authentication and authorization."""

from __future__ import annotations

import logging
from typing import Awaitable, Callable
from uuid import UUID

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .context import RequestContext
from .hashing import verify_api_key
from .jwt import decode_jwt
from .permissions import get_permissions_for_role

logger = logging.getLogger(__name__)


class GovernanceMiddleware(BaseHTTPMiddleware):
    """Middleware to handle authentication and set request context."""

    def __init__(
        self,
        app: ASGIApp,
        api_key_lookup: Callable[[str], Awaitable[dict | None]] | None = None,
        jwt_secret: str | None = None,
    ):
        super().__init__(app)
        self.api_key_lookup = api_key_lookup
        self.jwt_secret = jwt_secret

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process request and set context."""
        context = await self._authenticate(request)
        request.state.context = context

        response = await call_next(request)
        
        # Add request ID header if available
        if context.request_id:
            response.headers["X-Request-ID"] = context.request_id

        return response

    async def _authenticate(self, request: Request) -> RequestContext:
        """Authenticate request and build context."""
        context = RequestContext()
        
        # Try API key auth
        api_key = self._extract_api_key(request)
        if api_key and self.api_key_lookup:
            key_data = await self.api_key_lookup(api_key)
            if key_data:
                context.tenant_id = key_data.get("tenant_id")
                context.api_key_id = key_data.get("id")
                context.permissions = key_data.get("permissions", [])
                context.roles = ["api_key"]

        # Try JWT auth (if no API key or API key failed)
        if not context.tenant_id:
            token = self._extract_bearer_token(request)
            if token:
                payload = decode_jwt(token, self.jwt_secret)
                if payload:
                    context.user_id = UUID(payload.get("sub")) if payload.get("sub") else None
                    context.tenant_id = UUID(payload.get("tenant_id")) if payload.get("tenant_id") else None
                    context.roles = payload.get("roles", [])
                    # Derive permissions from roles
                    perms = []
                    for role in context.roles:
                        perms.extend(get_permissions_for_role(role))
                    context.permissions = list(set(perms))

        # Extract request ID
        context.request_id = request.headers.get("X-Request-ID") or str(UUID())

        return context

    def _extract_api_key(self, request: Request) -> str | None:
        """Extract API key from Authorization header."""
        auth_header = request.headers.get("Authorization", "")
        
        # Check for API key format: "ApiKey <key>" or "Bearer <key>"
        if auth_header.startswith("ApiKey "):
            return auth_header[7:].strip()
        if auth_header.startswith("Bearer "):
            # Could be API key or JWT - check format
            token = auth_header[7:].strip()
            if token.startswith("vf_"):
                return token
        
        return None

    def _extract_bearer_token(self, request: Request) -> str | None:
        """Extract bearer token from Authorization header."""
        auth_header = request.headers.get("Authorization", "")
        
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            # Skip if it looks like an API key
            if not token.startswith("vf_"):
                return token
        
        return None
