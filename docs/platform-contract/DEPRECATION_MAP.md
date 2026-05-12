# Fabric 4L Platform Contract - Deprecation Map

> Forbidden in new code. Migration deadlines are enforced by CI warnings that escalate to errors.

| Deprecated Pattern | Canonical Replacement | Migration Deadline | Notes |
|---|---|---|---|
| request.state.context | request.state.governance_context | 2026-05-15 | Layer 3 still uses old name |
| TenantContext (L4) | shared.identity.RequestContext | 2026-05-15 | services/layer4-agents/src/tenant/context.py |
| get_db() | get_db_from_context() | 2026-06-01 | Health checks excepted |
| get_db_with_tenant() | get_db_from_context() | 2026-06-01 | Header-based session creation |
| db_session() context manager | db_session_for_context() | 2026-06-01 | Background tasks |
| get_tiered_db_session() | get_db_from_context() | 2026-06-15 | Tier routing not yet implemented |
| get_db_with_optional_tenant() | get_db_from_context() + require_super_admin() | 2026-06-15 | Admin routes only |
| Layer 3 AuthenticationMiddleware | shared.identity.GovernanceMiddleware | 2026-05-15 | Remove duplicate middleware |
| Raw dict agent returns | AgentResultEnvelope | 2026-06-30 | Gradual migration |
| ToolRegistry.execute() direct call | ToolGateway.execute() | 2026-07-15 | Agents must use ctx['tool_gateway'] |
| GraphRAGEngine.query() direct call | MemoryGateway.query() | 2026-07-15 | Agents must use ctx['memory_gateway'] |
| datetime.utcnow() | datetime.now(timezone.utc) | 2026-06-01 | Deprecated in Python 3.12 |
| asyncio.get_event_loop().time() | asyncio.get_running_loop().time() | 2026-06-01 | Deprecated in Python 3.10 |
| useWorkflowStore + usePilotStore | useValuePilotStore (merged) | 2026-05-30 | Consolidate to one 7-step store |
| window.location.href | useLocation from wouter | 2026-05-15 | Immediate |
| React Context for server state | TanStack Query hooks | 2026-06-15 | Billing/Auth contexts excepted |
| `{"detail": ...}` error-only HTTP payloads | Canonical error envelope: `{"message","code","trace_id"}` | 2026-06-15 | Layer 1 keeps temporary `error=authentication_required` compatibility field for legacy clients |

## Layer 3 API Alias Deprecation Governance (Contract Council Tracked)

| Alias Field | Canonical Field | Contract Location | Target Removal Date | Owner | Migration Status | Contract Council Approval |
|---|---|---|---|---|---|---|
| `GraphNode.label` | `GraphNode.name` | `contracts/openapi/layer3-knowledge.json#/components/schemas/GraphNode` | 2026-07-01 | Layer 3 Knowledge Team | In progress — compatibility still active, consumers migrating | Pending |
| `GraphNode.type` | `GraphNode.entity_type` | `contracts/openapi/layer3-knowledge.json#/components/schemas/GraphNode` | 2026-07-01 | Layer 3 Knowledge Team | In progress — compatibility still active, consumers migrating | Pending |
| `GraphNode.confidence` | `GraphNode.confidence_score` | `contracts/openapi/layer3-knowledge.json#/components/schemas/GraphNode` | 2026-07-01 | Layer 3 Knowledge Team | In progress — compatibility still active, consumers migrating | Pending |
| `GraphEdge.relationship_type` | `GraphEdge.type` | `contracts/openapi/layer3-knowledge.json#/components/schemas/GraphEdge` | 2026-07-01 | Layer 3 Knowledge Team | In progress — compatibility still active, consumers migrating | Pending |
| `FormulaMetadata.formula_id` | `FormulaMetadata.id` | `contracts/openapi/layer3-knowledge.json#/components/schemas/FormulaMetadata` | TBD (compatibility alias, not yet date-bound) | Layer 3 Knowledge Team + UI Platform | Not started — no date set in OpenAPI yet | Pending |

**Removal rule:** aliases above must not be deleted before (1) the listed target date has passed, and (2) Contract Council approval is explicitly recorded in this table.

## Recommendation Guardrail: Layer 3 + Layer 4 Agent Consolidation

Use this wording by default in architecture recommendations:

- **"Evaluate consolidation feasibility"**

Do **not** recommend direct consolidation of Layer 3 and Layer 4 agent implementations unless analysis confirms both are true:

1. **Platform contract compliance:** tenant context propagation, DB/session boundaries, and output envelope/tool boundary rules remain compliant after the change.
2. **Low-risk dependency impact:** Layer 3 agent responsibilities (graph traversal/projection, ROI calculation, whitespace analysis, provenance, narrative synthesis, and scenario modeling) can be consolidated without introducing breaking API/runtime coupling risk.

## Migration Guide

### 1. TENANT_CONTEXT -> governance_context

Find all instances:

```bash
grep -r "request.state.context" services/ packages/shared/src/value_fabric/shared/
```

Replace with `request.state.governance_context`.

### 2. get_db() -> get_db_from_context()

Find all instances:

```bash
grep -r "Depends\s*(\s*get_db\b" services/ packages/shared/src/value_fabric/shared/
grep -r "with\s+db_session\s*(" services/ packages/shared/src/value_fabric/shared/
grep -r "get_db_with_tenant" services/ packages/shared/src/value_fabric/shared/
grep -r "get_db_with_optional_tenant" services/ packages/shared/src/value_fabric/shared/
grep -r "get_tiered_db_session" services/ packages/shared/src/value_fabric/shared/
```

Replace endpoints to use `Depends(get_db_from_context)`.
Replace background tasks to use `db_session_for_context()`.

### 3. useWorkflowStore + usePilotStore -> useValuePilotStore

Merge functionality into a single store in `client/src/stores/valuePilotStore.ts`.
Deprecate the old stores.

### 4. ToolRegistry.execute() -> ToolGateway.execute() (GATE Phase 2)

Find all instances:

```bash
grep -rn "registry.execute\|tool_registry.execute" services/layer4-agents/
```

Replace with `ctx['tool_gateway'].execute(tool_name, input_data)` inside agent `execute()` methods.
The `ToolGateway` is automatically injected by `BaseAgent.run()` when `tool_registry` and `abom` are present in context.

### 5. GraphRAGEngine.query() -> MemoryGateway.query() (GATE Phase 3)

Find all instances:

```bash
grep -rn "graph_rag.*query\|retrieval_engine.*query" services/layer4-agents/
```

Replace with `ctx['memory_gateway'].query(query_text)` inside agent `execute()` methods.
The `MemoryGateway` must be created and injected into context by the orchestration layer.
