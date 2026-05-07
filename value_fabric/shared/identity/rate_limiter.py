"""DEPRECATED compatibility adapter over authoritative identity rate limiter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .authoritative_rate_limiter import AuthoritativeRateLimiter, RateLimitDimensions
from .rate_limiting import RateLimitConfig


@dataclass
class RateLimitResult:
    """Outcome of a rate limit check."""

    allowed: bool
    remaining: int
    reset_at: float
    retry_after: int | None


class RedisRateLimiter:
    """Compatibility facade; delegates all logic to AuthoritativeRateLimiter."""

    def __init__(self, redis_client: Any | None = None, *, fail_open: bool | None = None) -> None:
        self._authoritative = AuthoritativeRateLimiter(redis_client)

    async def check(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        # Legacy key pathway retained for backwards compatibility with tests/callers.
        dim = RateLimitDimensions(tenant_id=key, endpoint_class="legacy")
        decision = await self._authoritative.evaluate(dim, config)
        return RateLimitResult(
            allowed=decision.allowed,
            remaining=decision.remaining,
            reset_at=float(decision.reset_epoch),
            retry_after=decision.retry_after,
        )
