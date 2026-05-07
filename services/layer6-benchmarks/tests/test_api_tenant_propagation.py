"""Hostile tenant isolation and context propagation tests.

Validates that Layer 6 handlers correctly extract tenant_id from the RequestContext
and propagate it strictly down to the BenchmarkRepository.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from src.api.main import app, _benchmark_repo
from src.api.deps import get_request_context
from value_fabric.shared.identity.context import RequestContext

@pytest.fixture
def mock_repo_hostile():
    """Create a pristine mock repo for asserting call arguments."""
    with patch("src.api.main._benchmark_repo") as repo:
        repo.list_datasets = AsyncMock(return_value=[])
        repo.get_dataset = AsyncMock(return_value=None)
        yield repo

@pytest.fixture
async def isolated_client():
    """Client that allows injecting specific tenant contexts."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

@pytest.mark.asyncio
async def test_list_datasets_propagates_tenant(isolated_client: AsyncClient, mock_repo_hostile: AsyncMock):
    """Verify list_datasets enforces the context tenant_id down to the repository."""
    hostile_tenant = "hostile-tenant-xyz"
    
    # Override the context dependency for this specific test
    app.dependency_overrides[get_request_context] = lambda: RequestContext(
        tenant_id=hostile_tenant,
        user_id="00000000-0000-0000-0000-000000000000",
        org_id="00000000-0000-0000-0000-000000000000",
        roles=["admin"],
        permissions=[],
        auth_source="mock",
        tenant_role="admin",
        isolation_tier="shared",
        request_id="test"
    )
    
    response = await isolated_client.get("/v1/benchmarks/datasets")
    assert response.status_code == 200
    
    # Crucial assertion: Did the handler pass the EXACT tenant_id to the DB layer?
    mock_repo_hostile.list_datasets.assert_called_once()
    _, kwargs = mock_repo_hostile.list_datasets.call_args
    assert kwargs.get("tenant_id") == hostile_tenant
    
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_dataset_propagates_tenant(isolated_client: AsyncClient, mock_repo_hostile: AsyncMock):
    """Verify get_dataset enforces the context tenant_id down to the repository."""
    hostile_tenant = "hostile-tenant-abc"
    
    app.dependency_overrides[get_request_context] = lambda: RequestContext(
        tenant_id=hostile_tenant,
        user_id="00000000-0000-0000-0000-000000000000",
        org_id="00000000-0000-0000-0000-000000000000",
        roles=["admin"],
        permissions=[],
        auth_source="mock",
        tenant_role="admin",
        isolation_tier="shared",
        request_id="test"
    )
    
    response = await isolated_client.get("/v1/benchmarks/datasets/some-dataset-id")
    assert response.status_code == 404  # Since mock returns None, it raises 404
    
    mock_repo_hostile.get_dataset.assert_called_once()
    _, kwargs = mock_repo_hostile.get_dataset.call_args
    assert kwargs.get("tenant_id") == hostile_tenant
    
    app.dependency_overrides.clear()
