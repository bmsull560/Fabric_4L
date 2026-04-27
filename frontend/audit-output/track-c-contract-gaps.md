# Track C: Contract Gap Analysis

## The 6 Canonical Contracts (from CONTRACT.md)

| Contract | Section | Status | Enforcement Date |
|----------|---------|--------|------------------|
| Tenant Context Propagation | 2.1 | Proposed | 2026-06-23 |
| DB Session and Isolation | 2.2 | Ratified | 2026-06-23 |
| Middleware and Auth Flow | 2.3 | Ratified | 2026-06-23 |
| Tool Invocation Boundary | 2.4 | Proposed | 2026-06-23 |
| Agent Output Shape | 2.5 | Proposed | 2026-06-23 |
| UI State Progression | 2.6 | Proposed | 2026-06-23 |

## Contract 2.1: Tenant Context Propagation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Context is explicit, not ambient | ⚠️ PARTIAL | useUserTierStore exists but not all hooks use it |
| X-Tenant-ID header propagated | ✅ PASS | apiClient.ts sets header consistently |
| ContextVar for async propagation | ⚠️ PARTIAL | Used in L4, some L3 hooks missing |

### Violations Found
- Multiple hooks use direct `apiClient` calls without tenant context validation
- No hook-level enforcement of tenant isolation

## Contract 2.2: DB Session and Isolation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| get_db_from_context() canonical | ⚠️ PARTIAL | Frontend doesn't use this directly |
| Session lifecycle managed | ✅ PASS | React Query handles caching/isolation |
| RLS via app.tenant_id | ✅ PASS | Backend enforces, transparent to frontend |

## Contract 2.3: Middleware and Auth Flow

| Criterion | Status | Evidence |
|-----------|--------|----------|
| GovernanceMiddleware resolves identity | ✅ PASS | App.tsx has RouteGuard |
| require_authenticated enforces | ✅ PASS | AuthenticatedRoute wrapper used |
| Rate limiting configured | ⚠️ PARTIAL | Via middleware but not visible in hooks |

## Contract 2.4: Tool Invocation Boundary

| Criterion | Status | Evidence |
|-----------|--------|----------|
| BaseTool -> Pydantic schema | ⚠️ PARTIAL | Tool manifests exist but not all used |
| ToolRegistry in frontend | ❌ FAIL | No frontend ToolRegistry implementation |
| JSON Schema manifests | ⚠️ PARTIAL | 9 manifests in contracts/tool-manifests/ |

## Contract 2.5: Agent Output Shape

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Declared schema for outputs | ❌ FAIL | Agent outputs not typed in frontend |
| No raw dict crossing | ⚠️ PARTIAL | Some hooks use `any` types |

## Contract 2.6: UI State Progression

| Criterion | Status | Evidence |
|-----------|--------|----------|
| URL is primary navigation | ✅ PASS | wouter routes in App.tsx |
| Zustand stores typed | ✅ PASS | userTierStore, accountContextStore typed |
| Server state in React Query | ⚠️ PARTIAL | Most hooks use RQ, some don't |

---

## Missing Contracts: Frontend-Backend Boundary

### Gap 1: API Boundary Contract (CRITICAL)

**Missing Standard:**
- No standardized frontend request patterns
- Inconsistent error handling across hooks
- No pagination/filtering/sorting standards

**Current State (Inconsistent):**
| Pattern | Hooks Using | Standard? |
|---------|-------------|-----------|
| Direct apiClient calls | useSources, useBilling | ❌ No standard |
| useApiShared wrappers | useAccounts, useFormulas | ⚠️ Partial |
| Inline error handling | Multiple | ❌ Inconsistent |

**Impact:** 47 hooks with 15+ different error handling patterns

### Gap 2: Type Synchronization Contract (CRITICAL)

**Missing Standard:**
- No automated backend→frontend type generation
- Manual types drift from OpenAPI specs
- Inline types instead of imported schemas

**Evidence:**
- OpenAPI specs: 244 endpoints with schemas
- Frontend types: Manual definitions in hooks
- Drift detected: Multiple `any` types in hooks

### Gap 3: Hook Architecture Contract (HIGH)

**Missing Standard:**
- Inconsistent React Query patterns
- No standard for mutations vs queries
- No optimistic update patterns defined

**Current Inconsistencies:**
| Hook | Query Keys | Cache Time | Retry | Error Handler |
|------|------------|------------|-------|---------------|
| POLL_INTERVALS       | No         | Default | Default | No            |
| SSEBuilders          | No         | Default | Default | No            |
| STALE_TIME           | No         | Default | Default | Yes           |
| billingKeys          | Yes        | Default | Default | Yes           |
| getDefaultSuggestedActions | No         | Default | Default | Yes           |
| invoiceKeys          | Yes        | Default | Default | No            |
| usageKeys            | Yes        | Default | Default | No            |
| useAccounts          | No         | Default | Default | Yes           |
| useActiveWorkflows   | No         | Default | Default | Yes           |
| useAuth              | No         | Default | Default | No            |
| useBenchmarks        | No         | Default | Default | Yes           |
| useBusinessCase      | Yes        | Default | Default | Yes           |
| useC1Stream          | No         | Default | Default | Yes           |
| useCanonicalCaseId   | No         | Default | Default | Yes           |
| useComposition       | No         | Default | Default | No            |

---

## Recommendations

1. **Ratify API Boundary Contract** - Standardize error handling, pagination, and request patterns
2. **Implement Type Generation Pipeline** - Auto-generate TypeScript from OpenAPI specs
3. **Define Hook Architecture Contract** - Standardize React Query usage patterns
4. **Enforce Contract 2.4** - Build frontend ToolRegistry for agent tool invocation
5. **Enforce Contract 2.5** - Add strict typing for agent outputs
