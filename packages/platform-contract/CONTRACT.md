# Fabric 4L Platform Contract v1.0

> **Source of truth for all cross-layer implementation patterns in Value Fabric.**
> This document is enforced by CI. Violations block merge.

---

## 1. Purpose

Fabric 4L has six layers, a shared services package, and a frontend. Without a single canonical contract, every feature addition re-opens debates about tenant context, DB sessions, middleware, tools, agent outputs, and UI state.

This contract ends those debates. **One pattern per concern. Enforced in CI.**

---

## 2. Principles

| # | Principle | Rationale |
|---|-----------|-----------|
| P1 | **Context is explicit, not ambient** | Typed parameters. No magic globals except the single ContextVar set by middleware. |
| P2 | **Fail-safe defaults** | Missing tenant context -> reject. Missing auth -> reject. Unknown isolation tier -> reject. |
| P3 | **One dependency, one lifetime** | DB session created once per request, committed once, rolled back on exception. No manual commit/rollback in route handlers. |
| P4 | **Schema-first at boundaries** | Every tool, agent output, and API response has a declared schema. No raw dict crossing layer boundaries. |
| P5 | **Traceability is mandatory** | Every request carries trace_id. Every agent run carries workflow_id. Every DB session carries audit_event_id. |
| P6 | **Frontend: route-driven, store-typed** | URL is primary navigation. Zustand stores are typed. Server state lives in React Query. |

---

## 3. Canonical Patterns

### 3.1 Tenant Context Propagation

**Canonical:** shared.identity.RequestContext + GovernanceMiddleware + _current_context ContextVar.

`python
# How context is SET (once per request)
# In shared/identity/middleware.py — GovernanceMiddleware
async def dispatch(self, request: Request, call_next):
    context = await self._authenticate(request)
    request.state.governance_context = context   # for sync extraction
    set_current_context(context)                  # ContextVar for async propagation
    response = await call_next(request)
    response.headers['X-Request-ID'] = context.request_id
    return response

# How context is READ in endpoints
from shared.identity.dependencies import get_request_context
from shared.identity.context import RequestContext

@router.get('/items')
async def list_items(ctx: RequestContext = Depends(get_request_context)):
    ...

# How context is READ in non-endpoint code
from shared.identity.context import get_current_context

def some_helper():
    ctx = get_current_context()
    if ctx is None:
        raise RuntimeError('No request context')
    return ctx.tenant_id
`

**Rules:**
- GovernanceMiddleware is the **outermost** middleware in every layer (after CORS).
- 
equest.state.governance_context is the canonical attribute name. No 
equest.state.context, no 
equest.state.tenant.
- Service-to-service calls propagate tenant via X-Tenant-ID header AND forward the X-Request-ID header.
- Layer 1 sync code uses _thread_local (set by middleware_sync.py), NOT a separate TenantContext class.

---

### 3.2 DB Session and Isolation Pattern

**Canonical:** Async SQLAlchemy + get_db_from_context() + PostgreSQL RLS via SET LOCAL app.tenant_id.

`python
# FastAPI endpoint (canonical)
from value_fabric.layer4_agents.database import get_db_from_context
from sqlalchemy.ext.asyncio import AsyncSession

@router.get('/items')
async def list_items(
    db: AsyncSession = Depends(get_db_from_context),
):
    # Session is opened, tenant is set, transaction is active.
    # DO NOT call db.commit() or db.rollback() here.
    result = await db.execute(select(Item))
    return result.scalars().all()

# Non-FastAPI usage (background task, service method)
from value_fabric.layer4_agents.database import db_session_for_context
from shared.identity.context import RequestContext

async def background_task(ctx: RequestContext):
    async with db_session_for_context(ctx) as db:
        ...
`

**Rules:**
- get_db_from_context() is the ONLY FastAPI dependency for DB sessions in new code.
- get_db(), get_db_with_tenant(), db_session(), get_tiered_db_session(), get_db_with_optional_tenant() are **DEPRECATED** (see section 6).
- Session lifecycle is managed by the dependency/context manager. Route handlers MUST NOT call commit() or 
ollback().
- RLS is set via SET LOCAL app.tenant_id = :tenant_id on every session.
- Super-admin bypass requires get_db_with_optional_tenant() ONLY in admin routes protected by 
equire_super_admin().

---

### 3.3 Middleware and Auth Flow

**Canonical:** GovernanceMiddleware (outermost) -> SecurityMiddleware -> RequestIDMiddleware -> route handlers.

`python
# How every FastAPI app should register middleware
app.add_middleware(GovernanceMiddleware,
    api_key_resolver=lookup_api_key_by_hash,
    jwt_secret=settings.jwt_secret,
    tenant_settings_lookup=get_tenant_settings,
    tenant_status_lookup=get_tenant_status,
)
app.add_middleware(SecurityMiddleware)
app.add_middleware(RequestIDMiddleware)

# Auth enforcement in routes
from shared.identity.dependencies import require_authenticated, require_tenant_admin

@router.post('/items')
async def create_item(
    ctx: RequestContext = Depends(require_authenticated),
    db: AsyncSession = Depends(get_db_from_context),
):
    ...
`

**Rules:**
- GovernanceMiddleware resolves identity. Depends(require_authenticated) enforces it. Public endpoints simply omit the dependency.
- Manual parsing of Authorization: Bearer ... is allowed ONLY inside GovernanceMiddleware. Route handlers use RequestContext.
- Rate limiting is configured via GovernanceMiddleware with Redis in production, in-memory fallback for dev.
- No layer should have its own auth middleware. Layer 3 legacy AuthenticationMiddleware is deprecated.

---

### 3.4 Tool Invocation Boundary

**Canonical:** BaseTool -> Pydantic input/output schema -> ToolRegistry -> JSON Schema manifest.

`python
# Tool implementation
from value_fabric.layer4_agents.tools.registry import BaseTool
from value_fabric.layer4_agents.models.tool_schemas import CalculateROIInput, CalculateROIOutput

class CalculateROITool(BaseTool):
    name = 'calculate_roi'
    input_schema = CalculateROIInput
    output_schema = CalculateROIOutput

    async def execute(self, validated_input: CalculateROIInput) -> CalculateROIOutput:
        ...

# Manifest (contracts/tool-manifests/calculate_roi.json)
{
  'name': 'calculate_roi',
  'description': 'Calculate ROI for a value driver',
  'parameters': { ... },
  'returns': { ... }
}
`

**Rules:**
- Every tool extends BaseTool and declares input_schema and output_schema as Pydantic models.
- Tool output crossing an API boundary MUST be .model_dump() — no raw dict construction in tool execute methods.
- JSON Schema manifests in contracts/tool-manifests/ are authoritative. Code schemas must stay in sync.
- Tools are registered in alue-fabric/layer4-agents/src/tools/__init__.py.
- No inline tool definitions inside workflow nodes. Nodes reference tools by name.

---

### 3.5 Agent Output Shape and Traceability

**Canonical:** All agent outputs conform to AgentResultEnvelope.

`python
from pydantic import BaseModel
from datetime import datetime
from typing import Any, Literal

class AgentResultEnvelope(BaseModel):
    status: Literal['success', 'error', 'paused']
    data: dict[str, Any] | None
    error: AgentErrorDetail | None
    metadata: AgentResultMetadata

class AgentResultMetadata(BaseModel):
    trace_id: str
    workflow_id: str
    tenant_id: str
    agent_type: str
    started_at: datetime
    completed_at: datetime
    duration_ms: int
    node_path: list[str]

class AgentErrorDetail(BaseModel):
    code: str
    message: str
    node_id: str | None
    retryable: bool
    details: dict[str, Any] | None
`

**Workflow state (LangGraph) is an INTERNAL concern.** The orchestrator converts BaseAgentState -> AgentResultEnvelope before returning to the client.

**Rules:**
- API responses NEVER return raw BaseAgentState. Always wrap in AgentResultEnvelope.
- 	race_id is sourced from OpenTelemetry span if available, else X-Request-ID, else generated UUID.
- workflow_id is generated at workflow start and persisted in checkpoints.
- Every agent run emits audit event with 	race_id, workflow_id, 	enant_id.
- Prometheus metrics include labels: 	enant_id, workflow_type, gent_type, status.

---

### 3.6 UI State Progression and Route Model

**Canonical:** wouter + Zustand (typed) + TanStack Query + useReducer for complex local state.

`	ypescript
// Routing — App.tsx — wouter <Route> components only
<Route path='/intelligence/:accountId/signals'>
  <AuthenticatedRoute>
    <AccountContextSync />
    <SignalsTab />
  </AuthenticatedRoute>
</Route>

// Navigation
import { useLocation } from 'wouter';
const [, navigate] = useLocation();
navigate(/intelligence//signals);

// Global UI state (Zustand)
import { create } from 'zustand';

interface AccountContextState {
  selectedAccountId: string | null;
  setSelectedAccountId: (id: string) => void;
}

export const useAccountContextStore = create<AccountContextState>()(
  persist(
    (set) => ({
      selectedAccountId: null,
      setSelectedAccountId: (id) => set({ selectedAccountId: id }),
    }),
    { name: 'fabric-account-context', partialize: (s) => ({ selectedAccountId: s.selectedAccountId }) }
  )
);

// Server state (TanStack Query)
import { useQuery } from '@tanstack/react-query';

function useSignals(accountId: string) {
  return useQuery({
    queryKey: ['signals', accountId],
    queryFn: () => api.getSignals(accountId),
  });
}

// Complex local state (useReducer)
// Use only when component state has >3 interdependent fields
type Action = { type: 'SELECT_COMPANY'; company: Company } | { type: 'SET_MODE'; mode: Mode };
function reducer(state: State, action: Action): State { ... }
`

**Rules:**
- wouter is the ONLY routing library. No React Router, no TanStack Router.
- Navigation is via useLocation from wouter. No window.location.href assignment.
- Zustand stores are typed with interfaces. No ny in store definitions.
- Server state lives in React Query hooks under client/src/hooks/. No Zustand for server state caching.
- React Context is used ONLY for cross-cutting concerns provided once at root: Auth, Billing.
- ONE workflow store per workflow type. The useWorkflowStore / usePilotStore split is deprecated (see section 6).
- Route guards check tier via canAccessRouteWithReason() and redirect or render <NotFound> — no silent failures.

---

### 3.7 GATE Audit Ledger Commit

**Canonical:** shared.audit.ledger.LedgerCommitHandler + shared.crypto.canonical.canonical_hash()

Every auditable action produces a hash-chained audit event. Events are partitioned by `chain_id` (typically `agent_type:tenant_id`). Each event's `prev_hash` references the preceding event in the same chain, forming a tamper-evident ledger.

```python
from shared.audit.emitter import emit_audit_event

# Emit an audit event with chain linkage
await emit_audit_event(
    event_type="TOOL_INVOCATION",
    agent_id="context-extraction-abc12345",
    details={"tool_name": "query_graph", "input_hash": "sha256:...", "output_hash": "sha256:..."},
    chain_id="context_extraction:tenant-1",
)
```

**Rules:**
- All audit events MUST include `chain_id`. Events without `chain_id` are rejected by the ledger handler.
- `canonical_hash()` from `shared.crypto.canonical` is the ONLY approved hashing function for audit payloads. No inline `hashlib.sha256(json.dumps(...))` patterns.
- The ledger handler is append-only. There is no API to modify or delete committed events.
- Chain integrity is verified by CI via `tests/contracts/gate/test_phase1_contracts.py`.

---

### 3.8 GATE Tool Gateway

**Canonical:** shared.governance.tool_gateway.ToolGateway

All tool invocations from agents MUST route through the ToolGateway. The gateway enforces a 6-step pipeline: ABOM allowlist check, OPA policy evaluation, invariant evaluation (call limits, budget caps), pre-invocation audit, tool execution, and post-invocation audit.

```python
# Inside any agent execute() method
async def execute(self, task, context):
    gateway = context.get("tool_gateway")
    if gateway:
        result = await gateway.execute("query_graph", {"query": "..."})
    else:
        # Fallback for testing — direct registry call
        result = await self.registry.execute("query_graph", {"query": "..."})
```

**Rules:**
- Direct `ToolRegistry.execute()` calls from agent code are FORBIDDEN in production. All calls route through `ctx['tool_gateway']`.
- API routes that invoke tools (`POST /tools/invoke`, `POST /tools/export-document`) MUST also route through ToolGateway when a GATE context is available.
- The gateway logs both pre-invocation and post-invocation audit events with input/output hashes.
- If OPA is unreachable, `high_privilege` tier agents are denied by default. Standard and elevated agents fall back to ABOM-only enforcement.

---

### 3.9 Agent Bill of Materials (ABOM)

**Canonical:** shared.governance.abom.AgentBillOfMaterials + JSON manifests in `value-fabric/layer4-agents/manifests/`

**Every deployed agent MUST have a matching ABOM manifest.** The manifest declares the agent's identity, privilege tier, allowed tools, invariant constraints (call limits, budget caps), and data scope.

```json
{
  "schema_version": "1.0.0",
  "agent_id": "context_extraction-abc12345",
  "agent_type": "context_extraction",
  "display_name": "ContextExtractionAgent",
  "privilege_tier": "standard",
  "allowed_tools": ["query_graph", "semantic_search", "get_entity", "..." ],
  "invariants": {
    "max_calls_per_run": 50,
    "budget_limit_usd": 3.00,
    "requires_human_approval": []
  }
}
```

**Rules:**
- Manifests are validated against `packages/platform-contract/schemas/gate/abom.schema.json` in CI.
- `agent_id` format is `<agent_type>-<8-char-prefix>`. No UUIDs.
- `privilege_tier` is one of: `standard`, `elevated`, `high_privilege`.
- Adding a tool to an agent requires updating the manifest AND the Rego policy bundle.
- The canonical 9-agent roster is: ContextExtractionAgent, ValueModelAgent, IntegrityAgent, NarrativeAgent, CompetitiveIntelAgent, SignalDetectionAgent, CRMSyncAgent, ConversationAgent, OrchestrationController.

---

### 3.10 GATE Memory Gateway

**Canonical:** shared.governance.memory_gateway.MemoryGateway

All knowledge retrieval operations from agents MUST route through the MemoryGateway. The gateway wraps graph and vector retrieval with provenance tracking: every retrieved chunk is hashed, its source lineage is recorded, and a `MEMORY_ACCESS` audit event is emitted.

```python
# Inside an agent that needs knowledge retrieval
async def execute(self, task, context):
    memory_gw = context.get("memory_gateway")
    if memory_gw:
        results = await memory_gw.retrieve(
            query="customer pain points",
            retrieval_type="semantic",
            scope={"account_id": "acct-123"},
        )
        # results include provenance metadata: content_hash, source_id, retrieval_timestamp
```

**Rules:**
- Direct calls to `GraphRAGRetriever` or vector search from agent code are FORBIDDEN in production. Route through MemoryGateway.
- Every retrieval result includes `content_hash` (SHA-256 of canonical content) and `source_id` for lineage tracking.
- Retrieval audit events are emitted with `chain_id="memory:{tenant_id}"` for ledger partitioning.

---

### 3.11 GATE Replay Recorder

**Canonical:** shared.governance.replay.ReplayRecorder

Every agent run produces a deterministic replay snapshot. The snapshot captures the sequence of tool calls, memory accesses, and decision points, enabling post-hoc audit and debugging.

```python
# BaseAgent.run() automatically injects the recorder
async def run(self, task, context):
    recorder = context.get("replay_recorder")
    # ... agent execution ...
    if recorder:
        await recorder.commit()  # Emits REPLAY_SNAPSHOT audit event
```

**Rules:**
- `ReplayRecorder.commit()` MUST be `await`-ed, not fire-and-forget via `asyncio.create_task()`. Silent loss on shutdown is unacceptable for audit trails.
- Replay snapshots are hashed with `canonical_hash()` for integrity verification.
- The snapshot includes: `agent_id`, `run_id`, `started_at`, `completed_at`, `steps` (ordered list of tool/memory operations), and `snapshot_hash`.
- Snapshots are emitted as `REPLAY_SNAPSHOT` audit events with `chain_id="replay:{agent_id}"`.

---

## 4. Reference Implementation

The canonical implementations live in packages/platform-contract/src/:

  src/python/canonical/
    context.py          # RequestContext, GovernanceMiddleware contract
    database.py         # get_db_from_context(), db_session_for_context()
    agent_output.py     # AgentResultEnvelope, AgentResultMetadata
    tool_boundary.py    # BaseTool, ToolRegistry contract
  src/typescript/
    agent-result.ts     # AgentResultEnvelope types
    stores.ts           # Zustand store patterns
    routing.ts          # Route model types

These files are not copied into layers. They are the contract spec. Each layer imports from its own path but MUST conform to the signatures and behaviors defined here.

---

## 5. Lint and CI Enforcement Strategy

### 5.1 Python Enforcement (scripts/ci/platform_contract_lint.py)

Scans value-fabric/ and shared/ for violations.

### 5.2 TypeScript/Frontend Enforcement

ESLint plugin rules (existing eslint-plugin-fabric-contracts) plus new rules.

### 5.3 CI Gate

.github/workflows/platform-contract-gate.yml runs on every PR.

---

## 6. Deprecation Map

These patterns exist in the codebase but are forbidden in new code. Migration deadlines are enforced by CI warnings that escalate to errors.

| Deprecated Pattern | Canonical Replacement | Migration Deadline | Notes |
|-------------------|----------------------|-------------------|-------|
| request.state.context | request.state.governance_context | 2026-05-15 | Layer 3 still uses old name |
| TenantContext (L4) | shared.identity.RequestContext | 2026-05-15 | value-fabric/layer4-agents/src/tenant/context.py |
| get_db() | get_db_from_context() | 2026-06-01 | Health checks excepted |
| get_db_with_tenant() | get_db_from_context() | 2026-06-01 | Header-based session creation |
| db_session() context manager | db_session_for_context() | 2026-06-01 | Background tasks |
| get_tiered_db_session() | get_db_from_context() | 2026-06-15 | Tier routing not yet implemented |
| get_db_with_optional_tenant() | get_db_from_context() + require_super_admin() | 2026-06-15 | Admin routes only |
| Layer 3 AuthenticationMiddleware | shared.identity.GovernanceMiddleware | 2026-05-15 | Remove duplicate middleware |
| Raw dict agent returns | AgentResultEnvelope | 2026-06-30 | Gradual migration |
| useWorkflowStore + usePilotStore | useValuePilotStore (merged) | 2026-05-30 | Consolidate to one 7-step store |
| window.location.href | useLocation from wouter | 2026-05-15 | Immediate |
| React Context for server state | TanStack Query hooks | 2026-06-15 | Billing/Auth contexts excepted |

---

## 7. Change Process

This contract is versioned. Changes require:

1. PR that updates packages/platform-contract/CONTRACT.md
2. Update reference implementations in src/python/canonical/ and src/typescript/
3. Update enforcement scripts
4. Update deprecation map with migration deadline
5. Approval from at least one maintainer outside the PR author
6. make verify passes

---

## 8. Quick Reference

### One-liners for developers


---

## 7. Adding a New Canonical Contract (Quick Guide)

When you add a new canonical contract, treat it as **code + enforcement + docs** in one change set.

1. Add or update canonical source files under:
   - `packages/platform-contract/src/python/canonical/` for Python signatures/patterns.
   - `packages/platform-contract/src/typescript/` for frontend/public TS contract types.
2. Add invariant and negative tests adjacent to canonical sources:
   - Python: `packages/platform-contract/src/python/canonical/test_contract_invariants.py`.
   - TypeScript compile-time assertions: `packages/platform-contract/src/typescript/contract-tests.ts`.
3. Ensure negative tests check error messaging (or static type errors) so enforcement failures are actionable.
4. Wire the checks into contract CI stages (Make + workflow jobs), not only local scripts.
5. Run verification before PR:
   - `make contract-tests`
   - `make verify`
6. If the new contract deprecates an older pattern, update `docs/platform-contract/DEPRECATION_MAP.md` in the same PR.

**Definition of done:** if the canonical rule is violated, CI fails with a clear, contract-specific failure.
`python
# Get tenant context in an endpoint
ctx: RequestContext = Depends(get_request_context)

# Get DB session with RLS
db: AsyncSession = Depends(get_db_from_context)

# Get trace_id for logging
trace_id = ctx.request_id  # or from OTel span

# Build agent response
return AgentResultEnvelope(status='success', data=..., metadata=...)
`

`	ypescript
// Navigate
const [, navigate] = useLocation();
navigate('/home');

// Read global state
const accountId = useAccountContextStore((s) => s.selectedAccountId);

// Read server state
const { data } = useQuery({ queryKey: ['key'], queryFn: fetchFn });
`

---

## 7. Adding a New Canonical Contract (Quick Guide)

When you add a new canonical contract, treat it as **code + enforcement + docs** in one change set.

1. Add or update canonical source files under:
   - `packages/platform-contract/src/python/canonical/` for Python signatures/patterns.
   - `packages/platform-contract/src/typescript/` for frontend/public TS contract types.
2. Add invariant and negative tests adjacent to canonical sources:
   - Python: `packages/platform-contract/src/python/canonical/test_contract_invariants.py`.
   - TypeScript compile-time assertions: `packages/platform-contract/src/typescript/contract-tests.ts`.
3. Ensure negative tests check error messaging (or static type errors) so enforcement failures are actionable.
4. Wire the checks into contract CI stages (Make + workflow jobs), not only local scripts.
5. Run verification before PR:
   - `make contract-tests`
   - `make verify`
6. If the new contract deprecates an older pattern, update `docs/platform-contract/DEPRECATION_MAP.md` in the same PR.

**Definition of done:** if the canonical rule is violated, CI fails with a clear, contract-specific failure.
