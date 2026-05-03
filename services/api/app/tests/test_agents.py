from fastapi.testclient import TestClient
from .conftest import auth_headers, TENANT_ALPHA
from app.main import app

HEADERS = auth_headers(TENANT_ALPHA)


def test_create_agent_run():
    with TestClient(app) as client:
        payload = {
            "workflow_type": "hypothesis_generation",
            "account_id": "acc-allego",
            "input": {"prompt": "Generate hypotheses"},
        }
        response = client.post("/v1/agents/runs", json=payload, headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["workflow_type"] == "hypothesis_generation"
        assert data["status"] in ["pending", "running", "completed"]


def test_get_agent_run():
    with TestClient(app) as client:
        response = client.get("/v1/agents/runs/run-1", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "run-1"


def test_cancel_agent_run():
    with TestClient(app) as client:
        response = client.post("/v1/agents/runs/run-1/cancel", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
