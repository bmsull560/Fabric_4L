"""Compatibility exports for tenant-scoped rate limiting."""

from .tenant_rate_limiter import (
    RateLimitConfig,
    RateLimitResult,
    RateLimitScope,
    TenantRateLimiter,
    TenantTier,
    validate_redis_config,
)

__all__ = [
    "RateLimitConfig",
    "RateLimitResult",
    "RateLimitScope",
    "TenantRateLimiter",
    "TenantTier",
    "validate_redis_config",
]
