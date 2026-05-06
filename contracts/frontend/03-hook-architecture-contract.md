# Contract C: Hook Architecture Contract

**Status:** Ratified  
**Version:** 1.0.0  
**Date:** 2026-04-26  
**Scope:** All React hooks that interact with backend APIs  
**Enforcement:** Code review checklist + ESLint rules (see Section 8)

---

## 1. Purpose

This contract defines the three-tier hook system that replaces the current ad-hoc approach (26 green, 5 yellow, 2 red, 11 unknown hooks with 3+ competing query key conventions). Every hook that interacts with a backend API MUST belong to exactly one tier and conform to its interface contract.

---

## 2. Three-Tier Hook System

```
┌─────────────────────────────────────────────────┐
│  Page Components                                │
│  (consume Tier 3 hooks only)                    │
├─────────────────────────────────────────────────┤
│  Tier 3: Page Hooks                             │
│  Compose domain hooks into page-specific shapes │
│  Location: src/hooks/pages/                     │
├─────────────────────────────────────────────────┤
│  Tier 2: Domain Hooks                           │
│  React Query wrappers for bounded contexts      │
│  Location: src/hooks/                           │
├─────────────────────────────────────────────────┤
│  Tier 1: Protocol Hooks                         │
│  HTTP mechanics + Zod validation                │
│  Location: src/api/protocol/                    │
├─────────────────────────────────────────────────┤
│  apiClient.ts (HTTP Gateway)                    │
│  Axios instance with interceptors               │
└─────────────────────────────────────────────────┘
```

### 2.1 Tier 1 — Protocol Hooks

Protocol hooks translate typed requests into HTTP calls and validate responses through Zod schemas. They contain no domain logic, no error formatting, no cache configuration, and no React Query.

**Rules:**
- MUST import only from `apiClient.ts`
- MUST validate every response against a Zod schema
- MUST NOT import React Query
- MUST NOT contain domain-specific error messages
- MUST accept `tenantId` as a required parameter

### 2.2 Tier 2 — Domain Hooks

Domain hooks manage data for a single backend entity or bounded context. They wrap React Query through `useFabricQuery` and `useFabricMutation` standardized wrappers.

**Rules:**
- MUST use `QK.{domain}.{action}({params})` query key convention
- MUST use `useFabricQuery` / `useFabricMutation` wrappers (not raw `useQuery`/`useMutation`)
- MUST declare cache policy through the fabric wrappers
- MUST extend `BaseApiError` for domain-specific error classes
- MUST invalidate related query keys on successful mutations
- SHOULD implement optimistic updates for user-facing mutations

### 2.3 Tier 3 — Page Hooks

Page hooks compose domain hooks into page-specific data shapes. They aggregate loading, error, and data states into a single return object.

**Rules:**
- MUST NOT call `useQuery` or `useMutation` directly
- MUST import only Tier 2 domain hooks
- MUST return a unified `{ data, isLoading, error }` shape
- MUST derive `isLoading` from all composed hooks
- MUST prioritize errors (auth > permission > not-found > server)

---

## 3. Query Key Namespace

All query keys MUST use the `QK` (Query Keys) registry in `src/hooks/queryKeys.ts`. The namespace convention is:

```typescript
QK.{domain}.{action}({params})
```

### 3.1 Registered Namespaces

| Namespace | Domain | Layer |
|-----------|--------|-------|
| `QK.accounts` | Account management | L4 |
| `QK.products` | Product portfolio | L3 |
| `QK.evidence` | Evidence library | L3 |
| `QK.competitive` | Competitive intelligence | L3 |
| `QK.roi` | ROI calculator | L3 |
| `QK.enrichment` | Account enrichment | L4 |
| `QK.hypotheses` | Value hypotheses | L4 |
| `QK.narratives` | Narrative builder | L4 |
| `QK.intelligence` | Intelligence orchestrator | L4 |
| `QK.formulas` | Formula management | L3 |
| `QK.ontology` | Ontology schema | L3 |
| `QK.workflows` | Agent workflows | L4 |
| `QK.businessCases` | Business cases | L4 |
| `QK.documents` | Document export | L4 |
| `QK.governance` | Governance/admin | L4 |
| `QK.integrations` | CRM integrations | L4 |
| `QK.platform` | Platform settings | L4 |
| `QK.valueTrees` | Value trees | L3 |
| `QK.provenance` | Provenance/audit | L5 |

### 3.2 Key Actions

Each namespace supports these standard actions:

| Action | Purpose | Example |
|--------|---------|---------|
| `all` | Base key for invalidation | `QK.products.all` |
| `list` | Paginated list with filters | `QK.products.list(filters)` |
| `detail` | Single entity by ID | `QK.products.detail(id)` |
| `stats` | Summary/analytics | `QK.products.stats()` |

---

## 4. Domain Hook Template

Every new domain hook MUST follow this template:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { withApiError, BaseApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';

// ── Types ──────────────────────────────────────────────────────────────────
// Import from generated types when available, otherwise define locally
export interface Entity { /* ... */ }
export interface CreateEntityRequest { /* ... */ }

// ── Domain Error ───────────────────────────────────────────────────────────
export class EntityApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'EntityApiError';
  }
}

// ── Fetch Functions ────────────────────────────────────────────────────────
async function fetchEntities(filters: Filters): Promise<PaginatedResponse<Entity>> {
  const response = await apiClient.get('l3', `/entities?${buildParams(filters)}`);
  return response.data as PaginatedResponse<Entity>;
}

// ── Query Hooks ────────────────────────────────────────────────────────────
export function useEntities(filters: Filters = {}) {
  return useQuery<PaginatedResponse<Entity>, EntityApiError>({
    queryKey: QK.entities.list(filters),
    queryFn: () => withApiError(fetchEntities(filters), EntityApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

// ── Mutation Hooks ─────────────────────────────────────────────────────────
export function useCreateEntity() {
  const queryClient = useQueryClient();
  return useMutation<Entity, EntityApiError, CreateEntityRequest>({
    mutationFn: async (params) => {
      const response = await apiClient.post('l3', '/entities', params);
      return response.data as Entity;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.entities.all });
    },
    onError: (error) => {
      // Domain-specific error handling
    },
  });
}
```

---

## 5. Mutation Invalidation Rules

When a mutation succeeds, it MUST invalidate the appropriate query keys:

| Mutation Type | Invalidation Target | Example |
|--------------|--------------------|---------| 
| Create | `QK.{domain}.all` | Creating a product invalidates `QK.products.all` |
| Update | `QK.{domain}.all` + `QK.{domain}.detail(id)` | Updating a hypothesis invalidates list and detail |
| Delete | `QK.{domain}.all` | Deleting a competitor invalidates `QK.competitive.all` |
| Cross-domain | Related domain's `all` key | Validating a hypothesis may invalidate `QK.intelligence.all` |

---

## 6. Hard Constraints

1. **No page component calls `fetch` directly.** The `fetch` primitive is the exclusive privilege of Tier 1.
2. **No mock data after T+30 days.** Any hook with mock data is a build failure after the 30-day migration window.
3. **No raw string query keys.** All query keys MUST use the `QK` registry.
4. **No inline React Query options.** Cache policy MUST use `STALE_TIME` and `RETRY_CONFIG` constants.

---

## 7. Hook Naming Convention

| Pattern | Example | Purpose |
|---------|---------|---------|
| `use{Domain}s` | `useProducts` | List query for a domain |
| `use{Domain}` | `useProduct` | Detail query for a single entity |
| `useCreate{Domain}` | `useCreateProduct` | Create mutation |
| `useUpdate{Domain}` | `useUpdateCompetitor` | Update mutation |
| `useDelete{Domain}` | `useDeleteHypothesis` | Delete mutation |
| `use{Domain}{Action}` | `useProductSignalMatching` | Domain-specific action |

---

## 8. Enforcement

### 8.1 Code Review Checklist

Every PR that adds or modifies a hook MUST be reviewed against:

- [ ] Hook belongs to exactly one tier
- [ ] Query keys use `QK.{domain}.{action}` convention
- [ ] Error class extends `BaseApiError`
- [ ] Mutations invalidate appropriate query keys
- [ ] Cache policy uses `STALE_TIME` constants
- [ ] No direct `fetch`/`axios` imports

### 8.2 ESLint Rules

- `no-restricted-imports`: Block `axios` and `fetch` outside `apiClient.ts`
- `fabric/query-key-convention`: Enforce `QK.` prefix on all query keys
- `fabric/no-mock-data`: Detect mock data patterns in hook files

---

## 9. Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-04-26 | Initial ratification |
| 1.0.1 | 2026-05-06 | Directory structure clarification: Tier 1 (src/api/protocol/) exists; Tier 3 (src/hooks/pages/) not yet implemented - page hooks currently inline in feature directories |
