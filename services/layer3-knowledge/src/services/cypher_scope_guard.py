"""Cypher tenant-scope query guard helpers for Layer 3 services."""

from __future__ import annotations

import re

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


def _tenant_scoped_aliases(query: str) -> set[str]:
    return {match.group("alias") for match in _TENANT_PREDICATE_PATTERN.finditer(query)}


def validate_tenant_scoped_cypher(
    query: str,
    *,
    tenant_owned_labels: set[str],
    query_name: str = "query",
) -> None:
    """Reject MATCH templates that read tenant-owned labels without tenant_id scoping.

    The guard is intentionally static and conservative. It accepts tenant scope
    either inline in the node pattern, for example ``(p:Product {tenant_id:
    $tenant_id})``, or as a predicate elsewhere in the same query template, for
    example ``WHERE p.tenant_id = $tenant_id``.
    """

    scoped_aliases = _tenant_scoped_aliases(query)
    violations: list[str] = []

    for match_clause in _MATCH_CLAUSE_PATTERN.findall(query):
        for alias, label, props in _NODE_PATTERN.findall(match_clause):
            if label not in tenant_owned_labels:
                continue

            prop_block = props or ""
            alias_name = alias.strip() if alias else ""
            has_tenant_in_props = bool(re.search(r"(?i)\btenant_id\b", prop_block))
            has_tenant_predicate = bool(alias_name) and alias_name in scoped_aliases

            if not has_tenant_in_props and not has_tenant_predicate:
                violations.append(f"{label}({alias_name or '?'})")

    if violations:
        raise ValueError(
            f"Tenant scope guard violation in {query_name}: missing tenant_id filter for "
            + ", ".join(violations)
        )
