# 1. Integration Contract Specification

## 1.1 Purpose and Scope

### 1.1.1 The API Boundary Contract as Foundational Agreement

The API Boundary Contract defines the complete set of rules, mappings, and guarantees governing every byte exchanged between the Fabric 4L React frontend and the DIL backend. It specifies which backend endpoints each frontend hook consumes, how request and response shapes are validated, what happens when the network or server fails, and how loading states progress from initial fetch to cached render. This document is the first of six design briefs because every subsequent brief — hook architecture, route recovery, testing strategy, CI/CD pipeline, and migration plan — depends on the contracts established here.

The current state demonstrates the consequences of operating without this contract. The frontend exposes 154 routes with tiered navigation and role-based access control, presenting a visually complete application. The Track A audit found that only 16 of 84 authenticated routes (10.4%) have verified live backend integration. The remaining 68 authenticated routes render hardcoded mock data, generic redirects, or empty surfaces — an 81% facade rate. Track B found 244 backend DIL endpoints with only 8 connected to frontend hooks (3.3%), leaving 236 orphan endpoints — a 96.7% orphan rate. These figures indicate a systemic absence of contractual agreement between frontend and backend teams about who owns which integration surface.

### 1.1.2 Scope: 244 DIL Endpoints and the 96.7% Orphan Gap

This specification covers all 244 DIL endpoints identified in the Track B OpenAPI analysis across six architectural layers. The scope includes the 8 currently connected endpoints (which this document formalizes and extends) and the 236 orphan endpoints (which this document assigns to frontend hooks in priority order). The 96.7% orphan gap must be addressed through a tiered mapping strategy: Priority 1 endpoints unblock core user workflows, Priority 2 endpoints enable knowledge-layer functionality, and Priority 3 endpoints complete the platform surface.

The scope extends beyond endpoint-to-hook assignment. It includes the type generation pipeline that ensures frontend TypeScript definitions never drift from backend Zod schemas. It specifies the error boundary hierarchy that converts HTTP status codes into actionable UI error types. It defines the loading state priority order that every async component must declare. And it establishes the governance process — including CI enforcement gates and the Facade Budget metric — that prevents the integration gap from recurring.

### 1.1.3 Reference to Canonical and Missing Contracts

The Track C contract gap audit identified six canonical contracts from CONTRACT.md sections 2.1 through 2.6, of which only two (2.2 DB Session and Isolation, 2.3 Middleware and Auth Flow) have been ratified. The remaining four contracts (2.1 Tenant Context Propagation at 60% compliance, 2.4 Tool Invocation Boundary at 30%, 2.5 Agent Output Shape at 40%, 2.6 UI State Progression at 70%) are in proposed status with compliance gaps that this specification addresses by defining the boundary layer at which those contracts must operate.

More critically, the Track C audit identified three missing contracts that this specification directly creates:

1. **API Boundary Contract** (this document, Sections 1.1-1.5) — standardizes error handling, pagination, filtering, and retry policies across all 47 frontend hooks.
2. **Type Synchronization Contract** (Section 1.3) — mandates automated OpenAPI-to-TypeScript generation with CI gates that fail builds when schemas drift.
3. **Hook Architecture Contract** (implicit throughout) — standardizes React Query patterns, distinguishes queries from mutations, and defines optimistic update behavior.

## 1.2 Endpoint-to-Hook Mapping Registry

### 1.2.1 Registry Structure and Ownership Model

The mapping registry assigns every DIL endpoint to a specific frontend hook with clear ownership semantics. Each entry contains: the endpoint path and method, the assigned hook name, the priority tier (1/2/3), the target component surface, the current status (CONNECTED, PLANNED, ORPHAN), and the acceptance criteria defining mapping completion. The registry follows a one-endpoint-per-primary-hook rule: a single endpoint must have one owning hook that manages its query key, cache invalidation, error handling, and loading state. Related endpoints within the same domain may share a hook family (e.g., `useWorkflows` as the parent hook with `useWorkflowStatus`, `useWorkflowEvents`, and `useWorkflowControl` as specialized children).

The following table summarizes the 50+ Priority 1 and 2 endpoint mappings by domain:

| Domain | Orphan Endpoints | Priority | Target Hook(s) | Target Component(s) |
|--------|-----------------|----------|----------------|---------------------|
| Accounts | 16 | 1 | useAccounts, useAccountDetail, useAccountSearch, useAccountSync | Accounts.tsx, CRM integration pages |
| Workflows | 9 | 1 | useWorkflows, useWorkflowStatus, useWorkflowEvents, useWorkflowControl | AgentWorkflows.tsx |
| Health | 12 | 1 | useSystemHealth, useHealthHistory, useHealthAlerts | HealthMonitor.tsx |
| Ontology | 14 | 2 | useOntologySchema (expand) | OntologyEditor.tsx, EntityBrowser.tsx |
| Checkpoints | 8 | 2 | useCheckpoints (new) | AgentWorkflows.tsx |
| ValuePacks | 9 | 3 | useValuePacks (expand) | ValuePacks.tsx |
| Model Registry | 7 | 3 | useModels (expand) | MyModels.tsx |
| Integrations | 6 | 3 | useIntegrations (expand) | Integrations.tsx |
| Formulas | 5 + 10 gov | 3 | useFormulas, useFormulaVersions | FormulaBuilder.tsx, FormulaList.tsx |
| Graph | 3 | 3 | useGraphQuery, useSubgraph | GraphExplorer.tsx |
| Value Trees | 2 | 3 | useValueTree | ValueTreeExplorer.tsx |
| Tenants | 5 | 3 | useTenants | PlatformSettings.tsx |
| Users | 5 | 3 | useUsers (new) | PermissionsAdmin.tsx |
| Ground Truth | 13 | 3 | useProvenanceTrail (expand) | DecisionTrace.tsx |

The registry prioritizes domains by user impact and technical dependency. Accounts, Workflows, and Health form Priority 1 because they unblock daily user workflows. Ontology and Checkpoints form Priority 2 because they enable the knowledge layer and agent recovery features. The remaining 180+ endpoints distribute across Priority 3 by functional domain.

### 1.2.2 Priority 1: 16 Account/CRM Endpoints

The Accounts domain presents the most extreme example of the orphan problem: 16 backend endpoints for account listing, search, filtering, synchronization, and CRM integration have no corresponding frontend hook consumption. The existing `useAccounts` hook in `useAccounts.ts` has a green data-source classification and consumes GET and POST endpoints on Layer 4, but the Track B audit reveals these do not map to the actual `/v1/accounts` DIL endpoints. The following endpoints must be mapped:

- `GET /v1/accounts` — List Accounts (mapped to `useAccounts`)
- `GET /v1/accounts/filters` — Get Filter Options (mapped to `useAccounts`)
- `POST /v1/accounts/search` — Search Accounts (mapped to new `useAccountSearch`)
- `POST /v1/accounts/sync` — Sync Accounts (mapped to new `useAccountSync`)
- `GET /v1/accounts/sync-status` — Get Sync Status All (mapped to `useAccountSync`)
- `GET /v1/accounts/{account_id}` — Get Account (mapped to new `useAccountDetail`)
- `GET /v1/accounts/{account_id}/activity` — Get Account Activity (mapped to `useAccountDetail`)
- `POST /v1/accounts/{account_id}/refresh` — Refresh Account (mapped to `useAccountSync`)

The remaining 8 Account endpoints (CRM webhook handlers, bulk operations, and metadata endpoints) follow the same ownership pattern: the four-hook family (`useAccounts`, `useAccountDetail`, `useAccountSearch`, `useAccountSync`) owns all 16 endpoints. Each child hook inherits tenant context propagation and error handling from the shared `useApiShared` base, ensuring consistency with Contract 2.1 and Contract 2.3 compliance.

### 1.2.3 Priority 1: 9 Workflow Endpoints

The Workflows domain has 9 orphan endpoints in Layer 4 (Agents) despite the existence of `useActiveWorkflows` in `useWorkflows.ts`, which carries a green classification. The disconnect occurs because `useActiveWorkflows` consumes only 3 generic Layer 4 endpoints (GET, POST, DELETE) rather than the specific `/v1/workflows` paths. The Track B orphan registry lists the exact endpoints:

- `POST /v1/workflows` — Create Workflow
- `GET /v1/workflows/active` — List Active Workflows
- `GET /v1/workflows/types` — List Available Workflows
- `GET /v1/workflows/{workflow_id}` — Get Workflow Status
- `DELETE /v1/workflows/{workflow_id}` — Cancel Workflow
- `GET /v1/workflows/{workflow_id}/events` — Get Workflow Events
- `POST /v1/workflows/{workflow_id}/pause` — Pause Workflow
- `GET /v1/workflows/{workflow_id}/result` — Get Workflow Result
- `POST /v1/workflows/{workflow_id}/resume` — Resume Workflow

The existing `useWorkflows` hook expands into a four-hook family. `useWorkflows` retains ownership of listing and creation. New hook `useWorkflowStatus` owns `GET /v1/workflows/{workflow_id}` and polling logic for active workflow state. New hook `useWorkflowEvents` consumes the events stream and normalizes payloads into a typed `WorkflowEvent[]` array. New hook `useWorkflowControl` owns pause, resume, and cancel mutations with optimistic updates that immediately reflect state changes in the React Query cache before server confirmation.

### 1.2.4 Priority 1: 12 Health Endpoints

The Health domain spans two tag categories: "Health" (2 endpoints in Layer 3) and "health" (12 endpoints in Layer 4). The Layer 4 health endpoints power HealthMonitor.tsx and are entirely orphan. The existing `useSystemHealth` hook consumes a single GET endpoint on Layer 4 but does not map to the `/v1/health` paths. The 12 Layer 4 health endpoints include:

- `GET /v1/health/detailed` — Get Detailed Health (mapped to `useSystemHealth`)
- `GET /v1/health/badges` — Get Active Badges (mapped to new `useHealthAlerts`)
- `GET /v1/health/websocket` — Get Websocket Status (mapped to `useSystemHealth`)
- `POST /v1/health/badges/dismiss` — Dismiss Badge (mapped to `useHealthAlerts`)
- `POST /v1/health/report-connection-quality` — Report Connection Quality (mapped to `useSystemHealth`)
- `GET /v1/health/components/{component_name}` — Get Component Health (mapped to new `useHealthHistory`)
- `GET /v1/workflows/{workflow_id}/state/schema` through `GET /v1/workflows/{workflow_id}/state/history` — six state-inspector endpoints mapped to `useCheckpoints` conceptually but surfacing within HealthMonitor.tsx as the agent state inspection panel.

The `useSystemHealth` hook expands to consume detailed health and websocket status. New hook `useHealthAlerts` owns badge listing and dismissal. New hook `useHealthHistory` owns per-component health time-series data.

### 1.2.5 Priority 2: 14 Ontology Endpoints

The Ontology domain is unique among Priority 2 mappings because it already has partial connectivity. The `useOntologySchema` hook in `useOntology.ts` carries a green classification and consumes 11 specific ontology endpoints including `GET /v1/ontology/schema`, `POST /v1/ontology/schema/validate`, `POST /v1/ontology/schema/publish`, `POST /v1/ontology/schema/import`, `POST /v1/ontology/schema/types`, and `POST /v1/ontology/schema/relationships`. The Track B audit confirms these as CONNECTED entries.

However, 14 ontology endpoints remain orphan despite the partially connected hook:

- `GET /v1/ontology/entities` — List Entities
- `GET /v1/ontology/relationships/{entity_id}` — Get Relationships
- `GET /v1/ontology/schema/export` — Export Ontology Schema
- `GET /v1/ontology/schema/relationships` — List Type Relationships
- `DELETE /v1/ontology/schema/relationships/{relationship_id}` — Delete Type Relationship
- `GET /v1/ontology/schema/types` — List Ontology Types
- `GET /v1/ontology/schema/types/{type_id}` — Get Ontology Type
- `PUT /v1/ontology/schema/types/{type_id}` — Update Ontology Type
- `DELETE /v1/ontology/schema/types/{type_id}` — Delete Ontology Type
- `POST /v1/ontology/schema/types/{type_id}/properties` — Add Type Property
- `PUT /v1/ontology/schema/types/{type_id}/properties/{property_id}` — Update Type Property
- `DELETE /v1/ontology/schema/types/{type_id}/properties/{property_id}` — Remove Type Property
- `GET /v1/ontology/schema/versions` — List Schema Versions
- `GET /v1/ontology/schema/versions/{version}` — Get Schema Version

The `useOntologySchema` hook expands to consume all 14 orphaned endpoints. The existing hook already implements runtime Zod validation (`OntologyTypeSchema.safeParse`) and cache invalidation (`queryClient.invalidateQueries({ queryKey: QK.ontology.schema() })`). These patterns extend directly to the orphan endpoints. The `useEntities` hook remains separate: the Layer 2 ontology entity endpoint serves schema editing while the Layer 3 entity endpoint serves runtime knowledge graph traversal.

### 1.2.6 Priority 2: 8 Checkpoint Endpoints

The Checkpoint domain contains 8 orphan endpoints in Layer 4 that enable agent resume functionality — a core value proposition of Fabric 4L. The existing `useActiveWorkflows` hook does not consume any checkpoint endpoints. The Track B orphan registry lists:

- `GET /v1/workflows/{workflow_id}/checkpoints` — List Checkpoints
- `GET /v1/workflows/{workflow_id}/checkpoints/{checkpoint_id}/state` — Get Checkpoint State
- `POST /v1/workflows/{workflow_id}/checkpoints/diff` — Compare Checkpoints
- `POST /v1/workflows/{workflow_id}/resume-from-checkpoint` — Resume From Checkpoint

The registry confirms 8 orphan endpoints total for agent state checkpoints. The remaining 4 endpoints (checkpoint creation, deletion, metadata, and restore validation) must be identified during implementation and added to the registry before hook development.

New hook `useCheckpoints` owns all 8 endpoints. It implements a checkpoint-aware mutation pattern: when `resumeFromCheckpoint` is called, the hook first invalidates the target workflow's query key, then invalidates all checkpoint listings for that workflow, and finally triggers a refetch of the workflow status. This three-phase invalidation ensures the UI never displays stale workflow state after a checkpoint resume.

### 1.2.7 Priority 3: Remaining 180+ Endpoints by Domain

Priority 3 encompasses all remaining orphan endpoints organized by functional domain. These endpoints do not unblock daily user workflows but complete the platform surface for administrators and advanced users.

| Domain | Endpoint Count | Target Hook | Target Component |
|--------|---------------|-------------|------------------|
| ValuePacks | 9 | useValuePacks, useApplyValuePack | ValuePacks.tsx |
| Models | 5 + 7 Model Registry | useModels | MyModels.tsx |
| Integrations | 6 | useIntegrations | Integrations.tsx |
| Formulas | 5 + 10 governance | useFormulas, useFormulaVersions | FormulaBuilder.tsx, FormulaList.tsx |
| Graph | 3 | useGraphQuery, useSubgraph | GraphExplorer.tsx |
| Value Trees | 2 | useValueTree | ValueTreeExplorer.tsx |
| Tenants | 5 | useTenants | PlatformSettings.tsx |
| Users | 5 | useUsers (new) | PermissionsAdmin.tsx |
| API Keys | 3 | useApiKeys (new) | PermissionsAdmin.tsx |
| Feature Flags | 5 | usePlatformSettings | PlatformSettings.tsx |
| Tools | 5 | useToolRegistry (new, Contract 2.4) | Unknown |
| Analysis | 5 | useBusinessCase (expand) | BusinessCase.tsx |
| CRM Webhooks | 3 | useAccountSync | Accounts.tsx |
| OIDC SSO | 3 | useAuth (expand) | Login/SSO flow |
| Audit | 2 | useProvenanceTrail | DecisionTrace.tsx |
| System | 3 | useSystemHealth | PlatformSettings.tsx |
| Ground Truth | 13 | useProvenanceTrail (expand) | DecisionTrace.tsx |

Priority 3 assignment follows the principle that domains with existing hooks receive expansion work, while domains with no hook surface receive new hook creation. The Tools domain (5 endpoints) requires special attention because Contract 2.4 (Tool Invocation Boundary) demands a frontend `ToolRegistry` that does not currently exist. The `useToolRegistry` hook is prerequisite to connecting these 5 endpoints and must be implemented as part of Contract 2.4 ratification.

## 1.3 Type Generation Pipeline

### 1.3.1 Backend Zod Schema to OpenAPI to TypeScript

The Type Synchronization Contract (one of three missing contracts identified in Track C) mandates that no frontend TypeScript type for a DIL endpoint may be written by hand. All types must derive from backend Zod schemas through an automated pipeline: backend engineers define request and response shapes using Zod schemas on Pydantic models; FastAPI generates an OpenAPI 3.0 specification at build time; a frontend code-generation step consumes the OpenAPI spec and emits TypeScript interfaces, request functions, and runtime validation code.

The pipeline executes in three phases. Phase 1 occurs at backend build time: FastAPI's native OpenAPI generation produces `openapi.json` containing all 244 endpoint definitions, parameter schemas, request bodies, and response shapes. Phase 2 occurs at a scheduled interval (initially daily, moving to per-merge after stabilization): a frontend script fetches the latest `openapi.json` from backend staging. Phase 3 executes the generator: `openapi-typescript` converts the spec into `src/generated/dil-api.ts` containing literal type unions for enums, strict interface definitions for all DTOs, and discriminated union types for polymorphic responses.

The generated types file exports a single namespace `DIL` that contains all endpoint-specific types. Hooks import from this namespace rather than defining inline types. The `useOntologySchema` hook already demonstrates partial compliance through its runtime `OntologyTypeSchema.safeParse` validation, but the DTO types it validates against must also migrate to the generated namespace.

### 1.3.2 CI Gate: Build Fails on Schema Drift

The type generation pipeline includes a CI gate preventing frontend builds from succeeding when the backend OpenAPI spec changes in ways that break frontend type safety. The gate runs on every pull request touching either backend schemas or the frontend generated types directory.

The gate executes four steps: check out the PR branch and backend staging OpenAPI spec; run the type generator; compare generated output to committed `src/generated/dil-api.ts`; if differences exist and the PR does not include the regenerated file, fail the build with a message listing changed schemas and affected hooks.

The gate also runs an `endpoint_coverage` check counting how many of 244 DIL endpoints have entries in the hook-to-endpoint mapping registry with CONNECTED or PLANNED status. Coverage ratchets upward: 30% at Month 1, 55% at Month 2, 80% at Month 3, and 95% at Month 4. A PR reducing coverage below the current threshold fails.

The following TypeScript configuration block illustrates the generator script:

```typescript
// scripts/generate-api-types.ts
import { execSync } from 'child_process';
import { writeFileSync } from 'fs';
import openapiTS, { astToString } from 'openapi-typescript';

const BACKEND_OPENAPI_URL = process.env.BACKEND_STAGING_URL + '/openapi.json';
const OUTPUT_PATH = './src/generated/dil-api.ts';
const LOCKFILE_PATH = './src/generated/openapi.lock';

async function generateTypes(): Promise<void> {
  const response = await fetch(BACKEND_OPENAPI_URL);
  if (!response.ok) {
    throw new Error(`Failed to fetch OpenAPI spec: ${response.status}`);
  }
  const spec = await response.json();

  const ast = await openapiTS(spec);
  const typesOutput = astToString(ast);

  writeFileSync(OUTPUT_PATH, typesOutput);

  const specHash = execSync(
    'echo -n \'' + JSON.stringify(spec) + '\' | sha256sum'
  ).toString();
  writeFileSync(LOCKFILE_PATH, specHash);

  console.log(`Generated types for ${Object.keys(spec.paths).length} endpoints`);
}

generateTypes().catch((error) => {
  console.error('Type generation failed:', error);
  process.exit(1);
});
```

### 1.3.3 Version-Locking Strategy

Frontend type generation is pinned to backend API version tags rather than tracking the moving target of `main`. The backend repository tags its OpenAPI spec with semantic version identifiers (e.g., `dil-api-v1.3.2`) at every release. The frontend `package.json` specifies the compatible API version range in a custom field:

```json
{
  "dilApi": {
    "version": "^1.3.0",
    "schemaLock": "sha256:a1b2c3d4..."
  }
}
```

When backend teams ship a breaking schema change, they increment the minor or major version. The frontend CI detects version mismatch during scheduled runs and creates an automated PR with regenerated types. Frontend engineers review the automated PR, update hook code affected by breaking type changes, and merge. This version-locking prevents "surprise breakage" where a backend deployment changes a field type and immediately breaks the production frontend.

## 1.4 Error Boundary Behavior

### 1.4.1 HTTP Status Code to UIErrorType Mapping

Every DIL endpoint returns HTTP status codes that the frontend must translate into a typed `UIErrorType` enum. The mapping is deterministic and exhaustive: no status code may fall through to a generic error message. The following table defines the canonical mapping:

| HTTP Status | UIErrorType | User-Facing Message | Required Action |
|-------------|-------------|---------------------|-----------------|
| 401 | AUTH_REQUIRED | "Your session has expired. Please sign in again." | Redirect to /login, clear auth token |
| 403 | PERMISSION_DENIED | "You do not have permission to access this resource." | Render permission error state |
| 404 | NOT_FOUND | "The requested resource was not found." | Render empty state with retry option |
| 409 | CONFLICT | "This resource was modified by another session." | Offer refresh or merge option |
| 422 | VALIDATION_ERROR | "The submitted data contains errors." | Display field-level validation errors |
| 429 | RATE_LIMITED | "Too many requests. Please wait." | Auto-retry after Retry-After header |
| 500 | SYSTEM_ERROR | "An unexpected error occurred. Please try again." | Log to error tracking, retry with backoff |
| 502 | SYSTEM_ERROR | "The service is temporarily unavailable." | Display maintenance banner |
| 503 | SYSTEM_ERROR | "The service is under maintenance." | Display maintenance page |
| 504 | SYSTEM_ERROR | "The request timed out. Please try again." | Retry with increased timeout |

The `UIErrorType` enum lives in the shared types package and is imported by all hooks. The `useApiShared` base hook (used by `useAccounts`, `useFormulas`, and other green hooks per Track C) performs the status-code-to-error-type translation in its response interceptor. Hooks not currently using `useApiShared` — Track C identified `useAuth`, `useComposition`, `useSources`, and others — must migrate to the shared handler for contract compliance.

### 1.4.2 Error Boundary Hierarchy

Error handling operates at three nested levels. Page-level boundaries catch unhandled errors from any child and display a full-page error state. Section-level boundaries catch errors within a logical UI section (e.g., the accounts table within the Accounts page) and display an inline error card. Component-level boundaries catch errors within a single widget and display a compact error indicator.

The hierarchy follows a containment rule: an error caught at section-level never propagates to page-level; an error caught at component-level never propagates to section-level. This prevents a single failing widget from crashing an entire page. The React error boundary implementation uses a shared `<ContractErrorBoundary>` component accepting a `level` prop (`"page"`, `"section"`, `"component"`) and rendering the appropriate error UI.

Each hook in the mapping registry declares its error boundary level. Data-fetching hooks powering entire pages (e.g., `useAccounts`) specify `level: "page"`. Hooks powering widgets (e.g., `useHealthAlerts`) specify `level: "component"`. Hooks powering major sections (e.g., `useWorkflowStatus`) specify `level: "section"`.

### 1.4.3 Retry Policy per Endpoint Category

Retry behavior varies by endpoint category to prevent unnecessary backend load and respect idempotency guarantees.

Idempotent read endpoints (GET, HEAD, OPTIONS on all paths except streams) receive 3 retry attempts with exponential backoff: 1s, 2s, 4s delay.

**Endpoint count scope (source-backed):**
- **Layer 4 only (`value-fabric/layer4-agents/src/api/`)**: **114 endpoints**.
- **Cross-layer platform total (Layers 1-6 API packages)**: **335 endpoints**.

**Counting method:** parsed Python route decorators and counted FastAPI-style HTTP method decorators (`@<router_name>.get/post/put/patch/delete/options/head`) in API modules. For Layer 4, the scan scope was exactly `value-fabric/layer4-agents/src/api/`; for the cross-layer total, the scan covered each layer's primary API package (`layer1-ingestion/src/api`, `layer2-extraction/src/layer2_extraction/api`, `layer3-knowledge/src/api`, `layer4-agents/src/api`, `layer5-ground-truth/src/layer5_ground_truth/api`, `layer6-benchmarks/src/api`).

This category covers read/list/detail/search routes, and graph query endpoints (`POST /v1/query/graph`, `POST /v1/query`) remain classified as idempotent reads because they do not modify server state.

Mutation endpoints (POST, PUT, PATCH, DELETE) receive 1 retry attempt after 2 seconds. This conservative policy prevents duplicate resource creation when a POST times out after the server has already processed it. Approximately 80 endpoints fall into this category. Mutations failing with 409 CONFLICT do not retry; the frontend fetches current state and offers merge resolution.

Stream endpoints (server-sent events, WebSocket connections, streaming analytics) receive 0 retries. When a stream drops, the hook establishes a new connection with fresh parameters. This applies to `GET /v1/workflows/{workflow_id}/events` and `POST /v1/query/graph/stream`. The `useWorkflowEvents` hook implements a connection manager monitoring `EventSource` readyState and reconnecting with exponential backoff only after the previous connection has fully closed.

## 1.5 Loading State Hierarchy

### 1.5.1 Skeleton > Spinner > Cache > Empty State Priority Order

Every async component must declare its loading strategy according to a four-tier priority order. No component may deviate without explicit registry documentation.

Skeleton screens render first, displaying the structural layout — placeholder rectangles for table rows, card shapes for grid items — without data. Skeletons appear when a query has no cached data and is executing for the first time. They provide the best perceived performance because users see page structure immediately. The `useAccounts` hook on its first load displays a skeleton table with 10 placeholder rows.

Spinners appear when skeletons are not implemented (legacy components) or when the operation is a mutation with no structural preview. Spinners must include a text label ("Syncing accounts...") and be positioned within component bounds, never as a full-page overlay unless the operation blocks page navigation.

Cached data appears when a React Query cache entry exists for the current query key, even if stale. The hook returns cached data immediately and triggers a background refetch. The UI displays cached data with a subtle "updating" indicator rather than a loading spinner. This pattern applies to `useOntologySchema` when returning to the ontology editor after navigating away.

Empty states render only when the query has completed successfully and returned an empty result set. Empty states are never loading indicators; they are content states. An empty state includes an icon, a descriptive message ("No accounts match your filters"), and a primary action button when appropriate ("Create your first account").

### 1.5.2 Loading Strategy Declaration in the Contract

Every registry entry includes a `loadingStrategy` field declaring which tiers the hook implements. The field accepts an array in priority order: `["skeleton", "cache", "empty"]` indicates the hook supports skeleton loading, cache fallback, and empty states but not spinners. Hooks must implement at least two tiers; a hook with only one tier fails registry validation.

The Track A hook audit found 11 of 44 hooks carry an `unknown` data-source classification. These hooks typically lack any loading strategy, rendering `null` or unstyled `<div>Loading...</div>` while data loads. The registry mandates all 11 unknown hooks declare and implement a loading strategy before promotion from `unknown` to `green`.

### 1.5.3 Loading State Aggregation for Composed Hooks

Page-level hooks frequently compose multiple domain hooks. The aggregation follows the "weakest link" rule: if any composed hook is in skeleton state, the page renders skeletons for all sections. If all composed hooks have cached data, the page renders from cache with section-level updating indicators. If one hook has loaded while another is still loading, the page renders the loaded section from cache and the loading section from skeleton — never a full-page spinner.

The `useLoadingAggregation` utility hook implements this logic. It accepts a record of `UseQueryResult` objects and returns a single `AggregatedLoadingState`:

```typescript
// src/hooks/useLoadingAggregation.ts
import { UseQueryResult } from '@tanstack/react-query';

export type LoadingTier = 'skeleton' | 'spinner' | 'cache' | 'empty';

export interface AggregatedLoadingState<T> {
  tier: LoadingTier;
  data: Partial<T>;
  isFetching: boolean;
  errors: Error[];
}

export function useLoadingAggregation<T extends Record<string, unknown>>(
  queries: Record<keyof T, UseQueryResult>
): AggregatedLoadingState<T> {
  const entries = Object.entries(queries) as [keyof T, UseQueryResult][];

  const errors = entries
    .filter(([, q]) => q.error)
    .map(([, q]) => q.error as Error);

  const hasInitialLoading = entries.some(([, q]) => q.isLoading && !q.data);
  const allHaveData = entries.every(([, q]) => q.data !== undefined);
  const isFetching = entries.some(([, q]) => q.isFetching);

  const data = entries.reduce((acc, [key, q]) => {
    if (q.data !== undefined) acc[key] = q.data;
    return acc;
  }, {} as Partial<T>);

  if (hasInitialLoading) {
    return { tier: 'skeleton', data, isFetching: true, errors };
  }

  if (allHaveData && !isFetching) {
    const allEmpty = entries.every(([, q]) =>
      Array.isArray(q.data) ? q.data.length === 0 : false
    );
    return { tier: allEmpty ? 'empty' : 'cache', data: data as T, isFetching: false, errors };
  }

  return { tier: allHaveData ? 'cache' : 'skeleton', data: data as T, isFetching, errors };
}
```

## 1.6 Contract Governance

### 1.6.1 RFC Process for New Endpoints

No backend endpoint may ship to production without a corresponding frontend hook specification. This rule applies retroactively to all 244 existing endpoints (receiving specifications through this document) and prospectively to all new endpoints created after contract ratification. The RFC process enforces the rule through a two-repository workflow:

When a backend engineer proposes a new endpoint, they create an RFC in the shared `rfcs/` directory. The RFC must include: endpoint path and method, Zod request and response schemas, OpenAPI operation ID, proposed owning frontend hook name, target component surface, loading strategy declaration, error boundary level, and priority tier. The RFC receives review from at least one frontend engineer who validates that the hook name does not conflict with existing hooks and that schema shapes are compatible with planned UI designs.

Without an RFC-approved hook specification, the backend endpoint cannot merge to `main`. Without the endpoint on `main`, the OpenAPI spec does not include it. Without the OpenAPI spec entry, the type generator does not produce types. And without types, no frontend engineer can implement the hook. This chain creates a structural guarantee that every new endpoint has a planned frontend surface before it exists.

### 1.6.2 CI Enforcement Gates

The contract specifies three CI gates running on every pull request affecting frontend hooks or backend endpoints.

The `detect_mock_data` gate scans all hook files for hardcoded data, `mock` imports, or inline JSON literals not originating from `apiClient` calls. Hooks classified as `red` — `useOpportunities` and `useSources` are the two confirmed red hooks — fail this gate until mock data is replaced with live endpoint calls. The gate also flags `yellow` hooks for review without failing the build.

The `endpoint_coverage` gate counts the percentage of 244 DIL endpoints appearing in the mapping registry with CONNECTED or PLANNED status. Coverage ratchets upward monthly: 30% at Month 1, 55% at Month 2, 80% at Month 3, 95% at Month 4. A PR reducing coverage below the current threshold fails. A PR adding registry entries without corresponding hook implementations also fails — the entry must include a link to the implementing hook file and line number.

The `type_sync_check` gate verifies that `src/generated/dil-api.ts` matches the current backend OpenAPI spec. It runs the type generator and compares output. If the committed generated file differs from freshly generated output, the gate fails with instructions to run `npm run generate:api-types` and commit the result. This gate is the technical enforcement mechanism for the Type Synchronization Contract.

### 1.6.3 The Facade Budget

The Facade Budget is the single metric tracking integration health. It measures the percentage of authenticated routes (84) that are not green — routes rendering hardcoded data, mock content, redirects, or having no backend connection. Track A found the current facade rate at 81%. The contract mandates quarterly reduction:

| Quarter | Max Facade Rate | Target Green Routes | Min Green Routes |
|---------|----------------|--------------------|--------------------|
| Q0 (Current) | 81% | 16 | 16 |
| Q1 | 40% | 50+ | 50 |
| Q2 | 30% | 59+ | 59 |
| Q3 | 20% | 68+ | 68 |
| Q4 | 5% | 80+ | 80 |

The Q1 target of 40% is achievable because the 50 Priority 1 and 2 endpoint mappings directly enable 34+ additional authenticated routes to transition from red or unknown to green. The Q4 target of 5% allows approximately 4 routes to remain non-green due to feature flags for unreleased functionality or admin-only diagnostic pages.

The Facade Budget serves as the primary recovery metric reported to engineering leadership. Every two weeks, automated CI produces a facade report counting green routes by querying the mapping registry and cross-referencing against the Track A route matrix. The report lists newly green routes, regressed routes, and the current facade percentage. A regression triggers an alert because it indicates either a backend endpoint deprecation without frontend notification or a hook migration that broke an existing connection.

Endpoint coverage and the Facade Budget move in tandem but are not identical. Endpoint coverage measures backend-to-frontend connectivity (target: 95% of 244 endpoints). The Facade Budget measures frontend route functionality (target: 95% of 84 authenticated routes green). A project could achieve 95% endpoint coverage with a high facade rate if connected endpoints power components rather than routes. The contract requires both metrics to meet their targets before integration recovery is complete.
