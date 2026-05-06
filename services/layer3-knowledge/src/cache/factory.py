"""CachePort provider selection for OSS substitution pilots.

Legacy cache remains the default provider.  OSS-backed providers must be
constructed explicitly so pilot code cannot change production behavior by
accident.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from .aiocache_adapter import AiocacheCacheAdapter
from .ports import CachePort, LegacyCacheAdapter
from .redis_cache import CacheConfig, RedisCache


class CacheProviderName(StrEnum):
    """Supported CachePort provider identifiers."""

    LEGACY = "legacy"
    AIOCACHE = "aiocache"


def build_cache_port(
    provider: str | CacheProviderName = CacheProviderName.LEGACY,
    *,
    legacy_cache: RedisCache | None = None,
    aiocache_backend: Any | None = None,
    redis_url: str | None = None,
    config: CacheConfig | None = None,
    namespace: str | None = None,
) -> CachePort:
    """Build a CachePort implementation without changing legacy defaults.

    Args:
        provider: Provider name. Defaults to ``legacy``.
        legacy_cache: Existing RedisCache instance to wrap when using legacy.
        aiocache_backend: Optional aiocache backend instance for tests or shadow mode.
        redis_url: Redis URL used only when constructing a legacy RedisCache.
        config: Cache configuration shared by compatible providers.
        namespace: aiocache namespace used only by the aiocache provider.

    Returns:
        A CachePort-compatible provider.
    """

    provider_name = CacheProviderName(provider)
    if provider_name == CacheProviderName.LEGACY:
        if legacy_cache is None:
            if redis_url is None:
                raise ValueError("redis_url or legacy_cache is required for legacy CachePort")
            legacy_cache = RedisCache(redis_url=redis_url, config=config)
        return LegacyCacheAdapter(legacy_cache)

    if provider_name == CacheProviderName.AIOCACHE:
        return AiocacheCacheAdapter(
            cache=aiocache_backend,
            config=config,
            namespace=namespace,
        )

    raise ValueError(f"Unsupported cache provider: {provider}")
