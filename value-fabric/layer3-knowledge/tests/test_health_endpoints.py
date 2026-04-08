"""Integration tests for health check endpoints."""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from tests.conftest import TestUtils


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_basic_health_check(self, test_client: TestClient, test_utils: TestUtils):
        """Test basic health check endpoint."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        test_utils.assert_valid_health_response(data)
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
    
    def test_detailed_health_check(self, test_client: TestClient, test_utils: TestUtils):
        """Test detailed health check endpoint."""
        response = test_client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        test_utils.assert_valid_health_response(data)
        assert "system_info" in data
        assert "configuration" in data
        
        # Validate system info
        system_info = data["system_info"]
        assert "platform" in system_info
        assert "python_version" in system_info
        assert "cpu_count" in system_info
        assert "memory_total_gb" in system_info
        
        # Validate configuration
        configuration = data["configuration"]
        assert "api_host" in configuration
        assert "api_port" in configuration
        assert "log_level" in configuration
        assert "neo4j_database" in configuration
    
    @pytest.mark.asyncio
    async def test_health_check_async(self, async_client: AsyncClient, test_utils: TestUtils):
        """Test health check endpoint with async client."""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        test_utils.assert_valid_health_response(data)
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_detailed_health_check_async(self, async_client: AsyncClient, test_utils: TestUtils):
        """Test detailed health check endpoint with async client."""
        response = await async_client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        test_utils.assert_valid_health_response(data)
        assert "system_info" in data
        assert "configuration" in data
    
    def test_health_check_response_headers(self, test_client: TestClient):
        """Test health check response headers."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]
    
    def test_health_check_with_mocks(self, test_client: TestClient, mock_app_state):
        """Test health check with mocked dependencies."""
        # Configure mock to return unhealthy status
        mock_app_state.schema_initializer.health_check.return_value = {
            "status": "unhealthy",
            "database": "test_neo4j",
            "uri": "bolt://localhost:7687",
            "error": "Connection failed"
        }
        
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still return 200 but with unhealthy status
        assert data["status"] == "unhealthy"
        assert data["neo4j"]["status"] == "unhealthy"
        assert "error" in data["neo4j"]
    
    def test_health_check_metrics_format(self, test_client: TestClient):
        """Test health check includes proper metrics format."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        metrics = data["metrics"]
        assert "uptime_seconds" in metrics
        assert "active_connections" in metrics
        assert "total_requests" in metrics
        assert "error_rate_percent" in metrics
        
        # Validate metric types
        assert isinstance(metrics["uptime_seconds"], (int, float))
        assert isinstance(metrics["active_connections"], int)
        assert isinstance(metrics["total_requests"], int)
        assert isinstance(metrics["error_rate_percent"], (int, float))
        
        # Validate metric ranges
        assert metrics["uptime_seconds"] >= 0
        assert metrics["active_connections"] >= 0
        assert metrics["total_requests"] >= 0
        assert 0 <= metrics["error_rate_percent"] <= 100
    
    def test_health_check_dependencies_format(self, test_client: TestClient):
        """Test health check dependencies format."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        dependencies = data["dependencies"]
        assert isinstance(dependencies, list)
        
        if dependencies:
            dep = dependencies[0]
            assert "name" in dep
            assert "status" in dep
            assert "response_time_ms" in dep
            assert "error" in dep
            assert "details" in dep
            
            # Validate status values
            assert dep["status"] in ["healthy", "unhealthy", "degraded"]
            
            # Validate response time
            if dep["response_time_ms"] is not None:
                assert isinstance(dep["response_time_ms"], (int, float))
                assert dep["response_time_ms"] >= 0
    
    def test_health_check_schema_status_format(self, test_client: TestClient):
        """Test health check schema status format."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        schema_status = data["schema_status"]
        assert "constraints" in schema_status
        assert "indexes" in schema_status
        assert "valid" in schema_status
        
        # Validate constraints format
        constraints = schema_status["constraints"]
        assert "expected" in constraints
        assert "found" in constraints
        assert "missing" in constraints
        assert isinstance(constraints["expected"], int)
        assert isinstance(constraints["found"], int)
        assert isinstance(constraints["missing"], list)
        
        # Validate indexes format
        indexes = schema_status["indexes"]
        assert "expected" in indexes
        assert "found" in indexes
        assert "missing" in indexes
        assert isinstance(indexes["expected"], int)
        assert isinstance(indexes["found"], int)
        assert isinstance(indexes["missing"], list)
        
        # Validate overall status
        assert isinstance(schema_status["valid"], bool)
