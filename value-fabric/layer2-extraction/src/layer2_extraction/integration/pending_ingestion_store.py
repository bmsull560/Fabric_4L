"""Durable pending-ingestion persistence for Layer 2 -> Layer 3 retries."""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from shared.models.typed_dict import TypedDictModel


class SqlitePendingIngestionStore_get_retry_metadataResult(TypedDictModel):
    last_error: Any
    next_retry_at: Any
    retry_count: Any

class PostgresPendingIngestionStore_get_retry_metadataResult(TypedDictModel):
    last_error: Any
    next_retry_at: Any
    retry_count: Any


@dataclass
class PendingIngestionRecord:
    """Durable pending ingestion record."""

    job_id: str
    source_url: str
    extraction_result_json: str
    relationships_json: str
    retry_count: int
    max_retries: int
    last_error: str | None
    next_retry_at: datetime


class PendingIngestionStore:
    """Storage abstraction for pending Layer 3 ingestion retries."""

    async def enqueue(
        self,
        job_id: str,
        source_url: str,
        extraction_result_json: str,
        relationships_json: str,
        retry_count: int,
        next_retry_at: datetime,
        max_retries: int,
        last_error: str | None,
    ) -> None:
        raise NotImplementedError

    async def get_due(self, now: datetime, limit: int = 25) -> list[PendingIngestionRecord]:
        raise NotImplementedError

    async def complete(self, job_id: str) -> None:
        raise NotImplementedError

    async def reschedule(
        self,
        job_id: str,
        retry_count: int,
        last_error: str,
        next_retry_at: datetime,
    ) -> None:
        raise NotImplementedError

    async def get_retry_metadata(self, job_id: str) -> dict | None:
        raise NotImplementedError


class SqlitePendingIngestionStore(PendingIngestionStore):
    """SQLite-backed durable pending ingestion store."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_ingestions (
                    job_id TEXT PRIMARY KEY,
                    source_url TEXT NOT NULL,
                    extraction_result_json TEXT NOT NULL,
                    relationships_json TEXT NOT NULL,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    max_retries INTEGER NOT NULL,
                    last_error TEXT,
                    next_retry_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_pending_ingestions_next_retry "
                "ON pending_ingestions(next_retry_at)"
            )
            conn.commit()

    async def enqueue(
        self,
        job_id: str,
        source_url: str,
        extraction_result_json: str,
        relationships_json: str,
        retry_count: int,
        next_retry_at: datetime,
        max_retries: int,
        last_error: str | None,
    ) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO pending_ingestions (
                    job_id, source_url, extraction_result_json, relationships_json,
                    retry_count, max_retries, last_error, next_retry_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    source_url=excluded.source_url,
                    extraction_result_json=excluded.extraction_result_json,
                    relationships_json=excluded.relationships_json,
                    retry_count=excluded.retry_count,
                    max_retries=excluded.max_retries,
                    last_error=excluded.last_error,
                    next_retry_at=excluded.next_retry_at,
                    updated_at=excluded.updated_at
                """,
                (
                    job_id,
                    source_url,
                    extraction_result_json,
                    relationships_json,
                    retry_count,
                    max_retries,
                    last_error,
                    next_retry_at.isoformat(),
                    now,
                    now,
                ),
            )
            conn.commit()

    async def get_due(self, now: datetime, limit: int = 25) -> list[PendingIngestionRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT job_id, source_url, extraction_result_json, relationships_json,
                       retry_count, max_retries, last_error, next_retry_at
                FROM pending_ingestions
                WHERE next_retry_at <= ? AND retry_count < max_retries
                ORDER BY next_retry_at ASC
                LIMIT ?
                """,
                (now.isoformat(), limit),
            ).fetchall()

        records: list[PendingIngestionRecord] = []
        for row in rows:
            records.append(
                PendingIngestionRecord(
                    job_id=row["job_id"],
                    source_url=row["source_url"],
                    extraction_result_json=row["extraction_result_json"],
                    relationships_json=row["relationships_json"],
                    retry_count=row["retry_count"],
                    max_retries=row["max_retries"],
                    last_error=row["last_error"],
                    next_retry_at=datetime.fromisoformat(row["next_retry_at"]),
                )
            )
        return records

    async def complete(self, job_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM pending_ingestions WHERE job_id = ?", (job_id,))
            conn.commit()

    async def reschedule(
        self,
        job_id: str,
        retry_count: int,
        last_error: str,
        next_retry_at: datetime,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE pending_ingestions
                SET retry_count = ?,
                    last_error = ?,
                    next_retry_at = ?,
                    updated_at = ?
                WHERE job_id = ?
                """,
                (
                    retry_count,
                    last_error,
                    next_retry_at.isoformat(),
                    datetime.utcnow().isoformat(),
                    job_id,
                ),
            )
            conn.commit()

    async def get_retry_metadata(self, job_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT retry_count, last_error, next_retry_at FROM pending_ingestions WHERE job_id = ?",
                (job_id,),
            ).fetchone()

        if not row:
            return None

        return SqlitePendingIngestionStore_get_retry_metadataResult.model_validate({
            "retry_count": row["retry_count"],
            "last_error": row["last_error"],
            "next_retry_at": row["next_retry_at"],
        })


class PostgresPendingIngestionStore(PendingIngestionStore):
    """Postgres-backed pending ingestion store."""

    def __init__(self, database_url: str):
        try:
            import psycopg  # type: ignore
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError("psycopg is required for PostgresPendingIngestionStore") from exc

        self._psycopg = psycopg
        self.database_url = database_url
        self._init_db()

    def _connect(self):
        return self._psycopg.connect(self.database_url)

    def _init_db(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS pending_ingestions (
                        job_id TEXT PRIMARY KEY,
                        source_url TEXT NOT NULL,
                        extraction_result_json TEXT NOT NULL,
                        relationships_json TEXT NOT NULL,
                        retry_count INTEGER NOT NULL DEFAULT 0,
                        max_retries INTEGER NOT NULL,
                        last_error TEXT,
                        next_retry_at TIMESTAMPTZ NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_pending_ingestions_next_retry
                    ON pending_ingestions(next_retry_at)
                    """
                )
            conn.commit()

    async def enqueue(
        self,
        job_id: str,
        source_url: str,
        extraction_result_json: str,
        relationships_json: str,
        retry_count: int,
        next_retry_at: datetime,
        max_retries: int,
        last_error: str | None,
    ) -> None:
        now = datetime.utcnow()
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO pending_ingestions (
                        job_id, source_url, extraction_result_json, relationships_json,
                        retry_count, max_retries, last_error, next_retry_at, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT(job_id) DO UPDATE SET
                        source_url = EXCLUDED.source_url,
                        extraction_result_json = EXCLUDED.extraction_result_json,
                        relationships_json = EXCLUDED.relationships_json,
                        retry_count = EXCLUDED.retry_count,
                        max_retries = EXCLUDED.max_retries,
                        last_error = EXCLUDED.last_error,
                        next_retry_at = EXCLUDED.next_retry_at,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (
                        job_id,
                        source_url,
                        extraction_result_json,
                        relationships_json,
                        retry_count,
                        max_retries,
                        last_error,
                        next_retry_at,
                        now,
                        now,
                    ),
                )
            conn.commit()

    async def get_due(self, now: datetime, limit: int = 25) -> list[PendingIngestionRecord]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                    SELECT job_id, source_url, extraction_result_json, relationships_json,
                           retry_count, max_retries, last_error, next_retry_at
                    FROM pending_ingestions
                    WHERE next_retry_at <= %s AND retry_count < max_retries
                    ORDER BY next_retry_at ASC
                    LIMIT %s
                    """,
                (now, limit),
            )
            rows = cur.fetchall()

        records: list[PendingIngestionRecord] = []
        for row in rows:
            records.append(
                PendingIngestionRecord(
                    job_id=row[0],
                    source_url=row[1],
                    extraction_result_json=row[2],
                    relationships_json=row[3],
                    retry_count=row[4],
                    max_retries=row[5],
                    last_error=row[6],
                    next_retry_at=row[7],
                )
            )
        return records

    async def complete(self, job_id: str) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM pending_ingestions WHERE job_id = %s", (job_id,))
            conn.commit()

    async def reschedule(
        self,
        job_id: str,
        retry_count: int,
        last_error: str,
        next_retry_at: datetime,
    ) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE pending_ingestions
                    SET retry_count = %s,
                        last_error = %s,
                        next_retry_at = %s,
                        updated_at = %s
                    WHERE job_id = %s
                    """,
                    (retry_count, last_error, next_retry_at, datetime.utcnow(), job_id),
                )
            conn.commit()

    async def get_retry_metadata(self, job_id: str) -> dict | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT retry_count, last_error, next_retry_at FROM pending_ingestions WHERE job_id = %s",
                    (job_id,),
                )
                row = cur.fetchone()

        if not row:
            return None

        return PostgresPendingIngestionStore_get_retry_metadataResult.model_validate({
            "retry_count": row[0],
            "last_error": row[1],
            "next_retry_at": row[2].isoformat() if row[2] else None,
        })


def _sqlite_path_from_url(database_url: str) -> str:
    if database_url.startswith("sqlite:///"):
        return database_url.replace("sqlite:///", "", 1)
    if database_url.startswith("sqlite://"):
        return database_url.replace("sqlite://", "", 1)
    return database_url


def build_pending_ingestion_store() -> PendingIngestionStore:
    """Resolve pending-ingestion persistence backend.

    Uses Layer 2 service DB when configured; otherwise uses SQLite fallback.
    """
    service_db_url = os.getenv("LAYER2_DATABASE_URL") or os.getenv("DATABASE_URL")

    if service_db_url:
        lower = service_db_url.lower()
        if lower.startswith("postgresql://") or lower.startswith("postgresql+"):
            return PostgresPendingIngestionStore(service_db_url)
        if lower.startswith("sqlite://"):
            return SqlitePendingIngestionStore(_sqlite_path_from_url(service_db_url))

    fallback_path = os.getenv("PENDING_INGESTION_SQLITE_PATH", "./data/pending_ingestion.db")
    return SqlitePendingIngestionStore(fallback_path)
