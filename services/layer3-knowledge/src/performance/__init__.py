"""Performance package initialization."""

from performance.cache import (
    CacheConfig,
    CacheEntry,
    CacheManager,
    CacheStats,
    CacheStrategy,
    CompressionType,
    MemoryCache,
    PerformanceOptimizer,
    RedisCache,
    SerializationType,
    get_cache_manager,
    get_performance_optimizer,
    initialize_caching,
)

__all__ = [
    "CacheStrategy",
    "CompressionType",
    "SerializationType",
    "CacheEntry",
    "CacheConfig",
    "CacheStats",
    "MemoryCache",
    "RedisCache",
    "CacheManager",
    "PerformanceOptimizer",
    "get_cache_manager",
    "get_performance_optimizer",
    "initialize_caching",
]
