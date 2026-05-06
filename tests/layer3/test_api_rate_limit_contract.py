from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from value_fabric.layer3.api.rate_limiter import RateLimiter, RateLimitMiddleware, TenantRateLimiter


@pytest.mark.asyncio
async def test_layer3_tenant_rate_limiter_headers_and_reset_semantics() -> None:
    limiter = TenantRateLimiter(redis_client=None)

    allowed_1, headers_1 = await limiter.check(tenant_id="t1", tier="free", window_seconds=60)
    allowed_2, headers_2 = await limiter.check(tenant_id="t1", tier="free", window_seconds=60)

    assert allowed_1 is True
    assert allowed_2 is True
    assert {"limit", "remaining", "reset", "retry_after"} <= set(headers_1.keys())
    assert headers_2["remaining"] <= headers_1["remaining"]
    assert headers_2["reset"] >= headers_1["reset"]
    assert headers_1["retry_after"] >= 0


class _Req:
    def __init__(self) -> None:
        self.headers = {}
        self.client = type("C", (), {"host": "127.0.0.1"})()
        self.url = type("U", (), {"path": "/v1/search"})()


@pytest.mark.asyncio
async def test_layer3_api_rate_limiter_standardized_contract() -> None:
    limiter = RateLimiter(requests_per_window=2, window_seconds=60)
    req = _Req()

    allowed_1, info_1 = await limiter.is_allowed(req)
    allowed_2, info_2 = await limiter.is_allowed(req)
    allowed_3, info_3 = await limiter.is_allowed(req)

    assert allowed_1 is True
    assert allowed_2 is True
    assert allowed_3 is False
    assert {"limit", "remaining", "reset", "retry_after"} <= set(info_3.keys())
    assert info_2["remaining"] <= info_1["remaining"]
    assert info_3["retry_after"] >= 0
    assert info_3["reset"] <= info_1["reset"]


def test_layer3_middleware_429_uses_standard_headers_and_body() -> None:
    app = FastAPI()

    @app.get("/limited")
    async def limited() -> dict[str, bool]:
        return {"ok": True}

    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=1,
        burst_size=1,
        enabled=True,
    )
    client = TestClient(app)

    first = client.get("/limited")
    second = client.get("/limited")

    assert first.status_code == 200
    assert all(
        header in first.headers
        for header in ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
    )
    assert second.status_code == 429
    assert second.headers["X-RateLimit-Limit"] == "1"
    assert second.headers["X-RateLimit-Remaining"] == "0"
    assert int(second.headers["X-RateLimit-Reset"]) <= int(first.headers["X-RateLimit-Reset"])
    assert int(second.headers["Retry-After"]) >= 0
    assert second.json() == {
        "detail": "Rate limit exceeded",
        "error": "Too many requests",
        "retry_after": int(second.headers["Retry-After"]),
    }
