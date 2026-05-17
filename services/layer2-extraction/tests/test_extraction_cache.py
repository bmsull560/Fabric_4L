"""Unit tests for layer2_extraction.extraction.cache.ExtractionCache."""

from __future__ import annotations

import pytest

from layer2_extraction.extraction.cache import ExtractionCache, _InMemoryLRUCache


# ---------------------------------------------------------------------------
# _InMemoryLRUCache (internal)
# ---------------------------------------------------------------------------

class TestInMemoryLRUCache:
    def test_get_returns_none_for_missing_key(self):
        cache = _InMemoryLRUCache()
        assert cache.get("missing") is None

    def test_set_and_get_round_trip(self):
        cache = _InMemoryLRUCache()
        cache.set("k1", {"result": 42})
        assert cache.get("k1") == {"result": 42}

    def test_set_overwrites_existing_key(self):
        cache = _InMemoryLRUCache()
        cache.set("k1", "first")
        cache.set("k1", "second")
        assert cache.get("k1") == "second"

    def test_evicts_oldest_when_maxsize_exceeded(self):
        cache = _InMemoryLRUCache(maxsize=2)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.set("k3", "v3")  # k1 should be evicted
        assert cache.get("k1") is None
        assert cache.get("k2") == "v2"
        assert cache.get("k3") == "v3"

    def test_get_promotes_key_to_prevent_eviction(self):
        cache = _InMemoryLRUCache(maxsize=2)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.get("k1")  # promote k1
        cache.set("k3", "v3")  # k2 should be evicted, not k1
        assert cache.get("k1") == "v1"
        assert cache.get("k2") is None


# ---------------------------------------------------------------------------
# ExtractionCache (in-memory fallback, no Redis)
# ---------------------------------------------------------------------------

class TestExtractionCacheInMemory:
    @pytest.mark.asyncio
    async def test_get_returns_none_on_cache_miss(self):
        cache = ExtractionCache()  # no redis_url → in-memory fallback
        result = await cache.get("some text", "entities")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get_round_trip(self):
        cache = ExtractionCache()
        value = {"entities": ["A", "B"]}
        await cache.set("some text", "entities", value)
        retrieved = await cache.get("some text", "entities")
        assert retrieved == value

    @pytest.mark.asyncio
    async def test_cache_hit_returns_stored_value(self):
        cache = ExtractionCache()
        call_count = 0

        async def expensive_fn():
            nonlocal call_count
            call_count += 1
            return {"result": "expensive"}

        # First call — miss
        cached = await cache.get("text", "endpoint")
        if cached is None:
            result = await expensive_fn()
            await cache.set("text", "endpoint", result)

        # Second call — hit
        cached = await cache.get("text", "endpoint")
        assert cached == {"result": "expensive"}
        assert call_count == 1  # expensive_fn called only once

    @pytest.mark.asyncio
    async def test_different_endpoints_have_different_keys(self):
        cache = ExtractionCache()
        await cache.set("text", "entities", {"type": "entities"})
        await cache.set("text", "relationships", {"type": "relationships"})
        assert await cache.get("text", "entities") == {"type": "entities"}
        assert await cache.get("text", "relationships") == {"type": "relationships"}

    @pytest.mark.asyncio
    async def test_different_texts_have_different_keys(self):
        cache = ExtractionCache()
        await cache.set("text A", "entities", "result A")
        await cache.set("text B", "entities", "result B")
        assert await cache.get("text A", "entities") == "result A"
        assert await cache.get("text B", "entities") == "result B"

    @pytest.mark.asyncio
    async def test_different_models_have_different_keys(self):
        cache = ExtractionCache()
        await cache.set("text", "entities", "gpt4", model="gpt-4")
        await cache.set("text", "entities", "gpt4mini", model="gpt-4o-mini")
        assert await cache.get("text", "entities", model="gpt-4") == "gpt4"
        assert await cache.get("text", "entities", model="gpt-4o-mini") == "gpt4mini"

    @pytest.mark.asyncio
    async def test_close_does_not_raise_without_redis(self):
        cache = ExtractionCache()
        await cache.close()  # should not raise


class TestExtractionCacheMakeKey:
    def test_same_inputs_produce_same_key(self):
        cache = ExtractionCache()
        k1 = cache._make_key("text", "entities", model="gpt-4", temperature=0.0)
        k2 = cache._make_key("text", "entities", model="gpt-4", temperature=0.0)
        assert k1 == k2

    def test_key_starts_with_l2_cache_prefix(self):
        cache = ExtractionCache()
        key = cache._make_key("text", "entities")
        assert key.startswith("l2_cache:")

    def test_different_temperatures_produce_different_keys(self):
        cache = ExtractionCache()
        k1 = cache._make_key("text", "entities", temperature=0.0)
        k2 = cache._make_key("text", "entities", temperature=0.5)
        assert k1 != k2
