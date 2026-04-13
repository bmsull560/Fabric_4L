"""Feature flag evaluation with Redis caching and deterministic bucketing.

This module lives in ``shared/identity`` and therefore must not import
heavy FastAPI or SQLAlchemy dependencies.  Redis is accepted as an
optional duck-typed client via ``init_feature_flags()``.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Awaitable, Callable, Optional
from uuid import UUID

from .isolation import tenant_cache_key

logger = logging.getLogger(__name__)

_feature_flags_redis: Any | None = None
_flag_lookup_callback: Callable[[str, UUID | None], Awaitable[dict[str, Any] | None]] | None = None


def init_feature_flags(redis_client: Any | None) -> None:
    """Set the module-level Redis client used for caching flag lookups."""
    global _feature_flags_redis
    _feature_flags_redis = redis_client


def get_feature_flags_redis() -> Any | None:
    """Return the currently configured Redis client, if any."""
    return _feature_flags_redis


def register_feature_flag_lookup(
    fn: Callable[[str, UUID | None], Awaitable[dict[str, Any] | None]],
) -> None:
    """Register an async callback that resolves a flag key to flag data.

    The callback receives ``(flag_key, tenant_id)`` and should return a dict
    with at least ``enabled`` (bool) and ``rollout_percentage`` (int), or
    ``None`` if the flag does not exist.  The consuming layer (e.g.
    layer4-agents) is expected to register its DB-backed lookup here during
    lifespan startup.
    """
    global _flag_lookup_callback
    _flag_lookup_callback = fn


async def is_enabled(
    flag_key: str,
    tenant_id: UUID | None,
    user_id: str | None = None,
) -> bool:
    """Evaluate whether a feature flag is enabled for the given context.

    Lookup order:
      1. Tenant-specific flag (when ``tenant_id`` is not None)
      2. Platform-wide flag (``tenant_id=None``)
      3. Default to ``False``

    If ``enabled=True`` but ``rollout_percentage < 100``, deterministic
    bucketing based on ``tenant_id:user_id:flag_key`` decides inclusion.

    Redis caching is used with a 30-second TTL.  If Redis is unavailable,
    the function degrades gracefully and performs the lookup via the
    registered callback (if any).
    """
    redis = _feature_flags_redis
    cache_key = _cache_key(flag_key, tenant_id)

    # Try cache first
    if redis is not None:
        try:
            cached = await redis.get(cache_key)
            if cached is not None:
                if isinstance(cached, bytes):
                    cached = cached.decode("utf-8")
                try:
                    data = json.loads(cached)
                    return _evaluate_flag(data, tenant_id, user_id, flag_key)
                except json.JSONDecodeError:
                    pass
        except Exception as exc:
            logger.warning("Feature flag Redis cache read failed: %s", exc)

    # Cache miss or Redis unavailable — ask the registered lookup callback
    flag_data: dict[str, Any] | None = None
    if _flag_lookup_callback is not None:
        try:
            flag_data = await _flag_lookup_callback(flag_key, tenant_id)
        except Exception as exc:
            logger.warning("Feature flag lookup callback failed: %s", exc)

    # Populate cache
    if redis is not None and flag_data is not None:
        try:
            await redis.setex(cache_key, 30, json.dumps(flag_data, default=str))
        except Exception as exc:
            logger.warning("Feature flag Redis cache write failed: %s", exc)

    if flag_data is None:
        return False

    return _evaluate_flag(flag_data, tenant_id, user_id, flag_key)


def _cache_key(flag_key: str, tenant_id: UUID | None) -> str:
    if tenant_id is not None:
        return tenant_cache_key(tenant_id, "feature_flags", flag_key)
    return f"feature_flags:platform:{flag_key}"


def _evaluate_flag(
    flag_data: dict[str, Any],
    tenant_id: UUID | None,
    user_id: str | None,
    flag_key: str,
) -> bool:
    """Apply deterministic rollout bucketing to cached or fetched flag data."""
    if not flag_data.get("enabled", False):
        return False

    pct = flag_data.get("rollout_percentage", 0)
    if pct >= 100:
        return True

    seed = f"{tenant_id}:{user_id or 'anon'}:{flag_key}"
    bucket = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) % 100
    return bucket < pct
