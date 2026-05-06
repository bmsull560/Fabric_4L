from __future__ import annotations

import pytest

from value_fabric.layer3.api.rate_limiter import TenantRateLimiter


@pytest.mark.asyncio
async def test_layer3_tenant_rate_limiter_headers_and_reset_semantics() -> None:
    limiter = TenantRateLimiter(redis_client=None)

    allowed_1, headers_1 = await limiter.check(tenant_id="t1", tier="free", window_seconds=60)
    allowed_2, headers_2 = await limiter.check(tenant_id="t1", tier="free", window_seconds=60)

    assert allowed_1 is True
    assert allowed_2 is True
    assert {"limit", "remaining", "reset"} <= set(headers_1.keys())
    assert headers_2["remaining"] <= headers_1["remaining"]
    assert headers_2["reset"] >= headers_1["reset"]
