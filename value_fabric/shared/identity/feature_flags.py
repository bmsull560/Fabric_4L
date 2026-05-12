"""Shared feature flag evaluator used by Layer 4 runtime and tests.

The Layer 4 service owns feature flag persistence, while this module owns the
runtime evaluation contract shared by workflows and startup wiring.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

FeatureFlagLookup = Callable[[str, UUID | None], Awaitable[Any | None]]

_CACHE_TTL_SECONDS = 30
_redis_client: Any | None = None
_lookup: FeatureFlagLookup | None = None


def init_feature_flags(redis_client: Any | None) -> None:
    """Configure the optional Redis cache used by feature flag evaluation."""

    global _redis_client
    _redis_client = redis_client


def register_feature_flag_lookup(callback: FeatureFlagLookup | None) -> None:
    """Register the Layer 4 DB-backed feature flag lookup callback."""

    global _lookup
    _lookup = callback


async def is_enabled(
    flag_key: str,
    tenant_id: UUID | None,
    user_id: str | None = None,
) -> bool:
    """Evaluate a feature flag using cache, lookup callback, and rollout bucket."""

    cache_key = _cache_key(flag_key, tenant_id)
    cached = await _cache_get(cache_key)
    flag_data = cached if cached is not None else await _lookup_flag(flag_key, tenant_id)

    if flag_data is None:
        return False

    if cached is None:
        await _cache_set(cache_key, flag_data)

    enabled = bool(_get_value(flag_data, "enabled", False))
    if not enabled:
        return False

    rollout_percentage = int(_get_value(flag_data, "rollout_percentage", 100) or 0)
    if rollout_percentage >= 100:
        return True
    if rollout_percentage <= 0:
        return False

    return _rollout_bucket(flag_key, tenant_id, user_id) < rollout_percentage


async def _lookup_flag(flag_key: str, tenant_id: UUID | None) -> Any | None:
    if _lookup is None:
        return None
    return await _lookup(flag_key, tenant_id)


async def _cache_get(cache_key: str) -> dict[str, Any] | None:
    if _redis_client is None:
        return None

    try:
        raw_value = await _redis_client.get(cache_key)
    except Exception:
        return None

    if raw_value is None:
        return None
    if isinstance(raw_value, bytes):
        raw_value = raw_value.decode("utf-8")

    try:
        value = json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        return None

    return value if isinstance(value, dict) else None


async def _cache_set(cache_key: str, flag_data: Any) -> None:
    if _redis_client is None:
        return

    payload = {
        "enabled": bool(_get_value(flag_data, "enabled", False)),
        "rollout_percentage": int(_get_value(flag_data, "rollout_percentage", 100) or 0),
    }
    try:
        await _redis_client.setex(cache_key, _CACHE_TTL_SECONDS, json.dumps(payload))
    except Exception:
        return


def _cache_key(flag_key: str, tenant_id: UUID | None) -> str:
    tenant_part = str(tenant_id) if tenant_id is not None else "platform"
    return f"feature_flag:{tenant_part}:{flag_key}"


def _get_value(flag_data: Any, key: str, default: Any) -> Any:
    if isinstance(flag_data, dict):
        return flag_data.get(key, default)
    return getattr(flag_data, key, default)


def _rollout_bucket(flag_key: str, tenant_id: UUID | None, user_id: str | None) -> int:
    subject = user_id or (str(tenant_id) if tenant_id is not None else "anonymous")
    digest = hashlib.sha256(f"{flag_key}:{tenant_id}:{subject}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100
