import pytest
from unittest.mock import AsyncMock

from value_fabric.layer3_knowledge.src.api import app_monolith


@pytest.mark.asyncio
async def test_monolith_entity_handlers_delegate_to_route_modules(monkeypatch):
    monkeypatch.setattr(app_monolith.entity_compat, "get_entity_context_impl", AsyncMock(return_value={"ok": 1}))
    monkeypatch.setattr(app_monolith.entity_compat, "traverse_value_tree_impl", AsyncMock(return_value={"ok": 2}))
    monkeypatch.setattr(app_monolith.entity_compat, "list_entities_impl", AsyncMock(return_value={"ok": 3}))
    monkeypatch.setattr(app_monolith.entity_compat, "query_entities_impl", AsyncMock(return_value={"ok": 4}))

    graph_rag = object()
    neo4j = object()

    await app_monolith.get_entity_context("e1", graph_rag=graph_rag)
    app_monolith.entity_compat.get_entity_context_impl.assert_awaited_once()

    await app_monolith.traverse_value_tree(request=object(), graph_rag=graph_rag)
    app_monolith.entity_compat.traverse_value_tree_impl.assert_awaited_once()

    await app_monolith.list_entities(request=object(), _ctx=object(), neo4j_driver=neo4j)
    app_monolith.entity_compat.list_entities_impl.assert_awaited_once()

    await app_monolith.query_entities(request=object(), fastapi_request=object(), _ctx=object(), neo4j_driver=neo4j)
    app_monolith.entity_compat.query_entities_impl.assert_awaited_once()
