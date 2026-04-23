"""
Redis cache layer with tenant isolation.

All cache operations are tenant-scoped to prevent cross-tenant data leakage.
Cache keys follow the pattern: cache:tenant:{tenant_id}:{resource_type}:{resource_id}
"""

import json
import logging
import os
import re
from typing import Any
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


def _sanitize_key_component(component: str) -> str:
    """Sanitize cache key component to prevent injection attacks.
    
    Args:
        component: Raw key component (e.g., entity_id)
    
    Returns:
        Sanitized component with dangerous characters removed
    """
    # Remove path traversal attempts
    component = component.replace("../", "").replace("..\\", "")
    # Remove Redis key separators
    component = component.replace(":", "_")
    # Allow only alphanumeric, dash, underscore
    component = re.sub(r"[^a-zA-Z0-9\-_]", "_", component)
    return component


def _build_cache_key(tenant_id: UUID, resource_type: str, resource_id: str) -> str:
    """Build tenant-scoped cache key.
    
    Args:
        tenant_id: Tenant UUID
        resource_type: Type of resource (e.g., 'entity', 'query')
        resource_id: Resource identifier
    
    Returns:
        Tenant-scoped cache key
    """
    # Sanitize all components
    safe_resource_type = _sanitize_key_component(resource_type)
    safe_resource_id = _sanitize_key_component(resource_id)
    
    return f"cache:tenant:{tenant_id}:{safe_resource_type}:{safe_resource_id}"


# ═══════════════════════════════════════════════════════════════════════════
# Entity Cache Operations
# ═══════════════════════════════════════════════════════════════════════════


async def get_cached_entity(tenant_id: UUID, entity_id: str) -> dict[str, Any] | None:
    """Get cached entity data.
    
    Args:
        tenant_id: Tenant UUID
        entity_id: Entity identifier
    
    Returns:
        Cached entity data or None if not found
    """
    try:
        client = await get_redis_client()
        key = _build_cache_key(tenant_id, "entity", entity_id)
        
        data = await client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.warning(f"Cache get failed for entity {entity_id}: {e}")
        return None


async def set_cached_entity(
    tenant_id: UUID,
    entity_id: str,
    entity_data: dict[str, Any],
    ttl_seconds: int = 3600
) -> bool:
    """Cache entity data with tenant scoping.
    
    Args:
        tenant_id: Tenant UUID
        entity_id: Entity identifier
        entity_data: Entity data to cache
        ttl_seconds: Cache TTL in seconds (default 1 hour)
    
    Returns:
        True if cached successfully
    """
    try:
        client = await get_redis_client()
        key = _build_cache_key(tenant_id, "entity", entity_id)
        
        await client.set(key, json.dumps(entity_data), ex=ttl_seconds)
        return True
    except Exception as e:
        logger.warning(f"Cache set failed for entity {entity_id}: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
# Query Cache Operations
# ═══════════════════════════════════════════════════════════════════════════


async def get_cached_query(tenant_id: UUID, query: str) -> list[dict[str, Any]] | None:
    """Get cached query results.
    
    Args:
        tenant_id: Tenant UUID
        query: Search query string
    
    Returns:
        Cached query results or None if not found
    """
    try:
        client = await get_redis_client()
        # Hash query to create stable key
        query_hash = str(hash(query))
        key = _build_cache_key(tenant_id, "query", query_hash)
        
        data = await client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.warning(f"Cache get failed for query: {e}")
        return None


async def set_cached_query(
    tenant_id: UUID,
    query: str,
    results: list[dict[str, Any]],
    ttl_seconds: int = 300
) -> bool:
    """Cache query results with tenant scoping.
    
    Args:
        tenant_id: Tenant UUID
        query: Search query string
        results: Query results to cache
        ttl_seconds: Cache TTL in seconds (default 5 minutes)
    
    Returns:
        True if cached successfully
    """
    try:
        client = await get_redis_client()
        query_hash = str(hash(query))
        key = _build_cache_key(tenant_id, "query", query_hash)
        
        await client.set(key, json.dumps(results), ex=ttl_seconds)
        return True
    except Exception as e:
        logger.warning(f"Cache set failed for query: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
# Cache Invalidation
# ═══════════════════════════════════════════════════════════════════════════


async def invalidate_tenant_cache(tenant_id: UUID) -> int:
    """Invalidate all cache entries for a tenant.
    
    Args:
        tenant_id: Tenant UUID
    
    Returns:
        Number of keys deleted
    """
    try:
        client = await get_redis_client()
        # Pattern must include tenant_id to prevent cross-tenant invalidation
        pattern = f"cache:tenant:{tenant_id}:*"
        
        keys = await client.keys(pattern)
        if keys:
            return await client.delete(*keys)
        return 0
    except Exception as e:
        logger.error(f"Cache invalidation failed for tenant {tenant_id}: {e}")
        return 0


async def invalidate_cache_pattern(tenant_id: UUID, pattern: str) -> int:
    """Invalidate cache entries matching pattern for a tenant.
    
    Args:
        tenant_id: Tenant UUID
        pattern: Pattern to match (e.g., 'entity:*')
    
    Returns:
        Number of keys deleted
    """
    try:
        client = await get_redis_client()
        # Sanitize pattern and enforce tenant scoping
        safe_pattern = _sanitize_key_component(pattern)
        # Always prefix with tenant scope
        full_pattern = f"cache:tenant:{tenant_id}:{safe_pattern}"
        
        keys = await client.keys(full_pattern)
        if keys:
            return await client.delete(*keys)
        return 0
    except Exception as e:
        logger.error(f"Cache invalidation failed for pattern {pattern}: {e}")
        return 0


async def invalidate_entity_cache(tenant_id: UUID, entity_id: str) -> bool:
    """Invalidate cache for a specific entity.
    
    Args:
        tenant_id: Tenant UUID
        entity_id: Entity identifier
    
    Returns:
        True if invalidated successfully
    """
    try:
        client = await get_redis_client()
        key = _build_cache_key(tenant_id, "entity", entity_id)
        
        await client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache invalidation failed for entity {entity_id}: {e}")
        return False
