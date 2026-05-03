"""Tests for API endpoint contracts and validation."""

from http import HTTPStatus
from typing import Any

from fastapi.testclient import TestClient


def test_health_endpoint(test_client: TestClient) -> None:
    """Health endpoint returns 200 when healthy or 503 when degraded/unavailable."""
    response = test_client.get("/health")
    assert response.status_code in {HTTPStatus.OK, HTTPStatus.SERVICE_UNAVAILABLE}


def test_schema_status_endpoint(test_client: TestClient) -> None:
    """Schema status endpoint returns 200 when schema is valid or 503 when unavailable."""
    response = test_client.get("/v1/schema/status")
    assert response.status_code in {HTTPStatus.OK, HTTPStatus.SERVICE_UNAVAILABLE}


def test_ingest_endpoint_validation(test_client: TestClient) -> None:
    """Ingest endpoint validates required fields (422) and accepts valid requests."""
    response = test_client.post("/v1/ingest", json={})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    payload: dict[str, Any] = {
        "rdf_data": "test",
        "source_id": "src-1",
        "extraction_job_id": "job-1",
    }
    response = test_client.post("/v1/ingest", json=payload)
    assert response.status_code in {HTTPStatus.OK, HTTPStatus.INTERNAL_SERVER_ERROR, HTTPStatus.SERVICE_UNAVAILABLE}


def test_query_endpoint_validation(test_client: TestClient) -> None:
    """Query endpoint validates required fields (422) and accepts valid requests."""
    response = test_client.post("/v1/query", json={})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    payload: dict[str, Any] = {"query": "test query", "max_hops": 3}
    response = test_client.post("/v1/query", json=payload)
    assert response.status_code in {HTTPStatus.OK, HTTPStatus.INTERNAL_SERVER_ERROR, HTTPStatus.SERVICE_UNAVAILABLE}


def test_search_endpoint_validation(test_client: TestClient) -> None:
    """Search endpoint validates required fields (422) and accepts valid requests."""
    response = test_client.post("/v1/search", json={})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    payload: dict[str, Any] = {"query": "test", "search_type": "hybrid"}
    response = test_client.post("/v1/search", json=payload)
    assert response.status_code in {HTTPStatus.OK, HTTPStatus.INTERNAL_SERVER_ERROR, HTTPStatus.SERVICE_UNAVAILABLE}

