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
