"""Unit tests for the shared.testability module.

Tests cover:
- Clock protocol and implementations (SystemClock, FixedClock)
- IDGenerator protocol and implementations (UUIDGenerator, SequentialIDGenerator)
- Cross-layer interface protocols (HTTPClientProtocol, CacheBackendProtocol)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ..clock import Clock, FixedClock, SystemClock
from ..id_generator import IDGenerator, SequentialIDGenerator, UUIDGenerator
from ..interfaces import CacheBackendProtocol, HTTPClientProtocol
from value_fabric.shared.models.typed_dict import TypedDictModel


class _FakeHTTPClient_getResult(TypedDictModel):
    status: int

class _FakeHTTPClient_postResult(TypedDictModel):
    status: int

class _FakeHTTPClient_putResult(TypedDictModel):
    status: int

class _FakeHTTPClient_deleteResult(TypedDictModel):
    status: int


# ═══════════════════════════════════════════════════════════════════════════
# Clock
# ═══════════════════════════════════════════════════════════════════════════


class TestSystemClock:
    def test_now_returns_tz_aware_utc(self):
        clock = SystemClock()
        now = clock.now()
        assert now.tzinfo is not None
        assert now.tzinfo == timezone.utc

    def test_now_returns_current_time(self):
        clock = SystemClock()
        before = datetime.now(timezone.utc)
        now = clock.now()
        after = datetime.now(timezone.utc)
        assert before <= now <= after

    def test_monotonic_increases(self):
        clock = SystemClock()
        t1 = clock.monotonic()
        t2 = clock.monotonic()
        assert t2 >= t1

    def test_satisfies_clock_protocol(self):
        assert isinstance(SystemClock(), Clock)


class TestFixedClock:
    def test_default_epoch(self):
        clock = FixedClock()
        assert clock.now() == datetime(2025, 1, 1, tzinfo=timezone.utc)
        assert clock.monotonic() == 0.0

    def test_custom_initial_time(self):
        t = datetime(2030, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        clock = FixedClock(initial=t, mono_start=100.0)
        assert clock.now() == t
        assert clock.monotonic() == 100.0

    def test_naive_datetime_gets_utc(self):
        t = datetime(2025, 6, 1, 0, 0, 0)
        clock = FixedClock(initial=t)
        assert clock.now().tzinfo == timezone.utc

    def test_deterministic_repeated_calls(self):
        clock = FixedClock()
        assert clock.now() == clock.now()
        assert clock.monotonic() == clock.monotonic()

    def test_advance_updates_both(self):
        clock = FixedClock()
        original_now = clock.now()
        original_mono = clock.monotonic()

        clock.advance(30.0)

        assert clock.now() == original_now + timedelta(seconds=30)
        assert clock.monotonic() == original_mono + 30.0

    def test_advance_zero_is_noop(self):
        clock = FixedClock()
        t = clock.now()
        clock.advance(0.0)
        assert clock.now() == t

    def test_advance_negative_raises(self):
        clock = FixedClock()
        with pytest.raises(ValueError, match="negative"):
            clock.advance(-1.0)

    def test_set_jumps_now(self):
        clock = FixedClock()
        new_time = datetime(2099, 12, 31, tzinfo=timezone.utc)
        clock.set(new_time)
        assert clock.now() == new_time

    def test_set_naive_gets_utc(self):
        clock = FixedClock()
        clock.set(datetime(2030, 1, 1))
        assert clock.now().tzinfo == timezone.utc

    def test_set_does_not_change_monotonic(self):
        clock = FixedClock(mono_start=42.0)
        clock.set(datetime(2030, 1, 1, tzinfo=timezone.utc))
        assert clock.monotonic() == 42.0

    def test_satisfies_clock_protocol(self):
        assert isinstance(FixedClock(), Clock)

    def test_multiple_advances(self):
        clock = FixedClock()
        clock.advance(1.0)
        clock.advance(2.0)
        clock.advance(3.0)
        assert clock.monotonic() == 6.0


# ═══════════════════════════════════════════════════════════════════════════
# IDGenerator
# ═══════════════════════════════════════════════════════════════════════════


class TestUUIDGenerator:
    def test_returns_string(self):
        gen = UUIDGenerator()
        assert isinstance(gen.generate(), str)

    def test_returns_32_char_hex(self):
        gen = UUIDGenerator()
        result = gen.generate()
        assert len(result) == 32
        int(result, 16)  # Should be valid hex

    def test_unique_ids(self):
        gen = UUIDGenerator()
        ids = [gen.generate() for _ in range(50)]
        assert len(set(ids)) == 50

    def test_satisfies_protocol(self):
        assert isinstance(UUIDGenerator(), IDGenerator)


class TestSequentialIDGenerator:
    def test_default_prefix_and_start(self):
        gen = SequentialIDGenerator()
        assert gen.generate() == "id-1"
        assert gen.generate() == "id-2"

    def test_custom_prefix(self):
        gen = SequentialIDGenerator(prefix="evt")
        assert gen.generate() == "evt-1"
        assert gen.generate() == "evt-2"

    def test_custom_start(self):
        gen = SequentialIDGenerator(start=100)
        assert gen.generate() == "id-100"
        assert gen.generate() == "id-101"

    def test_custom_prefix_and_start(self):
        gen = SequentialIDGenerator(prefix="agent", start=0)
        assert gen.generate() == "agent-0"
        assert gen.generate() == "agent-1"

    def test_satisfies_protocol(self):
        assert isinstance(SequentialIDGenerator(), IDGenerator)


# ═══════════════════════════════════════════════════════════════════════════
# Interface protocols — runtime checkable with stub implementations
# ═══════════════════════════════════════════════════════════════════════════


class _FakeHTTPClient:
    """Minimal stub for testing HTTPClientProtocol conformance."""

    async def get(self, url, **kw):
        return _FakeHTTPClient_getResult.model_validate({"status": 200})

    async def post(self, url, **kw):
        return _FakeHTTPClient_postResult.model_validate({"status": 201})

    async def put(self, url, **kw):
        return _FakeHTTPClient_putResult.model_validate({"status": 200})

    async def delete(self, url, **kw):
        return _FakeHTTPClient_deleteResult.model_validate({"status": 204})


class _FakeCacheBackend:
    """Minimal stub for testing CacheBackendProtocol conformance."""

    def __init__(self):
        self._store: dict = {}

    async def get(self, key):
        return self._store.get(key)

    async def set(self, key, value, ttl=None, tags=None):
        self._store[key] = value
        return True

    async def delete(self, key):
        return self._store.pop(key, None) is not None


class TestHTTPClientProtocol:
    def test_fake_satisfies_protocol(self):
        assert isinstance(_FakeHTTPClient(), HTTPClientProtocol)


class TestCacheBackendProtocol:
    def test_fake_satisfies_protocol(self):
        assert isinstance(_FakeCacheBackend(), CacheBackendProtocol)

    @pytest.mark.asyncio
    async def test_fake_round_trip(self):
        cache = _FakeCacheBackend()
        await cache.set("key1", "value1")
        assert await cache.get("key1") == "value1"
        assert await cache.delete("key1") is True
        assert await cache.get("key1") is None
