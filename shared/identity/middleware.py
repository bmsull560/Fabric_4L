"""Governance middleware for request authentication and authorization.

Task 84: Added optional per-tenant rate limiting support.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Awaitable, Callable
from uuid import UUID, uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .context import RequestContext
from .hashing import verify_api_key
from .jwt import decode_jwt
from .permissions import get_permissions_for_role

# Redis import for distributed rate limiting (optional)
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Default rate limit constants (Task 84)
DEFAULT_REQUESTS_PER_MINUTE = 120
RATE_LIMIT_WINDOW_SECONDS = 60
# Cache eviction: entries older than 2x window are cleaned up
RATE_LIMIT_CACHE_TTL_SECONDS = 120

# Simple in-memory rate limiter for tenant-scoped requests (Task 84)
# Maps tenant_id -> (requests_in_window, window_start)
# WARNING: This is per-process only. For multi-process deployments,
# Redis-backed rate limiting is required.
_tenant_rate_limit_buckets: dict[str, tuple[int, float]] = {}


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


def _get_worker_count() -> int:
    """Detect number of workers from environment variables.

    Checks common WSGI/ASGI server worker count settings.
    Returns 1 for single-worker deployments (default).

    Logs warning if detection fails, as this may indicate
    multi-worker deployment without explicit configuration.
    """
    for env_var in ("UVICORN_WORKERS", "GUNICORN_WORKERS", "WEB_CONCURRENCY"):
        value = os.getenv(env_var)
        if value:
            try:
                return max(1, int(value))  # Ensure at least 1
            except ValueError:
                continue
    logger.warning(
        "Could not detect worker count from UVICORN_WORKERS, GUNICORN_WORKERS, "
        "or WEB_CONCURRENCY. Defaulting to 1 worker. In multi-pod or multi-worker "
        "deployments, configure Redis for distributed rate limiting."
    )
    return 1


def _get_redis_client() -> redis.Redis | None:
    """Get Redis client if available and configured."""
    if not REDIS_AVAILABLE:
        return None
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return None
    try:
        return redis.from_url(redis_url, decode_responses=True)
    except Exception:
        return None


async def _check_redis_rate_limit(
    tenant_id: str,
    requests_per_minute: int,
    redis_client: redis.Redis,
) -> tuple[bool, int]:
    """Check rate limit using Redis for distributed state.

    Uses sliding window with Redis sorted sets for precise rate limiting
    across multiple workers.

    Args:
        tenant_id: Tenant identifier
        requests_per_minute: Max requests allowed per minute (must be >= 1)
        redis_client: Redis client instance

    Returns:
        Tuple of (allowed: bool, retry_after: int)

    Raises:
        ValueError: If requests_per_minute is not positive.
    """
    if requests_per_minute < 1:
        raise ValueError("requests_per_minute must be >= 1")

    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    key = f"rate_limit:{tenant_id}"

    # Remove entries outside the current window
    await redis_client.zremrangebyscore(key, 0, window_start)

    # Count requests in current window
    current_count = await redis_client.zcard(key)

    if current_count >= requests_per_minute:
        # Get oldest entry to calculate retry_after
        oldest = await redis_client.zrange(key, 0, 0, withscores=True)
        if oldest:
            oldest_timestamp = oldest[0][1]
            retry_after = int(RATE_LIMIT_WINDOW_SECONDS - (now - oldest_timestamp)) + 1
            return False, max(1, retry_after)
        return False, RATE_LIMIT_WINDOW_SECONDS

    # Add current request with unique member (timestamp + nanoseconds to avoid collision)
    unique_member = f"{now}:{uuid4().hex[:8]}"
    await redis_client.zadd(key, {unique_member: now})
    # Set expiry on the key
    await redis_client.expire(key, RATE_LIMIT_WINDOW_SECONDS)

    return True, 0


def _evict_stale_rate_limit_entries(now: float) -> None:
    """Evict stale entries from in-memory rate limit buckets.

    Called periodically to prevent unbounded growth. Runs every ~100 requests
    per tenant to amortize cleanup cost.
    """
    cutoff = now - RATE_LIMIT_CACHE_TTL_SECONDS
    with _buckets_lock:
        stale_keys = [k for k, (_, t) in _tenant_rate_limit_buckets.items() if t < cutoff]
        for k in stale_keys:
            if k in _tenant_rate_limit_buckets:
                del _tenant_rate_limit_buckets[k]


# Request counter for amortized cleanup
_request_count = 0
_request_count_lock = threading.Lock()
_cleanup_interval = 100  # Cleanup every 100 requests

# Threading lock for tenant rate limit buckets
_buckets_lock = threading.Lock()


def _check_tenant_rate_limit(
    tenant_id: str,
    requests_per_minute: int,
) -> tuple[bool, int]:
    """Check if tenant has exceeded rate limit using in-memory store.

    WARNING: This is per-process only and should NOT be used in multi-worker
    deployments. Use _check_redis_rate_limit for distributed rate limiting.

    Args:
        tenant_id: Tenant identifier
        requests_per_minute: Max requests allowed per minute (must be >= 1)

    Returns:
        Tuple of (allowed: bool, retry_after: int)

    Raises:
        ValueError: If requests_per_minute is not positive.
    """
    global _request_count

    if requests_per_minute < 1:
        raise ValueError("requests_per_minute must be >= 1")

    now = time.time()

    # Amortized cleanup: run every N requests instead of every request
    with _request_count_lock:
        _request_count += 1
        should_cleanup = _request_count % _cleanup_interval == 0
    if should_cleanup:
        _evict_stale_rate_limit_entries(now)

    with _buckets_lock:
        count, window_start = _tenant_rate_limit_buckets.get(tenant_id, (0, now))

        # Reset window if expired
        if now - window_start > RATE_LIMIT_WINDOW_SECONDS:
            count = 0
            window_start = now

        # Check limit
        if count >= requests_per_minute:
            window_elapsed = now - window_start
            _tenant_rate_limit_buckets[tenant_id] = (count, window_start)
            allowed = False
        else:
            # Increment and store
            _tenant_rate_limit_buckets[tenant_id] = (count + 1, window_start)
            return True, 0

    # Calculate retry_after outside the lock
    retry_after = int(RATE_LIMIT_WINDOW_SECONDS - window_elapsed) + 1
    return False, max(1, retry_after)


class MultiWorkerRateLimitError(RuntimeError):
    """Raised when rate limiting is enabled in multi-worker mode without Redis."""

    def __init__(self):
        super().__init__(
            "Multi-worker deployment detected but REDIS_URL is not configured. "
            "Rate limiting requires Redis for shared state across workers. "
            "Set REDIS_URL or disable rate limiting with enable_per_tenant_rate_limiting=False."
        )


class GovernanceMiddleware(BaseHTTPMiddleware):
    """Middleware to handle authentication, authorization, and rate limiting (Task 84)."""

    def __init__(
        self,
        app: ASGIApp,
        api_key_resolver: Callable[[str], Awaitable[dict | None]] | None = None,
        jwt_secret: str | None = None,
        on_rate_limit_hit: Callable[[str, str], None] | None = None,
        tenant_settings_lookup: Callable[[UUID], Awaitable[dict | None]] | None = None,
        enable_per_tenant_rate_limiting: bool = True,  # Task 84: Enable by default
        redis_client: redis.Redis | None = None,
    ):
        super().__init__(app)
        self.api_key_lookup = api_key_resolver  # Alias for compatibility
        self.jwt_secret = jwt_secret
        self.on_rate_limit_hit = on_rate_limit_hit
        self.tenant_settings_lookup = tenant_settings_lookup
        self.enable_per_tenant_rate_limiting = enable_per_tenant_rate_limiting

        # Multi-worker safety check (Task 84 Hardening)
        self._redis_client = redis_client or _get_redis_client()
        self._worker_count = _get_worker_count()

        if self.enable_per_tenant_rate_limiting and self._worker_count > 1:
            if not self._redis_client:
                raise MultiWorkerRateLimitError()

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
                    "Rate limit exceeded for tenant %s, retry_after=%ds",
                    tenant_id_str,
                    retry_after,
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

        Uses Redis for distributed rate limiting in multi-worker deployments.
        Falls back to in-memory rate limiting for single-worker dev/test.

        Args:
            tenant_id: Tenant UUID

        Returns:
            Tuple of (allowed: bool, retry_after: int)
        """
        tenant_id_str = str(tenant_id)

        # Try to get tenant-specific limits from settings
        rpm = DEFAULT_REQUESTS_PER_MINUTE
        if self.tenant_settings_lookup:
            try:
                settings = await self.tenant_settings_lookup(tenant_id)
                if settings:
                    rate_limits = settings.get("rate_limits", {})
                    rpm = rate_limits.get("requests_per_minute", DEFAULT_REQUESTS_PER_MINUTE)
            except Exception as e:
                logger.warning("Failed to load tenant settings for rate limit: %s", e)

        # Use Redis for distributed rate limiting in multi-worker mode
        if self._redis_client:
            return await _check_redis_rate_limit(tenant_id_str, rpm, self._redis_client)

        # Fall back to in-memory for single-worker dev/test
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
