from fastapi.testclient import TestClient

from app.main import app


def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "fabric-4l-api"


def test_metrics():
    with TestClient(app) as client:
        client.get("/health")
        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        body = response.text
        assert "fabric_api_http_requests_total" in body
        assert "fabric_api_http_request_duration_seconds_bucket" in body
        assert "fabric_api_http_errors_total" in body
        assert 'fabric_api_dependency_health{dependency="database"}' in body
