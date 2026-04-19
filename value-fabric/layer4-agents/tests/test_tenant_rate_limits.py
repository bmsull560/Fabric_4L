"""Tests for per-tenant rate limiting (Task 84).

Validates:
- TENANT scope rate limiting works
- Per-tenant limits from settings JSONB
- 429 responses include Retry-After header
- Tenant A cannot consume Tenant B's quota
- Rate limit events are logged (not audited)
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

# Module-level imports to avoid repetition in test methods
from fastapi import Request
from shared.identity.middleware import (
    GovernanceMiddleware,
    _check_tenant_rate_limit,
    _tenant_rate_limit_buckets,
)
from src.tenants.settings_schema import (
    RateLimitSettings,
    TenantSettings,
    get_tenant_rate_limits,
)
from starlette.datastructures import Headers


@pytest.fixture(autouse=True)
def clear_rate_limit_buckets():
    """Clear global rate limit buckets before and after each test."""
    _tenant_rate_limit_buckets.clear()
    yield
    _tenant_rate_limit_buckets.clear()


class TestTenantRateLimiting:
    """Test per-tenant rate limiting functionality."""

    def test_tenant_scope_added_to_enum(self):
        """Verify TENANT scope exists in RateLimitScope enum."""
        from src.rate_limiting.manager import RateLimitScope

        assert hasattr(RateLimitScope, "TENANT")
        assert RateLimitScope.TENANT == "tenant"

    def test_tenant_settings_schema_validation(self):
        """Verify tenant settings schema validates rate limits correctly."""
        # Valid settings
        settings = {"rate_limits": {"requests_per_minute": 200, "burst": 400}}
        tenant_settings = TenantSettings.from_json(settings)
        assert tenant_settings.rate_limits.requests_per_minute == 200
        assert tenant_settings.rate_limits.burst == 400

        # Invalid: burst < requests_per_minute should fail
        with pytest.raises(ValueError):
            RateLimitSettings(requests_per_minute=200, burst=100)

    def test_tenant_settings_defaults(self):
        """Verify defaults are applied when settings missing."""
        # Empty settings
        limits = get_tenant_rate_limits({})
        assert limits.requests_per_minute == 120  # Default
        assert limits.burst == 240  # Default
        assert limits.llm_requests_per_minute == 30  # Default

        # None settings
        limits = get_tenant_rate_limits(None)
        assert limits.requests_per_minute == 120

    def test_rate_limit_check_validates_positive_rpm(self):
        """Verify rate limit rejects non-positive requests_per_minute."""
        tenant_id = str(uuid4())

        with pytest.raises(ValueError, match="requests_per_minute must be >= 1"):
            _check_tenant_rate_limit(tenant_id, requests_per_minute=0)

        with pytest.raises(ValueError, match="requests_per_minute must be >= 1"):
            _check_tenant_rate_limit(tenant_id, requests_per_minute=-1)

    def test_rate_limit_check_allows_under_limit(self):
        """Verify requests under limit are allowed."""
        tenant_id = str(uuid4())

        # First 5 requests should be allowed
        for _ in range(5):
            allowed, retry_after = _check_tenant_rate_limit(tenant_id, requests_per_minute=10)
            assert allowed is True
            assert retry_after == 0

    def test_rate_limit_check_blocks_over_limit(self):
        """Verify requests over limit are blocked."""
        tenant_id = str(uuid4())
        rpm = 3

        # First 3 requests should be allowed
        for _ in range(3):
            allowed, _ = _check_tenant_rate_limit(tenant_id, requests_per_minute=rpm)
            assert allowed is True

        # 4th request should be blocked
        allowed, retry_after = _check_tenant_rate_limit(tenant_id, requests_per_minute=rpm)
        assert allowed is False
        assert retry_after > 0

    def test_tenant_isolation(self):
        """Verify Tenant A cannot consume Tenant B's quota (Task 84)."""
        tenant_a = str(uuid4())
        tenant_b = str(uuid4())
        rpm = 3

        # Exhaust Tenant A's quota
        for _ in range(3):
            allowed, _ = _check_tenant_rate_limit(tenant_a, requests_per_minute=rpm)
            assert allowed is True

        # Tenant A blocked
        allowed, _ = _check_tenant_rate_limit(tenant_a, requests_per_minute=rpm)
        assert allowed is False

        # Tenant B still allowed
        for _ in range(3):
            allowed, _ = _check_tenant_rate_limit(tenant_b, requests_per_minute=rpm)
            assert allowed is True

        # Tenant B now also blocked
        allowed, _ = _check_tenant_rate_limit(tenant_b, requests_per_minute=rpm)
        assert allowed is False

    def test_rate_limit_window_reset(self):
        """Verify rate limit window resets after 60 seconds."""
        tenant_id = str(uuid4())
        rpm = 2

        # Exhaust quota
        for _ in range(2):
            allowed, _ = _check_tenant_rate_limit(tenant_id, requests_per_minute=rpm)
            assert allowed is True

        # Blocked
        allowed, _ = _check_tenant_rate_limit(tenant_id, requests_per_minute=rpm)
        assert allowed is False

        # Advance time by 61 seconds
        with patch("time.time", return_value=time.time() + 61):
            allowed, _ = _check_tenant_rate_limit(tenant_id, requests_per_minute=rpm)
            assert allowed is True  # Window reset

    def test_tenant_settings_serialization(self):
        """Verify tenant settings can be serialized to JSON."""
        settings = TenantSettings()
        json_data = settings.to_json()

        assert "rate_limits" in json_data
        assert json_data["rate_limits"]["requests_per_minute"] == 120
        assert json_data["rate_limits"]["burst"] == 240


class TestRateLimitMiddlewareIntegration:
    """Test rate limiting integration with middleware."""

    @pytest.mark.asyncio
    async def test_middleware_rate_limit_check(self):
        """Verify middleware checks rate limits when enabled."""
        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.headers = Headers({"Authorization": "Bearer test-token"})
        mock_request.state = MagicMock()

        tenant_id = uuid4()

        # Mock context
        mock_context = MagicMock()
        mock_context.tenant_id = tenant_id
        mock_context.request_id = "test-request-id"

        # Create middleware
        middleware = GovernanceMiddleware(
            app=MagicMock(),
            enable_per_tenant_rate_limiting=True,
            tenant_settings_lookup=AsyncMock(return_value={"rate_limits": {"requests_per_minute": 1}}),
        )

        # Mock _authenticate to return our context
        with patch.object(middleware, "_authenticate", return_value=mock_context):
            # Mock call_next
            mock_call_next = AsyncMock()
            mock_call_next.return_value = MagicMock(headers={})

            # First call should pass
            response1 = await middleware.dispatch(mock_request, mock_call_next)
            assert response1.status_code != 429

            # Second call should be rate limited
            response2 = await middleware.dispatch(mock_request, mock_call_next)
            assert response2.status_code == 429
            assert "Retry-After" in response2.headers

    @pytest.mark.asyncio
    async def test_middleware_skips_rate_limit_when_disabled(self):
        """Verify rate limiting is skipped when disabled."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = Headers({})
        mock_request.state = MagicMock()

        tenant_id = uuid4()
        mock_context = MagicMock()
        mock_context.tenant_id = tenant_id
        mock_context.request_id = "test-id"

        middleware = GovernanceMiddleware(
            app=MagicMock(),
            enable_per_tenant_rate_limiting=False,  # Disabled
        )

        with patch.object(middleware, "_authenticate", return_value=mock_context):
            mock_call_next = AsyncMock()
            mock_call_next.return_value = MagicMock(headers={})

            # Multiple calls should all pass
            for _ in range(5):
                response = await middleware.dispatch(mock_request, mock_call_next)
                assert response.status_code != 429
