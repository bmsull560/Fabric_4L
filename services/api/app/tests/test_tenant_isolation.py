from fastapi.testclient import TestClient
from app.main import app


def test_cross_tenant_access_blocked():
    with TestClient(app) as client:
        headers_alpha = {"X-Tenant-ID": "tenant-alpha"}
        response = client.get("/v1/accounts/acc-allego", headers=headers_alpha)
        assert response.status_code == 200

        headers_beta = {"X-Tenant-ID": "tenant-beta"}
        response = client.get("/v1/accounts/acc-allego", headers=headers_beta)
        assert response.status_code == 404


def test_missing_tenant_header():
    with TestClient(app) as client:
        response = client.get("/v1/accounts")
        assert response.status_code == 400
