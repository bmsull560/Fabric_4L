"""Tests for Layer 6 Benchmark Service API."""


import pytest
from httpx import ASGITransport, AsyncClient

from src.api.main import _benchmark_store, _init_seed_data, app


@pytest.fixture(autouse=True)
def reset_store():
    """Reset benchmark store before each test."""
    _benchmark_store.clear()
    _init_seed_data()
    yield
    _benchmark_store.clear()


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "layer6-benchmarks"


@pytest.mark.asyncio
async def test_list_datasets(client: AsyncClient):
    """Test listing datasets."""
    response = await client.get("/v1/benchmarks/datasets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["dataset_id"] == "manufacturing-efficiency-2024"
    assert data[0]["industry"] == "manufacturing"


@pytest.mark.asyncio
async def test_get_dataset(client: AsyncClient):
    """Test getting dataset by ID."""
    response = await client.get("/v1/benchmarks/datasets/manufacturing-efficiency-2024")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == "manufacturing-efficiency-2024"
    assert "metrics" in data
    assert "oee_overall_equipment_effectiveness" in data["metrics"]


@pytest.mark.asyncio
async def test_get_dataset_not_found(client: AsyncClient):
    """Test getting non-existent dataset."""
    response = await client.get("/v1/benchmarks/datasets/non-existent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_compare(client: AsyncClient):
    """Test peer comparison."""
    payload = {
        "dataset_id": "manufacturing-efficiency-2024",
        "metric": "oee_overall_equipment_effectiveness",
        "company_value": "72.5",
        "industry": "manufacturing",
    }
    response = await client.post("/v1/benchmarks/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "percentile" in data
    assert "peer_median" in data
    assert "confidence" in data
    assert "assessment" in data


@pytest.mark.asyncio
async def test_validate(client: AsyncClient):
    """Test range validation."""
    payload = {
        "dataset_id": "manufacturing-efficiency-2024",
        "metric": "defect_rate_percent",
        "value": "2.0",
        "tolerance_percent": 10,
    }
    response = await client.post("/v1/benchmarks/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "is_valid" in data
    assert "expected_range" in data
    assert "severity" in data


@pytest.mark.asyncio
async def test_list_industries(client: AsyncClient):
    """Test listing industries."""
    response = await client.get("/v1/benchmarks/industries")
    assert response.status_code == 200
    data = response.json()
    assert "industries" in data
    assert "manufacturing" in data["industries"]
