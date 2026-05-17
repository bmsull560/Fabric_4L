"""Unit tests for layer2_extraction.integration.pending_ingestion_store."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from layer2_extraction.integration.pending_ingestion_store import (
    InMemoryPendingIngestionStore,
    SqlitePendingIngestionStore,
    build_pending_ingestion_store,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _enqueue(store, job_id: str = "j1", next_retry_at=None):
    await store.enqueue(
        job_id=job_id,
        source_url="https://example.com",
        extraction_result_json='{"entities": []}',
        relationships_json="[]",
        retry_count=0,
        next_retry_at=next_retry_at,
    )


# ---------------------------------------------------------------------------
# InMemoryPendingIngestionStore
# ---------------------------------------------------------------------------

class TestInMemoryPendingIngestionStore:
    @pytest.mark.asyncio
    async def test_enqueue_persists_record(self):
        store = InMemoryPendingIngestionStore()
        await _enqueue(store, "j1")
        due = await store.get_due(datetime.now(UTC) + timedelta(hours=1))
        assert len(due) == 1
        assert due[0].job_id == "j1"

    @pytest.mark.asyncio
    async def test_get_due_returns_records_with_no_retry_at(self):
        store = InMemoryPendingIngestionStore()
        await _enqueue(store, "j1", next_retry_at=None)
        due = await store.get_due(datetime.now(UTC))
        assert any(r.job_id == "j1" for r in due)

    @pytest.mark.asyncio
    async def test_get_due_returns_records_past_next_retry_at(self):
        store = InMemoryPendingIngestionStore()
        past = datetime.now(UTC) - timedelta(minutes=5)
        await _enqueue(store, "j1", next_retry_at=past)
        due = await store.get_due(datetime.now(UTC))
        assert any(r.job_id == "j1" for r in due)

    @pytest.mark.asyncio
    async def test_get_due_excludes_future_records(self):
        store = InMemoryPendingIngestionStore()
        future = datetime.now(UTC) + timedelta(hours=1)
        await _enqueue(store, "j1", next_retry_at=future)
        due = await store.get_due(datetime.now(UTC))
        assert not any(r.job_id == "j1" for r in due)

    @pytest.mark.asyncio
    async def test_complete_removes_record(self):
        store = InMemoryPendingIngestionStore()
        await _enqueue(store, "j1")
        await store.complete("j1")
        due = await store.get_due(datetime.now(UTC) + timedelta(hours=1))
        assert not any(r.job_id == "j1" for r in due)

    @pytest.mark.asyncio
    async def test_complete_nonexistent_does_not_raise(self):
        store = InMemoryPendingIngestionStore()
        await store.complete("nonexistent")  # should not raise

    @pytest.mark.asyncio
    async def test_reschedule_updates_retry_fields(self):
        store = InMemoryPendingIngestionStore()
        await _enqueue(store, "j1")
        future = datetime.now(UTC) + timedelta(minutes=10)
        await store.reschedule("j1", retry_count=1, last_error="timeout", next_retry_at=future)
        due = await store.get_due(datetime.now(UTC))
        assert not any(r.job_id == "j1" for r in due)  # not due yet
        due_later = await store.get_due(future + timedelta(seconds=1))
        record = next(r for r in due_later if r.job_id == "j1")
        assert record.retry_count == 1
        assert record.last_error == "timeout"

    @pytest.mark.asyncio
    async def test_enqueue_multiple_records(self):
        store = InMemoryPendingIngestionStore()
        for i in range(5):
            await _enqueue(store, f"j{i}")
        due = await store.get_due(datetime.now(UTC) + timedelta(hours=1))
        assert len(due) == 5


# ---------------------------------------------------------------------------
# SqlitePendingIngestionStore
# ---------------------------------------------------------------------------

class TestSqlitePendingIngestionStore:
    @pytest.mark.asyncio
    async def test_enqueue_persists_record(self, tmp_path):
        db = str(tmp_path / "test.db")
        store = SqlitePendingIngestionStore(db_path=db)
        await _enqueue(store, "j1")
        due = await store.get_due(datetime.now(UTC) + timedelta(hours=1))
        assert len(due) == 1
        assert due[0].job_id == "j1"

    @pytest.mark.asyncio
    async def test_complete_removes_record(self, tmp_path):
        db = str(tmp_path / "test.db")
        store = SqlitePendingIngestionStore(db_path=db)
        await _enqueue(store, "j1")
        await store.complete("j1")
        due = await store.get_due(datetime.now(UTC) + timedelta(hours=1))
        assert not any(r.job_id == "j1" for r in due)

    @pytest.mark.asyncio
    async def test_get_due_excludes_future_records(self, tmp_path):
        db = str(tmp_path / "test.db")
        store = SqlitePendingIngestionStore(db_path=db)
        future = datetime.now(UTC) + timedelta(hours=1)
        await _enqueue(store, "j1", next_retry_at=future)
        due = await store.get_due(datetime.now(UTC))
        assert not any(r.job_id == "j1" for r in due)

    @pytest.mark.asyncio
    async def test_reschedule_updates_retry_fields(self, tmp_path):
        db = str(tmp_path / "test.db")
        store = SqlitePendingIngestionStore(db_path=db)
        await _enqueue(store, "j1")
        future = datetime.now(UTC) + timedelta(minutes=10)
        await store.reschedule("j1", retry_count=2, last_error="err", next_retry_at=future)
        due_later = await store.get_due(future + timedelta(seconds=1))
        record = next(r for r in due_later if r.job_id == "j1")
        assert record.retry_count == 2
        assert record.last_error == "err"

    @pytest.mark.asyncio
    async def test_enqueue_replaces_existing_record(self, tmp_path):
        db = str(tmp_path / "test.db")
        store = SqlitePendingIngestionStore(db_path=db)
        await _enqueue(store, "j1")
        await store.enqueue(
            job_id="j1",
            source_url="https://updated.com",
            extraction_result_json='{"entities": [1]}',
        )
        due = await store.get_due(datetime.now(UTC) + timedelta(hours=1))
        assert len(due) == 1
        assert due[0].source_url == "https://updated.com"


# ---------------------------------------------------------------------------
# build_pending_ingestion_store
# ---------------------------------------------------------------------------

class TestBuildPendingIngestionStore:
    def test_returns_in_memory_store_in_development(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.delenv("PENDING_INGESTION_SQLITE_PATH", raising=False)
        store = build_pending_ingestion_store()
        assert isinstance(store, InMemoryPendingIngestionStore)

    def test_returns_sqlite_store_when_path_set(self, monkeypatch, tmp_path):
        db = str(tmp_path / "test.db")
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("PENDING_INGESTION_SQLITE_PATH", db)
        store = build_pending_ingestion_store()
        assert isinstance(store, SqlitePendingIngestionStore)

    def test_raises_in_production_without_db_url(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.delenv("LAYER2_DATABASE_URL", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(RuntimeError):
            build_pending_ingestion_store()
