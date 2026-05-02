"""
Tests for CRM webhook tenant isolation hardening.

Covers:
- tenant_id query parameter enforcement in production
- Rejection of webhooks for unknown/disabled tenants
- tenant_id propagation to sync_provider
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Patch problematic imports before loading the module
with patch.dict(
    "sys.modules",
    {
        "langgraph.checkpoint.postgres.aio": MagicMock(),
        "langgraph.checkpoint.postgres": MagicMock(),
        "langgraph.checkpoint": MagicMock(),
        "psycopg": MagicMock(),
    },
):
    from fastapi.testclient import TestClient
    from src.api.routes.crm_webhooks import router as crm_webhooks_router
    from src.database import get_db


@pytest.fixture(autouse=True)
def clear_env():
    """Clear environment overrides between tests."""
    original = os.environ.get("CRM_WEBHOOKS_REQUIRE_TENANT_ID", None)
    yield
    if original is None:
        os.environ.pop("CRM_WEBHOOKS_REQUIRE_TENANT_ID", None)
    else:
        os.environ["CRM_WEBHOOKS_REQUIRE_TENANT_ID"] = original


@pytest.fixture
def mock_db():
    """Create a mock database session with integration lookup support."""
    from sqlalchemy.ext.asyncio import AsyncSession

    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()

    # Default: no integration found
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result

    yield session


def _make_client(mock_db):
    """Build a minimal FastAPI app with just the CRM webhooks router."""
    from fastapi import FastAPI

    app = FastAPI()

    async def _override():
        yield mock_db

    app.dependency_overrides[get_db] = _override
    app.include_router(crm_webhooks_router, prefix="/v1")
    return TestClient(app)


def _make_integration(enabled: bool = True):
    """Create a mock Integration object."""
    from src.models.account import CRMProvider
    from src.models.integration import Integration, IntegrationStatus

    integration = MagicMock(spec=Integration)
    integration.enabled = enabled
    integration.tenant_id = "tenant-test"
    integration.provider = CRMProvider.SALESFORCE
    integration.refresh_token_encrypted = None
    integration.instance_url = "https://test.salesforce.com"
    integration.sync_status = IntegrationStatus.IDLE
    return integration


class TestSalesforceWebhookTenantIsolation:
    """Test Salesforce webhook tenant isolation."""

    def test_rejects_missing_tenant_id_when_required(self, mock_db):
        """Webhook must reject requests without tenant_id in production."""
        os.environ["CRM_WEBHOOKS_REQUIRE_TENANT_ID"] = "true"
        client = _make_client(mock_db)

        response = client.post("/v1/webhooks/crm/salesforce", json={})

        assert response.status_code == 400
        assert "tenant_id" in response.json()["detail"]

    def test_allows_missing_tenant_id_when_not_required(self, mock_db):
        """Webhook allows requests without tenant_id when not required."""
        os.environ["CRM_WEBHOOKS_REQUIRE_TENANT_ID"] = "false"
        client = _make_client(mock_db)

        with patch("src.api.routes.crm_webhooks.CRMSyncService") as mock_sync_class:
            mock_sync = AsyncMock()
            mock_sync_class.return_value = mock_sync
            mock_sync.sync_provider.return_value = {"synced": 0, "updated": 0, "failed": 0}

            response = client.post("/v1/webhooks/crm/salesforce", json={})

            assert response.status_code == 202
            # Should default to "default" tenant
            call_kwargs = mock_sync.sync_provider.call_args[1]
            assert call_kwargs.get("tenant_id") == "default"

    def test_rejects_unknown_tenant(self, mock_db):
        """Webhook must reject tenant with no Salesforce integration."""
        os.environ["CRM_WEBHOOKS_REQUIRE_TENANT_ID"] = "true"
        client = _make_client(mock_db)

        response = client.post(
            "/v1/webhooks/crm/salesforce?tenant_id=unknown-tenant",
            json={},
        )

        assert response.status_code == 404
        assert "No Salesforce integration configured" in response.json()["detail"]

    def test_rejects_disabled_integration(self, mock_db):
        """Webhook must reject tenant with disabled Salesforce integration."""
        os.environ["CRM_WEBHOOKS_REQUIRE_TENANT_ID"] = "true"
        client = _make_client(mock_db)

        disabled_integration = _make_integration(enabled=False)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = disabled_integration
        mock_db.execute.return_value = mock_result

        response = client.post(
            "/v1/webhooks/crm/salesforce?tenant_id=tenant-test",
            json={},
        )

        assert response.status_code == 403
        assert "disabled" in response.json()["detail"]

    def test_passes_tenant_id_to_sync(self, mock_db):
        """Webhook must pass the correct tenant_id to sync_provider."""
        os.environ["CRM_WEBHOOKS_REQUIRE_TENANT_ID"] = "true"
        client = _make_client(mock_db)

        enabled_integration = _make_integration(enabled=True)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = enabled_integration
        mock_db.execute.return_value = mock_result

        with patch("src.api.routes.crm_webhooks.CRMSyncService") as mock_sync_class:
            mock_sync = AsyncMock()
            mock_sync_class.return_value = mock_sync
            mock_sync.sync_provider.return_value = {"synced": 1, "updated": 0, "failed": 0}

            response = client.post(
                "/v1/webhooks/crm/salesforce?tenant_id=tenant-test",
                json={
                    "data": {
                        "payload": {
                            "RecordId": "001TEST123456789",
                            "ChangeEventHeader": {
                                "entityName": "Account",
                                "recordIds": ["001TEST123456789"],
                                "changeType": "UPDATE",
                            },
                        }
                    }
                },
            )

            assert response.status_code == 202
            call_kwargs = mock_sync.sync_provider.call_args[1]
            assert call_kwargs.get("tenant_id") == "tenant-test"


class TestHubSpotWebhookTenantIsolation:
    """Test HubSpot webhook tenant isolation."""

    def test_rejects_missing_tenant_id_when_required(self, mock_db):
        """Webhook must reject requests without tenant_id in production."""
        os.environ["CRM_WEBHOOKS_REQUIRE_TENANT_ID"] = "true"
        client = _make_client(mock_db)

        response = client.post("/v1/webhooks/crm/hubspot", json=[])

        assert response.status_code == 400
        assert "tenant_id" in response.json()["detail"]

    def test_passes_tenant_id_to_sync(self, mock_db):
        """Webhook must pass the correct tenant_id to sync_provider."""
        os.environ["CRM_WEBHOOKS_REQUIRE_TENANT_ID"] = "true"
        client = _make_client(mock_db)

        from src.models.account import CRMProvider
        from src.models.integration import Integration

        enabled_integration = MagicMock(spec=Integration)
        enabled_integration.enabled = True
        enabled_integration.provider = CRMProvider.HUBSPOT
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = enabled_integration
        mock_db.execute.return_value = mock_result

        with patch("src.api.routes.crm_webhooks.CRMSyncService") as mock_sync_class:
            mock_sync = AsyncMock()
            mock_sync_class.return_value = mock_sync
            mock_sync.sync_provider.return_value = {"synced": 1, "updated": 0, "failed": 0}

            response = client.post(
                "/v1/webhooks/crm/hubspot?tenant_id=tenant-test",
                json=[
                    {
                        "eventId": 1,
                        "subscriptionType": "company.propertyChange",
                        "objectId": 789012345,
                    }
                ],
            )

            assert response.status_code == 202
            call_kwargs = mock_sync.sync_provider.call_args[1]
            assert call_kwargs.get("tenant_id") == "tenant-test"
