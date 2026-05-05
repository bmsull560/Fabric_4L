# L3 Knowledge Graph API Contract Audit

**Status:** Audit Complete  
**Date:** 2026-05-05  
**Owner:** L3 Team + Frontend Platform

---

## 1. Endpoint Inventory

### Canonical Graph Endpoints

| Method | Path | Operation ID | Purpose | Schema Risk |
|---|---|---|---|---|
| POST | `/v1/query/graph` | `graph_rag_query_v1_query_graph_post` | GraphRAG multi-hop query | **High** — untyped entities/relationships |
| POST | `/v1/query/graph/stream` | `graph_rag_query_stream_v1_query_graph_stream_post` | Streaming GraphRAG | Medium |
| GET | `/v1/entity/{entity_id}/context` | `get_entity_context_v1_entity__entity_id__context_get` | Neighborhood context | **High** — untyped center/neighbors/relationships |
| POST | `/v1/entity/traverse` | `traverse_value_tree_v1_entity_traverse_post` | Value tree traversal | Low |
| GET | `/v1/entities/{entity_id}` | `get_entity_detail_v1_entities__entity_id__get` | Entity detail | Low |
| GET | `/entities/{entity_id}/subgraph` | — | Subgraph (legacy path) | Medium |
| GET | `/v1/graph/subgraph` | — | Subgraph (canonical) | Low — typed nodes/edges |

### Legacy / Deprecated Endpoints

| Method | Path | Status | Sunset / Migration |
|---|---|---|---|
| POST | `/v1/graphrag` | Alias | Use `/v1/query/graph` |
| POST | `/v1/query` | Deprecated | Use `/v1/query/graph` (sunset: 2026-05-18) |
| GET | `/v1/search` | Deprecated | Use `/v1/entities` with filters |
| GET | `/v1/search/hybrid` | Deprecated | Use `/v1/entities` |
| GET/POST | `/v1/v1/entities*` | Bug / Legacy | Use `/v1/entities*` (duplicate `v1` prefix) |
| GET | `/graph` | Legacy | Use `/v1/graph/subgraph` |

---

## 2. Schema Drift Findings

### Critical (P0)

#### 2.1 `GraphRAGResponse.entities` and `.relationships` are untyped

**Current:**
```json
"entities": {
  "items": { "additionalProperties": true, "type": "object" },
  "type": "array"
}
```

**Impact:** Frontend cannot safely consume GraphRAG results. Any field rename or type change in the backend breaks the UI silently.

**Fix:** Change to `items: { "$ref": "#/components/schemas/GraphNode" }`.

#### 2.2 `EntityContextResponse.center`, `.neighbors`, `.relationships` are untyped

**Current:**
```json
"center": { "additionalProperties": true, "type": "object" }
```

**Impact:** Same as above — no contract enforcement at the API boundary.

**Fix:** Type as `GraphNode`, `GraphNode[]`, and `GraphEdge[]` respectively.

### High (P1)

#### 2.3 `GraphNode` embeds visualization fields

**Current fields:** `x`, `y`, `r` are part of the core graph DTO.

**Impact:**
- Couples backend schema to frontend layout algorithms.
- Backend-computed positions are often discarded because `calculateLayout()` runs client-side.
- Violates separation of concerns between data model and presentation.

**Fix:** Remove `x`, `y`, `r` from `GraphNode`. Create `GraphNodeWithLayout` for endpoints that intentionally return positions.

#### 2.4 Legacy field aliases in `GraphNode` and `GraphEdge`

`GraphNode` has three alias pairs:
- `label` ↔ `name`
- `type` ↔ `entity_type`
- `confidence` ↔ `confidence_score`

`GraphEdge` has:
- `type` ↔ `relationship_type`

**Impact:** Serialization bloat, confusion about canonical field names, deprecation warnings in logs.

**Fix:** Choose canonical names (`name`, `entity_type`, `confidence_score`, `relationship_type`) and remove aliases in a future breaking change.

### Medium (P2)

#### 2.5 `GraphRAGResponse.context_graph` is untyped

**Current:** `dict[str, Any]`

**Fix:** Define `ContextGraph` as `{ nodes: GraphNode[], edges: GraphEdge[] }`.

#### 2.6 Multiple subgraph endpoint paths

`/entities/{entity_id}/subgraph` and `/v1/graph/subgraph` both exist. May return different shapes.

**Fix:** Consolidate on `/v1/graph/subgraph`; deprecate the other.

---

## 3. Migration Notes

### Backend → OpenAPI

1. Update `GraphRAGResponse` to use `list[GraphNode]` and `list[GraphEdge]`.
2. Update `EntityContextResponse` to use typed `GraphNode`/`GraphEdge`.
3. Remove `x`, `y`, `r` from `GraphNode`; introduce `GraphNodeWithLayout`.
4. Export OpenAPI via `python scripts/export_openapi.py`.
5. Run `pnpm run generate:api` to regenerate frontend types.

### Frontend

1. Update Zod schemas in `features/graph/domain/graph.schemas.ts` to match cleaned DTOs.
2. Create DTO-to-domain mapper in `features/graph/domain/graph.mapper.ts`.
3. Move layout fields out of domain model into `features/graph/viewmodel/graph.viewmodel.ts`.
4. Update `GraphExplorer.tsx` to consume domain model, then map to view model before passing to `GraphVisualization`.

---

## 4. Ticket Mapping

| Finding | Ticket |
|---|---|
| Untyped entities/relationships in GraphRAGResponse | T5.2 |
| Untyped EntityContextResponse fields | T5.2 |
| Visualization fields in GraphNode | T5.2, T5.5 |
| Legacy field aliases | T5.2 (notes), future breaking change |
| Untyped context_graph | T5.2 |
| Need frontend validation schemas | T5.3 |
| Need DTO-to-domain mapper | T5.4 |
| Need visualization view model | T5.5 |
