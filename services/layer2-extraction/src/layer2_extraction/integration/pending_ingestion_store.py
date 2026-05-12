"""Pending ingestion store for Layer 2 extraction pipeline."""

from __future__ import annotations

import os
import sqlite3
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PendingIngestionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    source_url: str
    extraction_result_json: str
    relationships_json: str = "[]"
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PendingIngestionStore(ABC):
    @abstractmethod
    async def enqueue(
        self,
        *,
        job_id: str,
        source_url: str,
        extraction_result_json: str,
        relationships_json: str = "[]",
        retry_count: int = 0,
        next_retry_at: datetime | None = None,
        last_error: str | None = None,
    ) -> None:
        ...

    @abstractmethod
    async def get_due(self, before: datetime) -> list[PendingIngestionRecord]:
        ...

    @abstractmethod
    async def complete(self, job_id: str) -> None:
        ...

    @abstractmethod
    async def reschedule(
        self,
        job_id: str,
        *,
        retry_count: int,
        last_error: str,
        next_retry_at: datetime,
    ) -> None:
        ...


class SqlitePendingIngestionStore(PendingIngestionStore):
    def __init__(self, db_path: str = "pending_ingestion.db") -> None:
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_ingestion (
                    job_id TEXT PRIMARY KEY,
                    source_url TEXT NOT NULL,
                    extraction_result_json TEXT NOT NULL,
                    relationships_json TEXT DEFAULT '[]',
                    retry_count INTEGER DEFAULT 0,
                    next_retry_at TIMESTAMP,
                    last_error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    async def enqueue(
        self,
        *,
        job_id: str,
        source_url: str,
        extraction_result_json: str,
        relationships_json: str = "[]",
        retry_count: int = 0,
        next_retry_at: datetime | None = None,
        last_error: str | None = None,
    ) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO pending_ingestion
                (job_id, source_url, extraction_result_json, relationships_json, retry_count, next_retry_at, last_error)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    source_url,
                    extraction_result_json,
                    relationships_json,
                    retry_count,
                    next_retry_at.isoformat() if next_retry_at else None,
                    last_error,
                ),
            )

    async def get_due(self, before: datetime) -> list[PendingIngestionRecord]:
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM pending_ingestion WHERE next_retry_at IS NULL OR next_retry_at <= ?",
                (before.isoformat(),),
            )
            rows = cursor.fetchall()
            cols = [d[0] for d in cursor.description]
            records: list[PendingIngestionRecord] = []
            for row in rows:
                data = dict(zip(cols, row))
                records.append(
                    PendingIngestionRecord(
                        job_id=data["job_id"],
                        source_url=data["source_url"],
                        extraction_result_json=data["extraction_result_json"],
                        relationships_json=data.get("relationships_json", "[]"),
                        retry_count=data.get("retry_count", 0),
                        next_retry_at=datetime.fromisoformat(data["next_retry_at"]) if data.get("next_retry_at") else None,
                        last_error=data.get("last_error"),
                        created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(UTC),
                    )
                )
            return records

    async def complete(self, job_id: str) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM pending_ingestion WHERE job_id = ?", (job_id,))

    async def reschedule(
        self,
        job_id: str,
        *,
        retry_count: int,
        last_error: str,
        next_retry_at: datetime,
    ) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                UPDATE pending_ingestion
                SET retry_count = ?, last_error = ?, next_retry_at = ?
                WHERE job_id = ?
                """,
                (retry_count, last_error, next_retry_at.isoformat(), job_id),
            )


class InMemoryPendingIngestionStore(PendingIngestionStore):
    def __init__(self) -> None:
        self._records: dict[str, PendingIngestionRecord] = {}

    async def enqueue(
        self,
        *,
        job_id: str,
        source_url: str,
        extraction_result_json: str,
        relationships_json: str = "[]",
        retry_count: int = 0,
        next_retry_at: datetime | None = None,
        last_error: str | None = None,
    ) -> None:
        self._records[job_id] = PendingIngestionRecord(
            job_id=job_id,
            source_url=source_url,
            extraction_result_json=extraction_result_json,
            relationships_json=relationships_json,
            retry_count=retry_count,
            next_retry_at=next_retry_at,
            last_error=last_error,
        )

    async def get_due(self, before: datetime) -> list[PendingIngestionRecord]:
        return [
            r for r in self._records.values()
            if r.next_retry_at is None or r.next_retry_at <= before
        ]

    async def complete(self, job_id: str) -> None:
        self._records.pop(job_id, None)

    async def reschedule(
        self,
        job_id: str,
        *,
        retry_count: int,
        last_error: str,
        next_retry_at: datetime,
    ) -> None:
        record = self._records.get(job_id)
        if record:
            record.retry_count = retry_count
            record.last_error = last_error
            record.next_retry_at = next_retry_at


def build_pending_ingestion_store() -> PendingIngestionStore:
    """Factory for pending ingestion store based on environment."""
    env = os.environ.get("ENVIRONMENT", os.environ.get("APP_ENV", "development")).lower()
    db_url = os.environ.get("LAYER2_DATABASE_URL", os.environ.get("DATABASE_URL", ""))

    if env in ("production", "staging"):
        if not db_url:
            raise RuntimeError("LAYER2_DATABASE_URL/DATABASE_URL must point to PostgreSQL in production/staging")
        if "sqlite" in db_url.lower():
            raise RuntimeError("refusing SQLite URL in production/staging for pending ingestion store")
        raise RuntimeError("production PostgreSQL pending ingestion store is not implemented")

    sqlite_path = os.environ.get("PENDING_INGESTION_SQLITE_PATH")
    if sqlite_path:
        return SqlitePendingIngestionStore(sqlite_path)
    return InMemoryPendingIngestionStore()
