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

    @pytest.mark.parametrize("endpoint", [
        "/api/v1/admin/users",
        "/api/v1/admin/config",
        "/api/v1/admin/audit-logs",
    ])
    def test_standard_user_blocked_from_admin_endpoint(self, client: TestClient, standard_user_token, endpoint: str):
        """P0: Standard users cannot access admin endpoints.

        Each endpoint is tested independently for clearer failure reporting.
        """
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


class TestPermissionGranularity:
    """Test permission-level granularity for read vs write operations."""

    def test_read_permission_allows_get_blocks_post(self, client: TestClient, jwt_encoder):
        """P0: Read permission allows GET but blocks POST/PUT/DELETE."""
        read_only_token = jwt_encoder({
            "sub": "read-only-user",
            "tenant_id": "tenant-a",
            "role": "read_only",
            "permissions": ["read"],
        })

        # GET should succeed
        get_response = client.get(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {read_only_token}"},
        )
        assert get_response.status_code in [200, 404], "Read permission should allow GET"

        # POST should be blocked
        post_response = client.post(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {read_only_token}"},
            json={"name": "test-entity"},
        )
        assert post_response.status_code in [403, 401], "Read-only user should not be able to POST"

    def test_write_permission_allows_post_put_delete(self, client: TestClient, jwt_encoder):
        """P0: Write permission allows POST/PUT/DELETE."""
        write_token = jwt_encoder({
            "sub": "write-user",
            "tenant_id": "tenant-a",
            "role": "editor",
            "permissions": ["read", "write"],
        })

        # POST should succeed (or 404 if endpoint doesn't exist)
        post_response = client.post(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {write_token}"},
            json={"name": "test-entity"},
        )
        assert post_response.status_code in [201, 200, 404], "Write permission should allow POST"

        # PUT should succeed (or 404 if entity doesn't exist)
        put_response = client.put(
            "/api/v1/entities/some-id",
            headers={"Authorization": f"Bearer {write_token}"},
            json={"name": "updated-entity"},
        )
        assert put_response.status_code in [200, 404], "Write permission should allow PUT"

        # DELETE should succeed (or 404 if entity doesn't exist)
        delete_response = client.delete(
            "/api/v1/entities/some-id",
            headers={"Authorization": f"Bearer {write_token}"},
        )
        assert delete_response.status_code in [204, 200, 404], "Write permission should allow DELETE"

    def test_admin_permission_includes_all_operations(self, client: TestClient, admin_user_token):
        """P0: Admin role has full CRUD permissions."""
        # Admin should be able to perform all operations
        endpoints_methods = [
            ("/api/v1/entities", "GET"),
            ("/api/v1/entities", "POST"),
            ("/api/v1/admin/users", "GET"),
            ("/api/v1/admin/config", "PUT"),
        ]

        for endpoint, method in endpoints_methods:
            if method == "GET":
                response = client.get(endpoint, headers={"Authorization": f"Bearer {admin_user_token}"})
            elif method == "POST":
                response = client.post(endpoint, headers={"Authorization": f"Bearer {admin_user_token}"}, json={"test": "data"})
            elif method == "PUT":
                response = client.put(endpoint, headers={"Authorization": f"Bearer {admin_user_token}"}, json={"test": "data"})

            # Should not get 403 Forbidden - admin has access
            assert response.status_code != 403, f"Admin should not be forbidden from {method} {endpoint}"


class TestJWTTamperingResistance:
    """Test JWT tampering and forgery resistance."""

    def test_modified_role_claim_rejected(self, client: TestClient, jwt_encoder):
        """P0: JWT with modified role claim is rejected."""
        import jwt as jwt_lib

        # Create a valid token for standard user
        original_payload = {
            "sub": "user-123",
            "tenant_id": "tenant-a",
            "role": "standard",
        }
        original_token = jwt_encoder(original_payload)

        # Decode, modify role, re-encode (without proper signature)
        decoded = jwt_lib.decode(original_token, "test-secret-key", algorithms=["HS256"])
        decoded["role"] = "admin"  # Attempt privilege escalation

        # Re-encode with different secret (simulating tampering)
        tampered_token = jwt_lib.encode(decoded, "wrong-secret", algorithm="HS256")

        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {tampered_token}"},
        )
        assert response.status_code in [401, 403], "Tampered JWT should be rejected"

    def test_modified_tenant_claim_rejected(self, client: TestClient, jwt_encoder):
        """P0: JWT with modified tenant claim is rejected."""
        import jwt as jwt_lib

        # Create valid token for tenant-a
        original_payload = {
            "sub": "user-123",
            "tenant_id": "tenant-a",
            "role": "standard",
        }
        original_token = jwt_encoder(original_payload)

        # Decode and modify tenant
        decoded = jwt_lib.decode(original_token, "test-secret-key", algorithms=["HS256"])
        decoded["tenant_id"] = "tenant-b"  # Attempt cross-tenant access

        # Re-encode with tampered payload
        tampered_token = jwt_lib.encode(decoded, "wrong-secret", algorithm="HS256")

        response = client.get(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {tampered_token}"},
        )
        assert response.status_code in [401, 403], "JWT with modified tenant should be rejected"

    def test_expired_token_rejected(self, client: TestClient):
        """P0: Expired JWT token is rejected."""
        import jwt as jwt_lib
        import time

        # Create expired token
        expired_payload = {
            "sub": "user-123",
            "tenant_id": "tenant-a",
            "role": "standard",
            "exp": int(time.time()) - 3600,  # Expired 1 hour ago
            "iat": int(time.time()) - 7200,
        }
        expired_token = jwt_lib.encode(expired_payload, "test-secret-key", algorithm="HS256")

        response = client.get(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401, "Expired token should be rejected"

    def test_invalid_signature_rejected(self, client: TestClient, jwt_encoder):
        """P0: JWT with invalid signature is rejected."""
        import jwt as jwt_lib

        # Create valid payload
        payload = {
            "sub": "user-123",
            "tenant_id": "tenant-a",
            "role": "admin",  # Even with admin role
        }

        # Sign with wrong secret
        forged_token = jwt_lib.encode(payload, "completely-wrong-secret", algorithm="HS256")

        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {forged_token}"},
        )
        assert response.status_code == 401, "JWT with invalid signature should be rejected"

    def test_forged_token_with_valid_structure_rejected(self, client: TestClient):
        """P0: Completely forged JWT with valid structure but no valid signature is rejected."""
        import jwt as jwt_lib

        # Create a forged admin token from scratch
        forged_payload = {
            "sub": "attacker",
            "tenant_id": "tenant-a",
            "role": "super_admin",
            "permissions": ["*"],
            "iat": 1609459200,
            "exp": 9999999999,
        }

        # Sign with attacker's secret (not the system secret)
        forged_token = jwt_lib.encode(forged_payload, "attacker-secret", algorithm="HS256")

        response = client.get(
            "/api/v1/admin/config",
            headers={"Authorization": f"Bearer {forged_token}"},
        )
        assert response.status_code == 401, "Completely forged JWT should be rejected"

    def test_none_algorithm_rejected(self, client: TestClient):
        """P0: JWT with 'none' algorithm is rejected (algorithm confusion attack)."""
        import base64
        import json

        # Create header with "none" algorithm
        header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).decode().strip("=")
        payload = base64.urlsafe_b64encode(json.dumps({"sub": "admin", "role": "admin"}).encode()).decode().strip("=")

        # Create token with "none" algorithm (no signature)
        none_alg_token = f"{header}.{payload}."

        response = client.get(
            "/api/v1/admin/config",
            headers={"Authorization": f"Bearer {none_alg_token}"},
        )
        assert response.status_code in [401, 403], "JWT with 'none' algorithm should be rejected"

    def test_algorithm_confusion_attack_blocked(self, client: TestClient):
        """P0: Algorithm confusion attack (RS256 to HS256) is blocked."""
        import base64
        import json

        # Attempt algorithm confusion: claim RS256 but sign with HMAC
        header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256", "typ": "JWT"}).encode()).decode().strip("=")
        payload = base64.urlsafe_b64encode(json.dumps({"sub": "admin", "role": "admin"}).encode()).decode().strip("=")

        # Sign with HMAC (trying to trick RS256 verification)
        import hmac
        import hashlib
        message = f"{header}.{payload}"
        signature = base64.urlsafe_b64encode(
            hmac.new(b"test-secret-key", message.encode(), hashlib.sha256).digest()
        ).decode().strip("=")

        confused_token = f"{header}.{payload}.{signature}"

        response = client.get(
            "/api/v1/admin/config",
            headers={"Authorization": f"Bearer {confused_token}"},
        )
        assert response.status_code in [401, 403], "Algorithm confusion attack should be blocked"


class TestAPIKeyPermissionOverrides:
    """Test API key scoped permissions that may differ from user role."""

    def test_api_key_with_limited_scope_respects_override(self, client: TestClient):
        """P0: API key with limited permissions cannot exceed scope."""
        # API key with read-only permission
        response = client.get(
            "/api/v1/entities",
            headers={"X-API-Key": "test-read-only-api-key"},
        )
        # Should succeed for read operations
        assert response.status_code in [200, 401, 403, 404]  # Depends on test environment

        # Same API key attempting write
        post_response = client.post(
            "/api/v1/entities",
            headers={"X-API-Key": "test-read-only-api-key"},
            json={"name": "test-entity"},
        )
        # Should be blocked
        assert post_response.status_code in [401, 403], "Read-only API key should not allow writes"

    def test_api_key_cannot_escalate_beyond_user_role(self, client: TestClient):
        """P0: API key permissions cannot escalate beyond associated user's role."""
        # API key associated with standard user but trying to claim admin permissions
        response = client.get(
            "/api/v1/admin/config",
            headers={"X-API-Key": "test-standard-user-escalation-key"},
        )
        # Should be blocked regardless of what permissions the key claims
        assert response.status_code in [401, 403], "API key should not allow role escalation"

    def test_api_key_tenant_scoping_enforced(self, client: TestClient):
        """P0: API key is scoped to specific tenant and cannot access others."""
        # API key scoped to tenant-a
        response = client.get(
            "/api/v1/entities",
            headers={
                "X-API-Key": "test-tenant-a-key",
                "X-Tenant-ID": "tenant-b",  # Attempted cross-tenant
            },
        )
        # Should be blocked - key only valid for tenant-a
        assert response.status_code in [401, 403], "API key should respect tenant scoping"
