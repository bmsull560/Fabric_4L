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
