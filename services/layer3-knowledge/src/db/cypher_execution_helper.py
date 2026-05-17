from __future__ import annotations

from typing import Any

from value_fabric.shared.identity.isolation import TenantScopedCypher

from ..db.query_execution import TenantExecutionContext, TenantQueryExecutor

_DEFAULT_LABELS = ("Capability", "UseCase", "Persona", "ValueDriver")


async def execute_tenant_cypher(
    *,
    operation: str,
    session: Any,
    query: str,
    params: dict[str, Any] | None,
    tenant_id: str,
    labels: tuple[str, ...] | None = None,
    allow_system_query: bool = False,
) -> Any:
    """Build + validate + execute tenant-scoped Cypher through one shared wrapper."""
    scoped = TenantScopedCypher(tenant_id).custom_tenant_query(
        query,
        params=params or {},
        operation=operation,
        labels=labels or _DEFAULT_LABELS,
    )

    context = TenantExecutionContext(
        tenant_id=tenant_id,
        allow_system_query=allow_system_query,
    )
    return await TenantQueryExecutor.run(
        session.run,
        scoped.cypher,
        scoped.params,
        context,
    )
