# Spec: Harness UI — Playwright E2E Coverage

## Status
Draft — pending user confirmation

## Problem Statement

The backend harness domain (`services/layer4-agents/src/harness/`) defines `HarnessRun`, `HarnessCheckpoint`, `HumanGate`, and `ClaimValidationResult` models with a full state machine. However:

1. **No frontend UI exists** for harness runs. `AgentWorkflows` (`/context/agents`) has no "Harness Runs" tab, no `HarnessRunDetail` component, and no `useHarnessRuns` hook.
2. **No API routes are registered** for `/v1/harness/*` in `services/layer4-agents/src/api/routers.py`.
3. **No E2E coverage** exists for any harness-specific flow.

This spec defines the Playwright E2E test suite to be written **TDD-first** to drive and regression-protect the Harness UI implementation. Tests are expected to fail until the UI is wired.

---

## Scope

### In scope
- `apps/web/e2e/contracts/harness-runs.spec.ts` — mocked contract tests (primary deliverable)
- `apps/web/e2e/journeys/j25-harness-run-lifecycle.spec.ts` — backend-integrated smoke spec (optional, tagged `@backend`)
- `apps/web/e2e/pages/AgentWorkflowsPage.ts` — page object for the AgentWorkflows page (Harness Runs tab)
- `apps/web/e2e/pages/HarnessRunDetailPage.ts` — page object for the HarnessRunDetail panel
- Fixture data for `HarnessRun`, `HarnessCheckpoint`, `HumanGate`, and `ClaimValidationResult`

### Out of scope
- Implementing the frontend components (`HarnessRunDetail`, `useHarnessRuns`, etc.)
- Implementing the backend API routes (`/v1/harness/*`)
- Modifying existing E2E specs
- Auth/session lifecycle tests (covered by `j0-auth-session.spec.ts`)
- Broad governance tests unrelated to harness runs

---

## Existing Infrastructure to Reuse

| Asset | Path | Usage |
|---|---|---|
| Contract test base | `e2e/fixtures/contract-test.ts` | Base `test` fixture with API harness auto-installed |
| Journey fixture | `e2e/helpers/journey-fixture.ts` | `journeyTest`, `authedPage`, `addMocks` |
| API harness | `e2e/helpers/api-harness.ts` | `MockEndpoint`, `installApiHarness`, `isLiveMode` |
| Auth helpers | `e2e/fixtures/auth-helpers.ts` | `seedAuthState`, `clearAuthState` |
| Tier helpers | `e2e/fixtures/tier-helpers.ts` | `setUserTier`, `clearUserTier` |
| Account helpers | `e2e/fixtures/account-helpers.ts` | `setSelectedAccount`, `TEST_ACCOUNTS` |
| Existing page objects | `e2e/pages/` | `AppShellPage` for navigation |
| Playwright config | `apps/web/playwright.config.ts` | `contracts` project (Chromium, mocked) |
| Run command | `pnpm test:e2e:contracts` | Runs the `contracts` project |

---

## API Contract Assumptions

The following API routes are assumed to be implemented (or mocked) before tests pass:

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/agents/harness/runs` | List harness runs (paginated) |
| `GET` | `/api/v1/agents/harness/runs/:runId` | Get single run detail |
| `GET` | `/api/v1/agents/harness/runs/:runId/checkpoints` | List checkpoints for a run |
| `GET` | `/api/v1/agents/harness/runs/:runId/gates` | List human gates for a run |
| `POST` | `/api/v1/agents/harness/gates/:gateId/decide` | Approve or reject a gate (gate-scoped, not run-scoped) |

These paths follow the existing `l4` prefix convention (`/agents` → Layer 4).

---

## Fixture Data Shapes

Derived from `services/layer4-agents/src/harness/models.py`.

### `HarnessRun` fixture
```typescript
{
  id: "run_abc123",
  tenant_id: "tenant-test-001",
  account_id: "acct-meridian-001",
  workflow_type: "business_case_generation",
  initiated_by: "user",
  status: "running",           // "queued" | "running" | "waiting_for_human" | "failed" | "completed" | "cancelled"
  current_state: "VALIDATE_CLAIMS", // HarnessState enum value
  trace_id: "trace_xyz789",
  created_at: "2025-01-15T10:00:00Z",
  updated_at: "2025-01-15T10:05:00Z"
}
```

### `HarnessCheckpoint` fixture
```typescript
{
  id: "chk_001",
  run_id: "run_abc123",
  tenant_id: "tenant-test-001",
  state_name: "GENERATE_HYPOTHESES",
  state_payload: { hypotheses_count: 4 },
  input_hash: "abc123def456",
  output_hash: "789xyz012",
  tool_calls: [],
  created_at: "2025-01-15T10:02:00Z"
}
```

### `HumanGate` fixture (pending)
```typescript
{
  id: "gate_001",
  run_id: "run_abc123",
  tenant_id: "tenant-test-001",
  gate_type: "approve_claims",
  status: "pending",           // "pending" | "approved" | "rejected" | "modified" | "expired"
  decision_by: null,
  decision_reason: null,
  created_at: "2025-01-15T10:04:00Z",
  decided_at: null
}
```

### `ClaimValidationResult` fixture
```typescript
{
  id: "cvr_001",
  tenant_id: "tenant-test-001",
  claim_id: "claim_001",
  validation_state: "needs_review",  // "passed" | "failed" | "needs_review" | "insufficient_evidence"
  evidence_refs: ["ev_001"],
  confidence: 0.72,
  trust_score: 0.68,
  validator: "agent",
  reason: "Confidence below threshold",
  created_at: "2025-01-15T10:03:00Z"
}
```

---

## Requirements

### R1 — AgentWorkflows Harness Runs Tab

- `AgentWorkflows` at `/context/agents` must render a "Harness Runs" tab alongside the existing "Workflow Dashboard", "Whitespace Analysis", and "Business Cases" tabs.
- The tab must be visible to users with `advanced` or `admin` tier.
- Selecting the tab must render the harness runs list.

### R2 — Harness Runs List

- The list must fetch from `GET /api/v1/agents/harness/runs`.
- Each row must display: run ID, workflow type, status badge, current state, and created date.
- Status badges must use the existing `StatusBadge` primitive.
- Loading, empty, and error states must use the existing `QueryState` component.

### R3 — Run Selection → HarnessRunDetail

- Clicking a run row must open a `HarnessRunDetail` panel (right-rail drawer, consistent with `WorkflowDetail`).
- The detail panel must display: run ID, trace ID, workflow type, status, current state.

### R4 — State Timeline / Checkpoints

- The detail panel must render a timeline of `HarnessCheckpoint` records fetched from `GET /api/v1/agents/harness/runs/:runId/checkpoints`.
- Each checkpoint must show: state name, created timestamp, and input hash (truncated).
- The timeline must be ordered chronologically (oldest first).

### R5 — Human Gates

- When a run has `status: "waiting_for_human"`, the detail panel must fetch gates from `GET /api/v1/agents/harness/runs/:runId/gates`.
- Pending gates must render an approve button and a reject button.
- Terminal gates (approved/rejected/expired) must render as read-only with their decision status.

### R6 — Approve / Reject Actions

- Clicking "Approve" must call `POST /api/v1/agents/harness/gates/:gateId/decide` with `{ status: "approved", decision_reason?: string, human_override: false }`.
- Clicking "Reject" must call the same endpoint with `{ status: "rejected", decision_reason?: string, human_override: false }`.
- `decision_by` is **not** sent by the client — it is derived server-side from the authenticated user context.
- After a successful decision, the gate status must update in the UI (optimistic update or refetch).
- Buttons must be disabled while the mutation is pending.

### R7 — Polling Behaviour

- Non-terminal runs (`status` not in `completed | failed | cancelled`) must poll the run detail at `POLL_INTERVALS.workflows` (5 s).
- Terminal runs must not poll (no `refetchInterval`).
- The polling pattern must follow `useActiveWorkflows` as the reference implementation.

### R8 — Empty / Loading / Error States

- Loading: skeleton or spinner consistent with `QueryState` loading pattern.
- Empty: "No harness runs found." message with sub-message.
- Error: error message consistent with `QueryState` error pattern.
- All three states must be testable via mocked API responses.

---

## Acceptance Criteria

| ID | Criterion |
|---|---|
| AC-01 | `AgentWorkflows` renders a "Harness Runs" tab |
| AC-02 | Harness Runs tab is visible for `advanced` and `admin` tiers |
| AC-03 | Harness runs list renders from mocked `GET /api/v1/agents/harness/runs` |
| AC-04 | Each run row shows ID, workflow type, status badge, current state |
| AC-05 | Clicking a run opens `HarnessRunDetail` panel |
| AC-06 | Detail panel shows run metadata (ID, trace ID, type, status, state) |
| AC-07 | Checkpoints render in chronological order from mocked fixture |
| AC-08 | Pending human gate renders approve and reject buttons |
| AC-09 | Approve button calls `POST /api/v1/agents/harness/gates/:gateId/decide` with `{ status: "approved" }` |
| AC-10 | Reject button calls `POST /api/v1/agents/harness/gates/:gateId/decide` with `{ status: "rejected" }` |
| AC-11 | Buttons are disabled while mutation is pending |
| AC-12 | Terminal gate renders as read-only (no approve/reject buttons) |
| AC-13 | Non-terminal run triggers polling (network request observed within 6 s) |
| AC-14 | Terminal run does not trigger polling after initial load |
| AC-15 | Loading state renders skeleton/spinner |
| AC-16 | Empty state renders "No harness runs found." |
| AC-17 | Error state renders error message |
| AC-18 | `@backend` smoke spec lists real runs and opens one detail (when `PLAYWRIGHT_BACKEND_URL` is set) |

---

## Implementation Approach

Steps are ordered for TDD: write tests first, then implement to make them pass.

1. **Add fixture data** — Create `apps/web/e2e/fixtures/harness-fixtures.ts` with typed `HarnessRun`, `HarnessCheckpoint`, `HumanGate`, and `ClaimValidationResult` factory functions and canned fixture sets (running run, terminal run, run with pending gate, run with approved gate, empty list, error response).

2. **Add page objects** — Create `apps/web/e2e/pages/AgentWorkflowsPage.ts` with locators for the Harness Runs tab, run rows, and run row click action. Create `apps/web/e2e/pages/HarnessRunDetailPage.ts` with locators for the detail panel, checkpoint timeline, gate approve/reject buttons, and gate status display.

3. **Export page objects** — Add both new page objects to `apps/web/e2e/pages/index.ts`.

4. **Write mocked contract spec** — Create `apps/web/e2e/contracts/harness-runs.spec.ts` using `import { test, expect } from '../fixtures/contract-test'`. Cover all AC-01 through AC-17. Mock all `/api/v1/agents/harness/*` routes via `page.route()`. Use `setUserTier(page, 'admin')` and `seedAuthState(page)` in `beforeEach`. Use `clearUserTier` and `clearAuthState` in `afterEach`. The gate decide mock must use the gate-scoped route `POST /api/v1/agents/harness/gates/:gateId/decide` with `DecideHumanGateRequest` payload (`status`, optional `decision_reason`, `human_override`).

5. **Write backend-integrated smoke spec** — Create `apps/web/e2e/journeys/j25-harness-run-lifecycle.spec.ts` using `journeyTest`. Tag all tests `@backend`. Cover AC-18. Guard with `journeyTest.skip(!isLiveMode(), 'PLAYWRIGHT_BACKEND_URL is required for j25 backend-integrated Harness smoke tests')`. Add a `TODO(j25)` comment: once `/v1/harness/*` endpoints are merged and in backend-integrated CI, replace the skip guard with `requireBackendOrThrow()` to match `j11`/`j16`/`j19`.

6. **Register harness mock routes in API harness** — Add default mock entries for `/api/v1/agents/harness/runs` (empty list) to `apps/web/e2e/helpers/api-harness.ts` `DEFAULT_MOCKS` so pages that incidentally hit this endpoint don't break existing tests.

7. **Verify guard compliance** — Run `pnpm test:e2e:guard` to confirm no critical E2E skip violations are introduced.

8. **Run contract suite** — Run `pnpm test:e2e:contracts` (or `playwright test --project=contracts e2e/contracts/harness-runs.spec.ts`). All tests are expected to **fail** (red phase) until the UI is implemented.

---

## File Deliverables

```
apps/web/e2e/
├── contracts/
│   └── harness-runs.spec.ts               ← primary mocked spec (new)
├── journeys/
│   └── j25-harness-run-lifecycle.spec.ts  ← @backend smoke spec (new)
├── fixtures/
│   └── harness-fixtures.ts                ← typed fixture factories (new)
├── pages/
│   ├── AgentWorkflowsPage.ts              ← page object for /context/agents (new)
│   ├── HarnessRunDetailPage.ts            ← page object for detail panel (new)
│   └── index.ts                           ← updated to export new page objects
└── helpers/
    └── api-harness.ts                     ← updated DEFAULT_MOCKS for /harness/runs
```

---

## Verified Assumptions

Both assumptions from the initial spec have been confirmed against the codebase.

### Assumption 1 — `POST .../decide` payload shape ✅ Resolved

The backend has no `/decide` route yet. When built, the canonical contract is:

**Endpoint:** `POST /v1/harness/gates/{gate_id}/decide`

**Request payload** (client sends):
```typescript
type DecideHumanGateRequest = {
  status: "approved" | "rejected" | "modified";
  decision_reason?: string;
  human_override?: boolean;
  metadata?: Record<string, unknown>;
}
```

**Response** (server creates — `decision_by` is derived from auth context, never trusted from client):
```typescript
type HumanGateDecision = {
  gate_id: string;
  run_id: string;
  tenant_id: string;
  status: "approved" | "rejected" | "modified";
  decision_by: string;           // server-derived from auth context
  decision_reason?: string;
  decided_at: string;
  human_override: boolean;
}
```

Note the route is `POST /v1/harness/gates/{gate_id}/decide` (gate-scoped, not run-scoped). The frontend call chain is: `useDecideGate` → `harnessApi.decideGate` → `apiClient.post('l4', '/harness/gates/{id}/decide', payload)`.

The mocked contract spec (`harness-runs.spec.ts`) must be updated to use this route pattern and payload shape.

### Assumption 2 — `@backend` smoke test skip behaviour ✅ Resolved

`j25` uses `journeyTest.skip(!isLiveMode(), ...)` — graceful skip while the backend contract is incomplete. This is intentional and temporary.

**Promotion rule:** Once `/v1/harness/*` endpoints are merged and included in backend-integrated CI, `j25` must be promoted to `requireBackendOrThrow()` to match `j11`/`j16`/`j19`. A `TODO(j25)` comment marks the promotion trigger in the spec file.

---

## Risk / Follow-up

- **Backend API routes not yet registered**: `/v1/harness/*` routes do not exist in `routers.py`. The backend-integrated spec will fail until these are added. The mocked spec is fully self-contained and can run immediately.
- **Frontend components not yet implemented**: `HarnessRunDetail`, `useHarnessRuns`, and the "Harness Runs" tab do not exist. All tests will fail (red phase) until the UI is built. This is intentional — the spec drives the implementation.
- **Polling test reliability**: Polling assertions (AC-13, AC-14) use network request observation with a 6 s window. If CI is slow, the timeout may need adjustment.
- **`j25` skip → throw promotion**: Tracked by `TODO(j25)` in the spec file. Trigger: Harness backend endpoints merged and in backend-integrated CI.

