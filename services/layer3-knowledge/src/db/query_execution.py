"""Compatibility wrapper for value_fabric.layer3.db.query_execution."""

<<<<<<< ours
from value_fabric.layer3.db.query_execution import *  # noqa: F401,F403
=======
import re
from dataclasses import dataclass
from typing import Any

from value_fabric.shared.identity.isolation import QueryScope, ScopedQuery

from value_fabric.layer3.security.query_validator import QueryValidator, ValidationSeverity


class TenantQueryValidationError(ValueError):
    """Raised when Cypher execution violates tenant isolation requirements."""


_MATCH_PATTERN = re.compile(r"\bMATCH\b", re.IGNORECASE)
_CLAUSE_PATTERN = re.compile(r"\b(MATCH|OPTIONAL\s+MATCH|CALL\s*\{|UNION(?:\s+ALL)?|WITH)\b", re.IGNORECASE)


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
        validator = QueryValidator(fail_closed=False)
        if context.is_bypass:
            return
        if not context.tenant_id and not context.allow_system_query:
            raise TenantQueryValidationError("Tenant context is required for Cypher execution")

        if _MATCH_PATTERN.search(query):
            findings = validator.validate_structural_tenant_scope(query, query_name="tenant_query_executor")
            structural_errors = [f for f in findings if f.severity == ValidationSeverity.ERROR]
            if structural_errors and not context.allow_system_query:
                details = "; ".join(f.message for f in structural_errors)
                raise TenantQueryValidationError(
                    f"Denied Cypher query due to missing tenant scoping in MATCH path: {details}"
                )

            clause_tokens = [m.group(1).upper() for m in _CLAUSE_PATTERN.finditer(query)]
            ambiguous = (
                clause_tokens.count("MATCH") + clause_tokens.count("OPTIONAL MATCH") > 1
                or any(token.startswith("UNION") for token in clause_tokens)
                or "CALL{" in "".join(token.replace(" ", "") for token in clause_tokens)
            )
            if ambiguous and not context.allow_system_query:
                raise TenantQueryValidationError(
                    "Denied ambiguous or multi-clause Cypher; only allowlisted system queries may opt in via allow_system_query=True"
                )


async def run_scoped_query(run_callable, scoped_query: ScopedQuery, *, is_bypass: bool = False) -> Any:
    """Central execution gateway for mandatory tenant-scope validation."""

    allow_system_query = scoped_query.scope != QueryScope.TENANT
    context = TenantExecutionContext(
        tenant_id=scoped_query.tenant_id,
        is_bypass=is_bypass,
        allow_system_query=allow_system_query,
    )
    return await TenantQueryExecutor.run(
        run_callable,
        scoped_query.cypher,
        scoped_query.params,
        context=context,
    )
>>>>>>> theirs
