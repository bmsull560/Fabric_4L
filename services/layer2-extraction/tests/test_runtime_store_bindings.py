from layer2_extraction.integration.job_store import InMemoryJobStore, build_job_store
from layer2_extraction.integration.pending_ingestion_store import (
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
    assert isinstance(store, SqlitePendingIngestionStore)
    assert isinstance(store, PendingIngestionStore)
