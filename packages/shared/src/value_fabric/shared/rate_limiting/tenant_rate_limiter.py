"""
Tenant-scoped rate limiting (Task 5).

Extends rate limiter to support tenant-level quotas with:
- Tenant tier-based limits (shared/dedicated/enterprise)
- Per-tenant Redis keys for isolation
- Sliding window algorithm
- Admin API for quota management
- Monitoring and alerting integration
"""

import logging
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID

import redis.asyncio as redis
from value_fabric.shared.models.typed_dict import TypedDictModel


class TenantRateLimiter_get_tenant_quota_statusResult(TypedDictModel):
    custom_limits: bool
    limits: dict[str, Any]
    tenant_id: Any
    tier: Any
    usage: Any

logger = logging.getLogger(__name__)

# Redis key TTL multiplier - keys live 2x window size for cleanup buffer
TTL_MULTIPLIER = 2


def validate_redis_config() -> None:
    """Validate Redis configuration for production safety.
    
    Raises:
        ValueError: If Redis is misconfigured in production
    """
    redis_url = os.getenv("REDIS_URL", "")
    environment = os.getenv("ENVIRONMENT", "").lower()
    
    if environment == "production":
        if not redis_url:
            raise ValueError(
                "REDIS_URL is required in production for tenant-scoped rate limiting. "
                "In-memory fallback is not safe for multi-worker deployments."
            )
        
        # Validate URL format
        if not (redis_url.startswith("redis://") or redis_url.startswith("rediss://")):
            raise ValueError(
                f"Invalid REDIS_URL format: {redis_url}. "
                "Must start with redis:// or rediss://"
            )
    elif environment == "development" and not redis_url:
        raise ValueError(
            "REDIS_URL is required in development mode. "
            "Configure Redis or set REDIS_URL=redis://localhost:6379"
        )


class TenantTier(str, Enum):
    """Tenant tier for rate limiting."""
    SHARED = "shared"
    DEDICATED = "dedicated"
    ENTERPRISE = "enterprise"


class RateLimitScope(str, Enum):
    """Scope of rate limit."""
    TENANT = "tenant"  # Per-tenant limit
    USER = "user"  # Per-user limit
    API_KEY = "api_key"  # Per-API-key limit
    ENDPOINT = "endpoint"  # Per-endpoint limit


@dataclass
class RateLimitConfig:
    """Rate limit configuration for a specific scope."""
    
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_allowance: int = 0  # Additional requests allowed in burst


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    
    allowed: bool
    limit: int
    remaining: int
    reset_at: datetime
    retry_after_seconds: int | None = None


# Default rate limits by tenant tier
DEFAULT_TENANT_LIMITS: dict[TenantTier, RateLimitConfig] = {
    TenantTier.SHARED: RateLimitConfig(
        requests_per_minute=100,
        requests_per_hour=5000,
        requests_per_day=100000,
        burst_allowance=20,
    ),
    TenantTier.DEDICATED: RateLimitConfig(
        requests_per_minute=500,
        requests_per_hour=25000,
        requests_per_day=500000,
        burst_allowance=100,
    ),
    TenantTier.ENTERPRISE: RateLimitConfig(
        requests_per_minute=2000,
        requests_per_hour=100000,
        requests_per_day=2000000,
        burst_allowance=500,
    ),
}


class TenantRateLimiter:
    """Tenant-scoped rate limiter with Redis backend.
    
    Features:
    - Sliding window algorithm for accurate rate limiting
    - Multi-level limits (minute/hour/day)
    - Tenant tier-based quotas
    - Burst allowance for traffic spikes
    - Per-tenant Redis key isolation
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        custom_limits: dict[UUID, RateLimitConfig] | None = None,
    ):
        """Initialize tenant rate limiter.
        
        Args:
            redis_client: Redis async client
            custom_limits: Optional custom limits per tenant ID
        """
        self.redis = redis_client
        self.custom_limits = custom_limits or {}
    
    async def check_rate_limit(
        self,
        tenant_id: UUID,
        tenant_tier: TenantTier | None = None,
        endpoint: str = "*",
        user_id: UUID | None = None,
        *,
        tier: TenantTier | None = None,
    ) -> RateLimitResult:
        """Check if request is within rate limit.
        
        Args:
            tenant_id: Tenant UUID
            tenant_tier: Tenant tier (determines default limits)
            endpoint: API endpoint pattern (e.g., "/v1/entities")
            user_id: Optional user ID for user-level limits
            
        Returns:
            RateLimitResult indicating if request is allowed
        """
        # Preserve the canonical tenant_tier API while accepting the historical
        # keyword used by older chaos/security fixtures.  The compatibility
        # mapping remains local to the shared rate-limiter boundary and does
        # not weaken tenant-scoped key construction.
        effective_tier = tenant_tier or tier
        if effective_tier is None:
            raise ValueError("tenant_tier is required for tenant-scoped rate limiting")

        # Get rate limit config
        config = self._get_limit_config(tenant_id, effective_tier)
        
        # Check minute limit (most restrictive)
        minute_result = await self._check_window(
            tenant_id=tenant_id,
            endpoint=endpoint,
            window_seconds=60,
            limit=config.requests_per_minute + config.burst_allowance,
        )
        
        if not minute_result.allowed:
            return minute_result
        
        # Check hour limit
        hour_result = await self._check_window(
            tenant_id=tenant_id,
            endpoint=endpoint,
            window_seconds=3600,
            limit=config.requests_per_hour,
        )
        
        if not hour_result.allowed:
            return hour_result
        
        # Check day limit
        day_result = await self._check_window(
            tenant_id=tenant_id,
            endpoint=endpoint,
            window_seconds=86400,
            limit=config.requests_per_day,
        )
        
        return day_result
    
    async def _check_window(
        self,
        tenant_id: UUID,
        endpoint: str,
        window_seconds: int,
        limit: int,
    ) -> RateLimitResult:
        """Check rate limit for a specific time window using sliding window.
        
        Args:
            tenant_id: Tenant UUID
            endpoint: API endpoint
            window_seconds: Window size in seconds
            limit: Maximum requests in window
            
        Returns:
            RateLimitResult for this window
            
        Raises:
            redis.RedisError: If Redis operations fail
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Redis key: tenant:{tenant_id}:endpoint:{endpoint}:window:{window_seconds}
        key = f"ratelimit:tenant:{tenant_id}:endpoint:{endpoint}:window:{window_seconds}"
        
        try:
            # Use Redis sorted set with timestamps as scores
            # Remove old entries outside window
            await self.redis.zremrangebyscore(
                key,
                min=0,
                max=window_start.timestamp(),
            )
            
            # Count requests in current window
            current_count = await self.redis.zcard(key)
        except (redis.RedisError, TimeoutError, ConnectionError) as e:
            logger.error("Redis error checking tenant rate limit", extra={"tenant_id": str(tenant_id)})
            raise RuntimeError("tenant_rate_limit_unavailable") from e
        
        # Check if limit exceeded
        if current_count >= limit:
            # Calculate when oldest request will expire
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                oldest_timestamp = oldest[0][1]
                reset_at = datetime.fromtimestamp(oldest_timestamp) + timedelta(seconds=window_seconds)
                retry_after = int((reset_at - now).total_seconds())
            else:
                reset_at = now + timedelta(seconds=window_seconds)
                retry_after = window_seconds
            
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_at=reset_at,
                retry_after_seconds=retry_after,
            )
        
        try:
            # Add current request to window with cryptographically secure unique ID
            request_id = f"{now.timestamp()}:{secrets.token_hex(8)}"
            await self.redis.zadd(key, {request_id: now.timestamp()})
            
            # Set expiry on key (cleanup) - TTL is 2x window for buffer
            await self.redis.expire(key, window_seconds * TTL_MULTIPLIER)
        except (redis.RedisError, TimeoutError, ConnectionError) as e:
            logger.error("Redis error updating tenant rate limit", extra={"tenant_id": str(tenant_id)})
            raise RuntimeError("tenant_rate_limit_unavailable") from e
        
        # Calculate reset time (end of current window)
        reset_at = now + timedelta(seconds=window_seconds)
        
        return RateLimitResult(
            allowed=True,
            limit=limit,
            remaining=limit - current_count - 1,
            reset_at=reset_at,
        )
    
    def _get_limit_config(
        self,
        tenant_id: UUID,
        tenant_tier: TenantTier,
    ) -> RateLimitConfig:
        """Get rate limit configuration for tenant.
        
        Args:
            tenant_id: Tenant UUID
            tenant_tier: Tenant tier
            
        Returns:
            RateLimitConfig (custom or default for tier)
        """
        # Check for custom limits first
        if tenant_id in self.custom_limits:
            return self.custom_limits[tenant_id]
        
        # Fall back to tier default
        return DEFAULT_TENANT_LIMITS[tenant_tier]
    
    async def get_tenant_usage(
        self,
        tenant_id: UUID,
        endpoint: str | None = None,
    ) -> dict[str, Any]:
        """Get current rate limit usage for tenant.
        
        Args:
            tenant_id: Tenant UUID
            endpoint: Optional endpoint filter
            
        Returns:
            Usage statistics
        """
        now = datetime.utcnow()
        
        # Get all keys for this tenant
        pattern = f"ratelimit:tenant:{tenant_id}:*"
        if endpoint:
            pattern = f"ratelimit:tenant:{tenant_id}:endpoint:{endpoint}:*"
        
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
        
        usage = {
            "tenant_id": str(tenant_id),
            "timestamp": now.isoformat(),
            "windows": {},
        }
        
        for key in keys:
            # Parse key to extract window size and endpoint
            # Expected format: ratelimit:tenant:{id}:endpoint:{name}:window:{seconds}
            parts = key.decode().split(":")
            try:
                window_seconds = int(parts[-1])
                # Find endpoint name between 'endpoint:' and ':window'
                endpoint_idx = parts.index("endpoint") if "endpoint" in parts else -1
                endpoint_name = parts[endpoint_idx + 1] if endpoint_idx >= 0 and endpoint_idx + 1 < len(parts) else "unknown"
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse rate limit key {key}: {e}")
                continue
            
            # Count requests in window
            window_start = now - timedelta(seconds=window_seconds)
            count = await self.redis.zcount(
                key,
                min=window_start.timestamp(),
                max=now.timestamp(),
            )
            
            window_key = f"{endpoint_name}_{window_seconds}s"
            usage["windows"][window_key] = count
        
        return usage
    
    async def reset_tenant_limits(self, tenant_id: UUID) -> int:
        """Reset all rate limits for a tenant (admin operation).
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            Number of keys deleted
        """
        pattern = f"ratelimit:tenant:{tenant_id}:*"
        
        deleted = 0
        async for key in self.redis.scan_iter(match=pattern):
            await self.redis.delete(key)
            deleted += 1
        
        logger.info(f"Reset {deleted} rate limit keys for tenant {tenant_id}")
        return deleted
    
    async def set_custom_limit(
        self,
        tenant_id: UUID,
        config: RateLimitConfig,
    ) -> None:
        """Set custom rate limit for a tenant (admin operation).
        
        Args:
            tenant_id: Tenant UUID
            config: Custom rate limit configuration
        """
        self.custom_limits[tenant_id] = config
        logger.info(f"Set custom rate limit for tenant {tenant_id}: {config}")
    
    async def get_tenant_quota_status(
        self,
        tenant_id: UUID,
        tenant_tier: TenantTier,
    ) -> dict[str, Any]:
        """Get quota status for tenant.
        
        Args:
            tenant_id: Tenant UUID
            tenant_tier: Tenant tier
            
        Returns:
            Quota status with limits and current usage
        """
        config = self._get_limit_config(tenant_id, tenant_tier)
        usage = await self.get_tenant_usage(tenant_id)
        
        return TenantRateLimiter_get_tenant_quota_statusResult.model_validate({
            "tenant_id": str(tenant_id),
            "tier": tenant_tier.value,
            "limits": {
                "requests_per_minute": config.requests_per_minute,
                "requests_per_hour": config.requests_per_hour,
                "requests_per_day": config.requests_per_day,
                "burst_allowance": config.burst_allowance,
            },
            "usage": usage,
            "custom_limits": tenant_id in self.custom_limits,
        })


