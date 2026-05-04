"""I-02 production fail-closed regression tests for Layer 2.

These tests lock the service-level startup policy that production-like runtimes must
not silently fall back to in-memory job state, SQLite retry queues, or local/default
PostgreSQL credentials.
"""

from __future__ import annotations

import pytest

from layer2_extraction.db.config import DatabaseConfig
from layer2_extraction.integration.job_store import InMemoryJobStore, build_job_store
from layer2_extraction.integration.pending_ingestion_store import (
    SqlitePendingIngestionStore,
    build_pending_ingestion_store,
)


def _clear_layer2_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "ENVIRONMENT",
        "APP_ENV",
        "LAYER2_ENV",
        "REDIS_URL",
        "LAYER2_DATABASE_URL",
        "DATABASE_URL",
        "PENDING_INGESTION_SQLITE_PATH",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_MIN_CONNECTIONS",
        "POSTGRES_MAX_CONNECTIONS",
    ):
        monkeypatch.delenv(key, raising=False)


class TestLayer2ProductionPersistenceFailClosed:
    def test_production_requires_redis_job_store(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_layer2_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "production")

        with pytest.raises(RuntimeError, match="REDIS_URL is required"):
            build_job_store()

    def test_development_keeps_in_memory_job_store_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_layer2_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "development")

        assert isinstance(build_job_store(), InMemoryJobStore)

    @pytest.mark.parametrize(
        ("env_key", "env_value"),
        (
            ("APP_ENV", "staging"),
            ("ENVIRONMENT", "staging"),
            ("APP_ENV", "production"),
            ("ENVIRONMENT", "production"),
        ),
    )
    def test_production_like_env_requires_postgres_pending_ingestion_store(
        self,
        monkeypatch: pytest.MonkeyPatch,
        env_key: str,
        env_value: str,
    ) -> None:
        _clear_layer2_env(monkeypatch)
        monkeypatch.setenv(env_key, env_value)

        with pytest.raises(RuntimeError, match="must point to PostgreSQL"):
            build_pending_ingestion_store()

    def test_production_rejects_sqlite_pending_ingestion_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_layer2_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("LAYER2_DATABASE_URL", "sqlite:///tmp/pending-ingestion.db")

        with pytest.raises(RuntimeError, match="refusing SQLite URL"):
            build_pending_ingestion_store()

    def test_development_keeps_sqlite_pending_ingestion_fallback(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        _clear_layer2_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("PENDING_INGESTION_SQLITE_PATH", str(tmp_path / "pending.db"))

        assert isinstance(build_pending_ingestion_store(), SqlitePendingIngestionStore)


class TestLayer2DatabaseConfigFailClosed:
    def test_production_rejects_default_database_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_layer2_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "production")

        with pytest.raises(RuntimeError) as exc_info:
            DatabaseConfig.from_env()

        message = str(exc_info.value)
        assert "POSTGRES_PASSWORD must be set" in message
        assert "POSTGRES_HOST must not point at localhost" in message
        assert "POSTGRES_USER must not use a default service account" in message
        assert "POSTGRES_DB must not use a default database name" in message

    def test_production_accepts_explicit_non_default_database_config(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _clear_layer2_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("POSTGRES_HOST", "layer2-db.internal")
        monkeypatch.setenv("POSTGRES_DB", "layer2_prod")
        monkeypatch.setenv("POSTGRES_USER", "layer2_app")
        monkeypatch.setenv("POSTGRES_PASSWORD", "not-a-default-password")

        config = DatabaseConfig.from_env()

        assert config.host == "layer2-db.internal"
        assert config.database == "layer2_prod"
        assert config.user == "layer2_app"
        assert config.password == "not-a-default-password"
