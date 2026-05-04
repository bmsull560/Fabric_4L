from __future__ import annotations

from uuid import uuid4

import pytest

from canonical.context import ISOLATION_TIER_SCHEMA, RequestContext
from canonical.database import (
    SessionLifecycleError,
    TenantContextError,
    UnsupportedIsolationTierError,
    clear_session_factory,
    db_session_for_context,
    get_db_from_context,
    set_session_factory,
    validate_tenant_id,
)


class FakeSession:
    def __init__(self) -> None:
        self.statements: list[tuple[str, dict[str, str] | None]] = []
        self.committed = False
        self.rolled_back = False

    async def execute(
        self,
        statement: str,
        params: dict[str, str] | None = None,
    ) -> dict[str, object]:
        self.statements.append((statement, params))
        return {"statement": statement, "params": params}

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


class FakeSessionContext:
    def __init__(self, session: FakeSession) -> None:
        self._session = session

    async def __aenter__(self) -> FakeSession:
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


@pytest.fixture
def fake_session() -> FakeSession:
    session = FakeSession()
    set_session_factory(lambda: FakeSessionContext(session))
    yield session
    clear_session_factory()


@pytest.mark.asyncio
async def test_get_db_from_context_sets_tenant_context_and_commits(
    fake_session: FakeSession,
) -> None:
    context = RequestContext(tenant_id=uuid4())
    generator = get_db_from_context(context)

    session = await anext(generator)
    await session.execute("SELECT 1")
    with pytest.raises(StopAsyncIteration):
        await generator.asend(None)

    assert fake_session.statements == [
        ("SET LOCAL app.tenant_id = :tenant_id", {"tenant_id": str(context.tenant_id)}),
        ("SELECT 1", None),
    ]
    assert fake_session.committed is True
    assert fake_session.rolled_back is False


@pytest.mark.asyncio
async def test_get_db_from_context_rolls_back_on_exception(
    fake_session: FakeSession,
) -> None:
    generator = get_db_from_context(RequestContext(tenant_id=uuid4()))
    await anext(generator)

    with pytest.raises(RuntimeError, match="boom"):
        await generator.athrow(RuntimeError("boom"))

    assert fake_session.committed is False
    assert fake_session.rolled_back is True


@pytest.mark.asyncio
async def test_db_session_for_context_uses_same_lifecycle_contract(
    fake_session: FakeSession,
) -> None:
    context = RequestContext(tenant_id=uuid4())

    async with db_session_for_context(context) as session:
        await session.execute("SELECT 42")

    assert fake_session.statements == [
        ("SET LOCAL app.tenant_id = :tenant_id", {"tenant_id": str(context.tenant_id)}),
        ("SELECT 42", None),
    ]
    assert fake_session.committed is True
    assert fake_session.rolled_back is False


@pytest.mark.asyncio
async def test_session_rejects_manual_commit_or_rollback(
    fake_session: FakeSession,
) -> None:
    generator = get_db_from_context(RequestContext(tenant_id=uuid4()))
    session = await anext(generator)

    with pytest.raises(
        SessionLifecycleError,
        match="MUST NOT call commit/rollback manually",
    ):
        await session.commit()

    with pytest.raises(
        SessionLifecycleError,
        match="MUST NOT call commit/rollback manually",
    ):
        await session.rollback()

    with pytest.raises(StopAsyncIteration):
        await generator.asend(None)
    assert fake_session.committed is True


def test_validate_tenant_id_accepts_uuid_and_reserved_keywords() -> None:
    tenant_id = uuid4()

    assert validate_tenant_id(tenant_id) == str(tenant_id)
    assert validate_tenant_id(" system ") == "system"


@pytest.mark.parametrize(
    ("tenant_id", "message"),
    [
        (
            None,
            "Tenant context is mandatory. Ensure request includes valid tenant_id",
        ),
        ("", "Empty tenant_id is not allowed. Provide a valid tenant context."),
        (
            "not-a-uuid",
            "Invalid tenant_id format: 'not-a-uuid'. Expected valid UUID or reserved keyword",
        ),
    ],
)
def test_validate_tenant_id_negative_messages(
    tenant_id: str | None,
    message: str,
) -> None:
    with pytest.raises(TenantContextError, match=message):
        validate_tenant_id(tenant_id)


@pytest.mark.asyncio
async def test_get_db_from_context_requires_tenant_context() -> None:
    with pytest.raises(
        TenantContextError,
        match="Tenant context required. Ensure request has passed through GovernanceMiddleware.",
    ):
        await anext(get_db_from_context(RequestContext()))


@pytest.mark.asyncio
async def test_get_db_from_context_rejects_unsupported_isolation_tier(
    fake_session: FakeSession,
) -> None:
    generator = get_db_from_context(
        RequestContext(
            tenant_id=uuid4(),
            isolation_tier=ISOLATION_TIER_SCHEMA,
        )
    )

    with pytest.raises(
        UnsupportedIsolationTierError,
        match="Isolation tier 'schema' not yet implemented",
    ):
        await anext(generator)

    assert fake_session.statements == []
