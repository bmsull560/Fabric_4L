"""Cache test fixtures.

Provides ``make_redis_mock`` / ``mock_redis_client`` with sensible int defaults
for the Redis sorted-set and key/value operations used by
``value_fabric.shared.rate_limiting.tenant_rate_limiter.TenantRateLimiter``.

Without these defaults, ``AsyncMock`` returns unset child mocks for methods like
``zcard``/``zremrangebyscore``, causing ``TypeError: '>=' not supported between
instances of 'AsyncMock' and 'int'`` at ``tenant_rate_limiter.py:324`` and
fail-closed errors elsewhere. See
``reports/TEST_COVERAGE_RUBRIC_AUDIT_2026-05-12.md`` §8 M0-2.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


def make_redis_mock() -> AsyncMock:
    """Return an ``AsyncMock`` for ``redis.asyncio.Redis`` with int defaults.

    Defaults cover every Redis method touched by the rate limiter and entity
    cache code paths under test. Individual tests may override any attribute
    (e.g. ``mock.zcount = custom_zcount``) before invoking the system under
    test — the override semantics match the prior per-test instantiation.
    """
    mock = AsyncMock()
    # Sorted-set ops used by TenantRateLimiter._check_window
    mock.zremrangebyscore = AsyncMock(return_value=0)
    mock.zcard = AsyncMock(return_value=0)
    mock.zcount = AsyncMock(return_value=0)
    mock.zrange = AsyncMock(return_value=[])
    mock.zadd = AsyncMock(return_value=1)
    # Key/value + admin ops used by reset paths and entity cache
    mock.expire = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=0)
    mock.keys = AsyncMock(return_value=[])
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.setex = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=0)
    mock.ttl = AsyncMock(return_value=-1)
    mock.incr = AsyncMock(return_value=1)
    mock.hset = AsyncMock(return_value=1)
    mock.hget = AsyncMock(return_value=None)
    mock.hdel = AsyncMock(return_value=0)
    return mock


@pytest.fixture
def mock_redis_client() -> AsyncMock:
    """Pytest fixture form of :func:`make_redis_mock`."""
    return make_redis_mock()
