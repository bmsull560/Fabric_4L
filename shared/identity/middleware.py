"""Governance middleware for request authentication and authorization.

Task 84: Added optional per-tenant rate limiting support.
"""

from __future__ import annotations

import logging
import time
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

# Simple in-memory rate limiter for tenant-scoped requests (Task 84)
# Maps tenant_id -> (requests_in_window, window_start)
_tenant_rate_limit_buckets: dict[str, tuple[int, float]] = {}


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


def _check_tenant_rate_limit(
    tenant_id: str,
    requests_per_minute: int,
) -> tuple[bool, int]:
    """Check if tenant has exceeded rate limit.

    Args:
        tenant_id: Tenant identifier
        requests_per_minute: Max requests allowed per minute

    Returns:
        Tuple of (allowed: bool, retry_after: int)
    """
    now = time.time()
    window_seconds = 60

    count, window_start = _tenant_rate_limit_buckets.get(tenant_id, (0, now))

    # Reset window if expired
    if now - window_start > window_seconds:
        count = 0
        window_start = now

    # Check limit
    if count >= requests_per_minute:
        retry_after = int(window_seconds - (now - window_start)) + 1
        return False, max(1, retry_after)

    # Increment and store
    _tenant_rate_limit_buckets[tenant_id] = (count + 1, window_start)
    return True, 0


class GovernanceMiddleware(BaseHTTPMiddleware):
    """Middleware to handle authentication, authorization, and rate limiting (Task 84)."""

    def __init__(
        self,
        app: ASGIApp,
        api_key_resolver: Callable[[str], Awaitable[dict | None]] | None = None,
        jwt_secret: str | None = None,
        rate_limiter=None,
        on_rate_limit_hit: Callable[[str, str], None] | None = None,
        tenant_settings_lookup: Callable[[UUID], Awaitable[dict | None]] | None = None,
        enable_per_tenant_rate_limiting: bool = True,  # Task 84: Enable by default
    ):
        super().__init__(app)
        self.api_key_lookup = api_key_resolver  # Alias for compatibility
        self.jwt_secret = jwt_secret
        self.rate_limiter = rate_limiter
        self.on_rate_limit_hit = on_rate_limit_hit
        self.tenant_settings_lookup = tenant_settings_lookup
        self.enable_per_tenant_rate_limiting = enable_per_tenant_rate_limiting

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process request with auth, context, and optional rate limiting (Task 84)."""
        context = await self._authenticate(request)
        request.state.context = context

        # Task 84: Per-tenant rate limiting
        if self.enable_per_tenant_rate_limiting and context.tenant_id:
            allowed, retry_after = await self._check_rate_limit(context.tenant_id)
            if not allowed:
                tenant_id_str = str(context.tenant_id)
                logger.warning(
                    f"Rate limit exceeded for tenant {tenant_id_str}, "
                    f"retry_after={retry_after}s"
                )
                # Call rate limit hit callback if provided (for metrics)
                if self.on_rate_limit_hit:
                    try:
                        self.on_rate_limit_hit(tenant_id_str, "tenant")
                    except Exception:
                        pass  # Don't fail request if metrics fail
                return Response(
                    content=f"Rate limit exceeded. Retry after {retry_after} seconds.",
                    status_code=429,
                    headers={"Retry-After": str(retry_after)},
                )

        response = await call_next(request)

        # Add request ID header if available
        if context.request_id:
            response.headers["X-Request-ID"] = context.request_id

        return response

    async def _check_rate_limit(self, tenant_id: UUID) -> tuple[bool, int]:
        """Check tenant rate limit from settings (Task 84).

        Args:
            tenant_id: Tenant UUID

        Returns:
            Tuple of (allowed: bool, retry_after: int)
        """
        tenant_id_str = str(tenant_id)
        default_rpm = 120  # Default requests per minute

        # Try to get tenant-specific limits from settings
        if self.tenant_settings_lookup:
            try:
                settings = await self.tenant_settings_lookup(tenant_id)
                if settings:
                    rate_limits = settings.get("rate_limits", {})
                    rpm = rate_limits.get("requests_per_minute", default_rpm)
                else:
                    rpm = default_rpm
            except Exception as e:
                logger.warning(f"Failed to load tenant settings for rate limit: {e}")
                rpm = default_rpm
        else:
            rpm = default_rpm

        return _check_tenant_rate_limit(tenant_id_str, rpm)

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
