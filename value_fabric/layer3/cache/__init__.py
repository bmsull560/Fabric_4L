"""Cache package initialization."""

from .aiocache_adapter import AiocacheCacheAdapter
from .factory import CacheProviderName, build_cache_port
from .ports import CachePort, LegacyCacheAdapter, as_cache_port
from .shadow import CacheParityMismatch, ShadowCacheComparator
from .redis_cache import (
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
