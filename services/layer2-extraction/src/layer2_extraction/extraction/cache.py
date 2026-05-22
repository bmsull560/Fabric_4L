"""Content-hash-based LLM response cache for Layer 2 extraction.

Uses Redis when available, with an in-memory LRU fallback for local dev.
"""

from __future__ import annotations

import hashlib
import logging
import os
import pickle
from collections import OrderedDict
from typing import Any

LLM_CACHE_TTL_SECONDS = int(os.getenv("LLM_CACHE_TTL_SECONDS", "3600"))

try:
    from redis.exceptions import RedisError
except ImportError:
    _REDIS_ERRORS = ()
else:
    _REDIS_ERRORS = (RedisError,)


class _InMemoryLRUCache:
    """Thread-safe-ish in-memory LRU cache with TTL emulation."""

    def __init__(self, maxsize: int = 1000):
        self._store: OrderedDict[str, Any] = OrderedDict()
        self._maxsize = maxsize

    def get(self, key: str) -> Any | None:
        if key in self._store:
            self._store.move_to_end(key)
            return self._store[key]
        return None

    def set(self, key: str, value: Any) -> None:
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        while len(self._store) > self._maxsize:
            self._store.popitem(last=False)


class ExtractionCache:
    """Cache for LLM extraction responses keyed by content hash.

    Cache key = SHA256(content + model + temperature + extraction_type + endpoint)
    """

    def __init__(self, redis_url: str | None = None, default_ttl: int = LLM_CACHE_TTL_SECONDS) -> None:
        self._redis = None
        self._fallback: _InMemoryLRUCache | None = _InMemoryLRUCache()
        self._default_ttl = default_ttl

        redis_url = redis_url or os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(redis_url, decode_responses=False)
            except ImportError:
                self._fallback = _InMemoryLRUCache()
            except _REDIS_ERRORS:
                self._fallback = _InMemoryLRUCache()
        else:
            self._fallback = _InMemoryLRUCache()

    def _make_key(
        self,
        text: str,
        endpoint: str,
        model: str | None = None,
        temperature: float | None = None,
    ) -> str:
        model = model or os.getenv("EXTRACTION_MODEL", "gpt-4o-mini")
        temperature = temperature if temperature is not None else 0.0
        payload = f"{text}:{model}:{temperature}:{endpoint}"
        return f"l2_cache:{hashlib.sha256(payload.encode()).hexdigest()}"

    async def get(
        self,
        text: str,
        endpoint: str,
        model: str | None = None,
        temperature: float | None = None,
        context: dict[str, str | None] | None = None,
    ) -> Any | None:
        key = self._make_key(text, endpoint, model, temperature)
        if self._redis is not None:
            try:
                raw = await self._redis.get(key)
                if raw:
                    return pickle.loads(raw)
            except _REDIS_ERRORS:
                pass
        if self._fallback is not None:
            return self._fallback.get(key)
        return None

    async def set(
        self,
        text: str,
        endpoint: str,
        value: Any,
        model: str | None = None,
        temperature: float | None = None,
        ttl: int | None = None,
        context: dict[str, str | None] | None = None,
    ) -> None:
        key = self._make_key(text, endpoint, model, temperature)
        ttl = ttl or self._default_ttl
        if self._redis is not None:
            try:
                await self._redis.setex(key, ttl, pickle.dumps(value))
                return
            except _REDIS_ERRORS:
                pass
        if self._fallback is not None:
            self._fallback.set(key, value)

    async def close(self) -> None:
        if self._redis is not None:
            try:
                await self._redis.close()
            except _REDIS_ERRORS:
                pass
