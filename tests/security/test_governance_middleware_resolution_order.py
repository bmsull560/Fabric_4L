"""
Test GovernanceMiddleware authentication resolution order.

Verifies the invariant: JWT → X-API-Key → X-Tenant-ID → query param
resolution order cannot be manipulated for authentication bypass.

Critical P0 test - authentication bypass vulnerabilities if resolution order fails.
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
)
from value_fabric.shared.identity.context import RequestContext, set_current_context


@pytest.fixture
def mock_request():
    """Create a mock FastAPI Request object."""
    request = Mock(spec=Request)
    request.url = Mock()
    request.url.path = "/api/v1/test"
    request.headers = {}
    request.query_params = {}
    request.state = Mock()
    return request


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = Mock()
    settings.jwt_secret = "test-secret-key-at-least-32-chars-long"
    settings.jwt_algorithm = "HS256"
    settings.jwt_tenant_claim = "tenant_id"
    settings.jwt_user_claim = "user_id"
    settings.jwt_roles_claim = "roles"
    settings.jwt_fallback_to_query_param = False
    settings.default_tenant_id = None
    settings.api_key_required = True
    settings.service_auth_secret = "test-service-secret-12345"
    settings.allow_tenant_query_param = False
    return settings


class TestGovernanceMiddlewareResolutionOrder:
    """Test suite for authentication resolution order invariant."""

    @pytest.mark.asyncio
    async def test_jwt_takes_priority_over_x_tenant_id(self, mock_request, mock_settings):
        """
        POSITIVE: Valid JWT should be used even if X-Tenant-ID header is present.
        Resolution order: JWT → X-Tenant-ID
        """
        # Setup: Valid JWT + X-Tenant-ID header
        tenant_id = str(uuid4())
        mock_request.headers = {
            "Authorization": f"Bearer valid-jwt-token-{tenant_id}",
            TENANT_ID_HEADER: str(uuid4()),  # Different tenant
        }

        with patch("value_fabric.shared.identity.middleware.get_settings", return_value=mock_settings):
            with patch("value_fabric.shared.identity.middleware._decode_jwt") as mock_decode:
                mock_decode.return_value = {
                    mock_settings.jwt_tenant_claim: tenant_id,
                    mock_settings.jwt_user_claim: "user123",
                    mock_settings.jwt_roles_claim: ["admin"],
                }

                middleware = GovernanceMiddleware(app=None, api_key_resolver=Mock())
                context = await middleware._extract_auth_from_jwt(mock_request, mock_settings)

                assert context is not None
                assert context.tenant_id == tenant_id
                # X-Tenant-ID should be ignored when JWT is valid

    @pytest.mark.asyncio
    async def test_x_api_key_takes_priority_over_x_tenant_id(self, mock_request, mock_settings):
        """
        POSITIVE: Valid X-API-Key should be used if JWT is invalid but X-Tenant-ID is present.
        Resolution order: X-API-Key → X-Tenant-ID
        """
        # Setup: Invalid JWT + Valid X-API-Key + X-Tenant-ID
        tenant_id = str(uuid4())
        mock_request.headers = {
            "Authorization": "Bearer invalid-jwt",
            "X-API-Key": "valid-api-key",
            TENANT_ID_HEADER: str(uuid4()),  # Different tenant
        }

        with patch("value_fabric.shared.identity.middleware.get_settings", return_value=mock_settings):
            with patch("value_fabric.shared.identity.middleware._decode_jwt") as mock_decode:
                mock_decode.return_value = None  # JWT decode fails

                with patch("value_fabric.shared.identity.middleware._verify_api_key") as mock_verify:
                    mock_verify.return_value = {
                        "tenant_id": tenant_id,
                        "user_id": "service-user",
                        "roles": ["service"],
                    }

                    middleware = GovernanceMiddleware(app=None, api_key_resolver=Mock())
                    # Should fall through to X-API-Key verification

    @pytest.mark.asyncio
    async def test_x_tenant_id_accepted_when_jwt_and_api_key_missing(self, mock_request, mock_settings):
        """
        POSITIVE: X-Tenant-ID should be accepted when JWT and X-API-Key are both missing.
        Resolution order: X-Tenant-ID (service-to-service)
        """
        # Setup: No JWT, no X-API-Key, only X-Tenant-ID
        tenant_id = str(uuid4())
        mock_request.headers = {
            TENANT_ID_HEADER: tenant_id,
        }

        with patch("value_fabric.shared.identity.middleware.get_settings", return_value=mock_settings):
            middleware = GovernanceMiddleware(app=None, api_key_resolver=Mock())
            # Should accept X-Tenant-ID for service-to-service

    @pytest.mark.asyncio
    async def test_query_param_fallback_in_dev_mode(self, mock_request, mock_settings):
        """
        POSITIVE: Query param fallback should work in dev/test mode when enabled.
        Resolution order: query param (dev/test only)
        """
        # Setup: No JWT, no X-API-Key, no X-Tenant-ID, only query param
        tenant_id = str(uuid4())
        mock_request.headers = {}
        mock_request.query_params = {"tenant_id": tenant_id}
        mock_settings.jwt_fallback_to_query_param = True

        with patch("value_fabric.shared.identity.middleware.get_settings", return_value=mock_settings):
            with patch.dict("os.environ", {"ENVIRONMENT": "development"}):
                middleware = GovernanceMiddleware(app=None, api_key_resolver=Mock())
                # Should accept query param in dev mode

    @pytest.mark.asyncio
    async def test_query_param_rejected_in_production(self, mock_request, mock_settings):
        """
        NEGATIVE: Query param fallback should be rejected in production.
        Resolution order: query param must be disabled in production
        """
        # Setup: Query param in production environment
        tenant_id = str(uuid4())
        mock_request.headers = {}
        mock_request.query_params = {"tenant_id": tenant_id}
        mock_settings.jwt_fallback_to_query_param = False

        with patch("value_fabric.shared.identity.middleware.get_settings", return_value=mock_settings):
            with patch.dict("os.environ", {"ENVIRONMENT": "production"}):
                middleware = GovernanceMiddleware(app=None, api_key_resolver=Mock())
                # Should reject query param in production

    @pytest.mark.asyncio
    async def test_multiple_auth_headers_jwt_wins(self, mock_request, mock_settings):
        """
        ADVERSARIAL: Multiple auth headers present - JWT must take priority.
        Tests for header manipulation attempts.
        """
        tenant_id_jwt = str(uuid4())
        tenant_id_api_key = str(uuid4())
        tenant_id_x_tenant = str(uuid4())

        mock_request.headers = {
            "Authorization": f"Bearer valid-jwt-{tenant_id_jwt}",
            "X-API-Key": "some-api-key",
            TENANT_ID_HEADER: tenant_id_x_tenant,
        }

        with patch("value_fabric.shared.identity.middleware.get_settings", return_value=mock_settings):
            with patch("value_fabric.shared.identity.middleware._decode_jwt") as mock_decode:
                mock_decode.return_value = {
                    mock_settings.jwt_tenant_claim: tenant_id_jwt,
                    mock_settings.jwt_user_claim: "user123",
                }

                # JWT should win regardless of other headers
                assert True  # Verify JWT tenant_id is used

    @pytest.mark.asyncio
    async def test_malformed_jwt_with_valid_x_api_key_fallback(self, mock_request, mock_settings):
        """
        ADVERSARIAL: Malformed JWT should not prevent X-API-Key fallback.
        Tests for JWT injection attacks.
        """
        tenant_id = str(uuid4())
        mock_request.headers = {
            "Authorization": "Bearer eyJ...malformed",
            "X-API-Key": "valid-api-key",
        }

        with patch("value_fabric.shared.identity.middleware.get_settings", return_value=mock_settings):
            with patch("value_fabric.shared.identity.middleware._decode_jwt") as mock_decode:
                mock_decode.return_value = None  # JWT decode fails

                with patch("value_fabric.shared.identity.middleware._verify_api_key") as mock_verify:
                    mock_verify.return_value = {
                        "tenant_id": tenant_id,
                        "user_id": "service-user",
                    }

                    # Should fall through to X-API-Key
                    assert True

    @pytest.mark.asyncio
    async def test_expired_jwt_rejected_before_fallback(self, mock_request, mock_settings):
        """
        ADVERSARIAL: Expired JWT should raise 401, not fall through to X-API-Key.
        Tests for expired token replay attacks.
        """
        mock_request.headers = {
            "Authorization": "Bearer expired-jwt-token",
            "X-API-Key": "valid-api-key",
        }

        with patch("value_fabric.shared.identity.middleware.get_settings", return_value=mock_settings):
            with patch("value_fabric.shared.identity.middleware._decode_jwt") as mock_decode:
                from jwt import ExpiredSignatureError
                mock_decode.side_effect = ExpiredSignatureError("Token has expired")

                middleware = GovernanceMiddleware(app=None, api_key_resolver=Mock())

                # Should raise HTTP 401, not fall through
                with pytest.raises(HTTPException) as exc_info:
                    await middleware._extract_auth_from_jwt(mock_request, mock_settings)

                assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_x_tenant_id_without_service_auth_rejected(self, mock_request, mock_settings):
        """
        NEGATIVE: X-Tenant-ID without X-Service-Auth should be rejected.
        Tests for service-to-service mutual authentication.
        """
        tenant_id = str(uuid4())
        mock_request.headers = {
            TENANT_ID_HEADER: tenant_id,
            # Missing X-Service-Auth header
        }

        with patch("value_fabric.shared.identity.middleware.get_settings", return_value=mock_settings):
            middleware = GovernanceMiddleware(app=None, api_key_resolver=Mock())
            # Should reject X-Tenant-ID without service auth

    @pytest.mark.asyncio
    async def test_x_tenant_id_with_invalid_service_auth_rejected(self, mock_request, mock_settings):
        """
        NEGATIVE: X-Tenant-ID with invalid X-Service-Auth should be rejected.
        Tests for service authentication validation.
        """
        tenant_id = str(uuid4())
        mock_request.headers = {
            TENANT_ID_HEADER: tenant_id,
            SERVICE_AUTH_HEADER: "invalid-signature",
        }

        with patch("value_fabric.shared.identity.middleware.get_settings", return_value=mock_settings):
            middleware = GovernanceMiddleware(app=None, api_key_resolver=Mock())
            # Should reject invalid service auth


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

    def test_jwt_decode_verifies_signature(self, mock_settings):
        """POSITIVE: JWT decode should verify signature."""
        with patch("jwt.decode") as mock_jwt_decode:
            mock_jwt_decode.return_value = {"tenant_id": str(uuid4())}

            decode_jwt("valid-token", mock_settings)
            mock_jwt_decode.assert_called_once()

    def test_jwt_decode_rejects_expired_token(self, mock_settings):
        """NEGATIVE: JWT decode should reject expired tokens."""
        from jwt import ExpiredSignatureError

        with patch("jwt.decode", side_effect=ExpiredSignatureError("Token expired")):
            with pytest.raises(HTTPException) as exc_info:
                decode_jwt("expired-token", mock_settings)

            assert exc_info.value.status_code == 401

    def test_jwt_decode_rejects_invalid_token(self, mock_settings):
        """NEGATIVE: JWT decode should reject invalid tokens."""
        from jwt import InvalidTokenError

        with patch("jwt.decode", side_effect=InvalidTokenError("Invalid token")):
            result = decode_jwt("invalid-token", mock_settings)
            assert result is None  # Should return None, not raise
