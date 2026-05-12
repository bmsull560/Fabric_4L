from __future__ import annotations

import re
from pathlib import Path

import pytest

from value_fabric.layer3.services.cypher_scope_guard import validate_tenant_scoped_cypher


_QUERY_BLOCK = re.compile(r'(?s)(?:query|count_query|list_query)\s*=\s*f?"""(.*?)"""')
_TENANT_OWNED = {
    "Product",
    "Feature",
    "Capability",
    "PainSignal",
    "Competitor",
    "Battlecard",
}


@pytest.mark.parametrize(
    "query",
    [
        "MATCH (p:Product {tenant_id: $tenant_id}) RETURN p",
        "MATCH (p:Product) WHERE p.tenant_id = $tenant_id RETURN p",
        "OPTIONAL MATCH (c:Capability) WHERE c.tenant_id = $tenant_id OR c.tenant_id IS NULL RETURN c",
        "MATCH (n:Industry) RETURN n",
    ],
)
def test_validate_tenant_scoped_cypher_accepts_scoped_or_unowned_queries(query: str) -> None:
    validate_tenant_scoped_cypher(query, tenant_owned_labels=_TENANT_OWNED)


@pytest.mark.parametrize(
    "query",
    [
        "MATCH (p:Product) RETURN p",
        "MATCH (:Product) RETURN count(*)",
        "MATCH (p:Product {id: $product_id}) RETURN p",
        "MATCH (p:Product {tenant_id: $tenant_id}) OPTIONAL MATCH (f:Feature) RETURN f",
    ],
)
def test_validate_tenant_scoped_cypher_rejects_unscoped_tenant_owned_reads(query: str) -> None:
    with pytest.raises(ValueError, match="missing tenant_id filter"):
        validate_tenant_scoped_cypher(query, tenant_owned_labels=_TENANT_OWNED)


@pytest.mark.parametrize(
    "relative_path",
    [
        "value_fabric/layer3/services/product_service.py",
        "value_fabric/layer3/services/competitive_intel_service.py",
        "services/layer3-knowledge/src/services/product_service.py",
        "services/layer3-knowledge/src/services/competitive_intel_service.py",
    ],
)
def test_query_templates_are_tenant_scoped(relative_path: str) -> None:
    content = Path(relative_path).read_text(encoding="utf-8")
    queries = [query for query in _QUERY_BLOCK.findall(content) if "MATCH" in query.upper()]

    assert queries, f"No query templates found in {relative_path}"
    for idx, query in enumerate(queries):
        validate_tenant_scoped_cypher(
            query,
            tenant_owned_labels=_TENANT_OWNED,
            query_name=f"{relative_path}#{idx}",
        )
