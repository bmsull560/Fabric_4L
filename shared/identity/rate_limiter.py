"""Redis-based rate limiting."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """Rate limiter using Redis backend."""

    def __init__(
        self,
        redis_client: Any | None = None,
        default_limit: int = 100,
        default_window: int = 60,
    ):
        self.redis = redis_client
        self.default_limit = default_limit
        self.default_window = default_window

    async def is_allowed(
        self,
        key: str,
        limit: int | None = None,
        window: int | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Check if request is allowed under rate limit.

        Args:
            key: Rate limit key (e.g., tenant_id or api_key)
            limit: Maximum requests in window
            window: Time window in seconds

        Returns:
            Tuple of (allowed, metadata)
        """
        if not self.redis:
            # No Redis, allow all
            return True, {"limit": limit or self.default_limit, "remaining": 1}

        limit = limit or self.default_limit
        window = window or self.default_window

        try:
            # Simple fixed window counter
            current = await self.redis.get(key)
            count = int(current) if current else 0

            if count >= limit:
                return False, {
                    "limit": limit,
                    "remaining": 0,
                    "window": window,
                }

            # Increment counter
            pipe = self.redis.pipeline()
            pipe.incr(key)
            if count == 0:
                pipe.expire(key, window)
            await pipe.execute()

            return True, {
                "limit": limit,
                "remaining": limit - count - 1,
                "window": window,
            }

        except Exception as e:
            logger.warning(f"Rate limit check failed: {e}")
            # Fail open on errors
            return True, {"limit": limit, "remaining": 1, "error": str(e)}

    async def check_tenant_limit(
        self,
        tenant_id: UUID,
        limit: int | None = None,
        window: int | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Check rate limit for a tenant."""
        key = f"ratelimit:tenant:{tenant_id}"
        return await self.is_allowed(key, limit, window)

    async def check_api_key_limit(
        self,
        api_key_id: UUID,
        limit: int | None = None,
        window: int | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Check rate limit for an API key."""
        key = f"ratelimit:apikey:{api_key_id}"
        return await self.is_allowed(key, limit, window)
