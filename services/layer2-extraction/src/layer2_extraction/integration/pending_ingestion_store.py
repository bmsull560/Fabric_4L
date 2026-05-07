"""Durable pending-ingestion retry persistence for Layer 2."""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from value_fabric.layer2.integration.interfaces import PendingIngestionStorePort

PRODUCTION_LIKE_ENVIRONMENTS = {"production", "prod", "staging", "stage"}


def _current_environment() -> str:
    return (
        os.getenv("ENVIRONMENT")
        or os.getenv("APP_ENV")
        or os.getenv("LAYER2_ENV")
        or "development"
    ).strip().lower()


def _is_production_like() -> bool:
    return _current_environment() in PRODUCTION_LIKE_ENVIRONMENTS


@dataclass
class PendingIngestionRecord:
    job_id: str
    source_url: str
    extraction_result_json: str
    relationships_json: str
    retry_count: int
    next_retry_at: datetime
    max_retries: int
    last_error: str | None = None


class PendingIngestionStore(PendingIngestionStorePort):
    """Backward-compatible alias for the pending-ingestion store port."""


class SqlitePendingIngestionStore(PendingIngestionStore):
    """SQLite-backed pending-ingestion queue for local development and tests."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_ingestions (
                    job_id TEXT PRIMARY KEY,
                    source_url TEXT NOT NULL,
                    extraction_result_json TEXT NOT NULL,
                    relationships_json TEXT NOT NULL,
                    retry_count INTEGER NOT NULL,
                    next_retry_at TEXT NOT NULL,
                    max_retries INTEGER NOT NULL,
                    last_error TEXT
                )
                """
            )

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
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO pending_ingestions (
                    job_id, source_url, extraction_result_json, relationships_json,
                    retry_count, next_retry_at, max_retries, last_error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    source_url = excluded.source_url,
                    extraction_result_json = excluded.extraction_result_json,
                    relationships_json = excluded.relationships_json,
                    retry_count = excluded.retry_count,
                    next_retry_at = excluded.next_retry_at,
                    max_retries = excluded.max_retries,
                    last_error = excluded.last_error
                """,
                (
                    job_id,
                    source_url,
                    extraction_result_json,
                    relationships_json,
                    retry_count,
                    next_retry_at.astimezone(UTC).isoformat(),
                    max_retries,
                    last_error,
                ),
            )

    async def get_due(self, now: datetime, limit: int = 25) -> list[PendingIngestionRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM pending_ingestions
                WHERE next_retry_at <= ?
                ORDER BY next_retry_at ASC
                LIMIT ?
                """,
                (now.astimezone(UTC).isoformat(), limit),
            ).fetchall()
        return [_record_from_mapping(row) for row in rows]

    async def complete(self, job_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM pending_ingestions WHERE job_id = ?", (job_id,))

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
                SET retry_count = ?, last_error = ?, next_retry_at = ?
                WHERE job_id = ?
                """,
                (retry_count, last_error, next_retry_at.astimezone(UTC).isoformat(), job_id),
            )

    async def get_retry_metadata(self, job_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT retry_count, next_retry_at, max_retries, last_error
                FROM pending_ingestions
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()
        return dict(row) if row else None


class PostgresPendingIngestionStore(PendingIngestionStore):
    """PostgreSQL-backed pending-ingestion queue for production."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._pool: Any = None

    async def _get_pool(self) -> Any:
        if self._pool is None:
            import asyncpg

            self._pool = await asyncpg.create_pool(self._database_url)
            await self._init_schema()
        return self._pool

    async def _init_schema(self) -> None:
        pool = self._pool
        async with pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_ingestions (
                    job_id TEXT PRIMARY KEY,
                    source_url TEXT NOT NULL,
                    extraction_result_json TEXT NOT NULL,
                    relationships_json TEXT NOT NULL,
                    retry_count INTEGER NOT NULL,
                    next_retry_at TIMESTAMPTZ NOT NULL,
                    max_retries INTEGER NOT NULL,
                    last_error TEXT
                )
                """
            )

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
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pending_ingestions (
                    job_id, source_url, extraction_result_json, relationships_json,
                    retry_count, next_retry_at, max_retries, last_error
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT(job_id) DO UPDATE SET
                    source_url = EXCLUDED.source_url,
                    extraction_result_json = EXCLUDED.extraction_result_json,
                    relationships_json = EXCLUDED.relationships_json,
                    retry_count = EXCLUDED.retry_count,
                    next_retry_at = EXCLUDED.next_retry_at,
                    max_retries = EXCLUDED.max_retries,
                    last_error = EXCLUDED.last_error
                """,
                job_id,
                source_url,
                extraction_result_json,
                relationships_json,
                retry_count,
                next_retry_at,
                max_retries,
                last_error,
            )

    async def get_due(self, now: datetime, limit: int = 25) -> list[PendingIngestionRecord]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM pending_ingestions
                WHERE next_retry_at <= $1
                ORDER BY next_retry_at ASC
                LIMIT $2
                """,
                now,
                limit,
            )
        return [_record_from_mapping(row) for row in rows]

    async def complete(self, job_id: str) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM pending_ingestions WHERE job_id = $1", job_id)

    async def reschedule(
        self,
        job_id: str,
        retry_count: int,
        last_error: str,
        next_retry_at: datetime,
    ) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE pending_ingestions
                SET retry_count = $1, last_error = $2, next_retry_at = $3
                WHERE job_id = $4
                """,
                retry_count,
                last_error,
                next_retry_at,
                job_id,
            )

    async def get_retry_metadata(self, job_id: str) -> dict | None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT retry_count, next_retry_at, max_retries, last_error
                FROM pending_ingestions
                WHERE job_id = $1
                """,
                job_id,
            )
        return dict(row) if row else None

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None


def _record_from_mapping(row: Any) -> PendingIngestionRecord:
    data = dict(row)
    next_retry_at = data["next_retry_at"]
    if isinstance(next_retry_at, str):
        next_retry_at = datetime.fromisoformat(next_retry_at)
    return PendingIngestionRecord(
        job_id=data["job_id"],
        source_url=data["source_url"],
        extraction_result_json=data["extraction_result_json"],
        relationships_json=data["relationships_json"],
        retry_count=data["retry_count"],
        next_retry_at=next_retry_at,
        max_retries=data["max_retries"],
        last_error=data["last_error"],
    )


def build_pending_ingestion_store() -> PendingIngestionStore:
    database_url = os.getenv("LAYER2_DATABASE_URL") or os.getenv("DATABASE_URL")

    if database_url:
        if database_url.startswith("sqlite"):
            if _is_production_like():
                raise RuntimeError(
                    "Layer 2 pending-ingestion store refusing SQLite URL in "
                    f"production-like environment {_current_environment()!r}."
                )
            return SqlitePendingIngestionStore(_sqlite_path_from_url(database_url))
        if not database_url.startswith(("postgres://", "postgresql://")):
            raise RuntimeError("Layer 2 pending-ingestion store must point to PostgreSQL.")
        return PostgresPendingIngestionStore(database_url)

    if _is_production_like():
        raise RuntimeError(
            "Layer 2 pending-ingestion store must point to PostgreSQL in "
            f"production-like environment {_current_environment()!r}."
        )

    return SqlitePendingIngestionStore(
        os.getenv("PENDING_INGESTION_SQLITE_PATH", "./data/pending_ingestion.db")
    )


def _sqlite_path_from_url(database_url: str) -> str:
    return database_url.removeprefix("sqlite:///").removeprefix("sqlite://")


__all__ = [
    "PendingIngestionRecord",
    "PendingIngestionStore",
    "PostgresPendingIngestionStore",
    "SqlitePendingIngestionStore",
    "build_pending_ingestion_store",
]
