"""
Async SQLAlchemy engine and session management for Layer 5.

Uses asyncpg for production and aiosqlite for tests (via DATABASE_URL override).
Follows the same pattern as Layer 1's database.py but with async support.
"""

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.types import CHAR, TypeDecorator

from .config import get_settings

# ---------------------------------------------------------------------------
# SQLite UUID type adapter
# ---------------------------------------------------------------------------


class SQLiteUUID(TypeDecorator):
    """
    Platform-independent UUID type.

    Uses PostgreSQL's UUID type when available, otherwise stores as CHAR(32).
    This is needed because SQLite doesn't have native UUID support and
    SQLAlchemy's UUID(as_uuid=True) stores as integers which causes issues.
    """

    impl = CHAR
    cache_ok = True

    def __init__(self):
        super().__init__(length=32)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value.hex
        return str(value).replace("-", "")

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, int):
            # Convert integer to UUID bytes then to UUID
            return uuid.UUID(int=value)
        if isinstance(value, str):
            if len(value) == 32:
                return uuid.UUID(value)
            return uuid.UUID(value)
        return value


# ---------------------------------------------------------------------------
# Engine — created once at import time, reused across requests
# ---------------------------------------------------------------------------

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _setup_sqlite_uuid_handling(url: str) -> None:
    """
    Configure SQLite to handle UUIDs properly.

    SQLite doesn't have native UUID support. When SQLAlchemy's UUID(as_uuid=True)
    is used with SQLite, UUIDs get stored as integers which causes retrieval issues.
    This patches the behavior to store UUIDs as strings instead.
    """
    if "sqlite" not in url.lower():
        return

    import sqlite3

    # Register adapter to convert UUID to string when storing
    sqlite3.register_adapter(uuid.UUID, lambda u: str(u))

    # Register converter to convert string back to UUID when retrieving
    sqlite3.register_converter(
        "UUID",
        lambda val: uuid.UUID(val.decode() if isinstance(val, bytes) else str(val)),
    )


def get_engine() -> AsyncEngine:
    """Return (or lazily create) the shared async engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=settings.db_pool_pre_ping,
            echo=settings.debug,
            future=True,
        )
        _setup_sqlite_uuid_handling(_engine, settings.database_url)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return (or lazily create) the shared session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _session_factory


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session.

    Usage::

        @router.get("/truths/{id}")
        async def get_truth(id: UUID, db: AsyncSession = Depends(get_db)):
            ...
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Context manager for non-FastAPI usage (services, background tasks)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for use outside of FastAPI request lifecycle."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Lifecycle helpers (called from FastAPI lifespan)
# ---------------------------------------------------------------------------


async def init_db() -> None:
    """Create all tables if they do not exist (dev/test convenience)."""
    from .models import Base

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose the engine connection pool on shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
