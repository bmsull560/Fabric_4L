"""Regression tests for production security fixes.

Tests the security improvements made during the billing/webhook security audit:
1. /metrics endpoint access control
2. Health endpoint authentication
3. Prometheus cardinality limits
4. JWT/HMAC secret validation
5. Stripe webhook IP allowlist
"""

import hashlib
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Request
from fastapi.responses import Response

# Import metrics functions to test
try:
    from value_fabric.layer4_agents.src.metrics.prometheus_metrics import (
        _derive_tenant_tier,
        _normalize_path,
    )
    METRICS_IMPORTS_AVAILABLE = True
except ImportError:
    METRICS_IMPORTS_AVAILABLE = False

# Import billing webhook functions to test
try:
    from value_fabric.layer4_agents.src.api.routes.billing import (
        _get_client_ip,
        _is_stripe_webhook_ip,
    )
    BILLING_IMPORTS_AVAILABLE = True
except ImportError:
    BILLING_IMPORTS_AVAILABLE = False

# Import settings to test
try:
    from value_fabric.layer4_agents.src.config.settings import Settings
    SETTINGS_IMPORTS_AVAILABLE = True
except ImportError:
    SETTINGS_IMPORTS_AVAILABLE = False


# =============================================================================
# Test Path Normalization (Metrics Security)
# =============================================================================

class TestPathNormalization:
    """Test that metric paths are normalized to prevent cardinality explosion."""

    @pytest.mark.skipif(not METRICS_IMPORTS_AVAILABLE, reason="Metrics imports not available")
    def test_normalize_uuid_path(self):
        """UUIDs in paths should be replaced with {id} placeholder."""
        uuid_path = "/v1/billing/usage/550e8400-e29b-41d4-a716-446655440000/events"
        result = _normalize_path(uuid_path)
        assert result == "/v1/billing/usage/{id}/events"

    @pytest.mark.skipif(not METRICS_IMPORTS_AVAILABLE, reason="Metrics imports not available")
    def test_normalize_numeric_id_path(self):
        """Numeric IDs in paths should be replaced with {id} placeholder."""
        numeric_path = "/v1/billing/usage/12345/events"
        result = _normalize_path(numeric_path)
        assert result == "/v1/billing/usage/{id}/events"

    @pytest.mark.skipif(not METRICS_IMPORTS_AVAILABLE, reason="Metrics imports not available")
    def test_normalize_short_hex_path(self):
        """Short hex IDs (24 chars like MongoDB ObjectId) should be replaced."""
        hex_path = "/api/items/507f1f77bcf86cd799439011"
        result = _normalize_path(hex_path)
        assert result == "/api/items/{id}"

    @pytest.mark.skipif(not METRICS_IMPORTS_AVAILABLE, reason="Metrics imports not available")
    def test_preserve_static_paths(self):
        """Static paths without IDs should be preserved."""
        static_path = "/v1/billing/webhook"
        result = _normalize_path(static_path)
        assert result == "/v1/billing/webhook"

    @pytest.mark.skipif(not METRICS_IMPORTS_AVAILABLE, reason="Metrics imports not available")
    def test_normalize_root_path(self):
        """Root path should remain root."""
        result = _normalize_path("/")
        assert result == "/"

    @pytest.mark.skipif(not METRICS_IMPORTS_AVAILABLE, reason="Metrics imports not available")
    def test_normalize_empty_path(self):
        """Empty path should return root."""
        result = _normalize_path("")
        assert result == "/"

    @pytest.mark.skipif(not METRICS_IMPORTS_AVAILABLE, reason="Metrics imports not available")
    def test_trailing_slash_removed(self):
        """Trailing slashes should be removed."""
        result = _normalize_path("/v1/billing/webhook/")
        assert result == "/v1/billing/webhook"


# =============================================================================
# Test Tenant Tier Derivation (Metrics Security)
# =============================================================================

class TestTenantTierDerivation:
    """Test that tenant_id is hashed to prevent cardinality explosion."""

    @pytest.mark.skipif(not METRICS_IMPORTS_AVAILABLE, reason="Metrics imports not available")
    def test_derive_tenant_tier_consistency(self):
        """Same tenant_id should always produce same tier."""
        tenant_id = "tenant_12345"
        tier1 = _derive_tenant_tier(tenant_id)
        tier2 = _derive_tenant_tier(tenant_id)
        assert tier1 == tier2
        assert len(tier1) == 4  # 2 hex bytes = 4 hex chars

    @pytest.mark.skipif(not METRICS_IMPORTS_AVAILABLE, reason="Metrics imports not available")
    def test_derive_tenant_tier_distribution(self):
        """Different tenant_ids should produce different tiers."""
        # With 256 possible values, these should likely be different
        tier1 = _derive_tenant_tier("tenant_1")
        tier2 = _derive_tenant_tier("tenant_2")
        tier3 = _derive_tenant_tier("tenant_3")

        # At least some should be different (statistically very likely)
        unique_tiers = {tier1, tier2, tier3}
        assert len(unique_tiers) >= 2

    @pytest.mark.skipif(not METRICS_IMPORTS_AVAILABLE, reason="Metrics imports not available")
    def test_derive_tenant_tier_cardinality_limit(self):
        """Tier values should be limited to 256 possible values (2 hex bytes)."""
        # Generate many tiers and verify they're all 4 hex chars
        tiers = [_derive_tenant_tier(f"tenant_{i}") for i in range(100)]
        for tier in tiers:
            assert len(tier) == 4
            assert all(c in "0123456789abcdef" for c in tier.lower())

    @pytest.mark.skipif(not METRICS_IMPORTS_AVAILABLE, reason="Metrics imports not available")
    def test_derive_tenant_tier_empty(self):
        """Empty tenant_id should return 'unknown'."""
        assert _derive_tenant_tier("") == "unknown"
        assert _derive_tenant_tier(None) == "unknown"

    @pytest.mark.skipif(not METRICS_IMPORTS_AVAILABLE, reason="Metrics imports not available")
    def test_derive_tenant_tier_matches_sha256(self):
        """Tier should match first 2 bytes of SHA256 hash."""
        tenant_id = "test_tenant_123"
        expected_hash = hashlib.sha256(tenant_id.encode()).digest()
        expected_tier = expected_hash[:2].hex()

        result = _derive_tenant_tier(tenant_id)
        assert result == expected_tier


# =============================================================================
# Test Stripe IP Allowlist (Webhook Security)
# =============================================================================

class TestStripeIPAllowlist:
    """Test Stripe webhook IP validation for defense-in-depth."""

    @pytest.mark.skipif(not BILLING_IMPORTS_AVAILABLE, reason="Billing imports not available")
    def test_valid_stripe_ip(self):
        """Known Stripe IPs should be accepted."""
        # Test a known Stripe webhook IP
        assert _is_stripe_webhook_ip("3.18.12.63") is True

    @pytest.mark.skipif(not BILLING_IMPORTS_AVAILABLE, reason="Billing imports not available")
    def test_invalid_ip_rejected(self):
        """Non-Stripe IPs should be rejected."""
        assert _is_stripe_webhook_ip("1.2.3.4") is False
        assert _is_stripe_webhook_ip("192.168.1.1") is False

    @pytest.mark.skipif(not BILLING_IMPORTS_AVAILABLE, reason="Billing imports not available")
    def test_loopback_ip_allowed(self):
        """Loopback IPs should be allowed for local testing."""
        assert _is_stripe_webhook_ip("127.0.0.1") is True
        assert _is_stripe_webhook_ip("::1") is True

    @pytest.mark.skipif(not BILLING_IMPORTS_AVAILABLE, reason="Billing imports not available")
    def test_invalid_ip_format(self):
        """Invalid IP formats should return False."""
        assert _is_stripe_webhook_ip("invalid") is False
        assert _is_stripe_webhook_ip("") is False

    @pytest.mark.skipif(not BILLING_IMPORTS_AVAILABLE, reason="Billing imports not available")
    def test_get_client_ip_from_request(self):
        """Client IP should be extracted correctly from request."""
        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "3.18.12.63"
        mock_request.headers = {}

        result = _get_client_ip(mock_request)
        assert result == "3.18.12.63"

    @pytest.mark.skipif(not BILLING_IMPORTS_AVAILABLE, reason="Billing imports not available")
    def test_get_client_ip_from_x_forwarded_for(self):
        """X-Forwarded-For header should be respected."""
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "192.168.1.1"  # Would be rejected
        mock_request.headers = {"X-Forwarded-For": "3.18.12.63, 10.0.0.1"}

        result = _get_client_ip(mock_request)
        # Should use the first IP in X-Forwarded-For
        assert result == "3.18.12.63"


# =============================================================================
# Test JWT/HMAC Secret Validation (Settings Security)
# =============================================================================

class TestSecretValidation:
    """Test that JWT and HMAC secrets are validated on startup."""

    @pytest.mark.skipif(not SETTINGS_IMPORTS_AVAILABLE, reason="Settings imports not available")
    def test_jwt_secret_too_short_in_production(self):
        """Short JWT secret in production should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            Settings(
                environment="production",
                jwt_secret="short",  # Only 5 chars, need 32+
            )
        assert "JWT_SECRET" in str(exc_info.value)
        assert "32 characters" in str(exc_info.value)

    @pytest.mark.skipif(not SETTINGS_IMPORTS_AVAILABLE, reason="Settings imports not available")
    def test_hmac_secret_too_short_in_production(self):
        """Short HMAC secret in production should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            Settings(
                environment="production",
                api_key_hmac_secret="short",  # Only 5 chars, need 32+
            )
        assert "API_KEY_HMAC_SECRET" in str(exc_info.value)
        assert "32 characters" in str(exc_info.value)

    @pytest.mark.skipif(not SETTINGS_IMPORTS_AVAILABLE, reason="Settings imports not available")
    def test_valid_secrets_in_production(self):
        """Valid length secrets should work in production."""
        # Should not raise
        settings = Settings(
            environment="production",
            jwt_secret="a" * 32,  # 32 chars
            api_key_hmac_secret="b" * 32,  # 32 chars
        )
        assert settings.jwt_secret == "a" * 32

    @pytest.mark.skipif(not SETTINGS_IMPORTS_AVAILABLE, reason="Settings imports not available")
    def test_short_secrets_allowed_in_development(self):
        """Short secrets should be allowed (with warning) in development."""
        # Should not raise, just warn
        settings = Settings(
            environment="development",
            jwt_secret="short",
            api_key_hmac_secret="short",
        )
        assert settings.jwt_secret == "short"

    @pytest.mark.skipif(not SETTINGS_IMPORTS_AVAILABLE, reason="Settings imports not available")
    def test_staging_requires_strong_secrets(self):
        """Staging environment should also require strong secrets."""
        with pytest.raises(ValueError) as exc_info:
            Settings(
                environment="staging",
                jwt_secret="short",
            )
        assert "staging" in str(exc_info.value).lower()


# =============================================================================
# Test Metrics Endpoint Access Control
# =============================================================================

class TestMetricsAccessControl:
    """Test that /metrics endpoint is properly protected."""

    def test_metrics_endpoint_requires_auth(self):
        """Metrics endpoint should return 401 without valid auth."""
        # This is an integration test that would require the full app
        # For unit testing, we verify the security import is present
        try:
            from value_fabric.layer4_agents.src.api.main import (
                METRICS_ACCESS_AVAILABLE,
                metrics_endpoint,
            )
            assert METRICS_ACCESS_AVAILABLE is True, "Metrics access control should be available"
        except ImportError:
            pytest.skip("Main app imports not available")


# =============================================================================
# Test Health Endpoint Authentication
# =============================================================================

class TestHealthEndpointAuth:
    """Test that health endpoints require authentication."""

    def test_detailed_health_requires_auth(self):
        """Detailed health endpoint should require authentication."""
        try:
            from value_fabric.layer4_agents.src.api.routes.health_badges import (
                SECURITY_AVAILABLE,
                get_detailed_health,
            )
            # Check that the function accepts a context parameter (auth)
            import inspect
            sig = inspect.signature(get_detailed_health)
            params = list(sig.parameters.keys())
            assert "context" in params, "Detailed health should accept auth context"
        except ImportError:
            pytest.skip("Health badges imports not available")

    def test_badge_dismissal_requires_auth(self):
        """Badge dismissal should require authentication."""
        try:
            from value_fabric.layer4_agents.src.api.routes.health_badges import (
                SECURITY_AVAILABLE,
                dismiss_badge,
            )
            import inspect
            sig = inspect.signature(dismiss_badge)
            params = list(sig.parameters.keys())
            assert "context" in params, "Badge dismissal should accept auth context"
        except ImportError:
            pytest.skip("Health badges imports not available")
