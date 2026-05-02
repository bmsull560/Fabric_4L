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
        fail_open: bool = False,  # SECURITY: Default to fail-closed
    ) -> tuple[bool, dict[str, Any]]:
        """Check if request is allowed under rate limit.

        SECURITY: Defaults to fail-closed (deny requests) when Redis is unavailable
        or errors occur. Set fail_open=True explicitly for public health endpoints.

        Args:
            key: Rate limit key (e.g., tenant_id or api_key)
            limit: Maximum requests in window
            window: Time window in seconds
            fail_open: If True, allow requests on infrastructure failure (less safe)

        Returns:
            Tuple of (allowed, metadata)
        """
        if not self.redis:
            # SECURITY: No Redis = cannot verify rate limit = deny by default
            if fail_open:
                logger.warning("Rate limiting unavailable (Redis not configured), failing open")
                return True, {"limit": limit or self.default_limit, "remaining": 1}
            
            logger.error("Rate limiting unavailable: Redis not configured, denying request")
            return False, {
                "error": "rate_limiting_unavailable",
                "retry_after": 60,
                "limit": limit or self.default_limit,
                "remaining": 0,
            }

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
            # SECURITY: Fail closed on errors - cannot verify rate limit = deny request
            logger.error(f"Rate limit check failed: {e}, denying request")
            if fail_open:
                logger.warning("fail_open=True, allowing request despite error")
                return True, {"limit": limit, "remaining": 1, "error": str(e)}
            return False, {
                "error": "rate_limit_check_failed",
                "retry_after": 60,
                "limit": limit,
                "remaining": 0,
            }

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
