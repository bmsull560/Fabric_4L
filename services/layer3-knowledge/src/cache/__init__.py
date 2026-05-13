"""Cache package initialization."""

from cache.aiocache_adapter import AiocacheCacheAdapter
from cache.factory import CacheProviderName, build_cache_port
from cache.ports import CachePort, LegacyCacheAdapter, as_cache_port
from cache.shadow import CacheParityMismatch, ShadowCacheComparator
from cache.redis_cache import (
    CacheConfig,
    CacheKey,
    CacheManager,
    RedisCache,
    RequestDeduplicator,
    cache_result,
    get_cache_manager,
    get_request_deduplicator,
    initialize_cache,
)

__all__ = [
    "CacheConfig",
    "CacheKey",
    "CachePort",
    "AiocacheCacheAdapter",
    "CacheProviderName",
    "RedisCache",
    "CacheManager",
    "LegacyCacheAdapter",
    "CacheParityMismatch",
    "RequestDeduplicator",
    "as_cache_port",
    "build_cache_port",
    "ShadowCacheComparator",
    "get_cache_manager",
    "get_request_deduplicator",
    "initialize_cache",
    "cache_result",
]
