"""
Async SQLAlchemy engine and session management for Layer 5.

Uses asyncpg for production and aiosqlite for tests (via DATABASE_URL override).
Follows the same pattern as Layer 1's database.py but with async support.

P0-08: Supports PostgreSQL Row-Level Security via SET LOCAL app.tenant_id
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Optional
from uuid import UUID

from fastapi import Header
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import get_settings

# ---------------------------------------------------------------------------
# Engine — created once at import time, reused across requests
# ---------------------------------------------------------------------------

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


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


async def set_tenant_context(session: AsyncSession, tenant_id: Optional[UUID | str]) -> None:
    """P0-08: Set PostgreSQL app.tenant_id for RLS policies.

    Executes SET LOCAL app.tenant_id = '...' which applies for the
    duration of the current transaction. RLS policies in PostgreSQL
    can reference current_setting('app.tenant_id') to filter rows.

    Args:
        session: SQLAlchemy async session
        tenant_id: Tenant UUID or string identifier (whitespace is stripped)
    """
    # Normalize tenant_id: strip whitespace, convert to string, check for empty
    normalized_id = str(tenant_id).strip() if tenant_id else ""
    
    if normalized_id:
        # Use SET LOCAL - only affects current transaction
        await session.execute(
            text("SET LOCAL app.tenant_id = :tenant_id"),
            {"tenant_id": normalized_id}
        )
    else:
        # Clear tenant context for system-level operations
        await session.execute(text("SET LOCAL app.tenant_id = ''"))


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


async def get_db_with_tenant(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session with RLS tenant context.

    Automatically extracts X-Tenant-ID header and sets PostgreSQL app.tenant_id
    for Row-Level Security policies.

    Usage::

        @router.get("/truths/{id}")
        async def get_truth(id: UUID, db: AsyncSession = Depends(get_db_with_tenant)):
            ...
    """
    factory = get_session_factory()
    async with factory() as session:
        # P0-08: Set tenant context for RLS
        await set_tenant_context(session, x_tenant_id)
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
async def db_session(tenant_id: Optional[UUID | str] = None) -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for use outside of FastAPI request lifecycle.

    Args:
        tenant_id: Optional tenant ID to set for RLS context (P0-08)
    """
    factory = get_session_factory()
    async with factory() as session:
        # P0-08: Set tenant context for RLS if provided
        if tenant_id:
            await set_tenant_context(session, tenant_id)
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
