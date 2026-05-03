"""I-02 production fail-closed regression tests for Layer 5.

Production-like Layer 5 deployments must reject insecure startup settings instead
of relying on developer auth fallbacks, wildcard CORS, weak JWT secrets, or local
SQLite/default database credentials.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from layer5_ground_truth.config import Settings


VALID_JWT_SECRET = "layer5-production-secret-with-more-than-32-characters"
VALID_DATABASE_URL = "postgresql://layer5_app:strong-password@layer5-db.internal:5432/layer5_prod"
VALID_CORS_ORIGINS = "https://fabric.example.com,https://admin.fabric.example.com"


def _clear_layer5_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "ENVIRONMENT",
        "APP_ENV",
        "JWT_SECRET",
        "JWT_FALLBACK_TO_QUERY_PARAM",
        "ALLOW_INSECURE_DEV_AUTH_BYPASS",
        "CORS_ORIGINS",
        "DATABASE_URL",
        "DATABASE_URL_SYNC",
        "DEFAULT_TENANT_ID",
    ):
        monkeypatch.delenv(key, raising=False)


def _set_valid_production_env(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_layer5_env(monkeypatch)
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", VALID_JWT_SECRET)
    monkeypatch.setenv("JWT_FALLBACK_TO_QUERY_PARAM", "false")
    monkeypatch.setenv("ALLOW_INSECURE_DEV_AUTH_BYPASS", "false")
    monkeypatch.setenv("CORS_ORIGINS", VALID_CORS_ORIGINS)
    monkeypatch.setenv("DATABASE_URL", VALID_DATABASE_URL)
    monkeypatch.setenv("DATABASE_URL_SYNC", VALID_DATABASE_URL.replace("postgresql://", "postgresql+psycopg://"))
    monkeypatch.setenv("DEFAULT_TENANT_ID", "11111111-1111-4111-8111-111111111111")


def _validation_message(exc_info: pytest.ExceptionInfo[ValidationError]) -> str:
    return "\n".join(error["msg"] for error in exc_info.value.errors())


class TestLayer5ProductionSettingsFailClosed:
    def test_valid_production_settings_are_accepted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_valid_production_env(monkeypatch)

        settings = Settings()

        assert settings.effective_environment == "production"
        assert settings.cors_origin_list == [
            "https://fabric.example.com",
            "https://admin.fabric.example.com",
        ]
        assert settings.jwt_fallback_to_query_param is False
        assert settings.allow_insecure_dev_auth_bypass is False

    def test_app_env_marks_runtime_as_production_like_when_environment_absent(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _set_valid_production_env(monkeypatch)
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        monkeypatch.setenv("APP_ENV", "staging")

        assert Settings().effective_environment == "staging"

    def test_production_rejects_wildcard_cors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_valid_production_env(monkeypatch)
        monkeypatch.setenv("CORS_ORIGINS", "*")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "CORS_ORIGINS must not contain wildcard '*' origins" in _validation_message(exc_info)

    def test_production_requires_explicit_cors_origins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_valid_production_env(monkeypatch)
        monkeypatch.delenv("CORS_ORIGINS", raising=False)

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "CORS_ORIGINS must list exact trusted origins" in _validation_message(exc_info)

    def test_production_rejects_query_param_jwt_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_valid_production_env(monkeypatch)
        monkeypatch.setenv("JWT_FALLBACK_TO_QUERY_PARAM", "true")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "JWT_FALLBACK_TO_QUERY_PARAM must be false" in _validation_message(exc_info)

    def test_production_rejects_insecure_dev_auth_bypass(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_valid_production_env(monkeypatch)
        monkeypatch.setenv("ALLOW_INSECURE_DEV_AUTH_BYPASS", "true")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "ALLOW_INSECURE_DEV_AUTH_BYPASS must be false" in _validation_message(exc_info)

    def test_production_rejects_local_or_default_database_credentials(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _set_valid_production_env(monkeypatch)
        monkeypatch.setenv("DATABASE_URL", "sqlite:///./layer5.db")
        monkeypatch.setenv("DATABASE_URL_SYNC", "sqlite:///./layer5.db")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        message = _validation_message(exc_info)
        assert "DATABASE_URL must point to non-local PostgreSQL with non-default credentials" in message
        assert "DATABASE_URL_SYNC must point to non-local PostgreSQL with non-default credentials" in message

    def test_development_still_allows_test_friendly_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_layer5_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("JWT_SECRET", VALID_JWT_SECRET)
        monkeypatch.setenv("JWT_FALLBACK_TO_QUERY_PARAM", "true")
        monkeypatch.setenv("ALLOW_INSECURE_DEV_AUTH_BYPASS", "true")
        monkeypatch.setenv("CORS_ORIGINS", "*")
        monkeypatch.setenv("DATABASE_URL", "sqlite:///./layer5.db")
        monkeypatch.setenv("DATABASE_URL_SYNC", "sqlite:///./layer5.db")
        monkeypatch.setenv("DEFAULT_TENANT_ID", "11111111-1111-4111-8111-111111111111")

        settings = Settings()

        assert settings.effective_environment == "development"
        assert settings.jwt_fallback_to_query_param is True
        assert settings.allow_insecure_dev_auth_bypass is True
        assert settings.cors_origin_list == ["*"]
