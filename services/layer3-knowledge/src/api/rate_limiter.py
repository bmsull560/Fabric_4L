"""Layer 3 request-limiting adapters and middleware.

Canonical sliding-window state math is implemented in
``value_fabric.shared.rate_limiting.tenant_rate_limiter``. This module must
only compose endpoint/client keys and map canonical decisions into HTTP
headers and response payload fields.
"""

import time
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from value_fabric.shared.models.typed_dict import TypedDictModel

from ..logging_config import get_logger
from value_fabric.shared.rate_limiting.tenant_rate_limiter import SlidingWindowAdapter


class RateLimitMiddleware_get_statsResult(TypedDictModel):
    active_clients: Any
    endpoint_limits: Any
    total_requests: Any

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter adapter that delegates counting to canonical state math."""

    def __init__(
        self,
        requests_per_window: int = 100,
        window_seconds: int = 60,
        redis_client: Any | None = None,
    ):
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.endpoint_limits: dict[str, tuple[int, int]] = {}
        self._adapter = SlidingWindowAdapter(redis_client)
        self._clients_seen: set[str] = set()
        self._total_allowed_requests = 0

    def set_endpoint_limit(self, endpoint: str, requests: int, seconds: int) -> None:
        self.endpoint_limits[endpoint] = (requests, seconds)
        logger.info(f"Set rate limit for {endpoint}: {requests}/{seconds}s")

    def _get_client_key(self, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        return request.client.host if request.client else "unknown"

    def _get_endpoint_limit(self, path: str) -> tuple[int, int]:
        for endpoint_pattern, (requests, seconds) in self.endpoint_limits.items():
            if endpoint_pattern in path:
                return requests, seconds
        return self.requests_per_window, self.window_seconds

    async def is_allowed(self, request: Request) -> tuple[bool, dict[str, int]]:
        current_time = time.time()
        client_key = self._get_client_key(request)
        path = request.url.path
        requests_limit, window_seconds = self._get_endpoint_limit(path)
        decision = await self._adapter.check(
            key=f"ratelimit:layer3:{client_key}:{path}:{window_seconds}",
            limit=requests_limit,
            window_seconds=window_seconds,
        )

        self._clients_seen.add(client_key)
        if decision.allowed:
            self._total_allowed_requests += 1

        return decision.allowed, {
            "limit": decision.limit,
            "remaining": decision.remaining,
            "reset": decision.reset_epoch,
            "retry_after": decision.retry_after or window_seconds,
        }


class RateLimitMiddleware_get_statsResult(TypedDictModel):
    active_clients: Any
    endpoint_limits: Any
    total_requests: Any

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter using sliding window algorithm."""

    def __init__(
        self,
        requests_per_window: int = 100,
        window_seconds: int = 60,
    ):
        """Initialize rate limiter.

        Args:
            requests_per_window: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.cleanup_interval = cleanup_interval

        # Client request tracking: {client_ip: deque of timestamps}
        self.client_requests: dict[str, deque] = defaultdict(lambda: deque())

        # Endpoint-specific limits: {endpoint: (requests, seconds)}
        self.endpoint_limits: dict[str, tuple[int, int]] = {}

        # Last cleanup time
        self.last_cleanup = time.time()

        # Lock for thread safety
        self._lock = asyncio.Lock()

    def set_endpoint_limit(self, endpoint: str, requests: int, seconds: int) -> None:
        """Set custom limit for specific endpoint.

        Args:
            endpoint: Endpoint path pattern
            requests: Max requests per window
            seconds: Window size in seconds
        """
        self.endpoint_limits[endpoint] = (requests, seconds)
        logger.info(f"Set rate limit for {endpoint}: {requests}/{seconds}s")

    def _get_client_key(self, request: Request) -> str:
        """Get client identifier for rate limiting.

        Args:
            request: FastAPI request

        Returns:
            Client key (IP address)
        """
        # Try to get real IP from headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to client IP
        return request.client.host if request.client else "unknown"

    def _get_endpoint_limit(self, path: str) -> tuple[int, int]:
        """Get rate limit for specific endpoint.

        Args:
            path: Request path

        Returns:
            Tuple of (requests, seconds)
        """
        for endpoint_pattern, (requests, seconds) in self.endpoint_limits.items():
            if endpoint_pattern in path:
                return requests, seconds

        return self.requests_per_window, self.window_seconds

    def _cleanup_old_requests(self, current_time: float) -> None:
        """Clean up old request timestamps.

        Args:
            current_time: Current timestamp
        """
        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        cutoff_time = current_time - self.window_seconds

        # Clean up each client's request history
        for client_ip, requests in list(self.client_requests.items()):
            while requests and requests[0] <= cutoff_time:
                requests.popleft()

            # Remove empty client entries
            if not requests:
                del self.client_requests[client_ip]

        self.last_cleanup = current_time
        logger.debug(
            f"Rate limiter cleanup completed. Active clients: {len(self.client_requests)}"
        )

    async def is_allowed(self, request: Request) -> tuple[bool, dict[str, int]]:
        """Check if request is allowed based on rate limits.

        Args:
            request: FastAPI request

        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        async with self._lock:
            current_time = time.time()
            client_key = self._get_client_key(request)
            path = request.url.path

            # Get endpoint-specific limits
            requests_limit, window_seconds = self._get_endpoint_limit(path)

            # Clean up old requests
            self._cleanup_old_requests(current_time)

            # Get client request history
            client_requests = self.client_requests[client_key]
            cutoff_time = current_time - window_seconds

            # Remove old requests from window
            while client_requests and client_requests[0] <= cutoff_time:
                client_requests.popleft()

            # Check if limit exceeded
            current_requests = len(client_requests)
            is_allowed = current_requests < requests_limit

            if is_allowed:
                # Add current request
                client_requests.append(current_time)

            # Calculate rate limit info
            reset_time = int(current_time + window_seconds)
            remaining_requests = max(0, requests_limit - current_requests)

            rate_limit_info = {
                "limit": requests_limit,
                "remaining": remaining_requests,
                "reset": reset_time,
                "retry_after": window_seconds if not is_allowed else 0,
            }

            return is_allowed, rate_limit_info


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI applications."""

    def __init__(
        self,
        app,
        requests_per_minute: int = 100,
        burst_size: int = 200,
        enabled: bool = True,
    ):
        """Initialize rate limiting middleware.

        Args:
            app: FastAPI application
            requests_per_minute: Base rate limit per minute
            burst_size: Maximum burst size
            enabled: Whether rate limiting is enabled
        """
        super().__init__(app)
        self.enabled = enabled

        # Initialize rate limiter with 1-minute window
        self.rate_limiter = RateLimiter(requests_per_window=burst_size, window_seconds=60)

        # Set base rate limit (per minute)
        self.rate_limiter.set_endpoint_limit("*", requests_per_minute, 60)

        # Configure stricter limits for sensitive endpoints
        self._configure_endpoint_limits()

    def _configure_endpoint_limits(self) -> None:
        """Configure rate limits for different endpoint categories."""
        # Health checks - more lenient
        self.rate_limiter.set_endpoint_limit("/health", 300, 60)
        self.rate_limiter.set_endpoint_limit("/health/detailed", 60, 60)

        # Schema operations - stricter
        self.rate_limiter.set_endpoint_limit("/v1/schema/init", 10, 60)
        self.rate_limiter.set_endpoint_limit("/v1/schema/status", 60, 60)
        self.rate_limiter.set_endpoint_limit("/v1/schema/statistics", 30, 60)

        # Ingestion operations - moderate
        self.rate_limiter.set_endpoint_limit("/v1/ingest", 50, 60)
        self.rate_limiter.set_endpoint_limit("/v1/sync", 30, 60)

        # Search operations - higher limit for user experience
        self.rate_limiter.set_endpoint_limit("/v1/search", 200, 60)
        self.rate_limiter.set_endpoint_limit("/v1/graphrag", 100, 60)

        # Analytics operations - moderate
        self.rate_limiter.set_endpoint_limit("/v1/analytics", 30, 60)
        self.rate_limiter.set_endpoint_limit("/v1/similarity", 50, 60)

        logger.info("Rate limiting configured for all endpoints")

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request through rate limiting."""
        if not self.enabled:
            return await call_next(request)

        # Check rate limit
        is_allowed, rate_limit_info = await self.rate_limiter.is_allowed(request)

        # Add rate limit headers to all responses
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset"])

        if not is_allowed:
            logger.warning(
                "Rate limit exceeded",
                client_ip=self.rate_limiter._get_client_key(request),
                path=request.url.path,
                limit=rate_limit_info["limit"],
                retry_after=rate_limit_info["retry_after"],
            )

            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "error": "Too many requests",
                    "retry_after": rate_limit_info["retry_after"],
                },
            )
            response.headers["Retry-After"] = str(rate_limit_info["retry_after"])
            response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset"])

            return response

        return response

    def enable(self) -> None:
        """Enable rate limiting."""
        self.enabled = True
        logger.info("Rate limiting enabled")

    def disable(self) -> None:
        """Disable rate limiting."""
        self.enabled = False
        logger.info("Rate limiting disabled")

    def get_stats(self) -> dict[str, int]:
        """Get rate limiting statistics.

        Returns:
            Dictionary with rate limiting stats
        """
        return RateLimitMiddleware_get_statsResult.model_validate({
            "active_clients": len(self.rate_limiter._clients_seen),
            "total_requests": self.rate_limiter._total_allowed_requests,
            "endpoint_limits": len(self.rate_limiter.endpoint_limits),
        })


def add_rate_limiting(
    app,
    requests_per_minute: int = 100,
    burst_size: int = 200,
    enabled: bool = True,
) -> RateLimitMiddleware:
    """Add rate limiting middleware to FastAPI application.

    Args:
        app: FastAPI application
        requests_per_minute: Base rate limit per minute
        burst_size: Maximum burst size
        enabled: Whether rate limiting is enabled

    Returns:
        Rate limit middleware instance
    """
    middleware = RateLimitMiddleware(
        app,
        requests_per_minute=requests_per_minute,
        burst_size=burst_size,
        enabled=enabled,
    )

    logger.info(
        "Rate limiting middleware added",
        extra={
            "requests_per_minute": requests_per_minute,
            "burst_size": burst_size,
            "enabled": enabled,
        },
    )

    return middleware


# ---------------------------------------------------------------------------
# Tenant-scoped rate limiter adapter (delegates to canonical shared module)
# ---------------------------------------------------------------------------

# Default request limits per subscription tier (requests per minute).
TIER_RATE_LIMITS: dict[str, int] = {
    "free": 60,
    "pro": 600,
    "enterprise": 6000,
    "system": 100_000,  # Internal service calls
}


class TenantRateLimiter:
    """Layer 3 adapter over canonical shared sliding-window limiter."""

    def __init__(self, redis_client=None) -> None:
        from value_fabric.shared.rate_limiting.tenant_rate_limiter import SlidingWindowAdapter
        self._adapter = SlidingWindowAdapter(redis_client)

    async def check(
        self,
        *,
        tenant_id,
        tier: str = "free",
        api_key_id: str | None = None,
        key_limit: int | None = None,
        window_seconds: int = 60,
    ) -> tuple[bool, dict[str, int]]:
        """Check whether the tenant (and optionally API key) is within limits.

        Returns ``(allowed, headers_dict)`` where ``headers_dict`` contains
        the values for ``X-RateLimit-*`` response headers.
        """
        tenant_limit = TIER_RATE_LIMITS.get(tier, TIER_RATE_LIMITS["free"])

        # Check tenant-level limit
        tenant_key = f"ratelimit:tenant:{tenant_id}:minute"
        tenant_decision = await self._adapter.check(
            key=tenant_key, limit=tenant_limit, window_seconds=window_seconds
        )

        # Check per-API-key limit if a key-specific override exists
        key_allowed = True
        key_headers: dict[str, int] = {}
        if api_key_id and key_limit:
            key_cache_key = f"ratelimit:apikey:{api_key_id}:minute"
            key_decision = await self._adapter.check(
                key=key_cache_key, limit=key_limit, window_seconds=window_seconds
            )
            key_allowed = key_decision.allowed
            key_headers = {
                "limit": key_decision.limit,
                "remaining": key_decision.remaining,
                "reset": key_decision.reset_epoch,
            }

        allowed = tenant_decision.allowed and key_allowed

        # Return the most restrictive headers
        tenant_headers = {
            "limit": tenant_decision.limit,
            "remaining": tenant_decision.remaining,
            "reset": tenant_decision.reset_epoch,
        }
        if key_headers:
            headers = {
                "limit": min(tenant_headers["limit"], key_headers["limit"]),
                "remaining": min(tenant_headers["remaining"], key_headers["remaining"]),
                "reset": max(tenant_headers["reset"], key_headers["reset"]),
            }
        else:
            headers = tenant_headers

        return allowed, headers
