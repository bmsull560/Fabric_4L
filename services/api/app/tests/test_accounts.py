"""Account endpoint tests — updated for JWT-authenticated requests."""

from fastapi.testclient import TestClient

from app.main import app

from .conftest import TENANT_ALPHA, auth_headers

HEADERS = auth_headers(TENANT_ALPHA)


def test_list_accounts():
    with TestClient(app) as client:
        response = client.get("/v1/accounts", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


def test_get_account():
    with TestClient(app) as client:
        response = client.get("/v1/accounts/acc-allego", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "acc-allego"
        assert data["tenant_id"] == TENANT_ALPHA


def test_get_account_not_found():
    with TestClient(app) as client:
        response = client.get("/v1/accounts/nonexistent", headers=HEADERS)
        assert response.status_code == 404


def test_create_account():
    with TestClient(app) as client:
        payload = {
            "id": "acc-test-1",
            "name": "Test Account",
            "industry": "Software",
            "tenant_id": TENANT_ALPHA,
        }
        response = client.post("/v1/accounts", json=payload, headers=HEADERS)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Account"


def test_unauthenticated_returns_401():
    with TestClient(app) as client:
        response = client.get("/v1/accounts")
        assert response.status_code == 401
