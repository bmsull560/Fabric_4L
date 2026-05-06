from fastapi.testclient import TestClient

from app.main import app

from .conftest import TENANT_ALPHA, auth_headers

HEADERS = auth_headers(TENANT_ALPHA)


def test_create_agent_run():
    with TestClient(app) as client:
        payload = {
            "workflow_type": "hypothesis_generation",
            "account_id": "acc-allego",
            "input": {"prompt": "Generate hypotheses"},
        }
        response = client.post("/v1/agents/runs", json=payload, headers=HEADERS)
        assert response.status_code == 201
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


def test_workflow_compat_routes():
    with TestClient(app) as client:
        create_resp = client.post(
            "/v1/agents/workflows",
            json={"workflow_type": "hypothesis_generation", "inputs": {"prompt": "x"}},
            headers=HEADERS,
        )
        assert create_resp.status_code == 201
        workflow_id = create_resp.json()["workflow_id"]

        active_resp = client.get("/v1/agents/workflows/active", headers=HEADERS)
        assert active_resp.status_code == 200
        assert isinstance(active_resp.json(), list)

        detail_resp = client.get(f"/v1/agents/workflows/{workflow_id}", headers=HEADERS)
        assert detail_resp.status_code == 200
        assert detail_resp.json()["workflow_id"] == workflow_id

        resume_resp = client.post(f"/v1/agents/workflows/{workflow_id}/resume", headers=HEADERS)
        assert resume_resp.status_code == 200

        pause_resp = client.post(f"/v1/agents/workflows/{workflow_id}/pause", headers=HEADERS)
        assert pause_resp.status_code == 200

        events_resp = client.get(f"/v1/agents/workflows/{workflow_id}/events", headers=HEADERS)
        assert events_resp.status_code == 200
        assert events_resp.headers["content-type"].startswith("text/event-stream")

        delete_resp = client.delete(f"/v1/agents/workflows/{workflow_id}", headers=HEADERS)
        assert delete_resp.status_code == 200
        assert delete_resp.json()["status"] == "cancelled"
