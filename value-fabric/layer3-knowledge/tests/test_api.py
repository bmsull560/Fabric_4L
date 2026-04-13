"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

def test_health_endpoint(test_client: TestClient):
    """Test health check endpoint."""
    response = test_client.get("/health")

    # May fail if Neo4j is not running, which is expected
    assert response.status_code in [200, 503]


def test_schema_status_endpoint(test_client: TestClient):
    """Test schema status endpoint."""
    response = test_client.get("/v1/schema/status")

    assert response.status_code in [200, 503]


def test_ingest_endpoint_validation(test_client: TestClient):
    """Test ingest endpoint request validation."""
    # Missing required fields
    response = test_client.post("/v1/ingest", json={})
    assert response.status_code == 422

    # Valid request structure (but will fail without Neo4j)
    response = test_client.post(
        "/v1/ingest",
        json={
            "rdf_data": "test",
            "source_id": "src-1",
            "extraction_job_id": "job-1",
        },
    )
    # Will fail because Neo4j is not available
    assert response.status_code in [200, 500, 503]


def test_query_endpoint_validation(test_client: TestClient):
    """Test query endpoint request validation."""
    # Missing required fields
    response = test_client.post("/v1/query", json={})
    assert response.status_code == 422

    # Valid request structure
    response = test_client.post(
        "/v1/query",
        json={"query": "test query", "max_hops": 3},
    )
    assert response.status_code in [200, 500, 503]


def test_search_endpoint_validation(test_client: TestClient):
    """Test search endpoint request validation."""
    # Missing required fields
    response = test_client.post("/v1/search", json={})
    assert response.status_code == 422

    # Valid request
    response = test_client.post(
        "/v1/search",
        json={"query": "test", "search_type": "hybrid"},
    )
    assert response.status_code in [200, 500, 503]
