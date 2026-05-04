"""
Redis cache layer with tenant isolation.

All cache operations are tenant-scoped to prevent cross-tenant data leakage.
Cache keys follow the pattern: cache:tenant:{tenant_id}:{resource_type}:{resource_id}
"""

import hashlib
import json
import logging
import os
import re
from typing import Any
from uuid import UUID

import redis.asyncio as redis

try:
    from value_fabric.shared.identity.context import require_context
except ImportError:
    # Fallback for when shared package not available
    require_context = None

logger = logging.getLogger(__name__)


def _get_tenant_id() -> str | None:
    """Safely retrieve tenant ID from request context.

    Returns None if context is not available (e.g., in tests or background tasks).
    """
    if not require_context:
        return None
    try:
        return str(require_context().tenant_id)
    except RuntimeError:
        return None

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


def _build_cache_key(resource_type: str, resource_id: str, tenant_id: UUID | None = None) -> str:
    """Build tenant-scoped cache key.
    
    Args:
        resource_type: Type of resource (e.g., 'entity', 'query')
        resource_id: Resource identifier
        tenant_id: Optional tenant UUID (uses context if not provided)
    
    Returns:
        Tenant-scoped cache key
    """
    # Get tenant_id from context if not provided
    if tenant_id is None:
        ctx_tenant_id = _get_tenant_id()
        if ctx_tenant_id is None:
            raise RuntimeError("require_context not available and tenant_id not provided")
        tenant_id = ctx_tenant_id

    # Sanitize all components
    safe_resource_type = _sanitize_key_component(resource_type)
    safe_resource_id = _sanitize_key_component(resource_id)
    
    return f"cache:tenant:{tenant_id}:{safe_resource_type}:{safe_resource_id}"


# ═══════════════════════════════════════════════════════════════════════════
# Entity Cache Operations
# ═══════════════════════════════════════════════════════════════════════════


async def get_cached_entity(entity_id: str, tenant_id: UUID | None = None) -> dict[str, Any] | None:
    """Get cached entity data.
    
    Args:
        entity_id: Entity identifier
        tenant_id: Optional tenant UUID (uses context if not provided)
    
    Returns:
        Cached entity data or None if not found
    """
    try:
        client = await get_redis_client()
        key = _build_cache_key("entity", entity_id, tenant_id)
        
        data = await client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.warning(f"Cache get failed for entity {entity_id}: {e}")
        return None


async def set_cached_entity(
    entity_id: str,
    entity_data: dict[str, Any],
    ttl_seconds: int = 3600,
    tenant_id: UUID | None = None,
) -> bool:
    """Cache entity data with tenant scoping.
    
    Args:
        entity_id: Entity identifier
        entity_data: Entity data to cache
        ttl_seconds: Cache TTL in seconds (default 1 hour)
        tenant_id: Optional tenant UUID (uses context if not provided)
    
    Returns:
        True if cached successfully
    """
    try:
        client = await get_redis_client()
        key = _build_cache_key("entity", entity_id, tenant_id)
        
        await client.set(key, json.dumps(entity_data), ex=ttl_seconds)
        return True
    except Exception as e:
        logger.warning(f"Cache set failed for entity {entity_id}: {e}")
        return False


async def get_cached_entities(
    entity_ids: list[str],
    tenant_id: UUID | None = None,
) -> dict[str, dict[str, Any]]:
    """Get multiple cached entities in a single Redis round-trip.

    Uses ``mget`` to batch all lookups into one network call, which is
    10-50× faster than calling :func:`get_cached_entity` in a loop.

    Args:
        entity_ids: List of entity identifiers to fetch
        tenant_id: Optional tenant UUID (uses context if not provided)

    Returns:
        Mapping of entity_id -> entity data for cache hits only
    """
    if not entity_ids:
        return {}
    try:
        client = await get_redis_client()
        keys = [_build_cache_key("entity", eid, tenant_id) for eid in entity_ids]
        values = await client.mget(*keys)
        result: dict[str, dict[str, Any]] = {}
        for eid, raw in zip(entity_ids, values):
            if raw:
                result[eid] = json.loads(raw)
        return result
    except Exception as e:
        logger.warning(f"Batch cache get failed: {e}")
        return {}


# ═══════════════════════════════════════════════════════════════════════════
# Query Cache Operations
# ═══════════════════════════════════════════════════════════════════════════


async def get_cached_query(query: str, tenant_id: UUID | None = None) -> list[dict[str, Any]] | None:
    """Get cached query results.
    
    Args:
        query: Search query string
        tenant_id: Optional tenant UUID (uses context if not provided)
    
    Returns:
        Cached query results or None if not found
    """
    try:
        client = await get_redis_client()
        # Hash query with SHA-256 for a stable, process-independent key.
        query_hash = hashlib.sha256(query.encode()).hexdigest()
        key = _build_cache_key("query", query_hash, tenant_id)
        
        data = await client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.warning(f"Cache get failed for query: {e}")
        return None


async def set_cached_query(
    query: str,
    results: list[dict[str, Any]],
    ttl_seconds: int = 300,
    tenant_id: UUID | None = None,
) -> bool:
    """Cache query results with tenant scoping.
    
    Args:
        query: Search query string
        results: Query results to cache
        ttl_seconds: Cache TTL in seconds (default 5 minutes)
        tenant_id: Optional tenant UUID (uses context if not provided)
    
    Returns:
        True if cached successfully
    """
    try:
        client = await get_redis_client()
        query_hash = hashlib.sha256(query.encode()).hexdigest()
        key = _build_cache_key("query", query_hash, tenant_id)
        
        await client.set(key, json.dumps(results), ex=ttl_seconds)
        return True
    except Exception as e:
        logger.warning(f"Cache set failed for query: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
# Cache Invalidation
# ═══════════════════════════════════════════════════════════════════════════


async def invalidate_tenant_cache(tenant_id: UUID | None = None) -> int:
    """Invalidate all cache entries for a tenant.
    
    Args:
        tenant_id: Optional tenant UUID (uses context if not provided)
    
    Returns:
        Number of keys deleted
    """
    if tenant_id is None:
        ctx_tenant_id = _get_tenant_id()
        if ctx_tenant_id is None:
            raise RuntimeError("require_context not available and tenant_id not provided")
        tenant_id = ctx_tenant_id

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


async def invalidate_cache_pattern(pattern: str, tenant_id: UUID | None = None) -> int:
    """Invalidate cache entries matching pattern for a tenant.
    
    Args:
        pattern: Pattern to match (e.g., 'entity:*')
        tenant_id: Optional tenant UUID (uses context if not provided)
    
    Returns:
        Number of keys deleted
    """
    if tenant_id is None:
        ctx_tenant_id = _get_tenant_id()
        if ctx_tenant_id is None:
            raise RuntimeError("require_context not available and tenant_id not provided")
        tenant_id = ctx_tenant_id

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


async def invalidate_entity_cache(entity_id: str, tenant_id: UUID | None = None) -> bool:
    """Invalidate cache for a specific entity.
    
    Args:
        entity_id: Entity identifier
        tenant_id: Optional tenant UUID (uses context if not provided)
    
    Returns:
        True if invalidated successfully
    """
    try:
        client = await get_redis_client()
        key = _build_cache_key("entity", entity_id, tenant_id)
        
        await client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache invalidation failed for entity {entity_id}: {e}")
        return False
