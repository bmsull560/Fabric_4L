"""Canonical database session contract for Fabric 4L."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any, Protocol
from uuid import UUID

from .context import ISOLATION_TIER_SHARED, RequestContext

RESERVED_TENANT_KEYWORDS = frozenset({"admin", "internal", "system"})


class SessionFactoryNotConfiguredError(RuntimeError):
    """Raised when the canonical session factory has not been configured."""


class TenantContextError(ValueError):
    """Raised when tenant context is missing or malformed."""


class UnsupportedIsolationTierError(RuntimeError):
    """Raised when the canonical contract sees an unsupported isolation tier."""


class SessionLifecycleError(RuntimeError):
    """Raised when callers try to manage a contract-owned session lifecycle."""


class SupportsAsyncSession(Protocol):
    async def execute(
        self,
        statement: str,
        params: dict[str, Any] | None = None,
    ) -> Any: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


SessionFactory = Callable[[], Any]
_session_factory: SessionFactory | None = None


def set_session_factory(factory: SessionFactory) -> None:
    """Configure the async session factory used by canonical tests."""

    global _session_factory
    _session_factory = factory


def clear_session_factory() -> None:
    """Reset the configured session factory."""

    global _session_factory
    _session_factory = None


def _require_session_factory() -> SessionFactory:
    if _session_factory is None:
        raise SessionFactoryNotConfiguredError(
            "Session factory is not configured. Use set_session_factory() in tests "
            "or wire the canonical contract to a real AsyncSession factory."
        )
    return _session_factory


def validate_tenant_id(tenant_id: UUID | str | None) -> str:
    """Validate tenant_id format using the canonical fail-closed rules."""

    if tenant_id is None:
        raise TenantContextError(
            "Tenant context is mandatory. Ensure request includes valid tenant_id "
            "in JWT token or X-Tenant-ID header. For admin operations, use "
            "get_db_with_optional_tenant() with require_super_admin() dependency."
        )

    normalized = str(tenant_id).strip()
    if not normalized:
        raise TenantContextError(
            "Empty tenant_id is not allowed. Provide a valid tenant context."
        )

    if normalized.lower() in RESERVED_TENANT_KEYWORDS:
        return normalized.lower()

    try:
        return str(UUID(normalized))
    except ValueError as exc:
        raise TenantContextError(
            f"Invalid tenant_id format: '{normalized}'. Expected valid UUID or "
            f"reserved keyword ({', '.join(sorted(RESERVED_TENANT_KEYWORDS))})."
        ) from exc


async def set_tenant_context(
    session: SupportsAsyncSession,
    tenant_id: UUID | str | None,
) -> None:
    """Apply the canonical RLS session setting."""

    normalized_id = validate_tenant_id(tenant_id)
    await session.execute(
        "SET LOCAL app.tenant_id = :tenant_id",
        {"tenant_id": normalized_id},
    )


def _require_context(context: RequestContext | None) -> RequestContext:
    if context is None or context.tenant_id is None:
        raise TenantContextError(
            "Tenant context required. Ensure request has passed through GovernanceMiddleware."
        )
    return context


def _require_supported_isolation_tier(context: RequestContext) -> None:
    if context.isolation_tier != ISOLATION_TIER_SHARED:
        raise UnsupportedIsolationTierError(
            f"Isolation tier '{context.isolation_tier}' not yet implemented"
        )


class _LifecycleManagedSession:
    """Thin wrapper that blocks manual commit/rollback by callers."""

    def __init__(self, session: SupportsAsyncSession):
        self._session = session

    async def execute(
        self,
        statement: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        if params is None:
            return await self._session.execute(statement)
        return await self._session.execute(statement, params)

    async def commit(self) -> None:
        raise SessionLifecycleError(
            "Route handlers MUST NOT call commit/rollback manually; session "
            "lifecycle is managed by get_db_from_context()/db_session_for_context()."
        )

    async def rollback(self) -> None:
        raise SessionLifecycleError(
            "Route handlers MUST NOT call commit/rollback manually; session "
            "lifecycle is managed by get_db_from_context()/db_session_for_context()."
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._session, name)


@asynccontextmanager
async def _session_scope(
    context: RequestContext | None,
) -> AsyncGenerator[_LifecycleManagedSession, None]:
    resolved_context = _require_context(context)
    _require_supported_isolation_tier(resolved_context)

    factory = _require_session_factory()
    async with factory() as session:
        await set_tenant_context(session, resolved_context.tenant_id)
        managed_session = _LifecycleManagedSession(session)
        try:
            yield managed_session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db_from_context(
    context: RequestContext | None,
) -> AsyncGenerator[_LifecycleManagedSession, None]:
    """Yield an async DB session with tenant context set for RLS.

    Rules:
    - Extract tenant_id from RequestContext (set by GovernanceMiddleware).
    - Validate tenant_id format (UUID or reserved keyword).
    - Execute SET LOCAL app.tenant_id = :tenant_id on session open.
    - Commit on success, rollback on exception.
    - Route handlers MUST NOT call commit/rollback manually.
    """

    async with _session_scope(context) as session:
        yield session


@asynccontextmanager
async def db_session_for_context(
    context: RequestContext | None,
) -> AsyncGenerator[_LifecycleManagedSession, None]:
    """Context manager for DB sessions outside FastAPI request lifecycle."""

    async with _session_scope(context) as session:
        yield session
