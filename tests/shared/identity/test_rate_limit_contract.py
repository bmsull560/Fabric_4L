from __future__ import annotations

from unittest.mock import patch

import pytest

from value_fabric.shared.identity.rate_limiter import RedisRateLimiter
from value_fabric.shared.identity.rate_limiting import RateLimitConfig


@pytest.mark.asyncio
async def test_identity_rate_limiter_contract_fields_and_reset_semantics() -> None:
    limiter = RedisRateLimiter(redis_client=None)
    config = RateLimitConfig(requests_per_minute=2, burst_size=1)

    first = await limiter.check("tenant:abc", config)
    second = await limiter.check("tenant:abc", config)
    third = await limiter.check("tenant:abc", config)

    assert first.allowed is True
    assert second.allowed is True
    assert third.allowed is False
    assert isinstance(third.retry_after, int)
    assert third.retry_after >= 0
    assert third.reset_at >= first.reset_at
    assert {"allowed", "remaining", "reset_at", "retry_after"} <= set(third.__dict__.keys())


@pytest.mark.asyncio
async def test_identity_rate_limiter_redis_failure_closed_mode_blocks() -> None:
    limiter = RedisRateLimiter(redis_client=None)
    config = RateLimitConfig(requests_per_minute=2, burst_size=1)

    async def boom(*, key: str, limit: int, window_seconds: int):
        raise RuntimeError("redis down")

    with patch("value_fabric.shared.identity.rate_limiter.get_rate_limit_fail_mode") as mock_mode:
        from value_fabric.shared.identity.rate_limiting import RateLimitFailMode

        mock_mode.return_value = RateLimitFailMode.CLOSED
        limiter._adapter.check = boom  # type: ignore[method-assign]
        result = await limiter.check("tenant:abc", config)

    assert result.allowed is False
    assert result.retry_after is not None
    assert result.retry_after >= 1


@pytest.mark.asyncio
async def test_identity_rate_limiter_redis_failure_local_fallback_enforces_low_ceiling() -> None:
    limiter = RedisRateLimiter(redis_client=None)
    config = RateLimitConfig(requests_per_minute=100, burst_size=20)

    async def boom(*, key: str, limit: int, window_seconds: int):
        raise RuntimeError("redis down")

    with patch("value_fabric.shared.identity.rate_limiter.get_rate_limit_fail_mode") as mock_mode:
        from value_fabric.shared.identity.rate_limiting import RateLimitFailMode

        mock_mode.return_value = RateLimitFailMode.LOCAL_FALLBACK
        limiter._adapter.check = boom  # type: ignore[method-assign]
        outcomes = [await limiter.check("tenant:abc:key:xyz", config) for _ in range(6)]

    assert all(o.allowed for o in outcomes[:5])
    assert outcomes[5].allowed is False
    assert outcomes[5].retry_after is not None
