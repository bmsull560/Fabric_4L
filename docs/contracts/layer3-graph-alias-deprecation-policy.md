# Layer 3 Graph Alias Deprecation Policy

## Scope

This policy tracks deprecations for Layer 3 graph response field aliases in the Layer 3 OpenAPI contract and generated frontend client.

Impacted alias pairs:
- `GraphNode.label` -> `GraphNode.name`
- `GraphNode.type` -> `GraphNode.entity_type`
- `GraphNode.confidence` -> `GraphNode.confidence_score`
- `GraphEdge.relationship_type` -> `GraphEdge.type`

## Versioned schedule

| Phase | API version window | Contract behavior |
|---|---|---|
| Current | `<= v2.3` | Responses emit canonical fields and deprecated aliases. |
| Warning | `v2.4` | Aliases remain available, explicitly deprecated, and usage should be monitored. |
| Removal | `>= v2.5` | Deprecated aliases are removed from serialized responses; canonical fields only. |

## Enforcement

- Runtime serializers in `value_fabric/layer3/api/models.py` and retrieval serializers in `services/layer3-knowledge/src/retrieval/graph_rag.py` must apply the same `v2.5` boundary behavior.
- OpenAPI descriptions in `contracts/openapi/layer3-knowledge.json` and generated TS client comments in `apps/web/src/api/generated/l3/index.ts` must document the same boundary.
- Contract tests covering before/after behavior are required:
  - `services/layer3-knowledge/tests/test_graph_alias_deprecation_policy.py`
  - `tests/contract/test_layer3_graph_deprecation_contract.py`

## Notes for consumers

Use only canonical fields in new clients:
- Nodes: `name`, `entity_type`, `confidence_score`
- Edges: `type`
