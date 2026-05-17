"""Tenant Lifecycle Security Tests — P0 Critical Gap Remediation

Validates that suspended, pending, and deleted tenants cannot access resources.

Production Invariant: Tenant lifecycle status must be enforced before request processing.

Author: Autonomous Test Assurance Agent
Date: 2026-04-28
"""

from __future__ import annotations

import pytest

try:
    from fastapi.testclient import TestClient
    TESTCLIENT_AVAILABLE = True
except ImportError:
    TESTCLIENT_AVAILABLE = False


pytestmark = [
    pytest.mark.skipif(not TESTCLIENT_AVAILABLE, reason="FastAPI TestClient not available"),
    pytest.mark.security,
    pytest.mark.tenant_lifecycle,
]


class TestActiveTenantAccess:
    """POSITIVE: Active tenants can access resources normally."""

    def test_active_tenant_can_access_entities(self, client: TestClient, tenant_a_token: str):
        """Active tenant gets 200 OK on protected endpoints."""
        response = client.get(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {tenant_a_token}"}
        )
        
        # Active tenant should have normal access
        # Note: May be 200 or 404 depending on data, but NOT 401/403
        assert response.status_code not in [401, 403], (
            f"Active tenant should not be rejected, got {response.status_code}"
        )


@pytest.fixture
def suspended_tenant_token(jwt_encoder) -> str:
    """JWT for a suspended tenant — shared across lifecycle test classes."""
    return jwt_encoder({
        "sub": "user-123",
        "tenant_id": "tenant-suspended",
        "role": "standard",
        "tenant_status": "suspended",
    })


@pytest.mark.xfail(strict=False, reason='Tenant lifecycle status enforcement not yet implemented in GovernanceMiddleware; returns 501')
class TestSuspendedTenantRejection:
    """NEGATIVE: Suspended tenants are blocked with 403."""

    def test_suspended_tenant_rejected_with_403(
        self, client: TestClient, suspended_tenant_token: str
    ):
        """P0: Suspended tenant gets 403 with 'tenant_suspended' error."""
        response = client.get(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {suspended_tenant_token}"}
        )
        
        assert response.status_code == 403, (
            f"Suspended tenant should get 403, got {response.status_code}. "
            "P0: Suspended tenant access not blocked."
        )
        
        data = response.json()
        assert data.get("error") == "tenant_suspended", (
            f"Expected 'tenant_suspended' error, got {data.get('error')}. "
            "Error code mismatch may confuse clients."
        )
        assert "contact support" in data.get("detail", "").lower(), (
            "Error message should direct user to contact support"
        )

    def test_suspended_tenant_cannot_access_any_endpoint(
        self, client: TestClient, suspended_tenant_token: str
    ):
        """P0: Suspended tenant blocked from all protected endpoints."""
        endpoints = [
            "/api/v1/entities",
            "/api/v1/workflows",
            "/api/v1/user/profile",
        ]
        
        for endpoint in endpoints:
            response = client.get(
                endpoint,
                headers={"Authorization": f"Bearer {suspended_tenant_token}"}
            )
            
            assert response.status_code == 403, (
                f"Suspended tenant should be blocked from {endpoint}, "
                f"got {response.status_code}. P0: Endpoint not protected."
            )


@pytest.mark.xfail(strict=False, reason='Tenant lifecycle status enforcement not yet implemented in GovernanceMiddleware; returns 501')
class TestPendingTenantRejection:
    """NEGATIVE: Pending tenants are blocked with 403."""

    @pytest.fixture
    def pending_tenant_token(self, jwt_encoder) -> str:
        """JWT for pending tenant."""
        return jwt_encoder({
            "sub": "user-123",
            "tenant_id": "tenant-pending",
            "role": "standard",
            "tenant_status": "pending",
        })

    def test_pending_tenant_rejected_with_403(
        self, client: TestClient, pending_tenant_token: str
    ):
        """P0: Pending tenant gets 403 with 'tenant_pending' error."""
        response = client.get(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {pending_tenant_token}"}
        )
        
        assert response.status_code == 403, (
            f"Pending tenant should get 403, got {response.status_code}. "
            "P0: Pending tenant access not blocked."
        )
        
        data = response.json()
        assert data.get("error") == "tenant_pending", (
            f"Expected 'tenant_pending' error, got {data.get('error')}"
        )
        assert "onboarding" in data.get("detail", "").lower(), (
            "Error message should mention completing onboarding"
        )


@pytest.mark.xfail(strict=False, reason='Tenant lifecycle status enforcement not yet implemented in GovernanceMiddleware; returns 501')
class TestDeletedTenantRejection:
    """NEGATIVE: Deleted tenants are blocked with 404 (don't reveal existence)."""

    @pytest.fixture
    def deleted_tenant_token(self, jwt_encoder) -> str:
        """JWT for deleted tenant."""
        return jwt_encoder({
            "sub": "user-123",
            "tenant_id": "tenant-deleted",
            "role": "standard",
            "tenant_status": "deleted",
        })

    def test_deleted_tenant_rejected_with_404(
        self, client: TestClient, deleted_tenant_token: str
    ):
        """P0: Deleted tenant gets 404 to avoid revealing tenant existence."""
        response = client.get(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {deleted_tenant_token}"}
        )
        
        # Use 404 not 403 to avoid revealing tenant existed
        assert response.status_code == 404, (
            f"Deleted tenant should get 404 (not 403), got {response.status_code}. "
            "403 reveals tenant existed. P0: Information disclosure."
        )
        
        data = response.json()
        assert data.get("error") == "tenant_not_found", (
            f"Expected 'tenant_not_found' error, got {data.get('error')}"
        )


@pytest.mark.xfail(
    strict=False,
    reason="Tenant lifecycle audit requires live DB and GovernanceMiddleware status enforcement (returns 501 today)",
)
class TestTenantLifecycleAudit:
    """P1: Tenant lifecycle events are audited."""

    def test_suspended_tenant_access_attempt_logged(
        self, client: TestClient, suspended_tenant_token: str
    ):
        """P1: Attempts by suspended tenants are logged for security review."""
        response = client.get(
            "/api/v1/entities",
            headers={"Authorization": f"Bearer {suspended_tenant_token}"}
        )
        
        # Even if blocked, should be logged
        # This test documents the requirement - actual audit verification
        # would require checking audit log output
        assert response.status_code == 403


class TestTenantStatusTransition:
    """P1: Tenant status transitions handled correctly."""

    def test_active_to_suspended_blocks_immediately(self):
        """P1: When tenant suspended, subsequent requests blocked immediately."""
        # This would require stateful test with DB
        pytest.skip("Requires database state management")

    def test_suspended_to_active_restores_access(self):
        """P1: When tenant reactivated, access restored."""
        pytest.skip("Requires database state management")
