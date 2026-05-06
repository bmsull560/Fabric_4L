"""Cache package initialization."""

from .ports import CachePort, LegacyCacheAdapter, as_cache_port
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
    "RedisCache",
    "CacheManager",
    "LegacyCacheAdapter",
    "RequestDeduplicator",
    "as_cache_port",
    "get_cache_manager",
    "get_request_deduplicator",
    "initialize_cache",
    "cache_result",
]
