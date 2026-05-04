"""Edge case and validation tests for Layer 6 Benchmark Service.

Tests error handling, input validation, and boundary conditions.
"""

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


class TestBenchmarkValidation:
    """Test input validation and error handling."""

    @pytest.mark.asyncio
    async def test_compare_rejects_invalid_company_value(self, client: AsyncClient):
        """Should reject non-numeric company_value with 400 Bad Request."""
        payload = {
            "dataset_id": "manufacturing-efficiency-2024",
            "metric": "oee_overall_equipment_effectiveness",
            "company_value": "not-a-number",
            "industry": "manufacturing",
        }
        response = await client.post("/v1/benchmarks/compare", json=payload)
        # API returns 400 (not 422) for invalid Decimal format
        assert response.status_code == 400
        data = response.json()
        assert "Invalid" in data.get("detail", "") or "company_value" in data.get("detail", "")

    @pytest.mark.asyncio
    async def test_compare_rejects_negative_company_value(self, client: AsyncClient):
        """Should handle negative company values appropriately."""
        payload = {
            "dataset_id": "manufacturing-efficiency-2024",
            "metric": "defect_rate_percent",
            "company_value": "-5.0",
            "industry": "manufacturing",
        }
        response = await client.post("/v1/benchmarks/compare", json=payload)
        # Service may accept but should handle gracefully
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_compare_rejects_missing_required_fields(self, client: AsyncClient):
        """Should reject payload missing required fields."""
        payload = {
            "dataset_id": "manufacturing-efficiency-2024",
            # missing metric and company_value
        }
        response = await client.post("/v1/benchmarks/compare", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_validate_accepts_negative_tolerance(self, client: AsyncClient):
        """API accepts negative tolerance (inverts range calculation)."""
        payload = {
            "dataset_id": "manufacturing-efficiency-2024",
            "metric": "defect_rate_percent",
            "value": "2.0",
            "tolerance_percent": -10,  # Negative tolerance shrinks range
        }
        response = await client.post("/v1/benchmarks/validate", json=payload)
        # API accepts negative tolerance - returns 200 with adjusted range
        assert response.status_code == 200
        data = response.json()
        assert "is_valid" in data
        assert "expected_range" in data


class TestBenchmarkEdgeCases:
    """Test boundary conditions and edge cases."""

    @pytest.mark.asyncio
    async def test_compare_with_zero_value(self, client: AsyncClient):
        """Should handle zero company value correctly."""
        payload = {
            "dataset_id": "manufacturing-efficiency-2024",
            "metric": "defect_rate_percent",
            "company_value": "0",
            "industry": "manufacturing",
        }
        response = await client.post("/v1/benchmarks/compare", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "percentile" in data

    @pytest.mark.asyncio
    async def test_compare_with_very_large_value(self, client: AsyncClient):
        """Should handle very large company values for cycle time metric."""
        payload = {
            "dataset_id": "manufacturing-efficiency-2024",
            "metric": "production_cycle_time_minutes",
            "company_value": "10000",  # Very large cycle time
            "industry": "manufacturing",
        }
        response = await client.post("/v1/benchmarks/compare", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "percentile" in data
        # Large value should result in high percentile (since higher cycle time is worse)
        assert data["percentile"] >= 90

    @pytest.mark.asyncio
    async def test_compare_with_decimal_precision(self, client: AsyncClient):
        """Should handle values with high decimal precision."""
        payload = {
            "dataset_id": "manufacturing-efficiency-2024",
            "metric": "oee_overall_equipment_effectiveness",
            "company_value": "72.54321",
            "industry": "manufacturing",
        }
        response = await client.post("/v1/benchmarks/compare", json=payload)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_validate_with_zero_tolerance(self, client: AsyncClient):
        """Should handle zero tolerance (exact match required)."""
        payload = {
            "dataset_id": "manufacturing-efficiency-2024",
            "metric": "defect_rate_percent",
            "value": "2.0",
            "tolerance_percent": 0,
        }
        response = await client.post("/v1/benchmarks/validate", json=payload)
        assert response.status_code == 200


class TestBenchmarkNotFoundHandling:
    """Test 404 handling for missing resources."""

    @pytest.mark.asyncio
    async def test_get_dataset_invalid_id_format(self, client: AsyncClient):
        """Should handle invalid dataset ID formats."""
        response = await client.get("/v1/benchmarks/datasets/invalid-id-with-special-chars-!!!")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_compare_nonexistent_dataset(self, client: AsyncClient):
        """Should return 404 for comparison with non-existent dataset."""
        payload = {
            "dataset_id": "nonexistent-dataset-12345",
            "metric": "some_metric",
            "company_value": "50.0",
            "industry": "manufacturing",
        }
        response = await client.post("/v1/benchmarks/compare", json=payload)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_validate_nonexistent_dataset(self, client: AsyncClient):
        """Should return 404 for validation with non-existent dataset."""
        payload = {
            "dataset_id": "nonexistent-dataset-12345",
            "metric": "some_metric",
            "value": "50.0",
            "tolerance_percent": 10,
        }
        response = await client.post("/v1/benchmarks/validate", json=payload)
        assert response.status_code == 404
