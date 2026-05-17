# Spec: Workflow Test Coverage — 7-Step Value Pilot

## Status
Ready for review — pending user confirmation

---

## Problem Statement

The 7-step Value Pilot workflow (`apps/web/src/workflow/`) is the primary customer-facing surface of Value Fabric. It is the path every user takes to produce a business case. Despite this, 5 of 7 workflow pages have **zero test coverage**, the persisted Zustand store (`workflowStore.ts`) has zero tests, and the shared layout shell (`WorkflowLayout.tsx`) has zero tests.

The test coverage audit (2026-05-12) grades `apps/web` at **B/74** overall but flags **45% line coverage** against an 80% target, with the workflow module as the largest zero-coverage surface. The `canProceed` gate logic in the store — which controls whether a user can advance through the workflow — is entirely untested.

All infrastructure to write these tests already exists: Vitest + Testing Library + MSW + `renderWithRouter` + `createTestQueryClient` are in place and used by the two existing workflow tests (`ValueCase.test.tsx`, `ProspectSetup.submission.test.tsx`).

---

## Scope

### In scope
- `apps/web/src/workflow/store/workflowStore.ts` — unit tests for all actions and canProceed logic
- `apps/web/src/workflow/components/WorkflowLayout.tsx` — rendering and navigation tests
- `apps/web/src/workflow/pages/Intelligence.tsx` — page tests
- `apps/web/src/workflow/pages/AIModel.tsx` — page tests
- `apps/web/src/workflow/pages/DriverTree.tsx` — page tests
- `apps/web/src/workflow/pages/Evidence.tsx` — page tests
- `apps/web/src/workflow/pages/Calculator.tsx` — page tests

### Out of scope
- `apps/web/src/value-pilot/` — separate prototype module, not in the canonical router
- Backend service tests (separate initiative)
- E2E Playwright tests (separate initiative)
- Modifying any source files under test

---

## Confirmed State (as of 2026-05-17)

| File | Lines | Existing tests |
|---|---|---|
| `workflow/store/workflowStore.ts` | 82 | None |
| `workflow/components/WorkflowLayout.tsx` | 101 | None |
| `workflow/pages/Intelligence.tsx` | 122 | None |
| `workflow/pages/AIModel.tsx` | 151 | None |
| `workflow/pages/DriverTree.tsx` | 220 | None |
| `workflow/pages/Evidence.tsx` | 121 | None |
| `workflow/pages/Calculator.tsx` | 33 | None |
| `workflow/pages/ValueCase.tsx` | 197 | `ValueCase.test.tsx` |
| `workflow/pages/ProspectSetup.tsx` | 81 | `ProspectSetup.submission.test.tsx` |

**Test infrastructure available:**
- `src/test/mocks/server.ts` — MSW Node server
- `src/test/mocks/handlers.ts` — shared API handlers
- `src/test-utils.tsx` — `renderWithRouter`, `createTestQueryClient`, `createWrapper`
- `test/setup.ts` — global Vitest setup with MSW lifecycle and `jest-dom`
- `vitest.config.ts` — coverage via v8, jsdom environment

**Canonical test patterns to follow:**
- `workflow/pages/ValueCase.test.tsx` — store mock via `vi.mock('../store/workflowStore', ...)`, hook mock via `vi.mock('@/hooks/useCalculators', ...)`
- `workflow/pages/ProspectSetup.submission.test.tsx` — mutation mock, navigation mock, MSW handler override

---

## Requirements

### R1 — Store unit tests (`workflowStore.test.ts`)

**R1.1** — Test initial state: all fields match `initialState` before `initSession` is called.

**R1.2** — Test `initSession`: sets a non-null `sessionId` matching the `wf_` prefix pattern; sets `currentStep` to 0; does not carry over state from a prior session.

**R1.3** — Test `reset`: returns all fields to `initialState`.

**R1.4** — Test `setCurrentStep`: stores the provided step index.

**R1.5** — Test `setProspect` / `setEnrichedEntities` / `setSelectedTreeId` / `setGeneratedCaseId` / `setWorkflowContext`: each action updates only its target field.

**R1.6** — Test canProceed conditions for all 7 steps (steps 0-6) by asserting the store field values that gate each step:
- Step 0: `prospect` is null cannot proceed; `prospect.companyId` is set can proceed.
- Step 1: `enrichedEntities` is empty cannot proceed; at least one entity present can proceed.
- Step 2: no selected hypothesis state cannot proceed; hypothesis selected can proceed.
- Step 3: `selectedTreeId` is null cannot proceed; `selectedTreeId` is set can proceed.
- Step 4: always passable (optional step).
- Step 5: scenario result is null cannot proceed; result set can proceed.
- Step 6: `generatedCaseId` is null cannot proceed; `generatedCaseId` is set can proceed.

**R1.7** — Tests must not access `localStorage` directly; interact only through the store API.

---

### R2 — WorkflowLayout tests (`WorkflowLayout.test.tsx`)

**R2.1** — Renders `children` inside the layout without crashing.

**R2.2** — Renders the sidebar navigation with all 7 workflow step labels: Prospect, Intelligence, AI Model, Driver Tree, Evidence, Calculator, Value Case.

**R2.3** — Highlights the active step based on the current route (use `MemoryRouter` with `initialEntries`).

**R2.4** — Collapse/expand toggle: clicking the collapse button changes the sidebar collapsed state.

**R2.5** — Theme toggle: clicking the theme button switches between light and dark mode indicators.

**R2.6** — Renders the top bar breadcrumb correctly for a workflow path vs. a non-workflow path.

---

### R3 — Intelligence page tests (`Intelligence.test.tsx`)

**R3.1** — Renders loading state while the intelligence query is in flight.

**R3.2** — Renders enriched entities when the API returns data; each entity name is visible.

**R3.3** — Renders an empty state when no entities are returned.

**R3.4** — Renders an error state when the API call fails (use MSW handler override to return 500).

**R3.5** — Selecting an entity calls the store's entity-update action.

---

### R4 — AIModel page tests (`AIModel.test.tsx`)

**R4.1** — Renders loading state while hypotheses are being fetched.

**R4.2** — Renders hypothesis cards when the API returns data.

**R4.3** — Renders an empty state when no hypotheses are returned.

**R4.4** — Selecting a hypothesis updates the store's selected hypothesis state.

**R4.5** — Deselecting a hypothesis removes it from the selected set.

---

### R5 — DriverTree page tests (`DriverTree.test.tsx`)

**R5.1** — Renders loading state while driver trees are being fetched.

**R5.2** — Renders available driver trees when the API returns data.

**R5.3** — Renders an empty state when no trees are available.

**R5.4** — Selecting a tree calls `setSelectedTreeId` with the correct ID.

**R5.5** — Renders the tree visualization when a tree is selected (node labels visible).

---

### R6 — Evidence page tests (`Evidence.test.tsx`)

**R6.1** — Renders loading state while evidence is being fetched.

**R6.2** — Renders evidence matches when the API returns data; each match's claim text is visible.

**R6.3** — Renders an empty state when no evidence is returned.

**R6.4** — Renders an error state when the API call fails.

**R6.5** — The continue action is available regardless of evidence count (optional step).

---

### R7 — Calculator page tests (`Calculator.test.tsx`)

**R7.1** — Renders the calculator form with baseline value and variable inputs.

**R7.2** — Renders loading state while scenario data is being fetched.

**R7.3** — Submitting the form with valid inputs calls the calculation API and stores the result.

**R7.4** — Renders the scenario result (ROI value) after a successful calculation.

**R7.5** — Renders a validation error when required fields are empty on submit.

---

## Acceptance Criteria

| ID | Criterion |
|---|---|
| AC-01 | `pnpm --dir apps/web test` passes with zero failures after all test files are added |
| AC-02 | `workflowStore.test.ts` covers all 7 step-gate conditions (steps 0-6) |
| AC-03 | Each of the 5 new page test files covers: loading state, success state, empty/error state |
| AC-04 | `WorkflowLayout.test.tsx` covers: render, active step highlight, collapse toggle |
| AC-05 | No test file imports from `@/api/legacy` or calls raw `apiClient` directly (per DESIGN.md ban) |
| AC-06 | All store mocks use `vi.mock('../store/workflowStore', ...)` pattern (not direct store mutation) |
| AC-07 | All API mocks use MSW handlers (either from `src/test/mocks/handlers.ts` or inline `server.use(...)` overrides) |
| AC-08 | No source files are modified — test files only |
| AC-09 | Frontend line coverage increases from 45% baseline (measurable via `pnpm --dir apps/web test:coverage`) |
| AC-10 | Each test file is co-located with its source file and follows the `<ComponentName>.test.tsx` naming convention |

---

## Implementation Approach

1. **Read existing patterns** — study `workflow/pages/ValueCase.test.tsx` and `workflow/pages/ProspectSetup.submission.test.tsx` to confirm mock patterns, provider wrappers, and MSW usage before writing any new tests.

2. **Write `workflowStore.test.ts`** — pure unit tests, no rendering. Import `useWorkflowStore` and call actions via `act`. Cover initial state, all actions, and all 7 step-gate conditions.

3. **Write `WorkflowLayout.test.tsx`** — use `MemoryRouter` with `initialEntries` to control the active route. Mock `useWorkflowStore` for `currentStep`. Test render, sidebar labels, active highlight, collapse toggle, theme toggle, breadcrumb.

4. **Write `Intelligence.test.tsx`** — mock `useWorkflowStore`. Use MSW to control API responses (success, empty, 500 error). Assert loading, success, empty, and error state transitions.

5. **Write `AIModel.test.tsx`** — same pattern as Intelligence. Mock store. Use MSW for hypothesis API. Assert hypothesis card rendering and selection state changes.

6. **Write `DriverTree.test.tsx`** — mock store. Use MSW for tree API. Assert tree list rendering, selection, and tree visualization node labels.

7. **Write `Evidence.test.tsx`** — mock store. Use MSW for evidence API. Assert evidence match rendering, empty state, error state, and that the continue action is always available.

8. **Write `Calculator.test.tsx`** — mock store. Use MSW for calculation API. Assert form rendering, submission, result display, and validation error on empty submit.

9. **Run `pnpm --dir apps/web test`** — verify zero failures across all existing tests plus new tests.

10. **Run `pnpm --dir apps/web test:coverage`** — record line coverage delta and confirm improvement from 45% baseline.
