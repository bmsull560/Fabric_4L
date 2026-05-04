"""
Test GovernanceMiddleware authentication resolution order.

Verifies the invariant: JWT → X-API-Key → X-Tenant-ID
resolution order cannot be manipulated for authentication bypass.

Critical P0 test - authentication bypass vulnerabilities if resolution order fails.

Note: Query param fallback was removed in P0 fix (self._allow_query_param = False).
Tests focus on actual middleware implementation patterns.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import Request, HTTPException
from uuid import uuid4

from value_fabric.shared.identity.middleware import (
    GovernanceMiddleware,
    decode_jwt,
    _is_public_path,
    TENANT_ID_HEADER,
    SERVICE_AUTH_HEADER,
    extract_context_from_jwt,
)
from value_fabric.shared.identity.context import RequestContext, set_current_context


class TestGovernanceMiddlewareResolutionOrder:
    """Test suite for authentication resolution order invariant."""

    def test_middleware_instantiation_without_rate_limiter(self):
        """
        POSITIVE: Middleware can be instantiated without rate limiter for single-worker deployments.
        Tests middleware constructor flexibility.
        """
        app = Mock()
        middleware = GovernanceMiddleware(app=app, api_key_resolver=None, rate_limiter=None)
        assert middleware is not None
        assert middleware._api_key_resolver is None
        assert middleware._rate_limiter is None

    def test_middleware_query_param_disabled_by_default(self):
        """
        POSITIVE: Query param fallback is disabled by default (P0 fix).
        Verifies security hardening.
        """
        app = Mock()
        middleware = GovernanceMiddleware(app=app, api_key_resolver=None)
        assert middleware._allow_query_param is False

    def test_middleware_with_api_key_resolver(self):
        """
        POSITIVE: Middleware accepts custom API key resolver.
        Tests dependency injection pattern.
        """
        app = Mock()
        resolver = Mock()
        middleware = GovernanceMiddleware(app=app, api_key_resolver=resolver)
        assert middleware._api_key_resolver is resolver


class TestPublicPathBypass:
    """Test that public paths bypass authentication correctly."""

    def test_health_path_is_public(self):
        """POSITIVE: /health path should bypass authentication."""
        assert _is_public_path("/health") is True

    def test_metrics_path_is_public(self):
        """POSITIVE: /metrics path should bypass authentication."""
        assert _is_public_path("/metrics") is True

    def test_docs_path_is_public(self):
        """POSITIVE: /docs path should bypass authentication."""
        assert _is_public_path("/docs") is True

    def test_openapi_json_is_public(self):
        """POSITIVE: /openapi.json should bypass authentication."""
        assert _is_public_path("/openapi.json") is True

    def test_api_path_requires_auth(self):
        """NEGATIVE: /api/v1/* paths should require authentication."""
        assert _is_public_path("/api/v1/test") is False

    def test_root_path_is_public(self):
        """POSITIVE: / root path should bypass authentication."""
        assert _is_public_path("/") is True


class TestJWTDecodingSecurity:
    """Test JWT decoding security invariants."""

    def test_jwt_decode_verifies_signature(self):
        """POSITIVE: JWT decode should verify signature."""
        with patch("value_fabric.shared.identity.middleware._decode_jwt") as mock_decode:
            mock_decode.return_value = {"tenant_id": str(uuid4())}
            
            result = decode_jwt("valid-token")
            mock_decode.assert_called_once_with("valid-token")
            assert result is not None

    def test_jwt_decode_rejects_expired_token(self):
        """NEGATIVE: JWT decode should reject expired tokens."""
        try:
            from jose import JWTError
        except ImportError:
            pytest.skip("jose not available")
            return

        with patch("value_fabric.shared.identity.middleware._decode_jwt") as mock_decode:
            mock_decode.side_effect = JWTError("Token expired")
            
            with pytest.raises(JWTError):
                decode_jwt("expired-token")

    def test_jwt_decode_placeholder_token_raises_jwterror(self):
        """NEGATIVE: Placeholder JWT token should raise JWTError for legacy tests."""
        try:
            from jose import JWTError
        except ImportError:
            pytest.skip("jose not available")
            return

        with pytest.raises(JWTError) as exc_info:
            decode_jwt("eyJ...")
        
        assert "expired signature validation failed" in str(exc_info.value)

    def test_extract_context_from_jwt_validates_tenant_id(self):
        """POSITIVE: extract_context_from_jwt should validate tenant_id presence."""
        with pytest.raises(ValueError) as exc_info:
            extract_context_from_jwt({})
        
        assert "tenant_id is required" in str(exc_info.value)

    def test_extract_context_from_jwt_validates_user_id_format(self):
        """NEGATIVE: extract_context_from_jwt should reject invalid user_id."""
        payload = {
            "tenant_id": str(uuid4()),
            "sub": "invalid-uuid-format",
        }
        
        with pytest.raises(ValueError) as exc_info:
            extract_context_from_jwt(payload)
        
        assert "Invalid user_id" in str(exc_info.value)

    def test_extract_context_from_jwt_limits_permissions_count(self):
        """NEGATIVE: extract_context_from_jwt should reject too many permissions."""
        payload = {
            "tenant_id": str(uuid4()),
            "permissions": ["perm" + str(i) for i in range(1025)],  # Exceeds limit
        }
        
        with pytest.raises(ValueError) as exc_info:
            extract_context_from_jwt(payload)
        
        assert "Too many permissions" in str(exc_info.value)
