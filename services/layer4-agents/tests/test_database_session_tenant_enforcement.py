from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession as SQLAAsyncSession

import src.database as database


@pytest.mark.asyncio
async def test_tenant_enforced_session_rejects_statement_without_context() -> None:
    session = database.TenantEnforcedAsyncSession()

    with pytest.raises(database.TenantContextError, match="statement execution"):
        await session.execute(text("SELECT 1"))


@pytest.mark.asyncio
async def test_tenant_enforced_session_allows_statement_after_context_set() -> None:
    session = database.TenantEnforcedAsyncSession()
    database._mark_session_tenant_context(session, "550e8400-e29b-41d4-a716-446655440000")

    with patch.object(SQLAAsyncSession, "execute", AsyncMock(return_value="ok")) as mocked_execute:
        result = await session.execute(text("SELECT 1"))

    assert result == "ok"
    mocked_execute.assert_awaited_once()


def test_get_engine_rejects_rls_disabled_database_in_protected_environment(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("LAYER4_DATABASE_URL", "sqlite+aiosqlite:///tmp/layer4.db")
    monkeypatch.setattr(database, "_engine", None)

    with pytest.raises(RuntimeError, match="PostgreSQL"):
        database.get_engine()
