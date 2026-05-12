"""Pending ingestion store for Layer 2 extraction pipeline."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PendingIngestionRecord(BaseModel):
    """Record of a pending ingestion retry."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    source_url: str
    extraction_result_json: str
    relationships_json: str
    retry_count: int = 0
    max_retries: int = 5
    last_error: str | None = None
    next_retry_at: datetime


class PendingIngestionStore(ABC):
    """Abstract pending ingestion store."""

    @abstractmethod
    async def enqueue(
        self,
        job_id: str,
        source_url: str,
        extraction_result_json: str,
        relationships_json: str,
        retry_count: int,
        next_retry_at: datetime,
        max_retries: int = 5,
        last_error: str | None = None,
    ) -> None:
        ...

    @abstractmethod
    async def get_due(self, now: datetime, limit: int = 25) -> list[PendingIngestionRecord]:
        ...

    @abstractmethod
    async def complete(self, job_id: str) -> None:
        ...

    @abstractmethod
    async def reschedule(
        self,
        job_id: str,
        retry_count: int,
        last_error: str,
        next_retry_at: datetime,
    ) -> None:
        ...

    @abstractmethod
    async def get_retry_metadata(self, job_id: str) -> dict | None:
        ...


class SqlitePendingIngestionStore(PendingIngestionStore):
    """SQLite-backed pending ingestion store."""

    def __init__(self, db_path: str = "pending_ingestion.db") -> None:
        import sqlite3
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pending_ingestion (
                job_id TEXT PRIMARY KEY,
                source_url TEXT NOT NULL,
                extraction_result_json TEXT NOT NULL,
                relationships_json TEXT NOT NULL,
                retry_count INTEGER NOT NULL DEFAULT 0,
                max_retries INTEGER NOT NULL DEFAULT 5,
                last_error TEXT,
                next_retry_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    async def enqueue(
        self,
        job_id: str,
        source_url: str,
        extraction_result_json: str,
        relationships_json: str,
        retry_count: int,
        next_retry_at: datetime,
        max_retries: int = 5,
        last_error: str | None = None,
    ) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO pending_ingestion VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                job_id,
                source_url,
                extraction_result_json,
                relationships_json,
                retry_count,
                max_retries,
                last_error,
                next_retry_at.isoformat(),
            ),
        )
        self._conn.commit()

    async def get_due(self, now: datetime, limit: int = 25) -> list[PendingIngestionRecord]:
        cursor = self._conn.execute(
            "SELECT * FROM pending_ingestion WHERE next_retry_at <= ? AND retry_count < max_retries ORDER BY next_retry_at LIMIT ?",
            (now.isoformat(), limit),
        )
        rows = cursor.fetchall()
        return [
            PendingIngestionRecord(
                job_id=row[0],
                source_url=row[1],
                extraction_result_json=row[2],
                relationships_json=row[3],
                retry_count=row[4],
                max_retries=row[5],
                last_error=row[6],
                next_retry_at=datetime.fromisoformat(row[7]),
            )
            for row in rows
        ]

    async def complete(self, job_id: str) -> None:
        self._conn.execute("DELETE FROM pending_ingestion WHERE job_id = ?", (job_id,))
        self._conn.commit()

    async def reschedule(
        self,
        job_id: str,
        retry_count: int,
        last_error: str,
        next_retry_at: datetime,
    ) -> None:
        self._conn.execute(
            "UPDATE pending_ingestion SET retry_count = ?, last_error = ?, next_retry_at = ? WHERE job_id = ?",
            (retry_count, last_error, next_retry_at.isoformat(), job_id),
        )
        self._conn.commit()

    async def get_retry_metadata(self, job_id: str) -> dict | None:
        cursor = self._conn.execute(
            "SELECT retry_count, last_error, next_retry_at FROM pending_ingestion WHERE job_id = ?",
            (job_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "retry_count": row[0],
            "last_error": row[1],
            "next_retry_at": row[2],
        }


class InMemoryPendingIngestionStore(PendingIngestionStore):
    """In-memory pending ingestion store for testing."""

    def __init__(self) -> None:
        self._records: dict[str, PendingIngestionRecord] = {}

    async def enqueue(
        self,
        job_id: str,
        source_url: str,
        extraction_result_json: str,
        relationships_json: str,
        retry_count: int,
        next_retry_at: datetime,
        max_retries: int = 5,
        last_error: str | None = None,
    ) -> None:
        self._records[job_id] = PendingIngestionRecord(
            job_id=job_id,
            source_url=source_url,
            extraction_result_json=extraction_result_json,
            relationships_json=relationships_json,
            retry_count=retry_count,
            max_retries=max_retries,
            last_error=last_error,
            next_retry_at=next_retry_at,
        )

    async def get_due(self, now: datetime, limit: int = 25) -> list[PendingIngestionRecord]:
        due = [
            r
            for r in self._records.values()
            if r.next_retry_at <= now and r.retry_count < r.max_retries
        ]
        due.sort(key=lambda r: r.next_retry_at)
        return due[:limit]

    async def complete(self, job_id: str) -> None:
        self._records.pop(job_id, None)

    async def reschedule(
        self,
        job_id: str,
        retry_count: int,
        last_error: str,
        next_retry_at: datetime,
    ) -> None:
        if job_id in self._records:
            record = self._records[job_id]
            self._records[job_id] = record.model_copy(
                update={
                    "retry_count": retry_count,
                    "last_error": last_error,
                    "next_retry_at": next_retry_at,
                }
            )

    async def get_retry_metadata(self, job_id: str) -> dict | None:
        record = self._records.get(job_id)
        if record is None:
            return None
        return {
            "retry_count": record.retry_count,
            "last_error": record.last_error,
            "next_retry_at": record.next_retry_at.isoformat(),
        }


def build_pending_ingestion_store() -> PendingIngestionStore:
    """Factory for pending ingestion store based on environment."""
    env = os.environ.get("ENVIRONMENT", "development").lower()
    if env == "development":
        return SqlitePendingIngestionStore()
    return SqlitePendingIngestionStore()
