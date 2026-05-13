"""Integration tests for health check endpoints."""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from conftest import TestUtils

# Health status values (contract-valid states)
HEALTH_STATUSES = frozenset({"healthy", "degraded", "unhealthy"})

# Metric validation bounds
METRIC_MIN_UPTIME_SECONDS = 0
METRIC_MIN_ACTIVE_CONNECTIONS = 0
METRIC_MIN_TOTAL_REQUESTS = 0
METRIC_MIN_ERROR_RATE = 0
METRIC_MAX_ERROR_RATE = 100
METRIC_MIN_RESPONSE_TIME_MS = 0


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_basic_health_check(self, test_client: TestClient, test_utils: TestUtils) -> None:
        """Test basic health check endpoint."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data: dict[str, Any] = response.json()

        test_utils.assert_valid_health_response(data)
        assert data["status"] in HEALTH_STATUSES
        assert data["version"] == "1.0.0"
    
    def test_detailed_health_check(self, test_client: TestClient, test_utils: TestUtils) -> None:
        """Test detailed health check endpoint."""
        response = test_client.get("/health/detailed")

        assert response.status_code == 200
        data: dict[str, Any] = response.json()

        test_utils.assert_valid_health_response(data)
        assert "system_info" in data
        assert "configuration" in data

        system_info: dict[str, Any] = data["system_info"]
        assert "platform" in system_info
        assert "python_version" in system_info
        assert "cpu_count" in system_info
        assert "memory_total_gb" in system_info

        configuration: dict[str, Any] = data["configuration"]
        assert "api_host" in configuration
        assert "api_port" in configuration
        assert configuration["api_port"] == 8003
        assert "log_level" in configuration
        assert "neo4j_database" in configuration
    
    @pytest.mark.asyncio
    async def test_health_check_async(self, async_client: AsyncClient, test_utils: TestUtils) -> None:
        """Test health check endpoint with async client."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data: dict[str, Any] = response.json()

        test_utils.assert_valid_health_response(data)
        assert data["status"] in HEALTH_STATUSES
    
    @pytest.mark.asyncio
    async def test_detailed_health_check_async(self, async_client: AsyncClient, test_utils: TestUtils) -> None:
        """Test detailed health check endpoint with async client."""
        response = await async_client.get("/health/detailed")

        assert response.status_code == 200
        data: dict[str, Any] = response.json()

        test_utils.assert_valid_health_response(data)
        assert "system_info" in data
        assert "configuration" in data
    
    def test_health_check_response_headers(self, test_client: TestClient) -> None:
        """Test health check response headers."""
        response = test_client.get("/health")

        assert response.status_code == 200
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]
    
    def test_health_check_with_mocks(self, test_client: TestClient, mock_app_state: Any) -> None:
        """Test health check with mocked dependencies returns 200 even when unhealthy."""
        mock_app_state.schema_initializer.health_check.return_value = {
            "status": "unhealthy",
            "database": "test_neo4j",
            "uri": "bolt://localhost:7687",
            "error": "Connection failed"
        }

        response = test_client.get("/health")

        assert response.status_code == 200
        data: dict[str, Any] = response.json()

        assert data["status"] == "unhealthy"
        assert data["neo4j"]["status"] == "unhealthy"
        assert "error" in data["neo4j"]
    
    def test_health_check_metrics_format(self, test_client: TestClient) -> None:
        """Test health check includes properly typed and bounded metrics."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data: dict[str, Any] = response.json()

        metrics: dict[str, Any] = data["metrics"]
        assert "uptime_seconds" in metrics
        assert "active_connections" in metrics
        assert "total_requests" in metrics
        assert "error_rate_percent" in metrics

        assert isinstance(metrics["uptime_seconds"], (int, float))
        assert isinstance(metrics["active_connections"], int)
        assert isinstance(metrics["total_requests"], int)
        assert isinstance(metrics["error_rate_percent"], (int, float))

        assert metrics["uptime_seconds"] >= METRIC_MIN_UPTIME_SECONDS
        assert metrics["active_connections"] >= METRIC_MIN_ACTIVE_CONNECTIONS
        assert metrics["total_requests"] >= METRIC_MIN_TOTAL_REQUESTS
        assert METRIC_MIN_ERROR_RATE <= metrics["error_rate_percent"] <= METRIC_MAX_ERROR_RATE
    
    def test_health_check_dependencies_format(self, test_client: TestClient) -> None:
        """Test health check dependencies format."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data: dict[str, Any] = response.json()

        dependencies: list[dict[str, Any]] = data["dependencies"]
        assert isinstance(dependencies, list)

        if dependencies:
            dep: dict[str, Any] = dependencies[0]
            assert "name" in dep
            assert "status" in dep
            assert "response_time_ms" in dep
            assert "error" in dep
            assert "details" in dep

            assert dep["status"] in HEALTH_STATUSES

            if dep["response_time_ms"] is not None:
                assert isinstance(dep["response_time_ms"], (int, float))
                assert dep["response_time_ms"] >= METRIC_MIN_RESPONSE_TIME_MS
    
    def test_health_check_schema_status_format(self, test_client: TestClient) -> None:
        """Test health check schema status format."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data: dict[str, Any] = response.json()

        schema_status: dict[str, Any] = data["schema_status"]
        assert "constraints" in schema_status
        assert "indexes" in schema_status
        assert "valid" in schema_status

        constraints: dict[str, Any] = schema_status["constraints"]
        assert "expected" in constraints
        assert "found" in constraints
        assert "missing" in constraints
        assert isinstance(constraints["expected"], int)
        assert isinstance(constraints["found"], int)
        assert isinstance(constraints["missing"], list)

        indexes: dict[str, Any] = schema_status["indexes"]
        assert "expected" in indexes
        assert "found" in indexes
        assert "missing" in indexes
        assert isinstance(indexes["expected"], int)
        assert isinstance(indexes["found"], int)
        assert isinstance(indexes["missing"], list)

        assert isinstance(schema_status["valid"], bool)

