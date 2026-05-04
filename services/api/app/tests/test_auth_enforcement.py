"""
Authentication enforcement tests for services/api.

Proves that:
  1. Every business endpoint returns 401 when no token is provided.
  2. A valid JWT grants access.
  3. An expired JWT returns 401.
  4. A tampered JWT returns 401.
  5. X-Tenant-ID alone (no JWT) returns 401 — header spoofing is blocked.
  6. A JWT for tenant-alpha cannot access tenant-beta resources.
  7. /health and /metrics remain public (no auth required).
  8. The app refuses to start with the default secret in production environments.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app

from .conftest import TENANT_ALPHA, TENANT_BETA, auth_headers, mint_token

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Representative endpoints — one per router — to verify blanket enforcement.
# All paths are verified to exist in the app's route table.
PROTECTED_ENDPOINTS = [
    ("GET", "/v1/accounts"),
    ("GET", "/v1/accounts/acc-allego"),
    ("GET", "/v1/accounts/acc-allego/signals"),
    ("GET", "/v1/accounts/acc-allego/hypotheses"),
    ("GET", "/v1/accounts/acc-allego/drivers"),
    ("GET", "/v1/accounts/acc-allego/evidence"),
    ("GET", "/v1/governance/review-queue"),
    ("GET", "/v1/context-engine/formulas"),
]

PUBLIC_ENDPOINTS = [
    ("GET", "/health"),
    ("GET", "/metrics"),
]


# ---------------------------------------------------------------------------
# 1. Unauthenticated requests → 401
# ---------------------------------------------------------------------------


class TestUnauthenticatedRequests:
    """Every protected endpoint must return 401 with no credentials."""

    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
    def test_no_credentials_returns_401(self, method: str, path: str) -> None:
        with TestClient(app) as client:
            response = client.request(method, path)
        assert response.status_code == 401, (
            f"{method} {path} returned {response.status_code}, expected 401. "
            "Endpoint is not protected."
        )

    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
    def test_tenant_header_alone_returns_401(self, method: str, path: str) -> None:
        """X-Tenant-ID without a JWT must not grant access."""
        with TestClient(app) as client:
            response = client.request(method, path, headers={"X-Tenant-ID": TENANT_ALPHA})
        assert response.status_code == 401, (
            f"{method} {path} with X-Tenant-ID only returned {response.status_code}. "
            "Tenant header spoofing is not blocked."
        )


# ---------------------------------------------------------------------------
# 2. Valid JWT → access granted
# ---------------------------------------------------------------------------


class TestAuthenticatedRequests:
    """A valid JWT must grant access to protected endpoints."""

    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
    def test_valid_jwt_grants_access(self, method: str, path: str) -> None:
        headers = auth_headers(TENANT_ALPHA)
        with TestClient(app) as client:
            response = client.request(method, path, headers=headers)
        assert response.status_code in (200, 201, 204), (
            f"{method} {path} returned {response.status_code} with valid JWT."
        )


# ---------------------------------------------------------------------------
# 3. Expired JWT → 401
# ---------------------------------------------------------------------------


class TestExpiredToken:
    def test_expired_jwt_returns_401(self) -> None:
        expired_token = mint_token(expires_delta=timedelta(seconds=-1))
        headers = {"Authorization": f"Bearer {expired_token}"}
        with TestClient(app) as client:
            response = client.get("/v1/accounts", headers=headers)
        assert response.status_code == 401

    def test_expired_jwt_error_message(self) -> None:
        expired_token = mint_token(expires_delta=timedelta(seconds=-1))
        headers = {"Authorization": f"Bearer {expired_token}"}
        with TestClient(app) as client:
            response = client.get("/v1/accounts", headers=headers)
        data = response.json()
        assert "expired" in data.get("detail", "").lower()


# ---------------------------------------------------------------------------
# 4. Tampered JWT → 401
# ---------------------------------------------------------------------------


class TestTamperedToken:
    def test_tampered_signature_returns_401(self) -> None:
        valid = mint_token()
        # Flip the last character of the signature
        tampered = valid[:-1] + ("A" if valid[-1] != "A" else "B")
        with TestClient(app) as client:
            response = client.get("/v1/accounts", headers={"Authorization": f"Bearer {tampered}"})
        assert response.status_code == 401

    def test_malformed_bearer_returns_401(self) -> None:
        with TestClient(app) as client:
            response = client.get("/v1/accounts", headers={"Authorization": "Bearer not.a.jwt"})
        assert response.status_code == 401

    def test_empty_bearer_returns_401(self) -> None:
        with TestClient(app) as client:
            response = client.get("/v1/accounts", headers={"Authorization": "Bearer "})
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# 5. Tenant isolation — JWT for alpha cannot access beta resources
# ---------------------------------------------------------------------------


class TestTenantIsolation:
    def test_alpha_token_cannot_spoof_beta_tenant_header(self) -> None:
        """JWT for tenant-alpha + X-Tenant-ID: tenant-beta must be rejected."""
        alpha_token = mint_token(tenant_id=TENANT_ALPHA)
        headers = {
            "Authorization": f"Bearer {alpha_token}",
            "X-Tenant-ID": TENANT_BETA,  # Mismatch — should be rejected
        }
        with TestClient(app) as client:
            response = client.get("/v1/accounts", headers=headers)
        assert response.status_code == 403

    def test_alpha_data_not_visible_to_beta_token(self) -> None:
        """Seed data for tenant-alpha must not appear in tenant-beta responses."""
        beta_headers = auth_headers(TENANT_BETA)
        with TestClient(app) as client:
            response = client.get("/v1/accounts/acc-allego", headers=beta_headers)
        # acc-allego belongs to tenant-alpha; beta should get 404
        assert response.status_code == 404

    def test_alpha_data_visible_to_alpha_token(self) -> None:
        alpha_headers = auth_headers(TENANT_ALPHA)
        with TestClient(app) as client:
            response = client.get("/v1/accounts/acc-allego", headers=alpha_headers)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# 6. Public endpoints remain unauthenticated
# ---------------------------------------------------------------------------


class TestPublicEndpoints:
    @pytest.mark.parametrize("method,path", PUBLIC_ENDPOINTS)
    def test_public_endpoint_accessible_without_auth(self, method: str, path: str) -> None:
        with TestClient(app) as client:
            response = client.request(method, path)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# 7. Production secret guard
# ---------------------------------------------------------------------------


class TestProductionSecretGuard:
    def test_default_secret_raises_in_production(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """App must refuse to start with the default secret in production."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "fabric-4l-dev-secret-key-change-in-production")

        # Clear the lru_cache so the new env vars are picked up
        from app.core.config import get_settings

        get_settings.cache_clear()

        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            get_settings()

        # Restore
        get_settings.cache_clear()

    def test_unset_secret_raises_in_production(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.delenv("SECRET_KEY", raising=False)

        from app.core.config import get_settings

        get_settings.cache_clear()

        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            get_settings()

        get_settings.cache_clear()

    def test_custom_secret_accepted_in_production(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SECRET_KEY", "a-sufficiently-long-production-secret-value-xyz")
        monkeypatch.setenv("MOCK_PERSISTENCE", "false")
        monkeypatch.setenv("DATABASE_URL", "sqlite:////var/lib/fabric_4l/api.db")
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("SEED_DEMO_DATA", "false")
        monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")

        from app.core.config import get_settings

        get_settings.cache_clear()

        settings = get_settings()
        assert settings.secret_key == "a-sufficiently-long-production-secret-value-xyz"
        assert settings.is_production_like is True
        assert settings.mock_persistence is False
        assert settings.seed_demo_data is False

        get_settings.cache_clear()

    def test_default_secret_allowed_in_development(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ENVIRONMENT", "development")

        from app.core.config import get_settings

        get_settings.cache_clear()

        settings = get_settings()  # Must not raise
        assert settings is not None

        get_settings.cache_clear()
