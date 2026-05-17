"""Shared Identity adapter over canonical runtime request limiting.

Canonical module decision: ``value_fabric.shared.rate_limiting.tenant_rate_limiter``
is the only location that owns sliding-window counter semantics.

Canonical state math lives in ``value_fabric.shared.rate_limiting.tenant_rate_limiter``.
This module keeps identity-facing config/result shapes while delegating checks
through a narrow adapter interface.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from .rate_limiting import RateLimitConfig
from ..rate_limiting.tenant_rate_limiter import SlidingWindowAdapter

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    """Outcome of a rate limit check."""

    allowed: bool
    remaining: int
    reset_at: float
    retry_after: int | None


class RedisRateLimiter:
    """Sliding-window rate limiter backed by Redis sorted sets."""

    def __init__(self, redis_client: Any | None = None) -> None:
        self._adapter = SlidingWindowAdapter(redis_client)

    async def check(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        """Check whether a request is allowed under the given config.

        If Redis is unavailable, the request is allowed and a warning is
        logged (graceful degradation).
        """
        # Support both per-minute and per-hour limits
        if config.requests_per_hour is not None:
            window = 3600  # per-hour window
            limit = config.requests_per_hour
        else:
            window = 60  # per-minute window
            limit = config.requests_per_minute

        try:
            decision = await self._adapter.check(key=key, limit=limit, window_seconds=window)
            return RateLimitResult(
                allowed=decision.allowed,
                remaining=decision.remaining,
                reset_at=float(decision.reset_epoch),
                retry_after=decision.retry_after,
            )
        except Exception as exc:
            logger.warning("Rate limiter Redis call failed, allowing request: %s", exc)
            now = time.time()
            return RateLimitResult(
                allowed=True,
                remaining=-1,
                reset_at=now + window,
                retry_after=None,
            )
