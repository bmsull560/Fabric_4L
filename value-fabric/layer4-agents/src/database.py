"""
Async SQLAlchemy engine and session management for Layer 4.

Extends the checkpoint database configuration to support operational data storage
for accounts, CRM sync metadata, and workflow state.

P0-08: Supports PostgreSQL Row-Level Security via SET LOCAL app.tenant_id
SECURITY: Fail-safe tenant isolation - tenant context is mandatory
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

# ---------------------------------------------------------------------------
# Declarative Base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Shared declarative base for all Layer 4 models."""

    pass


# ---------------------------------------------------------------------------
# Engine — created once at import time, reused across requests
# ---------------------------------------------------------------------------

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_database_url() -> str:
    """Get database URL from environment.

    Falls back to checkpoint database URL for compatibility,
    but allows separate configuration for operational data.
    """
    return os.getenv(
        "LAYER4_DATABASE_URL",
        os.getenv(
            "CHECKPOINT_DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@postgres:5432/layer4_agents",
        ),
    )


def get_engine() -> AsyncEngine:
    """Return (or lazily create) the shared async engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            get_database_url(),
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False,
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


class TenantContextError(Exception):
    """Raised when tenant context is missing or invalid in fail-safe mode."""
    pass


# SECURITY: Fail-safe mode - require explicit tenant context
# Set to False only for admin/system operations with proper role validation
FAIL_SAFE_MODE = True


def validate_tenant_id(tenant_id: UUID | str | None) -> str:
    """Validate tenant_id format and return normalized string.
    
    SECURITY: Strict validation to prevent tenant confusion attacks.
    
    Args:
        tenant_id: Tenant identifier to validate
        
    Returns:
        Normalized tenant ID string
        
    Raises:
        TenantContextError: If tenant_id is invalid or missing in fail-safe mode
    """
    if tenant_id is None:
        if FAIL_SAFE_MODE:
            raise TenantContextError(
                "Tenant context is mandatory in fail-safe mode. "
                "Use explicit admin role context for system operations."
            )
        return ""
    
    # Convert to string and normalize
    normalized = str(tenant_id).strip()
    
    # Fail-safe: empty tenant_id is not allowed
    if not normalized:
        raise TenantContextError(
            "Empty tenant_id is not allowed. Provide a valid tenant context."
        )
    
    # Validate UUID format for strict tenant isolation
    if normalized.lower() not in ('system', 'admin', 'internal'):
        try:
            UUID(normalized)
        except ValueError:
            raise TenantContextError(
                f"Invalid tenant_id format: {normalized}. Expected UUID."
            )
    
    return normalized


async def set_tenant_context(session: AsyncSession, tenant_id: UUID | str | None) -> None:
    """P0-08: Set PostgreSQL app.tenant_id for RLS policies.
    
    SECURITY: Fail-safe semantics - tenant context is mandatory unless
    explicitly using admin bypass with proper role authentication.

    Executes SET LOCAL app.tenant_id = '...' which applies for the
    duration of the current transaction. RLS policies in PostgreSQL
    can reference current_setting('app.tenant_id') to filter rows.

    Args:
        session: SQLAlchemy async session
        tenant_id: Tenant UUID or string identifier (whitespace is stripped)
        
    Raises:
        TenantContextError: If tenant_id is missing/invalid in fail-safe mode
    """
    # SECURITY: Validate tenant context with fail-safe semantics
    normalized_id = validate_tenant_id(tenant_id)
    
    # Set tenant context for RLS policies
    # Empty string only allowed for admin roles (enforced by RLS policy TO clause)
    await session.execute(
        text("SET LOCAL app.tenant_id = :tenant_id"),
        {"tenant_id": normalized_id}
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions (without RLS).
    
    SECURITY: Use only for health checks or admin operations with proper
    role authentication. All production endpoints should use get_db_with_tenant.
    """
    # SECURITY: Bypass tenant validation for health checks (admin role required in DB)
    factory = get_session_factory()
    async with factory() as session:
        # Clear tenant context - RLS bypass only works for admin/system roles
        await session.execute(text("SET LOCAL app.tenant_id = ''"))
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db_with_tenant(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID", description="Tenant UUID for RLS isolation")
) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session with RLS tenant context.
    
    SECURITY: Mandatory tenant context - X-Tenant-ID header is required.
    Fail-safe: Rejects requests without explicit tenant identification.

    Automatically extracts X-Tenant-ID header and sets PostgreSQL app.tenant_id
    for Row-Level Security policies.

    Usage::

        @router.get("/accounts/{id}")
        async def get_account(id: UUID, db: AsyncSession = Depends(get_db_with_tenant)):
            ...
    
    Raises:
        HTTPException: 400 if X-Tenant-ID header is missing or invalid
    """
    try:
        # SECURITY: Fail-safe validation via validate_tenant_id
        # This checks for empty values and validates UUID format
        validate_tenant_id(x_tenant_id)
    except TenantContextError as e:
        # Convert TenantContextError to HTTP 400 for FastAPI
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    
    factory = get_session_factory()
    async with factory() as session:
        # P0-08: Set tenant context for RLS (already validated above)
        await session.execute(
            text("SET LOCAL app.tenant_id = :tenant_id"),
            {"tenant_id": x_tenant_id}
        )
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
async def db_session(
    tenant_id: UUID | str | None = None,
    *,
    require_tenant: bool = True
) -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for use outside of FastAPI request lifecycle.

    SECURITY: Fail-safe by default - tenant context is mandatory.

    Args:
        tenant_id: Tenant ID to set for RLS context (P0-08)
        require_tenant: If True (default), enforce mandatory tenant context.
                       Set to False only for admin/system operations with
                       proper role authentication.
    
    Raises:
        TenantContextError: If tenant_id is missing/invalid and require_tenant=True
    """
    # SECURITY: Enforce mandatory tenant context by default
    if require_tenant:
        # This will raise TenantContextError in fail-safe mode if tenant_id is invalid
        tenant_id = validate_tenant_id(tenant_id)
    elif tenant_id is not None:
        # Validate even when require_tenant=False, if a tenant_id was provided
        tenant_id = validate_tenant_id(tenant_id)
    # If require_tenant=False and tenant_id is None, we skip validation (admin bypass)
    
    factory = get_session_factory()
    async with factory() as session:
        # P0-08: Set tenant context for RLS
        # Empty string for admin bypass, validated tenant_id otherwise
        normalized = str(tenant_id) if tenant_id is not None else ""
        await session.execute(
            text("SET LOCAL app.tenant_id = :tenant_id"),
            {"tenant_id": normalized}
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
