from layer2_extraction.integration.job_store import InMemoryJobStore, build_job_store
from layer2_extraction.integration.pending_ingestion_store import (
    InMemoryPendingIngestionStore,
    PendingIngestionStore,
    SqlitePendingIngestionStore,
    build_pending_ingestion_store,
)


def test_job_store_factory_returns_concrete_adapter(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")
    store = build_job_store()
    assert isinstance(store, InMemoryJobStore)


def test_pending_store_factory_returns_concrete_adapter(monkeypatch):
    monkeypatch.delenv("LAYER2_PENDING_INGESTION_STORE", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")
    store = build_pending_ingestion_store()
    assert isinstance(store, InMemoryPendingIngestionStore)
    assert isinstance(store, PendingIngestionStore)


def test_dev_fallback_does_not_create_on_disk_sqlite_by_default(monkeypatch, tmp_path):
    """Dev fallback must not create pending_ingestion.db in cwd by default."""
    monkeypatch.delenv("PENDING_INGESTION_SQLITE_PATH", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")
    # Run from tmp_path so any cwd-created file would land there
    monkeypatch.chdir(tmp_path)
    store = build_pending_ingestion_store()
    assert isinstance(store, InMemoryPendingIngestionStore)
    # Ensure no pending_ingestion.db was created
    assert not (tmp_path / "pending_ingestion.db").exists()
