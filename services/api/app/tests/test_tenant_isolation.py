"""Tenant isolation tests — updated for JWT-authenticated requests."""

from fastapi.testclient import TestClient

from app.main import app

from .conftest import TENANT_ALPHA, TENANT_BETA, auth_headers


def test_cross_tenant_access_blocked():
    """A resource owned by tenant-alpha must not be visible to tenant-beta."""
    with TestClient(app) as client:
        alpha = auth_headers(TENANT_ALPHA)
        response = client.get("/v1/accounts/acc-allego", headers=alpha)
        assert response.status_code == 200

        beta = auth_headers(TENANT_BETA)
        response = client.get("/v1/accounts/acc-allego", headers=beta)
        assert response.status_code == 404


def test_missing_credentials_returns_401():
    """Requests with no credentials must be rejected."""
    with TestClient(app) as client:
        response = client.get("/v1/accounts")
        assert response.status_code == 401


def test_tenant_header_without_jwt_returns_401():
    """X-Tenant-ID alone (no JWT) must not grant access."""
    with TestClient(app) as client:
        response = client.get("/v1/accounts", headers={"X-Tenant-ID": TENANT_ALPHA})
        assert response.status_code == 401
