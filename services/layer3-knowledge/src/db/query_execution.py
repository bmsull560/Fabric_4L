from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


class TenantQueryValidationError(ValueError):
    """Raised when Cypher execution violates tenant isolation requirements."""


_MATCH_PATTERN = re.compile(r"\bMATCH\b", re.IGNORECASE)
_TENANT_MARKERS = ("tenant_id", "tenantId", "$_tenant_id", "$tenant_id", "$tenantId")


@dataclass(frozen=True)
class TenantExecutionContext:
    tenant_id: str | None
    is_bypass: bool = False
    allow_system_query: bool = False


class TenantQueryExecutor:
    """Single query execution wrapper for tenant-scoped Cypher."""

    @classmethod
    async def run(
        cls,
        run_callable,
        query: str,
        parameters: dict[str, Any] | None,
        context: TenantExecutionContext,
    ) -> Any:
        params = dict(parameters or {})
        if context.tenant_id:
            params.setdefault("tenant_id", context.tenant_id)
            params.setdefault("_tenant_id", context.tenant_id)

        cls._validate(query=query, params=params, context=context)
        return await run_callable(query, params)

    @classmethod
    def _validate(cls, query: str, params: dict[str, Any], context: TenantExecutionContext) -> None:
        lowered = query.lower()
        if context.is_bypass:
            return
        if not context.tenant_id and not context.allow_system_query:
            raise TenantQueryValidationError("Tenant context is required for Cypher execution")

        if _MATCH_PATTERN.search(query):
            has_tenant = any(marker.lower() in lowered for marker in _TENANT_MARKERS) or any(
                key in params for key in ("tenant_id", "_tenant_id", "tenantId")
            )
            if not has_tenant and not context.allow_system_query:
                raise TenantQueryValidationError(
                    "Denied broad MATCH traversal without tenant constraints; set allow_system_query=True only for allowlisted system queries"
                )
