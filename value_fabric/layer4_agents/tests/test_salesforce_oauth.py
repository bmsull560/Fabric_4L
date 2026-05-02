"""
Tests for Salesforce OAuth token refresh and integration hardening.

Covers:
- Token refresh success/failure
- Credential encryption/decryption with refresh token
- Tenant isolation in scheduler (no empty tenant_id)
- Environment fallback disabled
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.account import CRMProvider
from src.models.integration import Integration, IntegrationStatus
from src.services.encryption_service import DEFAULT_KEY_ID, EncryptionService
from src.services.integration_service import (
    IntegrationService,
    IntegrationValidationError,
)


@pytest.fixture(autouse=True)
def clear_encryption_cache():
    """Clear encryption cache between tests to prevent pollution."""
    from collections import OrderedDict

    EncryptionService._MASTER_KEY = None
    EncryptionService._key_cache = OrderedDict()
    yield


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def sample_integration() -> Integration:
    """Create a sample Salesforce integration with encrypted refresh token."""
    return Integration(
        id="550e8400-e29b-41d4-a716-446655440000",
        tenant_id="tenant-123",
        provider=CRMProvider.SALESFORCE,
        enabled=True,
        credentials_encrypted=b"encrypted_credentials",
        refresh_token_encrypted=b"encrypted_refresh",
        encryption_key_id=DEFAULT_KEY_ID,
        instance_url="https://test.salesforce.com",
        salesforce_org_id="00Dxx0000001234",
        sync_status=IntegrationStatus.IDLE,
    )


class TestSalesforceTokenRefresh:
    """Test suite for Salesforce OAuth token refresh."""

    @pytest.mark.asyncio
    async def test_refresh_salesforce_token_success(self, mock_db, sample_integration):
        """Test successful token refresh updates credentials."""
        service = IntegrationService(mock_db)

        # Mock decrypt to return a refresh token
        with patch.object(
            EncryptionService, "decrypt", AsyncMock(return_value="old_refresh_token")
        ):
            with patch.object(
                EncryptionService, "encrypt", AsyncMock(return_value=b"new_encrypted")
            ):
                # Mock httpx response
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "access_token": "new_access_token_123",
                    "instance_url": "https://new-instance.salesforce.com",
                }

                with patch(
                    "httpx.AsyncClient.post", AsyncMock(return_value=mock_response)
                ):
                    with patch.dict(
                        os.environ,
                        {
                            "SALESFORCE_CLIENT_ID": "test_client_id",
                            "SALESFORCE_CLIENT_SECRET": "test_client_secret",
                            "CREDENTIALS_MASTER_KEY": "test-master-key-12345678901234567890123",
                            "ALLOW_EPHEMERAL_ENCRYPTION": "true",
                        },
                    ):
                        result = await service.refresh_salesforce_token(
                            sample_integration
                        )

        assert result["api_key"] == "new_access_token_123"
        assert sample_integration.instance_url == "https://new-instance.salesforce.com"
        assert sample_integration.sync_status == IntegrationStatus.IDLE
        mock_db.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_refresh_salesforce_token_no_refresh_token(self, mock_db):
        """Test that missing refresh token raises validation error."""
        service = IntegrationService(mock_db)
        integration = Integration(
            id="550e8400-e29b-41d4-a716-446655440000",
            tenant_id="tenant-123",
            provider=CRMProvider.SALESFORCE,
            enabled=True,
            credentials_encrypted=b"encrypted",
            refresh_token_encrypted=None,
            encryption_key_id=DEFAULT_KEY_ID,
        )

        with pytest.raises(IntegrationValidationError) as exc:
            await service.refresh_salesforce_token(integration)

        assert "No refresh token available" in str(exc.value)

    @pytest.mark.asyncio
    async def test_refresh_salesforce_token_http_401(self, mock_db, sample_integration):
        """Test that 401 response marks integration as degraded."""
        service = IntegrationService(mock_db)

        with patch.object(
            EncryptionService, "decrypt", AsyncMock(return_value="old_refresh_token")
        ):
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"

            with patch(
                "httpx.AsyncClient.post", AsyncMock(return_value=mock_response)
            ):
                with patch.dict(
                    os.environ,
                    {
                        "SALESFORCE_CLIENT_ID": "test_client_id",
                        "SALESFORCE_CLIENT_SECRET": "test_client_secret",
                        "CREDENTIALS_MASTER_KEY": "test-master-key-12345678901234567890123",
                        "ALLOW_EPHEMERAL_ENCRYPTION": "true",
                    },
                ):
                    with pytest.raises(IntegrationValidationError) as exc:
                        await service.refresh_salesforce_token(sample_integration)

        assert "Token refresh failed" in str(exc.value)
        assert sample_integration.sync_status == IntegrationStatus.DEGRADED
        mock_db.commit.assert_awaited()


class TestSchedulerTenantIsolation:
    """Test that scheduler never bypasses tenant isolation."""

    def test_scheduler_never_sets_empty_tenant_id(self):
        """Verify that CRMSyncScheduler does not set app.tenant_id = ''."""
        from src.services.crm_sync_scheduler import CRMSyncScheduler

        source = CRMSyncScheduler.__init__.__code__.co_consts
        # Check that the old unsafe pattern is not present in the module source
        import inspect

        module_source = inspect.getsource(CRMSyncScheduler)
        assert "app.tenant_id = ''" not in module_source
        assert "app.tenant_id = \"\"" not in module_source
        assert "app.tenant_id =" in module_source  # But proper usage exists


class TestNoEnvFallback:
    """Test that CRM sync service never falls back to environment variables."""

    def test_no_env_fallback_in_source(self):
        """Verify ALLOW_ENV_CRM_FALLBACK is removed from sync service."""
        from src.services.crm_sync_service import CRMSyncService
        import inspect

        module_source = inspect.getsource(CRMSyncService)
        assert "ALLOW_ENV_CRM_FALLBACK" not in module_source
        assert "os.getenv(\"CRM_API_KEY\")" not in module_source
