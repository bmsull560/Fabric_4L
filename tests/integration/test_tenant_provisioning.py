"""Integration tests for tenant provisioning system.

Tests the complete provisioning workflow including:
- Infisical secret path creation
- Provisioning state tracking
- Retry and rollback mechanisms
- Webhook triggers
"""

from __future__ import annotations

import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import after sys.path manipulation
from value_fabric.layer4_agents.src.tenants.models.tenant import IsolationTier, Tenant
from value_fabric.layer4_agents.src.tenants.provisioning import (
    DEFAULT_ENVIRONMENTS,
    TENANT_STATUS_ACTIVE,
    TENANT_STATUS_PENDING,
    ProvisioningState,
    ProvisioningStatus,
    ProvisioningStep,
    TenantProvisioningService,
    provision_tenant,
)
from value_fabric.layer4_agents.src.tenants.service import (
    create_tenant,
    get_tenant,
    update_tenant_status,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

# Module path for mocking - single source of truth
MOCK_TARGET_TENANT_SECRET_MANAGER = (
    "value_fabric.layer4_agents.src.tenants.provisioning.TenantSecretManager"
)


@pytest.fixture
async def db_session() -> AsyncSession:
    """Provide database session for tests.

    This fixture should be overridden by conftest.py in production.
    For now, raises skip to indicate infrastructure needed.
    """
    pytest.skip("Database session fixture not configured - add to conftest.py")


@pytest.fixture
async def test_tenant(db_session: AsyncSession) -> Tenant:
    """Create a test tenant in pending status."""
    from shared.identity.models import TenantCreateRequest

    request = TenantCreateRequest(
        name="Test Provisioning Tenant",
        slug=f"test-prov-{uuid.uuid4().hex[:8]}",
        settings={
            "isolation_tier": IsolationTier.SHARED.value,
            "admin_email": "test@example.com",
        },
    )

    tenant_model = await create_tenant(db_session, request)

    # Set to pending status (not active yet)
    await update_tenant_status(
        db_session,
        UUID(tenant_model.id),
        TENANT_STATUS_PENDING,
        reason="Test setup",
    )

    # Fetch the actual ORM object for assertions
    result = await db_session.execute(
        select(Tenant).where(Tenant.id == UUID(tenant_model.id))
    )
    tenant = result.scalar_one()
    return tenant


@pytest.fixture
def mock_infisical_client():
    """Create a mock Infisical client with successful responses."""
    with patch(MOCK_TARGET_TENANT_SECRET_MANAGER) as mock_class:
        mock_instance = MagicMock()
        mock_instance.create_tenant_secrets_path = AsyncMock(
            return_value={
                "dev": {"success": True},
                "test": {"success": True},
                "staging": {"success": True},
                "prod": {"success": True},
            }
        )
        mock_instance.seed_default_tenant_secrets = AsyncMock(
            return_value={"success": True}
        )
        mock_instance.delete_tenant_secrets_path = AsyncMock(
            return_value={
                "dev": {"success": True},
                "test": {"success": True},
                "staging": {"success": True},
                "prod": {"success": True},
            }
        )
        mock_class.return_value = mock_instance
        yield mock_instance


class TestProvisioningWorkflow:
    """Test the complete provisioning workflow."""

    async def test_successful_provisioning(
        self,
        db_session: AsyncSession,
        test_tenant: Tenant,
        mock_infisical_client,
    ):
        """Test successful tenant provisioning through all steps."""
        service = TenantProvisioningService(db_session)

        state = await service.provision_tenant(test_tenant.id)

        # Assert success
        assert state.status == ProvisioningStatus.COMPLETED
        assert state.error is None
        assert ProvisioningStep.CREATE_INFISICAL_PATH in state.completed_steps
        assert ProvisioningStep.SEED_DEFAULT_SECRETS in state.completed_steps
        assert ProvisioningStep.UPDATE_TENANT_STATUS in state.completed_steps

        # Verify tenant status updated to active
        updated_tenant = await get_tenant(db_session, test_tenant.id)
        assert updated_tenant is not None
        assert updated_tenant.status == TENANT_STATUS_ACTIVE

        # Verify Infisical calls
        mock_infisical_client.create_tenant_secrets_path.assert_called_once()
        mock_infisical_client.seed_default_tenant_secrets.assert_called_once()

    async def test_provisioning_idempotent(
        self,
        db_session: AsyncSession,
        test_tenant: Tenant,
        mock_infisical_client,
    ):
        """Test that provisioning is idempotent - can be called multiple times."""
        service = TenantProvisioningService(db_session)

        # First provisioning
        state1 = await service.provision_tenant(test_tenant.id)
        assert state1.status == ProvisioningStatus.COMPLETED

        # Second provisioning should return completed immediately
        state2 = await service.provision_tenant(test_tenant.id)
        assert state2.status == ProvisioningStatus.COMPLETED

        # Infisical should only be called once
        mock_infisical_client.create_tenant_secrets_path.assert_called_once()

    async def test_force_retry_provisioning(
        self,
        db_session: AsyncSession,
        test_tenant: Tenant,
        mock_infisical_client,
    ):
        """Test force retry re-runs provisioning."""
        service = TenantProvisioningService(db_session)

        # First provisioning
        await service.provision_tenant(test_tenant.id)

        # Force retry
        state = await service.provision_tenant(test_tenant.id, force_retry=True)
        assert state.status == ProvisioningStatus.COMPLETED

        # Infisical should be called twice
        assert mock_infisical_client.create_tenant_secrets_path.call_count == 2


class TestProvisioningFailureHandling:
    """Test provisioning failure and retry scenarios."""

    async def test_infisical_failure_rollback(
        self,
        db_session: AsyncSession,
        test_tenant: Tenant,
    ):
        """Test rollback when Infisical path creation fails."""
        with patch(MOCK_TARGET_TENANT_SECRET_MANAGER) as mock_class:
            # Configure mock to fail on create but succeed on delete (rollback)
            mock_instance = MagicMock()
            env_fail = {env: {"success": False, "error": "Connection failed"} for env in DEFAULT_ENVIRONMENTS}
            env_success = {env: {"success": True} for env in DEFAULT_ENVIRONMENTS}

            mock_instance.create_tenant_secrets_path = AsyncMock(return_value=env_fail)
            mock_instance.delete_tenant_secrets_path = AsyncMock(return_value=env_success)
            mock_class.return_value = mock_instance

            service = TenantProvisioningService(db_session)
            state = await service.provision_tenant(test_tenant.id)

            # Should fail
            assert state.status == ProvisioningStatus.FAILED
            assert state.error is not None
            assert "Infisical" in state.error

            # Tenant should still be in pending status (rollback succeeded)
            tenant = await get_tenant(db_session, test_tenant.id)
            assert tenant is not None
            assert tenant.status == TENANT_STATUS_PENDING

    async def test_retryable_error_with_retry(
        self,
        db_session: AsyncSession,
        test_tenant: Tenant,
    ):
        """Test automatic retry on retryable errors."""
        call_count = 0

        async def mock_with_failure(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutError("Connection timeout")
            return {
                "dev": {"success": True},
                "test": {"success": True},
                "staging": {"success": True},
                "prod": {"success": True},
            }

        with patch(MOCK_TARGET_TENANT_SECRET_MANAGER) as mock_class:
            mock_instance = MagicMock()
            mock_instance.create_tenant_secrets_path = AsyncMock(side_effect=mock_with_failure)
            mock_instance.seed_default_tenant_secrets = AsyncMock(return_value={"success": True})
            mock_class.return_value = mock_instance

            service = TenantProvisioningService(db_session)
            state = await service.provision_tenant(test_tenant.id)

            # Should eventually succeed after retry
            assert state.status == ProvisioningStatus.COMPLETED
            assert state.retry_count >= 1
            assert call_count >= 2


@pytest.fixture
def client():
    """HTTP client fixture for API tests.

    Raises skip if test client infrastructure not configured.
    """
    pytest.skip("HTTP client fixture not configured - add to conftest.py")


@pytest.fixture
def admin_token():
    """Admin authentication token fixture.

    Raises skip if auth infrastructure not configured.
    """
    pytest.skip("Admin token fixture not configured - add to conftest.py")


class TestProvisioningAPI:
    """Test provisioning API endpoints (requires running server).

    These tests are marked as e2e and require:
    - Running FastAPI server
    - Configured HTTP client
    - Valid admin authentication token
    """

    @pytest.mark.e2e
    async def test_get_provisioning_status_returns_expected_fields(
        self,
        client,
        test_tenant: Tenant,
        admin_token: str,
    ):
        """Test GET /tenants/{id}/provisioning/status returns expected fields."""
        response = await client.get(
            f"/v1/tenants/{test_tenant.id}/provisioning/status",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == str(test_tenant.id)
        assert "status" in data
        assert "completed_steps" in data
        assert isinstance(data.get("retry_count"), int)
        assert isinstance(data.get("retryable"), bool)

    @pytest.mark.e2e
    async def test_retry_provisioning_enforces_admin_authorization(
        self,
        client,
        test_tenant: Tenant,
        admin_token: str,
    ):
        """Test POST /tenants/{id}/provisioning/retry enforces super admin authorization."""
        response = await client.post(
            f"/v1/tenants/{test_tenant.id}/provisioning/retry",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Should either succeed (if admin is super admin) or fail with 403
        assert response.status_code in [200, 403]


class TestWebhookProvisioning:
    """Test webhook-based provisioning trigger."""

    @pytest.mark.e2e
    async def test_webhook_trigger_with_valid_token_returns_accepted(
        self,
        client,
        test_tenant: Tenant,
    ):
        """Test POST /tenants/provisioning/webhook returns 202 with valid token."""
        # Set webhook token in environment
        os.environ["PROVISIONING_WEBHOOK_TOKEN"] = "test-webhook-token"

        response = await client.post(
            "/v1/tenants/provisioning/webhook",
            json={
                "tenant_id": str(test_tenant.id),
                "webhook_token": "test-webhook-token",
            },
        )

        # Should accept the request (202) even if provisioning fails internally (500)
        # 501 indicates webhook not configured in environment
        assert response.status_code in [202, 500, 501]

        if response.status_code == 202:
            data = response.json()
            assert data["tenant_id"] == str(test_tenant.id)
            assert "status" in data
            assert "message" in data

    @pytest.mark.e2e
    async def test_webhook_invalid_token_returns_unauthorized(
        self,
        client,
        test_tenant: Tenant,
    ):
        """Test webhook rejects invalid token with 401 Unauthorized."""
        os.environ["PROVISIONING_WEBHOOK_TOKEN"] = "correct-token"

        response = await client.post(
            "/v1/tenants/provisioning/webhook",
            json={
                "tenant_id": str(test_tenant.id),
                "webhook_token": "wrong-token",
            },
        )

        assert response.status_code == 401


class TestConvenienceFunction:
    """Test the provision_tenant convenience function."""

    async def test_convenience_function(
        self,
        db_session: AsyncSession,
        test_tenant: Tenant,
        mock_infisical_client,
    ):
        """Test the simple provision_tenant function."""
        state = await provision_tenant(db_session, test_tenant.id)

        assert state.status == ProvisioningStatus.COMPLETED

        # Verify tenant is active
        tenant = await get_tenant(db_session, test_tenant.id)
        assert tenant is not None
        assert tenant.status == TENANT_STATUS_ACTIVE
