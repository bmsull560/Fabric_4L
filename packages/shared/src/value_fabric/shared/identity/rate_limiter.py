"""Redis-backed sliding-window rate limiter.

The implementation uses a Lua script executed atomically against Redis so
that the ``ZREMRANGEBYSCORE → ZCARD → ZADD`` sequence is race-free.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from .rate_limiting import RateLimitConfig

logger = logging.getLogger(__name__)

_SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local count = redis.call('ZCARD', key)
if count < limit then
    redis.call('ZADD', key, now, now .. ':' .. math.random(1000000))
    redis.call('EXPIRE', key, window)
    return({1, limit - count - 1})
else
    return({0, 0})
end
"""


@dataclass
class RateLimitResult:
    """Outcome of a rate limit check."""

    allowed: bool
    remaining: int
    reset_at: float
    retry_after: int | None


class RedisRateLimiter:
    """Sliding-window rate limiter backed by Redis sorted sets."""

    def __init__(self, redis_client: Any | None = None, *, fail_open: bool | None = None) -> None:
        self._redis = redis_client
        self._lua_sha: str | None = None
        self._fail_open = _default_fail_open() if fail_open is None else fail_open

    async def check(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        """Check whether a request is allowed under the given config.

        If Redis is unavailable, local/test environments may allow the request
        while production-like environments deny it.
        """
        now = time.time()
        
        # Support both per-minute and per-hour limits
        if config.requests_per_hour is not None:
            window = 3600  # per-hour window
            limit = config.requests_per_hour
        else:
            window = 60  # per-minute window
            limit = config.requests_per_minute

        if self._redis is None:
            logger.warning("Rate limiter Redis client unavailable")
            return self._fallback_result(now=now, window=window)

        try:
            if self._lua_sha is None:
                self._lua_sha = await self._redis.script_load(_SLIDING_WINDOW_LUA)

            result = await self._redis.evalsha(
                self._lua_sha,
                1,
                key,
                int(now * 1000),
                window,
                limit,
            )
            allowed = bool(result[0])
            remaining = int(result[1])
            reset_at = now + window
            retry_after = int(reset_at - now) if not allowed else None
            return RateLimitResult(
                allowed=allowed,
                remaining=remaining,
                reset_at=reset_at,
                retry_after=retry_after,
            )
        except Exception as exc:
            logger.warning("Rate limiter Redis call failed: %s", exc)
            return self._fallback_result(now=now, window=window)

    def _fallback_result(self, *, now: float, window: int) -> RateLimitResult:
        """Return environment-appropriate fallback behavior for Redis failures."""
        if self._fail_open:
            return RateLimitResult(
                allowed=True,
                remaining=-1,
                reset_at=now + window,
                retry_after=None,
            )
        return RateLimitResult(
            allowed=False,
            remaining=0,
            reset_at=now + window,
            retry_after=window,
        )


def _default_fail_open() -> bool:
    """Default Redis fallback policy: fail closed outside local/test."""
    import os

    environment = (
        os.getenv("ENVIRONMENT")
        or os.getenv("ENV")
        or os.getenv("APP_ENV")
        or "development"
    ).strip().lower()
    return environment not in {"prod", "production", "staging", "stage"}
