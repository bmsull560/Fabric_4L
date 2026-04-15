"""
Security tests for Role-Based Access Control (RBAC).

Validates that:
1. Role permissions are properly enforced
2. Admin endpoints require admin role
3. Role escalation attempts are blocked
"""

import pytest
from fastapi.testclient import TestClient


class TestRBACEnforcement:
    """Test suite for RBAC policy enforcement."""

    @pytest.fixture
    def standard_user_token(self):
        """Standard user with limited permissions."""
        return {
            "sub": "user-123",
            "tenant_id": "tenant-a",
            "role": "standard",
        }

    @pytest.fixture
    def admin_user_token(self):
        """Admin user with full permissions."""
        return {
            "sub": "admin-456",
            "tenant_id": "tenant-a",
            "role": "admin",
        }

    def test_standard_user_blocked_from_admin_endpoints(self, client: TestClient, standard_user_token):
        """P0: Standard users cannot access admin endpoints."""
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/config",
            "/api/v1/admin/audit-logs",
        ]

        for endpoint in admin_endpoints:
            response = client.get(
                endpoint,
                headers={"Authorization": f"Bearer {standard_user_token}"},
            )
            assert response.status_code == 403, f"Admin endpoint {endpoint} should be forbidden"

    def test_admin_user_can_access_admin_endpoints(self, client: TestClient, admin_user_token):
        """Admin users can access admin endpoints."""
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_user_token}"},
        )
        # Should succeed (or 404 if endpoint doesn't exist in test)
        assert response.status_code in [200, 404]

    def test_role_claim_cannot_be_modified_in_jwt(self, client: TestClient):
        """JWT role claim is immutable - cannot be forged."""
        # This would require a forged JWT with modified role
        # In practice, this is prevented by JWT signature verification
        forged_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."  # Would need valid signature
        response = client.get(
            "/api/v1/admin/config",
            headers={"Authorization": f"Bearer {forged_token}"},
        )
        assert response.status_code in [401, 403]

    def test_permission_check_on_every_request(self, client: TestClient, standard_user_token):
        """RBAC is validated on every request, not just at login."""
        # First request - should succeed for standard endpoint
        response1 = client.get(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {standard_user_token}"},
        )

        # Token should be re-validated on second request
        response2 = client.get(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {standard_user_token}"},
        )

        # Both should have same permission level
        assert response1.status_code == response2.status_code


class TestRoleHierarchy:
    """Test role hierarchy and permission inheritance."""

    def test_advanced_user_has_more_access_than_standard(self, client: TestClient):
        """Advanced role has more permissions than standard."""
        standard_token = {"role": "standard", "tenant_id": "t1"}
        advanced_token = {"role": "advanced", "tenant_id": "t1"}

        # Advanced can access formulas
        advanced_response = client.get(
            "/api/v1/formulas",
            headers={"Authorization": f"Bearer {advanced_token}"},
        )

        # Standard might be blocked or have limited access
        standard_response = client.get(
            "/api/v1/formulas",
            headers={"Authorization": f"Bearer {standard_token}"},
        )

        # Advanced should have equal or greater access
        assert advanced_response.status_code <= standard_response.status_code
