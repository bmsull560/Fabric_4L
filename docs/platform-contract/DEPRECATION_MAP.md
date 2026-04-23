# Fabric 4L Platform Contract - Deprecation Map

> Forbidden in new code. Migration deadlines are enforced by CI warnings that escalate to errors.

| Deprecated Pattern | Canonical Replacement | Migration Deadline | Notes |
|---|---|---|---|
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

## Migration Guide

### 1. TENANT_CONTEXT -> governance_context

Find all instances:

```bash
grep -r "request.state.context" value-fabric/ shared/
```

Replace with `request.state.governance_context`.

### 2. get_db() -> get_db_from_context()

Find all instances:

```bash
grep -r "Depends\s*(\s*get_db\b" value-fabric/ shared/
grep -r "with\s+db_session\s*(" value-fabric/ shared/
grep -r "get_db_with_tenant" value-fabric/ shared/
grep -r "get_db_with_optional_tenant" value-fabric/ shared/
grep -r "get_tiered_db_session" value-fabric/ shared/
```

Replace endpoints to use `Depends(get_db_from_context)`.
Replace background tasks to use `db_session_for_context()`.

### 3. useWorkflowStore + usePilotStore -> useValuePilotStore

Merge functionality into a single store in `client/src/stores/valuePilotStore.ts`.
Deprecate the old stores.
