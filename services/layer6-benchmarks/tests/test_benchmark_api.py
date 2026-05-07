"""Tests for Layer 6 Benchmark Service API."""


import pytest
from httpx import ASGITransport, AsyncClient

from src.api.main import app
import src.api.main as main_module
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture(autouse=True)
def setup_mock_repo(monkeypatch):
    """Setup mock repository before each test."""
    mock_repo = AsyncMock()
    mock_dataset = MagicMock()
    mock_dataset.dataset_id = "manufacturing-efficiency-2024"
    mock_dataset.industry = "manufacturing"
    mock_dataset.segment = "default"
    mock_dataset.version = "1.0.0"
    mock_dataset.name = "Manufacturing Efficiency"
    mock_dataset.description = "desc"
    mock_dataset.geography = "global"
    mock_dataset.data_source = "source"
    mock_dataset.metrics = {
        "oee_overall_equipment_effectiveness": MagicMock(
            name="oee",
            profile=MagicMock(p10=60, p25=70, p50=80, p75=90, p90=95, mean=80, std_dev=5, sample_size=1000)
        ),
        "defect_rate_percent": MagicMock(
            name="defect",
            profile=MagicMock(p10=1, p25=2, p50=3, p75=4, p90=5, mean=3, std_dev=1, sample_size=1000)
        ),
        "production_cycle_time_minutes": MagicMock(
            name="cycle_time",
            profile=MagicMock(p10=10, p25=20, p50=30, p75=40, p90=50, mean=30, std_dev=10, sample_size=1000)
        )
    }
    
    mock_dataset.get_metric = lambda m: mock_dataset.metrics.get(m)
    
    mock_repo.list_datasets.return_value = [mock_dataset]
    
    async def get_dataset(dataset_id, tenant_id="system"):
        if dataset_id == "manufacturing-efficiency-2024":
            return mock_dataset
        return None
        
    mock_repo.get_dataset = AsyncMock(side_effect=get_dataset)
    monkeypatch.setattr(main_module, "_benchmark_repo", mock_repo)
    yield mock_repo


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
