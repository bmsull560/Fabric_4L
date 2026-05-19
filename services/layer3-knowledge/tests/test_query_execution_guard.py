"""Regression coverage for Layer 3 query execution tenant fail-closed behavior."""

from __future__ import annotations

import pytest

from db.query_execution import TenantQueryValidationError, run_tenant_query


@pytest.mark.asyncio
async def test_run_tenant_query_rejects_tenant_owned_label_without_tenant_predicate() -> None:
    class FakeSession:
        async def run(self, query, params):  # pragma: no cover
            raise AssertionError("unsafe query must be blocked before execution")

    with pytest.raises(TenantQueryValidationError, match="missing tenant scoping"):
        await run_tenant_query(
            FakeSession(),
            "MATCH (e:Entity) WHERE e.id = $entity_id RETURN e",
            {"entity_id": "ent-1"},
            tenant_id="tenant-a",
        )
