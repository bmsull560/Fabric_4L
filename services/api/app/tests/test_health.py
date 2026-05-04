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
        response = client.get("/metrics")
        assert response.status_code == 200
