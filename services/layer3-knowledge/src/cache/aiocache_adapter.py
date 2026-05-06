"""aiocache-backed implementation of the stable CachePort contract.

The adapter is intentionally non-default for OSS-1.  It mirrors the current
RedisCache logical behavior at the CachePort boundary while avoiding direct
application imports of aiocache.
"""

from __future__ import annotations

import fnmatch
import json
import logging
from typing import Any

from aiocache import Cache

from .redis_cache import CacheConfig, RedisCache_get_statsResult

logger = logging.getLogger(__name__)


class AiocacheCacheAdapter:
    """CachePort-compatible adapter backed by an aiocache cache instance."""

    provider_name = "aiocache"

    def __init__(
        self,
        cache: Any | None = None,
        config: CacheConfig | None = None,
        *,
        namespace: str | None = None,
    ) -> None:
        self.config = config or CacheConfig()
        self.namespace = namespace
        self._cache = cache or Cache(Cache.MEMORY, namespace=namespace)
        self._known_keys: set[str] = set()
        self._hits = 0
        self._misses = 0
        self._commands = 0

    def _make_key(self, key: str) -> str:
        return f"{self.config.key_prefix}{key}"

    def _ttl(self, ttl: int | None = None) -> int:
        cache_ttl = ttl or self.config.default_ttl
        return min(cache_ttl, self.config.max_ttl)

    def _serialize(self, value: Any) -> str:
        if self.config.serializer == "pickle":
            raise ValueError("pickle serializer is disabled for security — use json or msgpack")
        return json.dumps(value, default=str)

    def _deserialize(self, value: Any) -> Any:
        if value is None:
            return None
        if self.config.serializer == "pickle":
            raise ValueError("pickle serializer is disabled for security — use json or msgpack")
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        if isinstance(value, str):
            return json.loads(value)
        return value

    async def close(self) -> None:
        """Close backend resources when the selected aiocache backend supports it."""

        close = getattr(self._cache, "close", None)
        if close is not None:
            await close()

    async def get(self, key: str) -> Any | None:
        self._commands += 1
        try:
            value = await self._cache.get(self._make_key(key))
            if value is None:
                self._misses += 1
                return None
            self._hits += 1
            return self._deserialize(value)
        except Exception as exc:  # pragma: no cover - defensive parity behavior
            logger.warning("aiocache get error for key %s: %s", key, exc)
            self._misses += 1
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        self._commands += 1
        try:
            prefixed_key = self._make_key(key)
            await self._cache.set(prefixed_key, self._serialize(value), ttl=self._ttl(ttl))
            self._known_keys.add(prefixed_key)
            return True
        except Exception as exc:  # pragma: no cover - defensive parity behavior
            logger.warning("aiocache set error for key %s: %s", key, exc)
            return False

    async def delete(self, key: str) -> bool:
        self._commands += 1
        try:
            prefixed_key = self._make_key(key)
            deleted = await self._cache.delete(prefixed_key)
            self._known_keys.discard(prefixed_key)
            return deleted > 0
        except Exception as exc:  # pragma: no cover - defensive parity behavior
            logger.warning("aiocache delete error for key %s: %s", key, exc)
            return False

    async def clear_pattern(self, pattern: str) -> int:
        self._commands += 1
        prefixed_pattern = self._make_key(pattern)
        matching_keys = [key for key in self._known_keys if fnmatch.fnmatch(key, prefixed_pattern)]
        deleted = 0
        for prefixed_key in matching_keys:
            try:
                result = await self._cache.delete(prefixed_key)
                if result > 0:
                    deleted += 1
                self._known_keys.discard(prefixed_key)
            except Exception as exc:  # pragma: no cover - defensive parity behavior
                logger.warning("aiocache clear-pattern error for key %s: %s", prefixed_key, exc)
        return deleted

    async def exists(self, key: str) -> bool:
        self._commands += 1
        try:
            return bool(await self._cache.exists(self._make_key(key)))
        except Exception as exc:  # pragma: no cover - defensive parity behavior
            logger.warning("aiocache exists error for key %s: %s", key, exc)
            return False

    async def increment(self, key: str, amount: int = 1, ttl: int | None = None) -> int:
        self._commands += 1
        prefixed_key = self._make_key(key)
        raw_current = await self._cache.get(prefixed_key)
        current = self._deserialize(raw_current) if raw_current is not None else 0
        next_value = int(current or 0) + amount
        await self._cache.set(prefixed_key, self._serialize(next_value), ttl=self._ttl(ttl))
        self._known_keys.add(prefixed_key)
        return next_value

    async def get_stats(self) -> dict[str, Any]:
        self._commands += 1
        return RedisCache_get_statsResult.model_validate(
            {
                "connected_clients": 1,
                "used_memory": 0,
                "used_memory_human": "0B",
                "keyspace_hits": self._hits,
                "keyspace_misses": self._misses,
                "total_commands_processed": self._commands,
            }
        )
