"""Authoritative identity rate-limiting orchestration.

This module is the single policy authority for authenticated/protected API
rate limiting in identity middleware and compatibility adapters.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from value_fabric.shared.rate_limiting.tenant_rate_limiter import SlidingWindowAdapter

from .rate_limiting import RateLimitConfig, RateLimitFailMode, get_rate_limit_fail_mode

logger = logging.getLogger(__name__)

# Redis-outage degraded-safe caps. Conservative by design.
DEGRADED_LIMIT_PER_MINUTE = 5


@dataclass(frozen=True)
class RateLimitDimensions:
    tenant_id: str
    endpoint_class: str
    api_key_id: str | None = None
    user_id: str | None = None
    source_ip: str | None = None


@dataclass
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    reset_epoch: int
    retry_after: int | None = None

    def as_headers(self) -> dict[str, str]:
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(0, self.remaining)),
            "X-RateLimit-Reset": str(self.reset_epoch),
        }
        if self.retry_after is not None:
            headers["Retry-After"] = str(max(0, self.retry_after))
        return headers


class AuthoritativeRateLimiter:
    """Single source for identity-facing rate-limit keying and failure policy."""

    def __init__(self, redis_client: Any | None = None) -> None:
        self._adapter = SlidingWindowAdapter(redis_client)
        self._fallback = SlidingWindowAdapter(redis_client=None)

    def build_dimension_keys(self, dimensions: RateLimitDimensions) -> list[str]:
        keys = [f"ratelimit:tenant:{dimensions.tenant_id}:{dimensions.endpoint_class}"]
        if dimensions.api_key_id:
            keys.append(
                f"ratelimit:tenant:{dimensions.tenant_id}:apikey:{dimensions.api_key_id}:{dimensions.endpoint_class}"
            )
        if dimensions.user_id:
            keys.append(
                f"ratelimit:tenant:{dimensions.tenant_id}:user:{dimensions.user_id}:{dimensions.endpoint_class}"
            )
        if dimensions.source_ip:
            keys.append(
                f"ratelimit:tenant:{dimensions.tenant_id}:ip:{dimensions.source_ip}:{dimensions.endpoint_class}"
            )
        return keys

    async def evaluate(self, dimensions: RateLimitDimensions, config: RateLimitConfig) -> RateLimitDecision:
        limit = config.requests_per_hour if config.requests_per_hour is not None else config.requests_per_minute
        window_seconds = 3600 if config.requests_per_hour is not None else 60
        keys = self.build_dimension_keys(dimensions)
        try:
            decisions = [
                await self._adapter.check(key=key, limit=limit, window_seconds=window_seconds) for key in keys
            ]
        except Exception as exc:
            return await self._handle_backend_failure(keys=keys, window_seconds=window_seconds, error=exc)

        winner = min(decisions, key=lambda d: d.remaining)
        allowed = all(d.allowed for d in decisions)
        retry_after = max((d.retry_after or 0) for d in decisions) if not allowed else winner.retry_after
        return RateLimitDecision(
            allowed=allowed,
            limit=winner.limit,
            remaining=winner.remaining,
            reset_epoch=winner.reset_epoch,
            retry_after=retry_after,
        )

    async def _handle_backend_failure(self, *, keys: list[str], window_seconds: int, error: Exception) -> RateLimitDecision:
        mode = get_rate_limit_fail_mode()
        logger.error(
            "rate_limit_backend_failure",
            extra={"mode": mode.value, "keys": keys, "error_type": type(error).__name__},
        )

        if mode is RateLimitFailMode.LOCAL_FALLBACK:
            decisions = [
                await self._fallback.check(key=key, limit=DEGRADED_LIMIT_PER_MINUTE, window_seconds=60)
                for key in keys
            ]
            winner = min(decisions, key=lambda d: d.remaining)
            allowed = all(d.allowed for d in decisions)
            retry_after = max((d.retry_after or 0) for d in decisions) if not allowed else winner.retry_after
            return RateLimitDecision(
                allowed=allowed,
                limit=winner.limit,
                remaining=winner.remaining,
                reset_epoch=winner.reset_epoch,
                retry_after=retry_after,
            )

        now = int(time.time())
        retry_after = max(1, min(window_seconds, 60))
        return RateLimitDecision(
            allowed=False,
            limit=0,
            remaining=0,
            reset_epoch=now + retry_after,
            retry_after=retry_after,
        )
