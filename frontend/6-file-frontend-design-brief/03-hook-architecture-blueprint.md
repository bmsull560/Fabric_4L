# 3. Hook Architecture Blueprint

The Fabric 4L frontend currently maintains 44 hooks across 37 source files, yet these hooks follow no uniform architectural pattern. Track A found 26 hooks with verified live backend integration (green), 5 hooks operating as generic endpoint passthroughs without domain-level abstraction (yellow), 2 hooks serving hardcoded mock data (red), and 11 hooks whose data source could not be determined (unknown). This distribution — 59% green, 11% yellow, 5% red, 25% unknown — signals not merely inconsistency but architectural absence: there is no contract governing how a hook should be structured, how it should interact with the HTTP layer, how it should manage cache keys, or how it should surface errors to the UI.

Track C identified this deficiency as **Gap 3: Hook Architecture Contract**, classified as HIGH severity. The gap manifests concretely across four dimensions: query key naming follows at least three competing conventions (`billingKeys.subscription()`, `QK.entities.list()`, and raw string arrays like `['entityFilterOptions']`); cache configuration is left at React Query defaults for the majority of hooks; mutation error handling ranges from inline `console.error` to global toast notifications with no standard taxonomy; and optimistic update patterns are entirely absent from the codebase. These inconsistencies raise the cost of every new feature, obscure bugs in production, and make code review an exercise in subjective preference rather than contract enforcement.

This document defines the **three-tier hook system** that replaces the current ad-hoc approach with a typed, validated, enforceable architecture. Each tier has a single responsibility, a strict interface contract, and explicit rules about what code at that tier may and may not do.

---

## 3.1 The Three-Tier Hook System

The three-tier model separates HTTP mechanics from domain logic from page-specific composition. This separation mirrors the backend's layer architecture (L1–L6) but adapts it to React's component-hook lifecycle. Every hook in the system must belong to exactly one tier. A hook that violates its tier boundary — for example, a domain hook that constructs raw `fetch` options, or a page hook that defines its own query key scheme — is considered architecturally non-compliant and must be refactored.

### 3.1.1 Tier 1 — Protocol Hooks

Protocol hooks are the lowest tier, positioned directly above `apiClient.ts`. They perform a single function: translate a typed request into an HTTP call and validate the response through a Zod schema before returning data to the caller. Protocol hooks contain no domain logic, no error message formatting for human consumption, no cache configuration, and no knowledge of React Query. They are pure async functions that wrap `apiClient.get`, `apiClient.post`, `apiClient.patch`, and `apiClient.delete` with generics for request payload and response shape.

The current codebase has no formal protocol hook layer. `apiClient.ts` is imported directly by domain hooks such as `useAccounts`, `useFormulas`, and `useOntologySchema`, which means every domain hook repeats the same boilerplate for tenant header propagation, request logging, and error interceptors. Centralizing this repetition into protocol hooks eliminates duplication and creates a single point of control for HTTP behavior.

### 3.1.2 Tier 2 — Domain Hooks

Domain hooks are the workhorse tier. Each domain hook manages data for a single backend entity or bounded context — accounts, formulas, ontology, ingestion jobs, etc. They wrap React Query's `useQuery` and `useMutation` through two standardized fabric wrappers: `useFabricQuery` and `useFabricMutation`. Every domain hook defines its query key using the `QK.{domain}.{action}({params})` namespace convention, declares its Zod validation schema, and specifies cache policy through the fabric wrappers rather than inline React Query options.

The 26 green hooks identified in Track A — `useAccounts`, `useBenchmarks`, `useFormulas`, `useEntities`, `useOntologySchema`, `useIngestionJobs`, and 20 others — represent the model for this tier. These hooks already consume live endpoints, already handle errors, and already carry TypeScript types. The standardization effort does not rewrite their APIs; it extracts their common patterns into the fabric wrappers and enforces the query key namespace where deviations exist.

### 3.1.3 Tier 3 — Page Hooks

Page hooks compose domain hooks into page-specific data shapes. A page hook does not call `useQuery` or `useMutation` directly; it imports domain hooks and aggregates their `isLoading`, `error`, and `data` states into a single return object tailored to the page component's props interface. For example, a dashboard page hook might combine `useSystemHealth`, `useIngestionJobs`, and `useActiveWorkflows` into a unified `DashboardData` shape with a single derived `isLoading` flag and a prioritized error list.

This tier currently does not exist in the Fabric 4L codebase. Page components call domain hooks directly, which means loading and error logic is scattered across JSX trees and repeated across routes. Introducing page hooks centralizes this aggregation and enforces the rule that page components receive fully resolved data or a unified loading/error state — never a mix of individual hook states.

### 3.1.4 Strict Tier Boundaries

Two hard constraints govern the three-tier system:

**No page component calls `fetch` directly.** The `fetch` primitive (or `apiClient` directly) is the exclusive privilege of Tier 1. Page components and even domain hooks are prohibited from constructing raw HTTP requests. This constraint ensures that every network call passes through Zod validation, tenant header injection, and request logging without exception.

**No page component uses mock data after T+30 days.** The two red hooks — `useOpportunities` and `useSources` — serve mock data. These hooks are grandfathered with a 30-day migration window from the date of this document's acceptance. After T+30, any hook with `is_mock: true` is a build failure. CI will enforce this through a lint rule that scans hook source files for mock data patterns (static arrays, hardcoded objects, `Math.random` in data generation).

---

## 3.2 Tier 1: Protocol Hooks

The protocol tier's single entry point is `apiClient.ts`, which functions as the HTTP gateway for the entire frontend. All protocol hooks consume this gateway; no other module in the application imports `axios` or `fetch`.

### 3.2.1 apiClient.ts as the Single HTTP Gateway

`apiClient.ts` configures an Axios instance with three cross-cutting concerns:

**Interceptors.** Every outgoing request passes through a request interceptor that injects the `X-Tenant-ID` header from `useUserTierStore`, attaches the current authentication bearer token, and stamps a `X-Request-ID` UUID for distributed tracing. Every incoming response passes through a response interceptor that logs timing metadata (request start, response end, total latency), captures non-2xx status codes for the health dashboard, and normalizes error shapes into a consistent `FabricApiError` object.

**Tenant Header Injection.** Track C found that while `apiClient.ts` sets the `X-Tenant-ID` header consistently at the client level, not all hooks validate tenant context before initiating requests. The protocol tier closes this gap: every protocol hook receives `tenantId` as a required parameter and validates it against the current user tier before calling `apiClient`. A missing or mismatched tenant ID throws before the HTTP request is dispatched.

**Request/Response Logging.** All protocol hooks operate in debug mode during development, logging full request and response bodies to the console. In production, request URLs, status codes, and latency are emitted to the monitoring pipeline; bodies are redacted for PII.

### 3.2.2 Zod Runtime Validation

Every response from a protocol hook is validated against a Zod schema before the data crosses the tier boundary into a domain hook. This is the **only** point in the system where runtime validation occurs; domain hooks and page hooks trust that data from Tier 1 is type-safe.

The `useOntologySchema` hook already demonstrates this pattern. It calls `OntologyTypeSchema.safeParse(response.data)` and `OntologyPropertySchema.safeParse(response.data)` after each `apiClient` operation, logging validation failures to the error tracker. The protocol tier formalizes this pattern: validation is no longer the responsibility of individual domain hooks but is baked into the protocol hook contract via the generic `TResponse extends ZodSchema` constraint.

### 3.2.3 Protocol Hook Generic Interface

All protocol hooks conform to a single generic interface. The interface separates request shape from response shape, enforces Zod schema binding, and declares the HTTP method explicitly. Below is the canonical TypeScript definition:

```typescript
import { ZodSchema, z } from 'zod';
import { AxiosRequestConfig } from 'axios';

// ── Error Types ──
interface FabricApiError {
  statusCode: number;
  code: string;
  message: string;
  requestId: string;
  timestamp: string;
}

// ── HTTP Method Literal ──
type HttpMethod = 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE';

// ── Protocol Hook Configuration ──
interface ProtocolHookConfig<TRequest, TResponse> {
  endpoint: string | ((params: TRequest) => string);
  method: HttpMethod;
  requestSchema?: ZodSchema<TRequest>;
  responseSchema: ZodSchema<TResponse>;
  baseConfig?: AxiosRequestConfig;
}

// ── Protocol Hook Return Type ──
interface ProtocolHookResult<TRequest, TResponse> {
  execute: (request: TRequest) => Promise<TResponse>;
  validateRequest: (request: unknown) => TRequest;
  validateResponse: (response: unknown) => TResponse;
}

// ── Factory Function ──
function createProtocolHook<TRequest, TResponse>(
  config: ProtocolHookConfig<TRequest, TResponse>
): ProtocolHookResult<TRequest, TResponse> {
  const execute = async (request: TRequest): Promise<TResponse> => {
    // Validate request against schema if provided
    const validatedRequest = config.requestSchema
      ? config.requestSchema.parse(request)
      : request;

    // Resolve endpoint (static string or function)
    const url = typeof config.endpoint === 'function'
      ? config.endpoint(validatedRequest)
      : config.endpoint;

    // Dispatch through apiClient gateway
    const response = await apiClient.request({
      method: config.method,
      url,
      data: config.method !== 'GET' ? validatedRequest : undefined,
      params: config.method === 'GET' ? validatedRequest : undefined,
      ...config.baseConfig,
    });

    // Runtime Zod validation — data does not cross tier boundary without passing
    const parsed = config.responseSchema.safeParse(response.data);
    if (!parsed.success) {
      logError('Protocol validation failed', {
        endpoint: url,
        errors: parsed.error.flatten(),
        requestId: response.headers['x-request-id'],
      });
      throw new FabricValidationError(parsed.error, url);
    }

    return parsed.data;
  };

  return {
    execute,
    validateRequest: (req) =>
      config.requestSchema ? config.requestSchema.parse(req) : req as TRequest,
    validateResponse: (res) => config.responseSchema.parse(res),
  };
}
```

This factory is the only mechanism for creating Tier 1 hooks. The `useApiGet`, `useApiPost`, and `useApiDelete` convenience wrappers are thin presets over `createProtocolHook` that bind the HTTP method and provide common Axios defaults (e.g., `useApiGet` sets `staleTime` headers for cache-control where applicable). Every protocol hook instantiated through this factory automatically inherits tenant header injection, request logging, and response validation without explicit configuration.

---

## 3.3 Tier 2: Domain Hooks

Domain hooks are the interface between protocol-level HTTP operations and React Query's caching system. The 26 green hooks in the current codebase — `useAccounts`, `useBenchmarks`, `useFormulas`, `useEntities`, `useOntologySchema`, `useIngestionJobs`, `useIntegrations`, `useGraphQuery`, and 18 others — already function at this tier but lack standardization in three areas: cache policy, error mapping, and query key naming. The Tier 2 specification extracts their common patterns into two fabric wrappers and enforces uniform conventions.

### 3.3.1 useFabricQuery: Standardized Query Wrapper

`useFabricQuery` wraps `@tanstack/react-query`'s `useQuery` with five fabric-level defaults:

**Stale time.** All fabric queries default to `STALE_TIME.default` (5 minutes) unless the domain hook overrides. Hooks that poll for job status — such as `useExtractionResults` and `useJobStream` — use `STALE_TIME.poll` (10 seconds) and declare `refetchInterval` explicitly. The `STALE_TIME` constant is already defined in `useApiShared.ts` (one of the 11 unknown-classified exports) and is promoted to a Tier 2 shared configuration.

**Retry policy.** The default retry count is 2, with exponential backoff. Status codes 401 and 403 trigger immediate logout via the auth interceptor; they are not retried. Status code 429 (rate limit) reads the `Retry-After` header and waits accordingly. Network errors (`ECONNREFUSED`, `ETIMEDOUT`) retry with jitter. This policy replaces the current default React Query behavior, which retries indiscriminately 3 times.

**Error mapping.** Every domain hook registers an `ErrorMap` that translates HTTP status codes into `UIErrorType` values: `network`, `permission`, `not_found`, `validation`, `server`, and `unknown`. The `useFabricQuery` wrapper applies this mapping before returning the error to the caller. Page hooks (Tier 3) receive already-classified errors and select UI treatment without inspecting HTTP status codes.

**Query key namespacing.** The `QK.{domain}.{action}({params})` convention eliminates the current fragmentation where some hooks use `billingKeys.subscription()`, others use `QK.entities.list()`, and still others use raw arrays. Section 3.3.3 defines the full namespace registry.

**TypeScript generics.** `useFabricQuery` accepts four generic parameters: `TRequest` (query parameters), `TResponse` (successful response), `TError` (error shape), and `TDomain` (a string literal for query key domain segment). This ensures that every domain hook call is fully typed end-to-end.

### 3.3.2 useFabricMutation: Standardized Mutation Wrapper

`useFabricMutation` wraps `useMutation` with three additions:

**Optimistic update patterns.** The wrapper accepts an optional `optimisticUpdate` callback that receives the query client, the current cache snapshot, and the mutation variables. If provided, the wrapper applies the optimistic update before the mutation fires, rolls it back on error, and confirms it on success. This pattern is currently absent from all 44 hooks; its introduction enables responsive UI for mutations in `useFormulas`, `useOntologySchema`, and `useActiveWorkflows`.

**Invalidation rules.** Every mutation declares an `invalidateOnSuccess` array of query key patterns. After a successful mutation, `useFabricMutation` invalidates all matching queries. For example, a formula creation mutation invalidates `QK.formulas.list()` and `QK.formulas.detail(*)`, ensuring that list views refresh automatically without manual invalidation logic in the domain hook.

**Mutation state aggregation.** The wrapper exposes a derived `isMutating` flag that is `true` from the moment the mutation fires until either success confirmation or error rollback completes. This flag differs from React Query's `isPending` because it includes the optimistic update window, giving page hooks a single boolean for "show loading overlay."

### 3.3.3 Query Key Namespace Convention

Cache consistency depends on every domain hook using the same query key structure. The current codebase exhibits three competing patterns: object-style factories (`billingKeys.subscription(customerId)`), namespaced string arrays (`QK.entities.list()`), and raw arrays (`['entityFilterOptions']`). The namespace convention unifies all three into a single hierarchical scheme.

| Namespace | Pattern | Example Key | Owning Hook(s) |
|-----------|---------|-------------|----------------|
| `accounts` | `QK.accounts.list()`, `QK.accounts.detail(id)` | `['accounts', 'list']`, `['accounts', 'detail', 'acc_123']` | `useAccounts` |
| `billing` | `QK.billing.subscription(custId)`, `QK.billing.entitlements(custId)` | `['billing', 'subscription', 'cust_456']` | `billingKeys` |
| `businessCases` | `QK.businessCases.list(filters)`, `QK.businessCases.detail(id)` | `['businessCases', 'list']`, `['businessCases', 'detail', 'bc_789']` | `useBusinessCase` |
| `documents` | `QK.documents.businessCase(bcId)` | `['documents', 'businessCase', 'bc_789']` | `useDocumentExport` |
| `entities` | `QK.entities.list()`, `QK.entities.search(q)`, `QK.entities.detail(id)` | `['entities', 'list']`, `['entities', 'search', 'query']` | `useEntities` |
| `extraction` | `QK.extraction.job(id)`, `QK.extraction.results(id)` | `['extraction', 'job', 'ext_001']` | `useExtractionJob`, `useExtractionResults` |
| `formulas` | `QK.formulas.list()`, `QK.formulas.detail(id)`, `QK.formulas.versions(id)` | `['formulas', 'list']`, `['formulas', 'detail', 'f_001']` | `useFormulas`, `useFormulaVersions` |
| `governance` | `QK.governance.tenants()` | `['governance', 'tenants']` | `useTenants` |
| `graph` | `QK.graph.context(entityId)`, `QK.graph.subgraph(query)` | `['graph', 'context', 'ent_001']`, `['graph', 'subgraph', 'q']` | `useGraphQuery` |
| `health` | `QK.health.system()` | `['health', 'system']` | `useSystemHealth` |
| `ingestion` | `QK.ingestion.jobs()`, `QK.ingestion.recent()`, `QK.ingestion.stats()` | `['ingestion', 'jobs']`, `['ingestion', 'recent']`, `['ingestion', 'stats']` | `useIngestionJobs` |
| `ontology` | `QK.ontology.schema()`, `QK.ontology.type(id)` | `['ontology', 'schema']`, `['ontology', 'type', 't_001']` | `useOntologySchema` |
| `provenance` | `QK.provenance.trail(entityId)`, `QK.provenance.audit(filters)` | `['provenance', 'trail', 'ent_001']` | `useProvenanceTrail` |
| `workflows` | `QK.workflows.active()` | `['workflows', 'active']` | `useActiveWorkflows` |

The `QK` object is a frozen registry exported from a single source file (`queryKeys.ts`). No domain hook constructs a query key as a raw array; all keys are generated through `QK` factory methods. This registry enables three capabilities that raw arrays cannot provide: (1) full-text search across all cache keys during debugging, (2) pattern-based invalidation (`queryClient.invalidateQueries({ queryKey: ['formulas'] })` invalidates all formula-related keys), and (3) automated detection of duplicate or conflicting keys during CI.

Hooks currently using the legacy `billingKeys`, `invoiceKeys`, and `usageKeys` object patterns are refactored to use `QK.billing.*`, `QK.invoices.*`, and `QK.usage.*` respectively. The old key objects are deprecated and removed during the yellow-hook migration phase.

### 3.3.4 useFabricQuery Implementation

The domain wrapper implementation is the second required TypeScript code block. It demonstrates the integration of protocol hooks, Zod validation, error mapping, and query key namespacing:

```typescript
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { ZodSchema } from 'zod';

// ── Error Classification ──
type UIErrorType = 'network' | 'permission' | 'not_found' | 'validation' | 'server' | 'unknown';

interface ErrorMap { [statusCode: number]: UIErrorType; }

const DEFAULT_ERROR_MAP: ErrorMap = {
  400: 'validation',
  401: 'permission',
  403: 'permission',
  404: 'not_found',
  409: 'validation',
  422: 'validation',
  429: 'server',
  500: 'server',
  502: 'server',
  503: 'server',
};

// ── Cache Policy Constants ──
const STALE_TIME = {
  default: 5 * 60 * 1000,   // 5 minutes
  poll: 10 * 1000,           // 10 seconds
  long: 30 * 60 * 1000,      // 30 minutes
} as const;

const RETRY_POLICY = {
  retries: 2,
  retryDelay: (attemptIndex: number) => Math.min(1000 * 2 ** attemptIndex, 30000),
  retryCondition: (error: FabricApiError) => {
    if (error.statusCode === 401 || error.statusCode === 403) return false;
    if (error.statusCode === 429) return true; // Respect Retry-After in interceptor
    return error.statusCode >= 500 || !error.statusCode;
  },
};

// ── useFabricQuery Wrapper ──
interface UseFabricQueryOptions<TRequest, TResponse, TDomain extends string> {
  domain: TDomain;
  action: string;
  request: TRequest;
  responseSchema: ZodSchema<TResponse>;
  protocolHook: ProtocolHookResult<TRequest, TResponse>;
  errorMap?: Partial<ErrorMap>;
  staleTime?: number;
  enabled?: boolean;
  refetchInterval?: number | false;
}

function useFabricQuery<TRequest, TResponse, TDomain extends string>(
  options: UseFabricQueryOptions<TRequest, TResponse, TDomain>
) {
  const {
    domain,
    action,
    request,
    responseSchema,
    protocolHook,
    errorMap = {},
    staleTime = STALE_TIME.default,
    enabled = true,
    refetchInterval = false,
  } = options;

  // Build namespaced query key
  const queryKey = [domain, action, JSON.stringify(request)] as const;

  // Merge domain error map with defaults
  const mergedErrorMap = { ...DEFAULT_ERROR_MAP, ...errorMap };

  return useQuery<TResponse, FabricApiError>({
    queryKey: [...queryKey],
    queryFn: () => protocolHook.execute(request),
    staleTime,
    retry: RETRY_POLICY.retries,
    retryDelay: RETRY_POLICY.retryDelay,
    enabled,
    refetchInterval,
    meta: {
      responseSchema,
      errorMap: mergedErrorMap,
      domain,
      action,
    },
  });
}

// ── useFabricMutation Wrapper ──
interface UseFabricMutationOptions<TVariables, TResponse, TContext = unknown> {
  mutationFn: (variables: TVariables) => Promise<TResponse>;
  invalidateOnSuccess?: string[][];
  optimisticUpdate?: {
    queryKey: string[];
    updater: (oldData: unknown, variables: TVariables) => unknown;
  }[];
  onError?: (error: FabricApiError, variables: TVariables, context?: TContext) => void;
  onSuccess?: (data: TResponse, variables: TVariables) => void;
}

function useFabricMutation<TVariables, TResponse, TContext = unknown>(
  options: UseFabricMutationOptions<TVariables, TResponse, TContext>
) {
  const queryClient = useQueryClient();
  const {
    mutationFn,
    invalidateOnSuccess = [],
    optimisticUpdate,
    onError,
    onSuccess,
  } = options;

  return useMutation<TResponse, FabricApiError, TVariables, TContext>({
    mutationFn,
    onMutate: async (variables) => {
      // Cancel outgoing refetches for optimistic targets
      if (optimisticUpdate) {
        for (const update of optimisticUpdate) {
          await queryClient.cancelQueries({ queryKey: update.queryKey });
        }

        // Snapshot previous values
        const previousData = new Map<string[], unknown>();
        for (const update of optimisticUpdate) {
          previousData.set(update.queryKey, queryClient.getQueryData(update.queryKey));
        }

        // Apply optimistic updates
        for (const update of optimisticUpdate) {
          queryClient.setQueryData(update.queryKey, (old: unknown) =>
            update.updater(old, variables)
          );
        }

        return { previousData } as TContext;
      }
      return undefined as TContext;
    },
    onError: (error, variables, context) => {
      // Rollback optimistic updates
      if (context && 'previousData' in context) {
        const ctx = context as { previousData: Map<string[], unknown> };
        ctx.previousData.forEach((value, key) => {
          queryClient.setQueryData(key, value);
        });
      }
      onError?.(error, variables, context);
    },
    onSuccess: (data, variables) => {
      // Invalidate affected queries
      for (const key of invalidateOnSuccess) {
        queryClient.invalidateQueries({ queryKey: key });
      }
      onSuccess?.(data, variables);
    },
  });
}
```

The `useFabricQuery` and `useFabricMutation` wrappers are exported from a single module (`fabricQuery.ts`) and are the only mechanisms through which domain hooks interact with React Query. A domain hook that imports `useQuery` or `useMutation` directly from `@tanstack/react-query` is non-compliant.

### 3.3.5 Current Domain Hooks Analysis

Of the 44 hooks analyzed, 26 green hooks are the model for Tier 2. They already consume live endpoints, already carry types, and already handle errors. The standardization effort preserves their external APIs and refactors only their internal implementation to use the fabric wrappers. The 5 yellow hooks (`useFormulaDependents`, `useFormulaVersions`, `invoiceKeys`, `usageKeys`, `useValueTree`) need creation of protocol hooks and binding to actual endpoints — they currently lack `api_endpoints` entries in the audit data. The 2 red hooks (`useOpportunities`, `useSources`) need mock data replaced with live protocol hooks. The 11 unknown hooks fall into two categories: utility hooks (`usePersistFn`, `useAuth`, `usePrefersReducedMotion`) that are not data-fetching hooks and thus exempt from the three-tier system, and potentially missing domain hooks (`useExtractionConfig`, `useGraphCanvas`, `useGraphData`) that require investigation to determine whether they should become Tier 2 domain hooks or remain as UI utilities.

---

## 3.4 Tier 3: Page Hooks

Page hooks are the top of the three-tier stack. Their exclusive responsibility is to compose domain hooks into page-specific data shapes and aggregate loading, error, and empty states into unified values that page components consume without further processing.

### 3.4.1 Composition Pattern

A page hook imports two or more Tier 2 domain hooks, calls each one, and returns a single object containing all data fields, a derived `isLoading` flag, and a prioritized error list. The page component destructures this object and renders accordingly. No page component calls more than one hook directly; if a page needs data from multiple domains, a page hook mediates.

Consider a dashboard page that displays system health tiles, recent ingestion jobs, and active workflow counts. Rather than the JSX tree calling `useSystemHealth`, `useIngestionJobs`, and `useActiveWorkflows` directly, the `useDashboardPage` hook composes all three:

```typescript
// ── Page Hook: useDashboardPage ──
// Composes three Tier 2 domain hooks into a page-specific data shape.
// All loading/error states are aggregated; the page component receives
// a single resolved object.

interface DashboardPageData {
  health: SystemHealth | undefined;
  recentJobs: IngestionJob[] | undefined;
  activeWorkflows: Workflow[] | undefined;
  workflowCount: number;
  isLoading: boolean;
  isFetching: boolean;
  error: UIError | null;
  errors: UIError[];
}

function useDashboardPage(): DashboardPageData {
  // ── Tier 2 Domain Hook Calls ──
  const {
    data: health,
    isLoading: healthLoading,
    isFetching: healthFetching,
    error: healthError,
  } = useFabricQuery({
    domain: 'health',
    action: 'system',
    request: {},
    responseSchema: SystemHealthSchema,
    protocolHook: healthProtocolHook,
    staleTime: STALE_TIME.poll, // Health data refreshes every 10s
    refetchInterval: 10000,
  });

  const {
    data: jobs,
    isLoading: jobsLoading,
    isFetching: jobsFetching,
    error: jobsError,
  } = useFabricQuery({
    domain: 'ingestion',
    action: 'recent',
    request: {},
    responseSchema: IngestionJobListSchema,
    protocolHook: ingestionRecentProtocolHook,
    staleTime: STALE_TIME.default,
  });

  const {
    data: workflows,
    isLoading: workflowsLoading,
    isFetching: workflowsFetching,
    error: workflowsError,
  } = useFabricQuery({
    domain: 'workflows',
    action: 'active',
    request: {},
    responseSchema: WorkflowListSchema,
    protocolHook: workflowsProtocolHook,
    staleTime: STALE_TIME.default,
  });

  // ── Loading State Aggregation ──
  // isLoading is TRUE if ANY constituent hook is in its initial load state.
  // isFetching is TRUE if ANY constituent hook is refetching in the background.
  const isLoading = healthLoading || jobsLoading || workflowsLoading;
  const isFetching = healthFetching || jobsFetching || workflowsFetching;

  // ── Error State Aggregation ──
  // Priority: first error wins for display; full list available for debugging.
  const errors: UIError[] = [
    healthError ? { source: 'health', type: mapError(healthError), original: healthError } : null,
    jobsError ? { source: 'ingestion', type: mapError(jobsError), original: jobsError } : null,
    workflowsError ? { source: 'workflows', type: mapError(workflowsError), original: workflowsError } : null,
  ].filter(Boolean) as UIError[];

  const error = errors.length > 0 ? errors[0] : null;

  return {
    health,
    recentJobs: jobs?.jobs,
    activeWorkflows: workflows?.workflows,
    workflowCount: workflows?.workflows?.length ?? 0,
    isLoading,
    isFetching,
    error,
    errors,
  };
}
```

The page hook enforces three architectural invariants. First, the page component (`DashboardPage.tsx`) receives `health`, `recentJobs`, and `activeWorkflows` as potentially undefined values but never as promise-returning functions or individual hook result objects. Second, the page component renders a single loading skeleton when `isLoading` is true and a single error banner when `error` is non-null; it does not branch on individual hook states. Third, the page hook is the only module that knows which domain hooks the page requires; the page component's props interface is a plain data object with no hook imports.

### 3.4.2 Loading State Aggregation

The derived `isLoading` flag uses a logical OR across all constituent domain hooks' `isLoading` states. This means the page displays a full skeleton until every domain hook has resolved its initial fetch. Background refetches are surfaced through a separate `isFetching` flag, which the page component may use to display a subtle "refreshing" indicator without replacing the existing content. This two-state model (loading vs. fetching) eliminates the visual flicker that occurs when one domain hook refetches while others remain stable.

Hooks that poll on an interval — such as `useSystemHealth` with its 10-second refetch — do not flip `isLoading` on each poll; only `isFetching` changes. This distinction is critical for pages that mix polling hooks with one-shot hooks: the user sees a stable dashboard with a health tile that updates silently, rather than a full-page skeleton flash every 10 seconds.

### 3.4.3 Error State Aggregation

Error aggregation follows a **first-error-wins** priority rule. When multiple domain hooks fail simultaneously, the page hook returns the first error in its internal composition order as the primary `error` value. The full `errors` array is also exposed for error detail panels or debugging UIs, but the primary banner displays only the first. This rule is deterministic: the page hook author controls priority through composition order.

The rationale for first-error-wins over most-recent-error or highest-severity-error is simplicity and predictability. Most-recent-error introduces race conditions when two hooks fail near-simultaneously; highest-severity-error requires a severity taxonomy that does not currently exist in the codebase. First-error-wins provides a consistent, reviewable priority that matches the visual stacking order of the page.

Each error in the `errors` array carries a `source` field identifying the domain hook that produced it (`'health'`, `'ingestion'`, `'workflows'`), enabling the page component to render domain-specific error messages ("Health monitoring unavailable" vs. "Cannot load ingestion jobs"). The `mapError` function translates `FabricApiError` into `UIErrorType` using the same error map declared in the domain hook, ensuring consistency between Tier 2 and Tier 3 error classification.

---

## 3.5 Migration Strategy for Existing Hooks

The current hook inventory of 44 hooks must be migrated into the three-tier system without breaking existing page components. This section defines the migration order, backward compatibility guarantees, and the criteria for promoting hooks from their current classification into the target architecture.

### 3.5.1 Current Hook Inventory

The table below inventories all 44 hooks with their exact names, source files, data source color, and the number of API endpoints each hook consumes. This inventory is the migration backlog. Every hook must either be classified into a tier or explicitly exempted.

| Hook Name | Source File | Color | API Endpoints | Tier Assignment | Migration Action |
|-----------|-------------|-------|--------------|-----------------|------------------|
| useAccounts | useAccounts.ts | green | 2 | T2 Domain | Refactor internal to fabric wrappers |
| getDefaultSuggestedActions | useAgentStream.ts | green | 1 | T2 Domain | Refactor internal to fabric wrappers |
| useBenchmarks | useBenchmarks.ts | green | 3 | T2 Domain | Refactor internal to fabric wrappers |
| billingKeys | useBilling.ts | green | 2 | T2 Domain | Migrate keys to QK namespace |
| useBusinessCase | useBusinessCases.ts | green | 2 | T2 Domain | Refactor internal to fabric wrappers |
| useDocumentExport | useDocuments.ts | green | 2 | T2 Domain | Refactor internal to fabric wrappers |
| useEntities | useEntities.ts | green | 4 | T2 Domain | Refactor internal to fabric wrappers |
| useExtractionJob | useExtraction.ts | green | 1 | T2 Domain | Refactor internal to fabric wrappers |
| useExtractionResults | useExtractionResults.ts | green | 3 | T2 Domain | Refactor internal to fabric wrappers |
| useFormulas | useFormulas.ts | green | 4 | T2 Domain | Refactor internal to fabric wrappers |
| useTenants | useGovernance.ts | green | 3 | T2 Domain | Refactor internal to fabric wrappers |
| useGraphQuery | useGraphQuery.ts | green | 2 | T2 Domain | Refactor internal to fabric wrappers |
| useSystemHealth | useHealthMonitor.ts | green | 1 | T2 Domain | Refactor internal to fabric wrappers |
| useIngestionJobs | useIngestion.ts | green | 3 | T2 Domain | Refactor internal to fabric wrappers |
| useIntegrations | useIntegrations.ts | green | 3 | T2 Domain | Refactor internal to fabric wrappers |
| useJobStream | useJobStream.ts | green | 1 | T2 Domain | Refactor internal to fabric wrappers |
| useModels | useModels.ts | green | 3 | T2 Domain | Refactor internal to fabric wrappers |
| useIndustries | useNarrativeGeneration.ts | green | 2 | T2 Domain | Refactor internal to fabric wrappers |
| useOntologySchema | useOntology.ts | green | 10 | T2 Domain | Refactor internal to fabric wrappers; model for Zod validation |
| usePlatformSettings | usePlatformSettings.ts | green | 2 | T2 Domain | Refactor internal to fabric wrappers |
| useProvenanceTrail | useProvenance.ts | green | 1 | T2 Domain | Refactor internal to fabric wrappers |
| useRunExtraction | useRunExtraction.ts | green | 2 | T2 Domain | Refactor internal to fabric wrappers |
| useValuePacks | useValuePacks.ts | green | 2 | T2 Domain | Refactor internal to fabric wrappers |
| useVariables | useVariables.ts | green | 2 | T2 Domain | Refactor internal to fabric wrappers |
| useActiveWorkflows | useWorkflows.ts | green | 3 | T2 Domain | Refactor internal to fabric wrappers |
| useCanonicalCaseId | useWorkspaceCase.ts | green | 4 | T2 Domain | Refactor internal to fabric wrappers |
| useFormulaDependents | useFormulaDependents.ts | yellow | 0 | T2 Domain | Create protocol hook + endpoint binding |
| useFormulaVersions | useFormulaVersions.ts | yellow | 0 | T2 Domain | Create protocol hook + endpoint binding |
| invoiceKeys | useInvoices.ts | yellow | 0 | T2 Domain | Create protocol hook + endpoint binding; migrate keys |
| usageKeys | useUsage.ts | yellow | 0 | T2 Domain | Create protocol hook + endpoint binding; migrate keys |
| useValueTree | useValueTrees.ts | yellow | 0 | T2 Domain | Create protocol hook + endpoint binding |
| useOpportunities | useOpportunities.ts | red | 1 | T2 Domain | Replace mock with live protocol hook |
| useSources | useSources.ts | red | 4 | T2 Domain | Replace mock with live protocol hook |
| usePrefersReducedMotion | useAccessibility.ts | unknown | 0 | Exempt | UI utility, not a data hook |
| STALE_TIME | useApiShared.ts | unknown | 0 | T2 Shared | Promote to shared config, not a hook |
| useAuth | useAuth.ts | unknown | 0 | Exempt | Authentication hook, special lifecycle |
| useC1Stream | useC1Stream.ts | unknown | 0 | T2 Domain | Investigate: likely stream data hook |
| useComposition | useComposition.ts | unknown | 0 | T2 Domain | Investigate: may need protocol hook |
| useExtractionConfig | useExtractionConfig.ts | unknown | 0 | T2 Domain | Investigate: extraction configuration |
| useGraphCanvas | useGraphCanvas.ts | unknown | 0 | Exempt | Canvas rendering utility |
| useGraphData | useGraphData.ts | unknown | 0 | T2 Domain | Investigate: graph data preparation |
| usePersistFn | usePersistFn.ts | unknown | 0 | Exempt | Utility hook (function persistence) |
| POLL_INTERVALS | usePolling.ts | unknown | 0 | T2 Shared | Promote to shared config |
| SSEBuilders | useSSEUtils.ts | unknown | 0 | Exempt | SSE utility, special transport |

This inventory confirms the target state: 31 hooks classified as Tier 2 domain hooks (the 26 green hooks plus 5 yellow hooks after endpoint binding), 3 hooks promoted to shared configuration constants (`STALE_TIME`, `POLL_INTERVALS`, and the `QK` registry), 2 red hooks replaced with live integrations, and 6 hooks exempted because they are UI utilities or authentication concerns outside the data-fetching tier system. The 11 unknown hooks require investigation, but the default assumption is Tier 2 unless exempted.

### 3.5.2 Refactor Order

The migration proceeds in three waves, prioritized by risk and user impact.

**Wave 1: Red Hooks (Weeks 1–2).** The two red hooks — `useOpportunities` and `useSources` — are the highest priority because they serve mock data to production users. `useOpportunities` consumes a `GET l4` endpoint in its configuration but overrides the response with hardcoded data; the refactor removes the mock override and lets the protocol hook return live data. `useSources` declares four endpoints (`DELETE l1`, `GET l1`, `POST l1`, `PUT l1`) but serves mock data for all of them; the refactor creates protocol hooks for each CRUD operation and binds them to the existing endpoints. Both refactors include backward-compatible API preservation: the return shape of `useOpportunities` and `useSources` remains identical, so page components require no changes.

**Wave 2: Yellow Hooks (Weeks 3–4).** The five yellow hooks — `useFormulaDependents`, `useFormulaVersions`, `invoiceKeys`, `usageKeys`, and `useValueTree` — have query keys defined but no API endpoints bound. This pattern indicates that the frontend queries are wired to React Query's cache but the `queryFn` is either a no-op or a mock. For each yellow hook, the engineering task is to: (1) identify the correct backend endpoint from the 244-endpoint registry (Track B orphan analysis), (2) create a protocol hook using `createProtocolHook`, (3) bind the domain hook to the protocol hook via `useFabricQuery`, and (4) migrate legacy key objects (`invoiceKeys`, `usageKeys`) to the `QK` namespace. The yellow hooks are dependent on backend endpoint availability; if an endpoint does not yet exist, the hook remains yellow and is tracked as a backend dependency.

**Wave 3: Unknown Hooks (Weeks 5–6).** The 11 unknown hooks are investigated individually. Hooks classified as utilities (`usePrefersReducedMotion`, `usePersistFn`, `useAuth`, `useGraphCanvas`, `SSEBuilders`) are formally exempted from the three-tier system and documented in an exemption registry. Hooks with potential domain data responsibilities (`useC1Stream`, `useComposition`, `useExtractionConfig`, `useGraphData`) are evaluated for Tier 2 classification: if they fetch or mutate backend state, they are refactored as domain hooks; if they are pure UI computations, they are exempted. `STALE_TIME` and `POLL_INTERVALS` are not hooks but constants; they are promoted to the Tier 2 shared configuration module and removed from the hook inventory.

### 3.5.3 Backward Compatibility

Every migrated hook preserves its existing exported API — function signature, return type, and hook name — during the refactor. Internal implementation changes (switching from raw `apiClient` calls to `useFabricQuery`, migrating query keys to the `QK` namespace, adding Zod validation) are invisible to page components. This rule eliminates the risk of cascading refactors across the component tree.

The enforcement mechanism is a TypeScript compatibility check in CI. Before a hook refactor is merged, the CI pipeline runs `tsc --noEmit` against all files that import the hook. If any call site breaks, the build fails. This check ensures that interface contracts, not just implementation details, are preserved.

After all 44 hooks are migrated into their assigned tiers, the **Facade Budget** governance rule applies: the percentage of hooks classified as non-green (yellow, red, or unknown) must not exceed 10%. The current rate is 41% (18 of 44). The target is <10% by the end of Quarter 2, measured through automated classification scans that run in CI and report to the integration dashboard.

---

## 3.6 Summary of Tier Responsibilities

| Tier | Responsibility | May Use | May NOT Use | Examples |
|------|---------------|---------|-------------|----------|
| **T1 Protocol** | HTTP abstraction, Zod validation | `apiClient.ts`, Zod schemas | React Query, error formatting, domain logic | `createProtocolHook`, `useApiGet`, `useApiPost` |
| **T2 Domain** | Cache management, error classification | `useFabricQuery`, `useFabricMutation`, T1 hooks | Raw `fetch`, inline `apiClient` calls, page-level composition | `useAccounts`, `useFormulas`, `useEntities` |
| **T3 Page** | State aggregation, page-specific composition | T2 domain hooks, derived state | `useQuery`, `useMutation`, T1 hooks, mock data | `useDashboardPage`, `useEntityBrowserPage` |

This table is the architectural contract. A hook's classification into a tier is not advisory; it determines which modules the hook may import and which patterns it must follow. Code review checklists include this table as a reference: any hook that imports from a tier below its minimum level is rejected.

The three-tier system transforms the current 44-hook ad-hoc collection into a maintainable, typed, contract-enforced architecture. The 26 green hooks provide the pattern; the fabric wrappers provide the standard; the migration strategy provides the path. The target is 100% green hook coverage — 44 hooks connected to live backend data, zero mocks, zero unknowns — with automated enforcement preventing regression.
