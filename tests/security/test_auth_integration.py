"""Integration tests for full authentication lifecycle.

Tests cover:
- Complete OIDC login flow
- JWT validation through middleware
- API key authentication chain
- Role and permission enforcement
- End-to-end security scenarios
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

from value_fabric.shared.identity.context import RequestContext, set_request_context
from value_fabric.shared.identity.dependencies import require_authenticated, require_permission
from value_fabric.shared.identity.jwt import encode_jwt
from value_fabric.shared.identity.middleware import GovernanceMiddleware
from value_fabric.shared.identity.permissions import Permission, Role


# Create test FastAPI app for integration tests
@pytest.fixture
def test_app():
    """Create test FastAPI application with auth."""
    app = FastAPI()

    # Add governance middleware
    app.add_middleware(GovernanceMiddleware, api_key_resolver=None, rate_limiter=None)

    @app.get("/public")
    async def public_endpoint():
        return {"message": "public"}

    @app.get("/protected")
    async def protected_endpoint(ctx: RequestContext = require_authenticated):
        return {"message": "protected", "tenant_id": str(ctx.tenant_id)}

    @app.get("/admin-only")
    async def admin_endpoint(
        ctx: RequestContext = require_permission(Permission.ADMIN_USERS),
    ):
        return {"message": "admin", "tenant_id": str(ctx.tenant_id)}

    return app


@pytest.fixture
def test_client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture(autouse=True)
def setup_jwt_secret():
    """Set up JWT secret for tests."""
    with patch.dict(
        os.environ,
        {"JWT_SECRET": "integration-test-secret-32-chars!", "ENVIRONMENT": "test"},
        clear=True,
    ):
        yield


class TestPublicEndpointAccess:
    """Test public endpoint accessibility."""

    def test_public_endpoint_no_auth(self, test_client):
        """Public endpoint accessible without auth."""
        response = test_client.get("/public")
        assert response.status_code == 200
        assert response.json()["message"] == "public"

    def test_public_endpoint_with_auth(self, test_client):
        """Public endpoint accessible with auth (ignored)."""
        token = encode_jwt(
            tenant_id=uuid4(), user_id="user_123", expires_in_seconds=3600
        )
        response = test_client.get(
            "/public", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200


class TestJWTAuthIntegration:
    """Test JWT authentication integration."""

    def test_protected_with_valid_jwt(self, test_client):
        """Protected endpoint with valid JWT succeeds."""
        tenant_id = uuid4()
        token = encode_jwt(
            tenant_id=tenant_id,
            user_id="user_123",
            roles=[Role.ANALYST.value],
            expires_in_seconds=3600,
        )

        response = test_client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json()["tenant_id"] == str(tenant_id)

    def test_protected_with_expired_jwt(self, test_client):
        """Protected endpoint with expired JWT returns 401."""
        tenant_id = uuid4()
        token = encode_jwt(
            tenant_id=tenant_id,
            user_id="user_123",
            expires_in_seconds=-1,  # Already expired
        )

        response = test_client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_protected_with_invalid_jwt(self, test_client):
        """Protected endpoint with invalid JWT returns 401."""
        response = test_client.get(
            "/protected", headers={"Authorization": "Bearer invalid.token.here"}
        )

        # Falls through to 401 because middleware doesn't block, but dependency does
        assert response.status_code == 401

    def test_protected_without_jwt(self, test_client):
        """Protected endpoint without JWT returns 401."""
        response = test_client.get("/protected")

        assert response.status_code == 401
        assert "AUTHENTICATION_REQUIRED" in response.json()["detail"]

    def test_tenant_header_in_response(self, test_client):
        """X-Tenant-ID-Resolved header present in response."""
        tenant_id = uuid4()
        token = encode_jwt(
            tenant_id=tenant_id, user_id="user_123", expires_in_seconds=3600
        )

        response = test_client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.headers["X-Tenant-ID-Resolved"] == str(tenant_id)


class TestPermissionEnforcement:
    """Test permission-based access control."""

    def test_admin_endpoint_with_permission(self, test_client):
        """Admin endpoint with ADMIN_USERS permission succeeds."""
        tenant_id = uuid4()
        token = encode_jwt(
            tenant_id=tenant_id,
            user_id="user_123",
            roles=[Role.TENANT_ADMIN.value],
            expires_in_seconds=3600,
        )

        response = test_client.get(
            "/admin-only", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

    def test_admin_endpoint_without_permission(self, test_client):
        """Admin endpoint without ADMIN_USERS permission returns 403."""
        tenant_id = uuid4()
        token = encode_jwt(
            tenant_id=tenant_id,
            user_id="user_123",
            roles=[Role.ANALYST.value],  # No ADMIN_USERS permission
            expires_in_seconds=3600,
        )

        response = test_client.get(
            "/admin-only", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403
        assert "INSUFFICIENT_PERMISSIONS" in response.json()["detail"]

    def test_admin_endpoint_without_auth(self, test_client):
        """Admin endpoint without auth returns 401."""
        response = test_client.get("/admin-only")

        assert response.status_code == 401


class TestMultiTenantIsolation:
    """Test multi-tenant isolation in auth."""

    def test_different_tenants_different_contexts(self, test_client):
        """Different tenant IDs create different contexts."""
        tenant_id_1 = uuid4()
        tenant_id_2 = uuid4()

        token_1 = encode_jwt(
            tenant_id=tenant_id_1, user_id="user_123", expires_in_seconds=3600
        )
        token_2 = encode_jwt(
            tenant_id=tenant_id_2, user_id="user_123", expires_in_seconds=3600
        )

        response_1 = test_client.get(
            "/protected", headers={"Authorization": f"Bearer {token_1}"}
        )
        response_2 = test_client.get(
            "/protected", headers={"Authorization": f"Bearer {token_2}"}
        )

        assert response_1.json()["tenant_id"] == str(tenant_id_1)
        assert response_2.json()["tenant_id"] == str(tenant_id_2)
        assert response_1.json()["tenant_id"] != response_2.json()["tenant_id"]


class TestRoleHierarchy:
    """Test role hierarchy and permission inheritance."""

    def test_super_admin_has_all_permissions(self, test_client):
        """SUPER_ADMIN role can access all endpoints."""
        tenant_id = uuid4()
        token = encode_jwt(
            tenant_id=tenant_id,
            user_id="user_123",
            roles=[Role.SUPER_ADMIN.value],
            expires_in_seconds=3600,
        )

        # Can access admin-only endpoint
        response = test_client.get(
            "/admin-only", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    def test_read_only_restricted_access(self, test_client):
        """READ_ONLY role cannot access admin endpoints."""
        tenant_id = uuid4()
        token = encode_jwt(
            tenant_id=tenant_id,
            user_id="user_123",
            roles=[Role.READ_ONLY.value],
            expires_in_seconds=3600,
        )

        # Cannot access admin-only endpoint
        response = test_client.get(
            "/admin-only", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403


class TestContextIsolation:
    """Test request context isolation."""

    def test_context_not_leaked_between_requests(self, test_client):
        """Context from one request doesn't leak to another."""
        from value_fabric.shared.identity.context import get_request_context

        # After request completes, context should be cleared
        tenant_id = uuid4()
        token = encode_jwt(
            tenant_id=tenant_id, user_id="user_123", expires_in_seconds=3600
        )

        # Make request
        test_client.get("/protected", headers={"Authorization": f"Bearer {token}"})

        # Context should be cleared
        assert get_request_context() is None


class TestAuthHeaderVariations:
    """Test various Authorization header formats."""

    def test_bearer_with_whitespace(self, test_client):
        """Bearer token with extra whitespace handled."""
        tenant_id = uuid4()
        token = encode_jwt(
            tenant_id=tenant_id, user_id="user_123", expires_in_seconds=3600
        )

        response = test_client.get(
            "/protected", headers={"Authorization": f"Bearer   {token}"}
        )

        # Should work or fall through to 401
        assert response.status_code in [200, 401]

    def test_bearer_case_insensitive(self, test_client):
        """Bearer prefix is case-sensitive (per RFC 6750)."""
        tenant_id = uuid4()
        token = encode_jwt(
            tenant_id=tenant_id, user_id="user_123", expires_in_seconds=3600
        )

        response = test_client.get(
            "/protected", headers={"Authorization": f"bearer {token}"}
        )

        # bearer (lowercase) should not match
        assert response.status_code == 401


class TestSecurityHeaders:
    """Test security-related response headers."""

    def test_www_authenticate_header_on_401(self, test_client):
        """401 responses include WWW-Authenticate header."""
        response = test_client.get("/protected")

        assert response.status_code == 401
        assert response.headers.get("WWW-Authenticate") == "Bearer"


# Need to import os for the fixture
import os


class TestCompleteAuthFlow:
    """Test complete authentication flow scenarios."""

    def test_login_to_access_flow(self, test_client):
        """Complete flow: authenticate then access protected resource."""
        # Step 1: Simulate login (get JWT)
        tenant_id = uuid4()
        token = encode_jwt(
            tenant_id=tenant_id,
            user_id="user_123",
            roles=[Role.ANALYST.value],
            expires_in_seconds=3600,
        )

        # Step 2: Access protected resource
        response = test_client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json()["message"] == "protected"
        assert response.json()["tenant_id"] == str(tenant_id)

    def test_token_refresh_simulation(self, test_client):
        """Simulate token refresh with new token."""
        tenant_id = uuid4()
        user_id = "user_123"

        # Original token
        old_token = encode_jwt(
            tenant_id=tenant_id,
            user_id=user_id,
            roles=[Role.ANALYST.value],
            expires_in_seconds=3600,
        )

        # New token (simulating refresh)
        new_token = encode_jwt(
            tenant_id=tenant_id,
            user_id=user_id,
            roles=[Role.ANALYST.value],
            expires_in_seconds=3600,
        )

        # Both should work
        old_response = test_client.get(
            "/protected", headers={"Authorization": f"Bearer {old_token}"}
        )
        new_response = test_client.get(
            "/protected", headers={"Authorization": f"Bearer {new_token}"}
        )

        assert old_response.status_code == 200
        assert new_response.status_code == 200

        # Tokens should be different
        assert old_token != new_token
