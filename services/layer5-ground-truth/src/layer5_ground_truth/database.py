"""Async database setup and tenant-scoped dependencies for Layer 5."""

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.types import CHAR, TypeDecorator

from .api.tenant_context import enforce_authenticated_tenant_precedence
from .config import get_settings

try:
    from value_fabric.shared.identity.context import RequestContext, get_request_context

    SHARED_IDENTITY_AVAILABLE = True
except ImportError:
    SHARED_IDENTITY_AVAILABLE = False
    RequestContext = None  # type: ignore

    def get_request_context():  # type: ignore
        return None

try:
    from value_fabric.shared.database import TenantContextError, validate_tenant_id

    SHARED_DATABASE_AVAILABLE = True
except ImportError:
    SHARED_DATABASE_AVAILABLE = False

    class TenantContextError(Exception):  # type: ignore
        pass

    def validate_tenant_id(tenant_id: UUID | str | None) -> str:  # type: ignore
        if tenant_id is None:
            raise TenantContextError(
                "Tenant context is mandatory. Use explicit admin role context for system operations."
            )
        normalized = str(tenant_id).strip()
        if not normalized:
            raise TenantContextError("Empty tenant_id is not allowed.")
        if normalized.lower() not in ("system", "admin", "internal"):
            try:
                UUID(normalized)
            except ValueError as exc:
                raise TenantContextError(f"Invalid tenant_id format: {normalized}") from exc
        return normalized


class SQLiteUUID(TypeDecorator):
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
            return uuid.UUID(int=value)
        if isinstance(value, str):
            return uuid.UUID(value)
        return value


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _setup_sqlite_uuid_handling(url: str) -> None:
    if "sqlite" not in url.lower():
        return
    import sqlite3

    sqlite3.register_adapter(uuid.UUID, lambda u: str(u))
    sqlite3.register_converter(
        "UUID",
        lambda val: uuid.UUID(val.decode() if isinstance(val, bytes) else str(val)),
    )


def get_engine() -> AsyncEngine:
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
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    import warnings

    context = get_request_context() if SHARED_IDENTITY_AVAILABLE else None
    if context is not None and context.tenant_id is not None:
        raise RuntimeError(
            "Unsafe get_db() usage detected with tenant request context. "
            "Tenant-scoped routes must depend on get_db_from_context()."
        )

    warnings.warn(
        "get_db() does not enforce RLS tenant context. Use get_db_from_context() for tenant-scoped queries.",
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


@asynccontextmanager
async def db_session(tenant_id: str | None = None) -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        if tenant_id is not None:
            validated = validate_tenant_id(tenant_id)
            await session.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": validated})
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    from .models import Base

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


async def get_db_from_context(
    request: Request,
    context: "RequestContext" = Depends(get_request_context),  # type: ignore
) -> AsyncGenerator[AsyncSession, None]:
    if not SHARED_IDENTITY_AVAILABLE:
        raise RuntimeError("shared.identity required for get_db_from_context")
    if not context or not context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required. Ensure request passed through GovernanceMiddleware.",
        )

    try:
        tenant_id = validate_tenant_id(context.tenant_id)
    except TenantContextError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    auth_tid = UUID(tenant_id)
    await enforce_authenticated_tenant_precedence(
        request,
        auth_tid,
        actor=str(context.user_id) if getattr(context, "user_id", None) else None,
    )

    factory = get_session_factory()
    async with factory() as session:
        await session.execute(text("SET LOCAL app.tenant_id = :tenant_id"), {"tenant_id": tenant_id})
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db_with_optional_tenant(
    request: Request,
    context: "RequestContext" = Depends(get_request_context),  # type: ignore
) -> AsyncGenerator[AsyncSession, None]:
    if not SHARED_IDENTITY_AVAILABLE:
        raise RuntimeError("shared.identity required for get_db_with_optional_tenant")

    factory = get_session_factory()
    async with factory() as session:
        if context.is_super_admin():
            await session.execute(text("SET LOCAL app.tenant_id = ''"))
        elif context.tenant_id:
            try:
                tenant_id = validate_tenant_id(context.tenant_id)
            except TenantContextError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
            await enforce_authenticated_tenant_precedence(
                request,
                UUID(tenant_id),
                actor=str(context.user_id) if getattr(context, "user_id", None) else None,
            )
            await session.execute(text("SET LOCAL app.tenant_id = :tenant_id"), {"tenant_id": tenant_id})
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
