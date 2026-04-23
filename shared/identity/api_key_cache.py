"""
API key validation cache with tenant isolation.

API key validation results are cached per tenant to prevent key reuse between tenants.
"""

import logging
import os
from uuid import UUID

import redis.asyncio as redis

logger = logging.getLogger(__name__)

# Redis client singleton
_redis_client: redis.Redis | None = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client singleton."""
    global _redis_client
    
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis_client = redis.from_url(redis_url, decode_responses=True)
    
    return _redis_client


def _build_api_key_cache_key(api_key: str, tenant_id: UUID) -> str:
    """Build tenant-scoped API key cache key.
    
    Args:
        api_key: API key string
        tenant_id: Tenant UUID
    
    Returns:
        Tenant-scoped cache key
    """
    # Hash API key for security (don't store raw keys in Redis keys)
    key_hash = str(hash(api_key))
    return f"apikey:tenant:{tenant_id}:hash:{key_hash}"


async def validate_api_key(
    api_key: str,
    tenant_id: UUID,
    is_valid: bool | None = None
) -> bool | None:
    """Validate API key with tenant-scoped caching.
    
    If is_valid is provided, caches the validation result.
    If is_valid is None, checks cache for existing validation.
    
    Args:
        api_key: API key to validate
        tenant_id: Tenant UUID
        is_valid: Validation result to cache, or None to check cache
    
    Returns:
        Cached validation result, or None if not cached
    """
    try:
        client = await get_redis_client()
        key = _build_api_key_cache_key(api_key, tenant_id)
        
        if is_valid is not None:
            # Cache validation result
            await client.set(key, "1" if is_valid else "0", ex=300)  # 5 min TTL
            return is_valid
        else:
            # Check cache
            cached = await client.get(key)
            if cached is not None:
                return cached == "1"
            return None
    except Exception as e:
        logger.warning(f"API key cache operation failed: {e}")
        return None if is_valid is None else is_valid


async def invalidate_api_key_cache(api_key: str, tenant_id: UUID) -> bool:
    """Invalidate cached API key validation.
    
    Args:
        api_key: API key to invalidate
        tenant_id: Tenant UUID
    
    Returns:
        True if invalidated successfully
    """
    try:
        client = await get_redis_client()
        key = _build_api_key_cache_key(api_key, tenant_id)
        
        await client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"API key cache invalidation failed: {e}")
        return False
