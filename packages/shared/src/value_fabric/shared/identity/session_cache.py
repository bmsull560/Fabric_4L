"""
Session cache with tenant isolation.

Sessions are scoped by both tenant_id and user_id to prevent session hijacking
between tenants.
"""

import json
import logging
import os
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


def _build_session_key(tenant_id: UUID, user_id: UUID) -> str:
    """Build tenant-scoped session key.
    
    Args:
        tenant_id: Tenant UUID
        user_id: User UUID
    
    Returns:
        Tenant-scoped session key
    """
    return f"session:tenant:{tenant_id}:user:{user_id}"


async def get_session(tenant_id: UUID, user_id: UUID) -> dict[str, Any] | None:
    """Get cached session data.
    
    Args:
        tenant_id: Tenant UUID
        user_id: User UUID
    
    Returns:
        Session data or None if not found
    """
    try:
        client = await get_redis_client()
        key = _build_session_key(tenant_id, user_id)
        
        data = await client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.warning(f"Session get failed for user {user_id}: {e}")
        return None


async def set_session(
    tenant_id: UUID,
    user_id: UUID,
    session_data: dict[str, Any],
    ttl_seconds: int = 86400
) -> dict[str, Any]:
    """Cache session data with tenant scoping.
    
    Args:
        tenant_id: Tenant UUID
        user_id: User UUID
        session_data: Session data to cache
        ttl_seconds: Session TTL in seconds (default 24 hours)
    
    Returns:
        The session data that was cached
    """
    try:
        client = await get_redis_client()
        key = _build_session_key(tenant_id, user_id)
        
        await client.set(key, json.dumps(session_data), ex=ttl_seconds)
        return session_data
    except Exception as e:
        logger.warning(f"Session set failed for user {user_id}: {e}")
        return session_data


async def delete_session(tenant_id: UUID, user_id: UUID) -> bool:
    """Delete cached session.
    
    Args:
        tenant_id: Tenant UUID
        user_id: User UUID
    
    Returns:
        True if deleted successfully
    """
    try:
        client = await get_redis_client()
        key = _build_session_key(tenant_id, user_id)
        
        await client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Session delete failed for user {user_id}: {e}")
        return False
