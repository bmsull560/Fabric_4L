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
        _setup_sqlite_uuid_handling(settings.database_url)
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
    Internal-only FastAPI dependency that yields an async database session.

    .. warning::

        INTERNAL ONLY — Use ``get_db_from_context`` for all tenant routes.
        This dependency does NOT set ``SET LOCAL app.tenant_id``, so RLS
        policies will block all rows.  It is retained only for the
        ``init_db`` / health-check paths that run before tenant context
        is available.

    Usage::

        @router.get("/truths/{id}")
        async def get_truth(id: UUID, db: AsyncSession = Depends(get_db_from_context)):
            ...
    """
    import warnings

    context = get_request_context() if SHARED_IDENTITY_AVAILABLE else None
    if context is not None and context.tenant_id is not None:
        raise RuntimeError(
            "Unsafe get_db() usage detected with tenant request context. "
            "Tenant-scoped routes must depend on get_db_from_context()."
        )

    warnings.warn(
        "get_db() does not enforce RLS tenant context. "
        "Use get_db_from_context() for tenant-scoped queries.",
        DeprecationWarning,
        stacklevel=2,
    )
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
async def db_session(tenant_id: str | None = None) -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for use outside of FastAPI request lifecycle.

    Args:
        tenant_id: UUID string of the tenant.  When provided, the session
            executes ``SET LOCAL app.tenant_id`` so that PostgreSQL RLS
            policies are enforced.  Omitting ``tenant_id`` is only valid
            for system-level operations (migrations, health checks).

    Raises:
        TenantContextError: If ``tenant_id`` is provided but invalid.
    """
    factory = get_session_factory()
    async with factory() as session:
        if tenant_id is not None:
            validated = validate_tenant_id(tenant_id)
            await session.execute(
                text("SET LOCAL app.tenant_id = :tid"),
                {"tid": validated},
            )
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


# ---------------------------------------------------------------------------
# Sprint 5: Context-aware database session for async layers (Task 5.2.2)
# ---------------------------------------------------------------------------

from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import text

try:
    from value_fabric.shared.identity.context import RequestContext, get_request_context
    SHARED_IDENTITY_AVAILABLE = True
except ImportError:
    SHARED_IDENTITY_AVAILABLE = False
    RequestContext = None  # type: ignore

    def get_request_context():  # type: ignore
        """Fail-closed fallback used when the shared identity package is unavailable."""
        return None

try:
    from value_fabric.shared.database import TenantContextError, validate_tenant_id
    SHARED_DATABASE_AVAILABLE = True
except ImportError:
    SHARED_DATABASE_AVAILABLE = False

    class TenantContextError(Exception):  # type: ignore
        """Fallback when shared database module is unavailable."""

        pass

    def validate_tenant_id(tenant_id: UUID | str | None) -> str:  # type: ignore
        """Fallback validation when shared database module is unavailable."""
        if tenant_id is None:
            raise TenantContextError(
                "Tenant context is mandatory. "
                "Use explicit admin role context for system operations."
            )

        normalized = str(tenant_id).strip()
        if not normalized:
            raise TenantContextError("Empty tenant_id is not allowed.")

        # Validate UUID format
        if normalized.lower() not in ("system", "admin", "internal"):
            try:
                UUID(normalized)
            except ValueError:
                raise TenantContextError(f"Invalid tenant_id format: {normalized}")

        return normalized


async def get_db_from_context(
    context: "RequestContext" = Depends(get_request_context),  # type: ignore
) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for DB session with tenant from RequestContext (Sprint 5).

    SECURITY: Uses RequestContext set by GovernanceMiddleware.
    Fail-safe: Rejects requests without explicit tenant identification.

    Usage::

        @router.get("/items")
        async def list_items(
            db: AsyncSession = Depends(get_db_from_context),
            context: RequestContext = Depends(get_request_context)
        ):
            ...

    Raises:
        HTTPException: 400 if tenant context is missing
    """
    if not SHARED_IDENTITY_AVAILABLE:
        raise RuntimeError(
            "shared.identity required for get_db_from_context"
        )

    if not context or not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required. Ensure request passed through GovernanceMiddleware.",
        )

    try:
        tenant_id = validate_tenant_id(context.tenant_id)
    except TenantContextError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    factory = get_session_factory()
    async with factory() as session:
        await session.execute(
            text("SET LOCAL app.tenant_id = :tenant_id"),
            {"tenant_id": tenant_id}
        )
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db_with_optional_tenant(
    context: "RequestContext" = Depends(get_request_context),  # type: ignore
) -> AsyncGenerator[AsyncSession, None]:
    """DB session with optional tenant for super-admin operations (Sprint 5).

    SECURITY: Must be combined with privileged access checks.
    Super-admins can bypass tenant context for cross-tenant operations.

    Usage::

        @router.get("/admin/all-tenants")
        async def get_all_tenants(
            db: AsyncSession = Depends(get_db_with_optional_tenant),
            context: RequestContext = Depends(require_request_context)
        ):
            ...

    Raises:
        HTTPException: 400 if non-super-admin without tenant context
    """
    if not SHARED_IDENTITY_AVAILABLE:
        raise RuntimeError(
            "shared.identity required for get_db_with_optional_tenant"
        )

    factory = get_session_factory()
    async with factory() as session:
        if context.is_super_admin():
            await session.execute(text("SET LOCAL app.tenant_id = ''"))
        elif context.tenant_id:
            try:
                tenant_id = validate_tenant_id(context.tenant_id)
            except TenantContextError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                ) from e
            await session.execute(
                text("SET LOCAL app.tenant_id = :tenant_id"),
                {"tenant_id": tenant_id}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant context required or super_admin role.",
            )
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
