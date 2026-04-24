# Canonical database session contract for Fabric 4L.
from collections.abc import AsyncGenerator
from contextlib import asyncontextmanager
from sqlalchemy.ext.asyncio import AsyncSession


nasync def get_db_from_context(context) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session with tenant context set for RLS.

    Rules:
    - Extract tenant_id from RequestContext (set by GovernanceMiddleware).
    - Validate tenant_id format (UUID or reserved keyword).
    - Execute SET LOCAL app.tenant_id = :tenant_id on session open.
    - Commit on success, rollback on exception.
    - Route handlers MUST NOT call commit/rollback manually.
    """
    ...


@asyncontextmanager
async def db_session_for_context(context) -> AsyncGenerator[AsyncSession, None]:
    """Context manager for DB sessions outside FastAPI request lifecycle."""
    ...
