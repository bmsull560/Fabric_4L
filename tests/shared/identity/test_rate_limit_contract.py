from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from value_fabric.shared.identity.middleware import GovernanceMiddleware
from value_fabric.shared.identity.rate_limiter import RedisRateLimiter
from value_fabric.shared.identity.rate_limiter import RateLimitResult
from value_fabric.shared.identity.rate_limiting import RateLimitConfig
from value_fabric.shared.rate_limiting.tenant_rate_limiter import SlidingWindowAdapter


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
async def test_canonical_adapter_denied_reset_tracks_earliest_expiry() -> None:
    adapter = SlidingWindowAdapter(redis_client=None)

    first = await adapter.check(key="tenant:abc:read", limit=1, window_seconds=60)
    denied = await adapter.check(key="tenant:abc:read", limit=1, window_seconds=60)

    assert first.allowed is True
    assert denied.allowed is False
    assert denied.retry_after is not None
    assert 0 <= denied.retry_after <= 60
    assert denied.reset_epoch <= first.reset_epoch


def test_identity_middleware_429_uses_standard_headers_and_body() -> None:
    tenant_id = str(uuid4())
    user_id = str(uuid4())

    class BlockingLimiter:
        async def check(self, key: str, config: RateLimitConfig) -> RateLimitResult:
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=12345.0,
                retry_after=17,
            )

    app = FastAPI()

    @app.get("/protected")
    async def protected() -> dict[str, bool]:
        return {"ok": True}

    app.add_middleware(
        GovernanceMiddleware,
        rate_limiter=BlockingLimiter(),
    )

    with patch(
        "value_fabric.shared.identity.middleware.decode_jwt",
        return_value={"tenant_id": tenant_id, "sub": user_id, "roles": ["read_only"]},
    ):
        response = TestClient(app).get(
            "/protected",
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 429
    assert response.headers["X-RateLimit-Limit"] == "30"
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert response.headers["X-RateLimit-Reset"] == "12345"
    assert response.headers["Retry-After"] == "17"
    assert response.json() == {
        "detail": "Rate limit exceeded",
        "error": "Too many requests",
        "retry_after": 17,
    }


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
