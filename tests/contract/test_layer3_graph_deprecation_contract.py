from value_fabric.layer3.api.models import (
    GraphEdge,
    GraphNode,
    get_deprecated_field_usage_counters,
)


def test_graph_node_contract_includes_legacy_and_canonical_fields() -> None:
    node = GraphNode(id="n1", name="Node", entity_type="Capability", confidence_score=0.9)
    payload = node.model_dump()

    assert payload["label"] == "Node"
    assert payload["type"] == "Capability"
    assert payload["confidence"] == 0.9

    assert payload["name"] == "Node"
    assert payload["entity_type"] == "Capability"
    assert payload["confidence_score"] == 0.9


def test_graph_edge_contract_includes_legacy_and_canonical_fields() -> None:
    edge = GraphEdge(source="n1", target="n2", type="RELATES_TO")
    payload = edge.model_dump()

    assert payload["type"] == "RELATES_TO"
    assert payload["relationship_type"] == "RELATES_TO"


def test_deprecated_field_usage_counters_increment_for_request_and_response() -> None:
    before = get_deprecated_field_usage_counters()

    GraphNode.model_validate({"id": "n2", "label": "Legacy", "type": "Capability", "confidence": 0.7})
    GraphEdge.model_validate({"source": "n2", "target": "n3", "type": "DEPENDS_ON"})
    GraphNode(id="n3", label="New", type="Outcome").model_dump()
    GraphEdge(source="n3", target="n4", type="ENABLES").model_dump()

    after = get_deprecated_field_usage_counters()
    assert after["graph_node_request_legacy_fields"] >= before["graph_node_request_legacy_fields"] + 1
    assert after["graph_edge_request_legacy_fields"] >= before["graph_edge_request_legacy_fields"] + 1
    assert after["graph_node_response_legacy_fields"] >= before["graph_node_response_legacy_fields"] + 1
    assert after["graph_edge_response_legacy_fields"] >= before["graph_edge_response_legacy_fields"] + 1


def test_layer3_contract_fixtures_prefer_canonical_fields() -> None:
    """Regression guard: tests that represent consumers should not drift back to legacy aliases."""
    sample = GraphNode(id="n4", name="Canonical", entity_type="Capability", confidence_score=0.8).model_dump()
    assert sample["name"] == "Canonical"
    assert sample["entity_type"] == "Capability"
    assert sample["confidence_score"] == 0.8
