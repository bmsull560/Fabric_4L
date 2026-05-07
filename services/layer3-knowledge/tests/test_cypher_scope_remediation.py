"""Regression tests for Layer 3 Cypher tenant-scope hardening."""

from __future__ import annotations

import pytest

from value_fabric.layer3_knowledge.src.db.tenant_queries import get_entity_context
from value_fabric.layer3_knowledge.src.retrieval.graph_rag import GraphRAGEngine


class _NoopSession:
    async def run(self, query, params):
        class _Result:
            async def single(self):
                return None

        self.query = query
        self.params = params
        return _Result()


@pytest.mark.asyncio
async def test_tenant_queries_reject_malicious_relationship_type() -> None:
    session = _NoopSession()
    with pytest.raises(ValueError, match="Invalid relationship type"):
        await get_entity_context(
            session,
            entity_id="entity-1",
            tenant_id="tenant-a",
            relationship_types=["enables']) MATCH (x) DETACH DELETE x //"],
        )


@pytest.mark.asyncio
async def test_tenant_queries_parameterize_relationship_filter() -> None:
    session = _NoopSession()
    await get_entity_context(
        session,
        entity_id="entity-1",
        tenant_id="tenant-a",
        relationship_types=["enables"],
    )

    assert "type(r) IN $relationship_types" in session.query
    assert session.params["relationship_types"] == ["enables"]


def test_graphrag_rejects_malicious_relationship_type() -> None:
    with pytest.raises(ValueError, match="Invalid relationship type"):
        from value_fabric.layer3_knowledge.src.retrieval.graph_rag import _validate_relationship_types

        _validate_relationship_types(["enables']) MATCH (x) RETURN x //"])


def test_graphrag_rejects_invalid_entity_type() -> None:
    with pytest.raises(ValueError, match="Invalid entity_type"):
        from value_fabric.layer3_knowledge.src.retrieval.graph_rag import _validate_entity_type

        _validate_entity_type("Entity`) MATCH (x) RETURN x //")


def test_graphrag_rejects_unbounded_hops() -> None:
    with pytest.raises(ValueError, match="hops must"):
        from value_fabric.layer3_knowledge.src.retrieval.graph_rag import _validate_hops

        _validate_hops(99)


def test_graphrag_engine_instantiates_for_static_contract() -> None:
    assert GraphRAGEngine(driver=object())._driver is not None
