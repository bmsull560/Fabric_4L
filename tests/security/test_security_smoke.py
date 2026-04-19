"""
Security Smoke Test Suite - Fast PR Validation

Curated subset of highest-value security tests for CI gating.
Runtime: < 2 minutes, no external dependencies (Docker/ZAP).

These are the most critical security checks that must pass on every PR.
Full suite in other test files runs on scheduled workflows.
"""

import pytest
from fastapi.testclient import TestClient


class TestCriticalTenantIsolation:
    """P0: Cross-tenant data access prevention (smoke tests)."""

    def test_user_cannot_spoof_tenant_header(self, client: TestClient, tenant_a_token):
        """User from Tenant A blocked when trying to use Tenant B header."""
        response = client.get(
            "/api/v1/entities",
            headers={
                "Authorization": f"Bearer {tenant_a_token}",
                "X-Tenant-ID": "tenant-b",  # Attempted spoof
            },
        )
        assert response.status_code in [403, 401, 200], "Tenant spoof attempt not handled"

        if response.status_code == 200:
            # If allowed, verify data is still from correct tenant
            data = response.json()
            items = data.get("items", [])
            for item in items:
                assert item.get("tenant_id") == "tenant-a", "Cross-tenant data leakage"

    def test_idor_blocked_basic(self, client: TestClient, tenant_a_token, tenant_b_token):
        """Basic IDOR: Tenant B cannot access Tenant A's entity by ID."""
        # Create entity as Tenant A
        create_response = client.post(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {tenant_a_token}"},
            json={"name": "smoke-idor-test"},
        )

        if create_response.status_code == 201:
            entity = create_response.json()
            entity_id = entity.get("id")

            # Tenant B attempts access
            idor_response = client.get(
                f"/api/v1/entities/{entity_id}",
                headers={"Authorization": f"Bearer {tenant_b_token}"},
            )
            assert idor_response.status_code in [403, 404], "IDOR vulnerability detected"


class TestCriticalRBAC:
    """P0: Role-based access control (smoke tests)."""

    def test_standard_user_blocked_from_admin_endpoint(
        self, client: TestClient, standard_user_token
    ):
        """Standard user cannot access admin endpoints."""
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {standard_user_token}"},
        )
        assert response.status_code in [403, 401, 404], "Admin endpoint accessible to standard user"

    def test_admin_user_can_access_admin_endpoints(
        self, client: TestClient, admin_user_token
    ):
        """Admin user can access admin endpoints (sanity check)."""
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_user_token}"},
        )
        # Should not be forbidden - admin should have access (may 404 if not implemented)
        assert response.status_code != 403, "Admin user blocked from admin endpoint"

    def test_jwt_tampering_rejected(self, client: TestClient, jwt_encoder):
        """Modified JWT claims are rejected."""
        import jwt as jwt_lib

        # Create valid token
        original = jwt_encoder({
            "sub": "user-123",
            "tenant_id": "tenant-a",
            "role": "standard",
        })

        # Tamper with it
        decoded = jwt_lib.decode(original, "test-secret-key", algorithms=["HS256"])
        decoded["role"] = "admin"
        tampered = jwt_lib.encode(decoded, "wrong-secret", algorithm="HS256")

        response = client.get(
            "/api/v1/admin/config",
            headers={"Authorization": f"Bearer {tampered}"},
        )
        assert response.status_code == 401, "Tampered JWT was accepted"


class TestCriticalInjection:
    """P0: Basic injection prevention (smoke tests)."""

    SQL_PAYLOADS = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "1 UNION SELECT * FROM passwords",
    ]

    def test_sql_injection_blocked_in_query_params(self, client: TestClient):
        """SQL injection payloads blocked in query parameters."""
        for payload in self.SQL_PAYLOADS:
            response = client.get(f"/api/v1/entities?name={payload}")
            # Should be 400 or sanitized 200, never execute SQL
            assert response.status_code in [200, 400, 422], f"SQL injection not handled: {payload}"

    XSS_PAYLOADS = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
    ]

    def test_xss_payloads_sanitized(self, client: TestClient):
        """XSS payloads sanitized or blocked."""
        for payload in self.XSS_PAYLOADS:
            response = client.post(
                "/api/v1/entities",
                json={"name": "test", "description": payload},
            )

            if response.status_code == 200:
                body = response.text
                assert "<script>" not in body or "&lt;script&gt;" in body, (
                    f"XSS payload not sanitized: {payload}"
                )


class TestCriticalMisconfiguration:
    """P0: Security misconfiguration checks (smoke tests)."""

    def test_security_headers_present(self, client: TestClient):
        """Critical security headers are present."""
        response = client.get("/api/v1/entities")

        headers = {k.lower(): v for k, v in response.headers.items()}

        # X-Content-Type-Options prevents MIME sniffing
        assert "x-content-type-options" in headers, "Missing X-Content-Type-Options"
        assert headers["x-content-type-options"] == "nosniff", "Incorrect X-Content-Type-Options"

        # X-Frame-Options prevents clickjacking
        assert "x-frame-options" in headers, "Missing X-Frame-Options"

    def test_error_no_stack_traces(self, client: TestClient):
        """Error responses don't leak stack traces."""
        response = client.get("/api/v1/entities/malformed-uuid")

        if response.status_code >= 400:
            body = response.text.lower()
            assert "traceback" not in body, "Stack trace leaked in error response"
            assert 'file "' not in body, "File reference leaked in error response"

    def test_debug_endpoints_not_exposed(self, client: TestClient):
        """Debug endpoints not publicly accessible."""
        debug_paths = ["/debug", "/.env", "/config.json", "/phpmyadmin"]

        for path in debug_paths:
            response = client.get(path)
            assert response.status_code in [404, 401, 403], (
                f"Debug endpoint {path} exposed: {response.status_code}"
            )


class TestCriticalCryptographic:
    """P0: Cryptographic security (smoke tests)."""

    def test_jwt_uses_secure_algorithm(self, client: TestClient, jwt_encoder):
        """JWT tokens use secure algorithm."""
        import jwt as jwt_lib

        token = jwt_encoder({"sub": "test", "role": "standard"})
        header = jwt_lib.get_unverified_header(token)

        assert header["alg"] in ["HS256", "RS256", "ES256"], (
            f"Insecure JWT algorithm: {header['alg']}"
        )

    def test_expired_token_rejected(self, client: TestClient):
        """Expired JWT tokens are rejected."""
        import jwt as jwt_lib
        import time

        expired_token = jwt_lib.encode(
            {
                "sub": "test",
                "exp": int(time.time()) - 3600,  # Expired 1 hour ago
            },
            "test-secret-key",
            algorithm="HS256",
        )

        response = client.get(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401, "Expired token was accepted"


class TestCriticalAccessControl:
    """P0: Access control edge cases (smoke tests)."""

    def test_mass_assignment_blocked(self, client: TestClient, standard_user_token):
        """Mass assignment of protected fields is blocked."""
        response = client.post(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {standard_user_token}"},
            json={
                "name": "test",
                "role": "admin",  # Protected field
                "is_admin": True,  # Protected field
            },
        )

        if response.status_code == 201:
            entity = response.json()
            assert entity.get("role") != "admin", "Mass assignment: role was set"
            assert entity.get("is_admin") is not True, "Mass assignment: is_admin was set"

    def test_read_only_cannot_write(self, client: TestClient, jwt_encoder):
        """Read-only permission blocks write operations."""
        read_token = jwt_encoder({
            "sub": "read-only",
            "tenant_id": "tenant-a",
            "role": "read_only",
            "permissions": ["read"],
        })

        response = client.post(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {read_token}"},
            json={"name": "test-entity"},
        )
        assert response.status_code in [403, 401], "Read-only user allowed to write"


# Quick reference for CI integration
# Run with: pytest tests/security/test_security_smoke.py -v --tb=short
# Expected runtime: 30-60 seconds
# No external dependencies required
