from __future__ import annotations

import threading
import time

from src.shared.identity.oidc import InMemoryOIDCStateStore, RedisOIDCStateStore


class _FakeRedis:
    def __init__(self) -> None:
        self._data: dict[str, tuple[str, float]] = {}
        self._lock = threading.Lock()

    def set(self, key: str, value: str, ex: int) -> None:
        with self._lock:
            self._data[key] = (value, time.time() + ex)

    def getdel(self, key: str):
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            value, expires_at = item
            if time.time() > expires_at:
                del self._data[key]
                return None
            del self._data[key]
            return value


def test_in_memory_store_enforces_one_time_use() -> None:
    store = InMemoryOIDCStateStore(ttl_seconds=60, allow_non_production=True)
    store.store("state-1", "verifier-1")

    assert store.validate_and_consume("state-1") == "verifier-1"
    assert store.validate_and_consume("state-1") is None


def test_in_memory_store_enforces_expiry() -> None:
    store = InMemoryOIDCStateStore(ttl_seconds=1, allow_non_production=True)
    store.store("state-exp", "verifier-exp")

    time.sleep(1.1)
    assert store.validate_and_consume("state-exp") is None


def test_redis_store_concurrent_consume_allows_single_winner() -> None:
    redis_store = RedisOIDCStateStore(redis_client=_FakeRedis(), ttl_seconds=30)
    redis_store.store("state-race", "verifier-race")

    results: list[str | None] = []

    def _consume() -> None:
        results.append(redis_store.validate_and_consume("state-race"))

    threads = [threading.Thread(target=_consume) for _ in range(16)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert results.count("verifier-race") == 1
    assert results.count(None) == 15
