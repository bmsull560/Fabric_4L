from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from value_fabric.shared.identity.isolation import QueryScope, ScopedQuery

class TenantQueryValidationError(ValueError):
    """Raised when Cypher execution violates tenant isolation requirements."""


_MATCH_PATTERN = re.compile(r"\bMATCH\b", re.IGNORECASE)
_CLAUSE_PATTERN = re.compile(r"\b(MATCH|OPTIONAL\s+MATCH|CALL\s*\{|UNION(?:\s+ALL)?|WITH)\b", re.IGNORECASE)
_MATCH_CLAUSE_PATTERN = re.compile(
    r"(?is)\b(?:OPTIONAL\s+MATCH|MATCH)\b\s+"
    r"(.*?)(?=\bOPTIONAL\s+MATCH\b|\bMATCH\b|\bWITH\b|\bRETURN\b|\bUNWIND\b|\bCALL\b|\bORDER\s+BY\b|\bLIMIT\b|\bSKIP\b|$)"
)
_NODE_PATTERN = re.compile(
    r"\(\s*([A-Za-z_][A-Za-z0-9_]*)?\s*:\s*([A-Za-z_][A-Za-z0-9_]*)\s*(\{[^}]*\})?"
)
_TENANT_PREDICATE_PATTERN = re.compile(
    r"(?i)\b(?P<alias>[A-Za-z_][A-Za-z0-9_]*)\.tenant_id\s*(?:=|IN)\s*[$A-Za-z_]"
)
_TENANT_OWNED_LABELS = {
    "Battlecard",
    "Capability",
    "Competitor",
    "DecisionStep",
    "DecisionTrace",
    "Entity",
    "Feature",
    "Formula",
    "Outcome",
    "PROVEntity",
    "PainSignal",
    "Persona",
    "Product",
    "UseCase",
    "ValueDriver",
    "ValueSignal",
}


def _tenant_scoped_aliases(query: str) -> set[str]:
    return {match.group("alias") for match in _TENANT_PREDICATE_PATTERN.finditer(query)}


def _structural_tenant_scope_errors(query: str) -> list[str]:
    scoped_aliases = _tenant_scoped_aliases(query)
    errors: list[str] = []

    for match_clause in _MATCH_CLAUSE_PATTERN.findall(query):
        for alias, label, props in _NODE_PATTERN.findall(match_clause):
            if label not in _TENANT_OWNED_LABELS:
                continue
            prop_block = props or ""
            alias_name = alias.strip() if alias else ""
            has_tenant_in_props = bool(re.search(r"(?i)\btenant_id\b", prop_block))
            has_tenant_predicate = bool(alias_name) and alias_name in scoped_aliases
            if not has_tenant_in_props and not has_tenant_predicate:
                errors.append(f"{label}({alias_name or '?'})")

    return errors


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
        if context.is_bypass:
            return
        if not context.tenant_id and not context.allow_system_query:
            raise TenantQueryValidationError("Tenant context is required for Cypher execution")

        if _MATCH_PATTERN.search(query):
            structural_errors = _structural_tenant_scope_errors(query)
            if structural_errors and not context.allow_system_query:
                details = ", ".join(structural_errors)
                raise TenantQueryValidationError(
                    f"Denied Cypher query due to missing tenant scoping in MATCH path: {details}"
                )

            clause_tokens = [m.group(1).upper() for m in _CLAUSE_PATTERN.finditer(query)]
            ambiguous = (
                clause_tokens.count("MATCH") + clause_tokens.count("OPTIONAL MATCH") > 1
                or any(token.startswith("UNION") for token in clause_tokens)
                or bool(re.search(r"(?is)\bCALL\s*\{", query))
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
