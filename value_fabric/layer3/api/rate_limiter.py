"""Layer 3 request-limiting adapters and middleware.

Canonical sliding-window state math is implemented in
``value_fabric.shared.rate_limiting.tenant_rate_limiter``. This module must
only compose endpoint/client keys and map canonical decisions into HTTP
headers and response payload fields.
"""

from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from value_fabric.shared.models.typed_dict import TypedDictModel
from value_fabric.shared.rate_limiting.tenant_rate_limiter import SlidingWindowAdapter

from ..logging_config import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware_get_statsResult(TypedDictModel):
    active_clients: Any
    endpoint_limits: Any
    total_requests: Any

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


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI applications."""

    def __init__(
        self,
        app,
        requests_per_minute: int = 100,
        burst_size: int = 200,
        enabled: bool = True,
    ):
        super().__init__(app)
        self.enabled = enabled
        self.rate_limiter = RateLimiter(requests_per_window=burst_size, window_seconds=60)
        self.rate_limiter.set_endpoint_limit("*", requests_per_minute, 60)
        self._configure_endpoint_limits()

    def _configure_endpoint_limits(self) -> None:
        self.rate_limiter.set_endpoint_limit("/health", 300, 60)
        self.rate_limiter.set_endpoint_limit("/health/detailed", 60, 60)
        self.rate_limiter.set_endpoint_limit("/v1/schema/init", 10, 60)
        self.rate_limiter.set_endpoint_limit("/v1/schema/status", 60, 60)
        self.rate_limiter.set_endpoint_limit("/v1/schema/statistics", 30, 60)
        self.rate_limiter.set_endpoint_limit("/v1/ingest", 50, 60)
        self.rate_limiter.set_endpoint_limit("/v1/sync", 30, 60)
        self.rate_limiter.set_endpoint_limit("/v1/search", 200, 60)
        self.rate_limiter.set_endpoint_limit("/v1/graphrag", 100, 60)
        self.rate_limiter.set_endpoint_limit("/v1/analytics", 30, 60)
        self.rate_limiter.set_endpoint_limit("/v1/similarity", 50, 60)
        logger.info("Rate limiting configured for all endpoints")

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.enabled:
            return await call_next(request)

        is_allowed, rate_limit_info = await self.rate_limiter.is_allowed(request)
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
        self.enabled = True
        logger.info("Rate limiting enabled")

    def disable(self) -> None:
        self.enabled = False
        logger.info("Rate limiting disabled")

    def get_stats(self) -> dict[str, int]:
        return RateLimitMiddleware_get_statsResult.model_validate(
            {
                "active_clients": len(self.rate_limiter._clients_seen),
                "total_requests": self.rate_limiter._total_allowed_requests,
                "endpoint_limits": len(self.rate_limiter.endpoint_limits),
            }
        )


def add_rate_limiting(
    app,
    requests_per_minute: int = 100,
    burst_size: int = 200,
    enabled: bool = True,
) -> RateLimitMiddleware:
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


TIER_RATE_LIMITS: dict[str, int] = {
    "free": 60,
    "pro": 600,
    "enterprise": 6000,
    "system": 100_000,
}


class TenantRateLimiter:
    """Layer 3 adapter over canonical shared sliding-window limiter."""

    def __init__(self, redis_client=None) -> None:
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
        tenant_limit = TIER_RATE_LIMITS.get(tier, TIER_RATE_LIMITS["free"])
        tenant_decision = await self._adapter.check(
            key=f"ratelimit:tenant:{tenant_id}:minute", limit=tenant_limit, window_seconds=window_seconds
        )

        key_allowed = True
        key_headers: dict[str, int] = {}
        if api_key_id and key_limit:
            key_decision = await self._adapter.check(
                key=f"ratelimit:apikey:{api_key_id}:minute", limit=key_limit, window_seconds=window_seconds
            )
            key_allowed = key_decision.allowed
            key_headers = {
                "limit": key_decision.limit,
                "remaining": key_decision.remaining,
                "reset": key_decision.reset_epoch,
                "retry_after": key_decision.retry_after or 0,
            }

        allowed = tenant_decision.allowed and key_allowed
        tenant_headers = {
            "limit": tenant_decision.limit,
            "remaining": tenant_decision.remaining,
            "reset": tenant_decision.reset_epoch,
            "retry_after": tenant_decision.retry_after or 0,
        }
        if key_headers:
            headers = {
                "limit": min(tenant_headers["limit"], key_headers["limit"]),
                "remaining": min(tenant_headers["remaining"], key_headers["remaining"]),
                "reset": max(tenant_headers["reset"], key_headers["reset"]),
                "retry_after": max(tenant_headers["retry_after"], key_headers["retry_after"]),
            }
        else:
            headers = tenant_headers

        return allowed, headers
