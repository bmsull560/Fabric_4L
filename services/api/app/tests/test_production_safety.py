import importlib

import pytest

from app.core.config import Settings


def test_production_like_environment_rejects_mock_persistence_and_mock_llm():
    with pytest.raises(Exception, match="Unsafe production configuration"):
        Settings(
            app_env="production",
            mock_persistence=True,
            database_url=None,
            llm_provider="mock",
            secret_key="fabric-4l-dev-secret-key-change-in-production",
            cors_origins=["*"],
        )


def test_production_like_environment_accepts_durable_configuration():
    settings = Settings(
        app_env="production",
        mock_persistence=False,
        database_url="postgresql://fabric:example@db.internal:5432/fabric",
        llm_provider="openai",
        secret_key="x" * 48,
        cors_origins=["https://app.example.com"],
    )

    assert settings.is_production_like is True
    assert settings.mock_persistence is False


def test_database_factory_fails_when_mock_persistence_is_disabled(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    database = importlib.import_module("app.core.database")

    safe_dev_settings = Settings(
        app_env="development",
        mock_persistence=False,
        database_url="postgresql://fabric:example@localhost:5432/fabric",
        llm_provider="mock",
        secret_key="fabric-4l-dev-secret-key-change-in-production",
    )
    monkeypatch.setattr(database, "get_settings", lambda: safe_dev_settings)

    with pytest.raises(database.ProductionPersistenceNotConfigured):
        database.create_database()


def test_unknown_environment_is_treated_as_production_like_and_fails_closed():
    with pytest.raises(Exception, match="Unsafe production configuration") as exc_info:
        Settings(
            app_env="qa",
            mock_persistence=False,
            database_url="postgresql://fabric:example@db.internal:5432/fabric",
            llm_provider="openai",
            secret_key="x" * 48,
            cors_origins=[],
        )

    assert "cors_origins must be configured" in str(exc_info.value)


def test_production_like_environment_rejects_placeholder_and_wildcard_cors():
    with pytest.raises(Exception, match="Unsafe production configuration") as exc_info:
        Settings(
            app_env="production",
            mock_persistence=False,
            database_url="postgresql://fabric:example@db.internal:5432/fabric",
            llm_provider="openai",
            secret_key="x" * 48,
            cors_origins=["https://*.example.com", "CHANGE_ME"],
        )

    message = str(exc_info.value)
    assert "wildcard" in message.lower()
    assert "deployable origin" in message


def test_standalone_api_cors_policy_is_explicit_and_credentials_safe():
    settings = Settings(
        app_env="production",
        mock_persistence=False,
        database_url="postgresql://fabric:example@db.internal:5432/fabric",
        llm_provider="openai",
        secret_key="x" * 48,
        cors_origins=["https://app.example.com"],
    )

    assert settings.cors_policy == {
        "allow_origins": ["https://app.example.com"],
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Authorization", "Content-Type", "X-Request-ID", "X-Tenant-ID"],
    }
