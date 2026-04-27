# 5. UI/UX Component Strategy

## 5.1 Skeleton System

The Fabric 4L frontend presents a critical surface-level integrity problem: the application renders 154 routes with polished visual components and tiered navigation, yet 81% of authenticated routes — 68 of 84 — display hardcoded data or mock responses with no proper async state rendering. When a user navigates to any of these 68 facades, they encounter either instant "data" (mock objects hardcoded in the component) or empty containers masquerading as loaded states. There is no visual distinction between a page that has actually fetched data from the backend and one that has silently rendered a placeholder. This fundamentally breaks user trust and masks the true integration status of every feature.

The skeleton system mandates that every async component must ship with a corresponding skeleton state that replicates the final layout shape with pixel-accurate dimensions. This is not a cosmetic enhancement; it is a structural requirement for honest UI. The skeleton communicates to the user that the application is actively working, preserves layout stability during data fetching (eliminating cumulative layout shift), and — critically — exposes which routes are genuinely integrated versus which are still mocked. A route that renders a skeleton indefinitely makes its orphaned status visible; a route that renders instant hardcoded data conceals it.

### 5.1.1 Skeleton Hierarchy and Granularity

Skeleton components operate at four nested levels of granularity. The correct level is determined by the scope of the async operation and the visual surface area of the pending content.

The **page skeleton** covers the full viewport layout and renders when an entire route awaits its primary data payload. It mirrors the page-level chrome: navigation rail, header bar, content grid, and footer region. Page skeletons apply to top-level route components such as `Accounts`, `EntityBrowser`, and `FormulaList` — the 16 green routes with verified backend integration via hooks including `useAccounts`, `useEntities`, and `useFormulas`.

The **section skeleton** covers a bounded content region within a page and renders when a subsection fetches independently from the parent. This pattern applies to dashboard panels, tabbed content areas, and sidebar widgets that load secondary data after the primary page content has resolved. The `GraphExplorer` component mounted at `/context/ontology/graph`, which uses `useGraphQuery` for subgraph data, would employ a section skeleton within the larger ontology page chrome.

The **card skeleton** covers individual card-shaped content containers and renders for list-item-level async operations. This applies to grids of account cards, formula cards in `FormulaList`, and entity cards in the `EntityBrowser`. Each card skeleton mirrors the exact dimensions of its loaded counterpart: avatar region, title block, metadata lines, and action buttons.

The **inline skeleton** covers single-line or single-element placeholders and renders for micro-async operations such as user name resolution, status badge rendering, or inline permission checks. Inline skeletons use the smallest shimmer footprint — typically a single rounded rectangle matching the expected text line height.

### 5.1.2 Skeleton Implementation Contract

Skeleton components must be co-located with their async counterparts in the source tree, following a strict naming convention: the skeleton for `Accounts.tsx` is `AccountsSkeleton.tsx`, living in the same directory. This co-location enforces the pairing rule: if a component performs any async data fetch, its skeleton must be defined alongside it. Importing a component without its skeleton triggers a lint-level rule violation.

The implementation uses a shimmer-based visual treatment with a `skeleton` CSS class applied to placeholder divs shaped to match the final content geometry. The shimmer animation is a global CSS keyframe defined once in the design system and applied uniformly. No per-component animation logic is permitted; consistency is enforced by the shared class.

The skeleton system ships in two passes. Pass one targets the 16 green routes — these represent immediate integration wins because they already have live backend hooks (`useAccounts`, `useEntities`, `useGraphQuery`, `useIntegrations`, `useBenchmarks`, `useSystemHealth`, `useVariables`, `usePlatformSettings`, and others from the verified green set). Pass two extends skeleton coverage to the 51 red routes, which require hook remediation before skeletons become meaningful. Red routes such as `/context/sources` (`useSources`, mock data), `/command-center`, and the 18 intelligence workspace routes all receive skeletons during their respective integration sprints. The priority mapping is absolute: no red-route skeleton work begins before every green route has full skeleton coverage.

| Route Status | Count | Skeleton Priority | Example Routes | Backend Hook |
|-------------|-------|-------------------|----------------|--------------|
| Green (live) | 16 | **Pass 1 — Immediate** | `/accounts`, `/context/ontology/entities`, `/governance/benchmarks` | `useAccounts`, `useEntities`, `useBenchmarks` |
| Red (mock) | 51 | **Pass 2 — Post-integration** | `/context/sources`, `/command-center`, `/intelligence/:accountId/*` | `useSources` (mock), `UNKNOWN` |
| Unknown | 17 | **Pass 3 — Evaluation-dependent** | `/context/agents`, `/context/formulas/:formulaId` | `useWorkflows`, `useFormula` |
| Redirect | 70 | No skeleton required | N/A | N/A |

The 17 unknown routes present a special case. Routes such as `/context/agents` (using `useWorkflows`, endpoint status N/A) and `/context/formulas/:formulaId` (using `useFormula`, endpoint status N/A) have hooks defined but no verified backend connection. Skeletons for these routes are built during Pass 3, contingent on hook integration outcomes from Track B endpoint archaeology. The unknown category must not be a holding pen for indefinitely deferred skeleton work — each route graduates to either green or red within two sprint cycles, and skeleton coverage follows within the same cycle.

### 5.1.3 Skeleton-Shaping Methodology

Every skeleton is shaped by measuring its loaded counterpart and replicating every structural block as a placeholder rectangle. The measurement covers four properties per block: width (as percentage of container or fixed pixel value), height (in pixels), border-radius (to match the loaded element's corner treatment), and vertical offset (to preserve spacing). For table-based layouts such as the variable registry at `/settings/data/variables` (powered by `useVariables`), the skeleton renders column-aligned placeholders matching each header's declared width. For form-based layouts such as platform settings at `/settings/system/settings` (powered by `usePlatformSettings`), the skeleton renders field-aligned placeholders matching each input's expected footprint.

The design system maintains a `SkeletonRegistry` — a TypeScript record mapping route paths to their designated skeleton components. This registry is the single source of truth for which skeleton renders on which route. During route guard initialization in `App.tsx`, the router checks the registry: if a route has a registered skeleton, that skeleton renders during the loading phase; if no skeleton is registered, the route renders a generic full-page shimmer as a fallback. The generic fallback is a temporary measure only; its presence on any route triggers a Pass 1 or Pass 2 assignment.

---

## 5.2 Error State Taxonomy

The Fabric 4L frontend currently exhibits 15+ distinct error handling patterns across 47 hooks. Hooks such as `useAccounts` and `useFormulas` implement inline error handling with try-catch wrappers, while hooks such as `useAuth`, `useComposition`, and `useGraphCanvas` implement no error handling at all. This inconsistency produces a fragmented user experience: some failures surface as silent console errors, others as unstyled text dumps, and others as full-page crashes. The error state taxonomy replaces this fragmentation with a six-category classification system, where every error maps to exactly one category, and every category maps to exactly one UI treatment.

The taxonomy operates at two levels: the hook level (where errors are intercepted and categorized) and the component level (where categorized errors are rendered). The hook-level contract is implemented via the `useApiShared` wrapper, which all hooks must adopt. The wrapper inspects the HTTP status code of every failed request and maps it to a typed error category. The component-level contract is implemented via the `AsyncWrapper` component (specified in Section 5.5), which receives the typed error category and renders the appropriate fallback UI.

### 5.2.1 Network Error (0 / Timeout / CORS)

Network errors occur when the request never reaches the backend: connection refused, DNS failure, CORS preflight rejection, or timeout. These are the most common errors in production and the most damaging to user trust when handled poorly. The current codebase responds with inconsistent behavior — some hooks return `undefined` data silently, others throw unhandled exceptions.

The standardized treatment requires three elements. First, a **retry button** displayed prominently in the error fallback UI with the label "Retry Connection." Second, **automatic retry with exponential backoff** — the `useApiShared` wrapper configures React Query with `retry: 3`, `retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000)`, producing delays of 1s, 2s, 4s before the final attempt at 8s (capped at 30s). Third, **offline detection** — the error boundary subscribes to `navigator.onLine` events and renders a distinct offline state when `online === false`, suppressing retry attempts until connectivity resumes. The offline state displays a "You are offline" message with a connection-status indicator that auto-resolves when the browser re-detects network availability.

### 5.2.2 Permission Error (403)

Permission errors occur when an authenticated user lacks the role or entitlement required for the requested resource. In Fabric 4L's tiered workspace model, this is a common and expected error — not a system failure. The standardized treatment must never display a generic "Forbidden" message.

The permission error UI renders an **upgrade prompt** tailored to the user's current tier: "This feature requires Professional tier — upgrade to access." For enterprise deployments, the prompt is replaced with a **contact admin message**: "Your organization restricts this feature — contact your workspace admin for access." The component gating the feature must implement a **feature gating check** before initiating the request: if the user's tier (read from `userTierStore`) is below the required threshold, the feature renders a locked-state UI with the upgrade CTA immediately, avoiding an unnecessary 403 round-trip. Hooks that call guarded endpoints — such as `useBenchmarks` (GET l6) and `useTenants` (GET l4, POST l4, DELETE l4) — must validate tier eligibility at the call site.

### 5.2.3 Not Found Error (404)

Not found errors occur when a requested resource does not exist: a deleted account, an expired formula, or a non-existent entity. The standardized treatment prioritizes **helpful navigation** over apology. The 404 fallback UI displays a context-aware message: "This [resource type] could not be found" followed by a list of navigation suggestions drawn from the current workspace context. For entity detail routes (`/context/ontology/entities/:entityId`), the suggestions include "Return to Entity Browser" and "Search for a different entity." Where applicable, the 404 state includes a **create-new CTA**: "This [resource type] does not exist — create it now" with a button linking to the creation flow. The `EntityDetail` component mounted at the parameterized entity route implements this pattern, offering entity creation as a direct recovery path from a 404.

### 5.2.4 Validation Error (422)

Validation errors occur when the backend rejects request payload structure: missing required fields, type mismatches, or business-rule violations. These are the most context-rich errors and require the most granular UI treatment. The standardized treatment implements three layers: **inline field errors** (displayed beneath the offending form field), **form-level summary** (a banner at the top of the form listing all validation failures), and **scroll-to-first-error** (on form submission, the viewport scrolls to the first invalid field and focuses it).

The `useApiShared` wrapper intercepts 422 responses and extracts the `errors` array from the response body, which follows the standardized `{ field: string, message: string, code: string }[]` shape. The wrapper normalizes this array into a `Record<string, string>` mapping field names to error messages, which the form component consumes via context. Hooks that perform mutations with complex payloads — `useFormulas` (DELETE l3, POST l3, PATCH l3), `useOntologySchema` (POST, PUT, DELETE on `/v1/ontology/schema`), and `useModels` (DELETE l3, POST l3) — must all implement this three-layer validation error treatment.

### 5.2.5 System Error (500+)

System errors indicate backend failure: unhandled exceptions, database connectivity loss, or service unavailability. These are the errors users can do nothing about, and the UI treatment must reflect that reality honestly. The standardized treatment displays an **incident reference** — a unique error code (derived from `x-request-id` response header or a client-generated UUID) that the user can provide to support. The UI message reads: "Something went wrong on our end. Reference: [code]." Below this, a **support contact** link opens the help desk ormailto link with the reference code pre-populated. Where the failing component is non-critical, the treatment implements **graceful degradation**: the component renders a collapsed error state (a small warning icon with "Failed to load" text) while the rest of the page continues to function. The `HealthMonitor` component at `/governance/health` (using `useSystemHealth`, GET l4) implements this pattern — a backend health check failure does not crash the governance dashboard.

### 5.2.6 Empty State

Empty states are not errors in the traditional sense, but they share the same UI contract: they represent a condition where the async operation succeeded and returned zero results. The empty state treatment is the most variable across the application because it must be context-specific. The standardized treatment requires three elements: a **contextual illustration** (a themed SVG illustration specific to the domain — empty accounts, empty formulas, empty entities), **next-step guidance** (a one-sentence explanation of why the state is empty and what the user can do), and a **create-first CTA** (a primary button initiating the first-record creation flow).

For the accounts page (`/accounts`, `useAccounts`), the empty state displays an illustration of an empty workspace with the text "No accounts found — add your first account to get started" and a "Create Account" button. For the ontology entity browser (`/context/ontology/entities`, `useEntities`), the empty state reads "No entities match your search — try adjusting filters or create a new entity" with both "Clear Filters" and "Create Entity" actions. Every route with a list-fetching hook must define its empty state components alongside its skeleton and loaded states.

| Error Category | HTTP Status | Primary UI Element | Recovery Action | Example Hook |
|---------------|-------------|-------------------|-----------------|--------------|
| Network | 0 / Timeout | Retry button + offline badge | Automatic retry with backoff | `useAccounts`, `useExtractionJob` |
| Permission | 403 | Upgrade prompt / contact admin | Tier upgrade or admin request | `useBenchmarks`, `useTenants` |
| Not Found | 404 | Navigation suggestions + create CTA | Navigate to list or create resource | `useEntities` (detail view) |
| Validation | 422 | Inline errors + form summary | Fix fields and resubmit | `useFormulas`, `useOntologySchema` |
| System | 500+ | Incident reference code | Contact support with reference | `useSystemHealth` |
| Empty | 200 (zero results) | Contextual illustration + create CTA | Create first record or adjust filters | `useAccounts`, `useVariables` |

---

## 5.3 Optimistic Update Patterns

Optimistic updates improve perceived performance by mutating the UI state immediately — before the server confirms the operation — and reconciling with the server response asynchronously. This pattern applies exclusively to user-initiated mutations with predictable outcomes: creating a record (the new record appears in the list instantly), updating a field (the edited value renders before the PATCH resolves), and deleting a record (the record vanishes from the list immediately). In the Fabric 4L frontend, optimistic updates are currently nonexistent: no hook implements the pattern, and Contract 2.6 (UI State Progression) explicitly flags the absence of optimistic update patterns as a gap in its compliance matrix.

### 5.3.1 Applicability Criteria

Optimistic updates are enabled only when three conditions are met. First, the mutation outcome must be **predictable from the request payload**: a formula name update submitted via `useFormulas` (PATCH l3) can be optimistically rendered because the new name is known at submission time. Second, the mutation must be **user-initiated**: optimistic updates do not apply to background sync operations, polling-driven refetches, or SSE-driven state changes. Third, the hook must have a **verified backend connection**: optimistic updates without a real mutation endpoint are indistinguishable from mock data manipulation — they create false confidence and hide integration gaps.

Based on these criteria, the 26 green hooks are candidates for optimistic update implementation. The `useIntegrations` hook (GET l4, POST l4, DELETE l4), for example, supports optimistic deletion: when the user removes an integration, the integration card vanishes from the list immediately, and the DELETE request proceeds in the background. The `useModels` hook (DELETE l3, POST l3, GET l3) supports optimistic creation and deletion for model registry entries. The `useValuePacks` hook (POST l3, GET l3) supports optimistic application of value packs to workspace contexts.

### 5.3.2 Rollback Strategy

The rollback strategy defines what happens when an optimistic update encounters a server-side failure. The sequence is: (1) the UI state updates optimistically on mutation submission; (2) the mutation executes; (3) on failure, the UI state reverts to its pre-mutation form; (4) an error toast displays with the failure reason. This sequence is implemented via React Query's `onMutate` / `onError` / `onSettled` lifecycle.

The `useApiShared` wrapper standardizes this lifecycle. Every mutation-enabled hook receives a pre-configured mutation helper that handles the optimistic cache update, rollback, and toast notification. The wrapper stores the previous cache snapshot in `onMutate`, restores it via `queryClient.setQueryData` in `onError`, and invalidates the affected query in `onSettled` to trigger a background refetch. The toast notification uses the error category (from Section 5.2 taxonomy) to determine its content: a network error produces "Connection lost — changes reverted," a validation error produces "Changes could not be saved — [field-level message]," and a system error produces "Something went wrong — changes reverted. Reference: [code]."

### 5.3.3 Conflict Resolution

Conflict resolution addresses the edge case where the optimistic state diverges from the server response on background refetch. This occurs when the server applies side effects that the optimistic update could not predict: auto-generated fields (timestamps, computed values), concurrent modifications by other users, or trigger-driven state changes. The resolution strategy is **server-wins**: when the background refetch returns data that differs from the optimistic projection, the refetched data replaces the optimistic state unconditionally. The UI flashes briefly (a 200ms opacity transition) to signal the reconciliation, but no user confirmation is required. The server is the source of truth; the optimistic update was a performance illusion that served its purpose during the latency window.

The `useOntologySchema` hook illustrates this pattern. When a user creates a new ontology type via POST `/v1/ontology/schema/types`, the type appears in the schema list optimistically. On refetch, the server may return additional fields — `created_at`, `updated_at`, or computed `property_count` — that were not in the optimistic projection. The refetched record replaces the optimistic entry, and the UI reconciles silently.

### 5.3.4 Current Gaps: Mock-Data Hooks

Two RED hooks present a special barrier to optimistic update adoption: `useSources` (useSources.ts, DELETE l1, GET l1, POST l1, PUT l1, `is_mock: true`) and `useOpportunities` (useOpportunities.ts, GET l4, `is_mock: true`). These hooks return mock data arrays constructed in-module rather than data fetched from the backend. Optimistic updates are impossible against mock data because there is no real mutation endpoint to reconcile against. Attempting to implement optimistic updates on these hooks would produce a double illusion: the user sees instant UI changes that appear to persist, but nothing reaches the server, and on page refresh all changes vanish.

The remediation path for these hooks is integration-first: the mock data is replaced with real `apiClient` calls to the designated endpoints (L1 ingestion layer for `useSources`, L4 agent layer for `useOpportunities`), and optimistic update patterns are added only after the hook achieves green status. Until that integration is complete, these hooks render static mock data with no mutation surface and no optimistic update capability. The skeleton system (Section 5.1) still applies: even mock-data routes render a skeleton during their simulated loading phase, making the facade nature of the data explicit to the user.

---

## 5.4 Async State Machine

Every async component in the Fabric 4L frontend must implement a unified five-state machine: idle, loading, success, error, and refreshing. The current codebase violates this requirement comprehensively. Contract 2.6 (UI State Progression) found that while most hooks use React Query, several do not — and even among React Query hooks, the `isLoading`, `isError`, `isSuccess`, and `isFetching` flags are not consistently consumed by their rendering components. Hooks such as `useAuth`, `useComposition`, and `useGraphCanvas` (`data_source_color: unknown`, no error handling) render as if data is always available, producing undefined-reference crashes when queries fail or return empty.

### 5.4.1 Five-State Definition

The **idle** state occurs before any fetch has been initiated. This is the initial mount state for components that load lazily or conditionally. A component in idle renders nothing (not even a skeleton) unless the fetch trigger is user-initiated — for example, a search component that fetches only after the user enters a query. For route-level components, idle is a transient state that transitions immediately to loading on mount.

The **loading** state occurs while the initial fetch is in flight. This state renders the component's registered skeleton (from Section 5.1). The loading state persists until the query resolves with data or error. For the 16 green routes, this state is backed by a real network request to a verified endpoint (GET l4 for `useAccounts`, GET l6 for `useBenchmarks`, POST l3 for `useGraphQuery`). For the 51 red routes, the loading state is currently absent because mock data resolves synchronously — the remediation adds an artificial delay (300ms minimum) to mock-data hooks so the loading state is visible, making the facade nature of the route detectable by users and test suites.

The **success** state occurs when the query resolves with data. This state renders the component's loaded UI. Success is not a terminal state: it can transition to refreshing on background refetch or to error if a subsequent refetch fails.

The **error** state occurs when the query fails with an error. This state renders the component's error fallback UI, categorized by the taxonomy in Section 5.2. The error state is recoverable: a retry action transitions back to loading, and a background refetch triggered by window-focus or interval polling can transition to success if the backend has recovered.

The **refreshing** state occurs when a background refetch is in flight while the component is already in success. This state does not replace the loaded content with a skeleton; instead, it renders a subtle loading indicator (a spinning icon in the header bar or a pulsing border on the content region) while preserving the existing data. This pattern is critical for data that updates frequently: the `HealthMonitor` component (`useSystemHealth`, GET l4) refreshes on an interval, and the `useExtractionResults` hook polls job status until completion.

### 5.4.2 State Transition Enforcement

Every async component must handle all five states explicitly. This is enforced by the `AsyncWrapper` component (Section 5.5), which acts as a gate: if a child component does not provide render props or slots for all five states, `AsyncWrapper` renders a development-mode warning and falls back to the generic treatment for missing states. In production, missing state handlers render the generic fallback to prevent crashes.

The state transition diagram is:

```
                    +---------+
                    |  idle   |
                    +----+----+
                         | mount / trigger
                         v
                    +---------+
              +---->| loading |<----+
              |     +----+----+     | retry
              |          |          |
         error|          | success  | error (refetch)
              |          v          |
              |     +---------+     |
              +-----+ success |-----+
                    +----+----+
                         | refetch
                         v
                    +---------+
                    |refreshing|
                    +---------+
```

### 5.4.3 Refresh Patterns

Three refresh patterns are available, and each async component declares which patterns it supports via the `AsyncWrapper` `refreshMode` prop.

**Pull-to-refresh** is available on touch-enabled devices for scrollable content regions. The user pulls the content area downward beyond a threshold (60px), triggering a full query invalidation and refetch. This pattern applies to list views: `Accounts` (`/accounts`, `useAccounts`), `EntityBrowser` (`/context/ontology/entities`, `useEntities`), and `FormulaList` (`/context/formulas`, `useFormulas`).

**Background refetch** is automatic and invisible. React Query's `refetchOnWindowFocus` and `refetchInterval` options handle this pattern. Hooks with rapidly changing data — `useExtractionResults` (polling job status), `useSystemHealth` (GET l4, interval refresh), and `useJobStream` (GET l2, streaming updates) — configure `refetchInterval` to their domain-appropriate cadence. Background refetch always transitions through the refreshing state, never through loading, to preserve content stability.

**Manual refresh** is user-triggered via a refresh button in the component header bar. Every list and detail view must expose this button. The button triggers `queryClient.invalidateQueries` for the component's query key, forcing a refetch. Manual refresh is the recovery path from error states: the error fallback UI includes a "Try Again" button that invokes the same invalidate-and-refetch sequence.

| State | Visual Treatment | User Interaction | Transition Trigger |
|-------|-----------------|------------------|-------------------|
| Idle | None (transparent) | None | Component mount, user trigger |
| Loading | Skeleton (full/component) | None | Query initiated |
| Success | Loaded content | Full interactivity | Data resolved |
| Error | Error fallback UI | Retry button, navigation | Query failed |
| Refreshing | Subtle spinner on loaded content | Full interactivity (stale data) | Background refetch |

---

## 5.5 Component Library Requirements

The async state strategy requires four foundational components that do not currently exist in the Fabric 4L frontend. These components are the building blocks for every async UI pattern described in Sections 5.1 through 5.4. They must be implemented before any route-level skeleton or error work begins, as they provide the infrastructure that route components consume.

### 5.5.1 AsyncWrapper Component

`AsyncWrapper` is a generic container component that handles loading, error, empty, and refreshing states for any child component. It accepts a React Query result object (`UseQueryResult<T, Error>`) and renders the appropriate state UI based on the result's status flags. The component signature is:

```typescript
interface AsyncWrapperProps<T> {
  query: UseQueryResult<T, Error>;
  skeleton: React.ReactNode;
  empty?: React.ReactNode;
  error?: (error: Error, retry: () => void) => React.ReactNode;
  refreshMode?: 'none' | 'pull' | 'background' | 'manual' | 'all';
  children: (data: T, isRefreshing: boolean) => React.ReactNode;
}

function AsyncWrapper<T>({
  query,
  skeleton,
  empty,
  error,
  refreshMode = 'manual',
  children,
}: AsyncWrapperProps<T>): React.ReactElement;
```

`AsyncWrapper` subscribes to `query.status` and renders `skeleton` when `status === 'pending'`, renders `error?.(query.error, query.refetch)` when `status === 'error'`, renders `empty` (or a generic empty state) when `status === 'success' && !query.data`, and renders `children(query.data, query.isFetching)` when `status === 'success' && query.data`. The `refreshMode` prop configures which refresh patterns are active: pull-to-refresh wraps the content in a touch handler, background enables `refetchInterval` passthrough, and manual renders a refresh button in the header slot.

Every async route component must wrap its content in `AsyncWrapper`. The `Accounts` component, for example, wraps its `useAccounts` query result, passing `<AccountsSkeleton />` as the skeleton prop and `(data, isRefreshing) => <AccountsTable data={data} isRefreshing={isRefreshing} />` as the children render prop.

### 5.5.2 ErrorBoundary Component

`ErrorBoundary` is a React class component (error boundaries require class components) that catches unhandled errors thrown during rendering, in lifecycle methods, or in constructors of the entire subtree below it. It displays a fallback UI and logs the error to the monitoring service. The component catches errors that escape the `AsyncWrapper` error handling — typically programming errors (undefined property access, invalid React element returns) or errors in non-async code paths.

The `ErrorBoundary` renders a system error fallback (Section 5.2.5) with an incident reference code, a "Reload Page" button, and a support contact link. It logs the error stack, component stack, and reference code to the monitoring endpoint via `POST /v1/telemetry/error`. The boundary is mounted at the route level in `App.tsx`, wrapping each route's component export, and at the page-section level for complex pages with independently loading regions.

### 5.5.3 DataTable Skeleton

`DataTableSkeleton` is a specialized skeleton component for table-based layouts. It renders column-aligned shimmer placeholders matching the declared column headers and row count. The component accepts a column definition array and generates placeholder rows with cell widths proportional to each column's declared `width` or `minWidth`.

```typescript
interface DataTableSkeletonProps {
  columns: Array<{ key: string; header: string; width?: number | string }>;
  rowCount?: number;
  className?: string;
}
```

The `DataTableSkeleton` is used by the variable registry (`/settings/data/variables`, `useVariables`), the accounts table (`/accounts`, `useAccounts`), and any other route rendering tabular data. The column-aligned shimmer preserves the table's horizontal layout during loading, preventing column-width flicker when the real data arrives.

### 5.5.4 Form Skeleton

`FormSkeleton` is a specialized skeleton component for form-based layouts. It renders field-aligned shimmer placeholders matching the form's field layout: input fields render as rounded rectangles matching expected input heights, textareas render as taller rectangles, and select fields render with a chevron-icon placeholder. The component accepts a field definition array and generates placeholders in the correct vertical sequence with appropriate spacing.

```typescript
interface FormSkeletonProps {
  fields: Array<{
    type: 'input' | 'textarea' | 'select' | 'checkbox' | 'radio-group';
    label: string;
    lines?: number;
  }>;
  className?: string;
}
```

The `FormSkeleton` is used by the platform settings form (`/settings/system/settings`, `usePlatformSettings`), the formula builder (`/context/formulas/new`, `useFormula`), and any creation or edit form. The field-aligned shimmer preserves the form's vertical rhythm during loading, preventing input-field position shift when the real form renders.

### 5.5.5 Implementation Priority

The four library components must be implemented in the following order: `AsyncWrapper` first (it is the dependency for all route-level async work), `ErrorBoundary` second (it provides the safety net), then `DataTableSkeleton` and `FormSkeleton` in parallel (they are leaf components consumed by `AsyncWrapper`). The implementation is a prerequisite for Pass 1 skeleton work on the 16 green routes: no green-route skeleton ticket is assignable until `AsyncWrapper` is available in the component library.

| Component | Type | Depends On | Used By | Priority |
|-----------|------|-----------|---------|----------|
| `AsyncWrapper` | Generic container | React Query | All async routes | **1 — Foundation** |
| `ErrorBoundary` | Class component | Monitoring service | Route wrappers, section wrappers | **2 — Safety** |
| `DataTableSkeleton` | Specialized skeleton | None | Table views (`useAccounts`, `useVariables`) | **3 — Parallel** |
| `FormSkeleton` | Specialized skeleton | None | Form views (`usePlatformSettings`, `useFormula`) | **3 — Parallel** |

---

## 5.6 Integration with Contract 2.6 (UI State Progression)

Contract 2.6 requires that URL be the primary navigation mechanism, Zustand stores be typed, and server state reside in React Query. The contract compliance audit found 70% adherence: routing and store typing pass, but some server state lives outside React Query. The skeleton system, error taxonomy, optimistic update patterns, and async state machine defined in this chapter directly address the 30% gap. Every async component that adopts `AsyncWrapper` moves its server state fully into React Query. Every hook that migrates to `useApiShared` standardizes its error handling and query-key management. The 17 unknown-category routes — `/context/agents` (`useWorkflows`), `/context/formulas/:formulaId` (`useFormula`), `/context/ingestion/jobs` (`useIngestion`) — graduate to full Contract 2.6 compliance when they complete hook integration and adopt the async state patterns specified here.

The three missing contracts identified in Track C — API Boundary Contract, Type Synchronization Contract, and Hook Architecture Contract — are prerequisites for sustainable UI state management. The API Boundary Contract standardizes the error shapes that the Section 5.2 taxonomy consumes. The Hook Architecture Contract mandates the `useApiShared` wrapper and the optimistic update patterns from Section 5.3. Until these contracts are ratified and enforced, the UI/UX component strategy operates as a voluntary standard, implemented green-route by green-route through code review enforcement rather than architectural constraint. The ratification of these contracts must be treated as a blocking dependency for red-route integration work.
