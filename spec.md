# Spec: Sprint 4 — Frontend Launch Paths and Demo-Grade UX

## Status
Ready for implementation

---

## Problem Statement

The frontend has several coherence gaps that make it unsuitable for a launch demo:

1. **Harness Runs UI** — The tab and detail sheet are built, but the Playwright contract spec is in TDD red phase (`test.fail()` guards). Specific interaction gaps (approve/reject mutation shape, polling behavior, async registry calls) must be confirmed and fixed before the guards can be removed.

2. **AIModel.tsx** — The page is 100% hardcoded static data (manufacturing hypotheses for a fictional "Meridian" account). There is no connection to backend workflow state. A live status banner must be added without replacing the demo content.

3. **BusinessCase.tsx** — Export gating exists but users cannot tell *why* export is blocked. There is no visual distinction between degraded, pending-review, and validated states. An "internal draft only" badge is absent.

4. **Auth/session** — `services/api` uses `tenant_required` (JWT via `TenantRequired`); `services/layer4-agents` uses `require_authenticated` (shared `RequestContext`). Both are already protected. The frontend `AuthContext` uses OIDC with an httpOnly cookie. No structural auth wiring is needed for the demo; the gap is that `AIModel.tsx` and the workflow path bypass auth entirely because they use static data.

5. **Admin/static data pages** — `BenchmarkPolicies`, `VariableRegistry`, `FormulaGovernance`, and `ValuePacks` already call real L3/L6 API hooks. They need graceful empty/error banners so the demo does not look broken when the backend returns empty or errors.

6. **Playwright coverage** — `test.fail()` must be removed from the harness contract spec only after gaps are fixed. New mocked unit tests are needed for BusinessCase trust states and AIModel status rendering. Targeted Playwright gap-fill for end-to-end state visibility.

---

## Requirements

### W1 — Harness Runs UI: close contract spec gaps

| ID | Requirement |
|---|---|
| W1.1 | Confirm the canonical gate-decision route is `POST /api/v1/agents/harness/gates/{gate_id}/decide` and the payload field is `decision` (not `status`). Fix any mismatch in `harnessApi` or the contract spec fixture. |
| W1.2 | Confirm `useDecideGate` mutation awaits the registry call correctly; fix if the mutation fires but the backend returns 422 on invalid transitions. |
| W1.3 | Confirm polling: non-terminal runs refetch on the `POLL_INTERVALS.workflows` interval; terminal runs do not. Fix if the `refetchInterval` callback is broken. |
| W1.4 | Remove `test.fail()` from `e2e/contracts/harness-runs.spec.ts` only after W1.1–W1.3 are verified stable. |
| W1.5 | `e2e/journeys/j25-harness-run-lifecycle.spec.ts` must continue to pass (or remain correctly skipped when `PLAYWRIGHT_BACKEND_URL` is absent). |

### W2 — AIModel.tsx: live workflow status banner

| ID | Requirement |
|---|---|
| W2.1 | Add a `WorkflowStatusBanner` component (or inline section) at the top of `AIModel.tsx` that reads `runId` from URL params if the route already supports it, or falls back to the most recent harness run for the current account. |
| W2.2 | The banner must display: run status (`queued` / `running` / `waiting_for_human` / `failed` / `cancelled` / `completed`), current state/step if available, last-updated timestamp, and gate/validation state if present. |
| W2.3 | The banner must have loading, error, and empty states (no run found). |
| W2.4 | The static Meridian/manufacturing hypotheses remain untouched. Add a small annotation below the hypothesis list: `"Hypotheses are demo data — backend model generation is not yet wired."` |
| W2.5 | No full-screen rewrite. The banner is additive; existing layout and hypothesis cards are unchanged. |
| W2.6 | TypeScript must pass for the new banner component and its props. |

### W3 — BusinessCase.tsx: trust status row

| ID | Requirement |
|---|---|
| W3.1 | Add a compact status row near the header/export controls that renders one of: `Degraded`, `Pending Review`, `Validated`, `Export Blocked`, or `Export Ready` based on the business case's validation state and enrichment flags. |
| W3.2 | When `degraded` (i.e., `customer_facing_allowed === false` or `degraded_reason` is set): show `Degraded` badge + `Internal draft only` badge, disable export, show tooltip/help text: `"LLM, validation, or evidence enrichment was incomplete. Human review required."` |
| W3.3 | When `pending_review` (status is `pending` or `needs_review`): show `Pending Review` badge + `Internal draft only` badge, disable export, show tooltip/help text: `"Claims require validation or human approval before export."` |
| W3.4 | When `validated` (status is `approved`/`active`/`completed` and `document_url` is present): show `Validated` badge, enable export if all other existing export requirements pass. |
| W3.5 | When validation failed or evidence is insufficient: show `Export Blocked` badge, disable export. |
| W3.6 | The existing `isApproved && hasExportDocument` export gate logic is preserved; the new status row is additive. |
| W3.7 | No full redesign. The status row is a targeted addition; existing layout, ROI hero card, and sections are unchanged. |

### W4 — Auth/session: demo-path verification only

| ID | Requirement |
|---|---|
| W4.1 | Document the auth path alignment: `services/api` (`tenant_required` / JWT) and `services/layer4-agents` (`require_authenticated` / `RequestContext`) are both protected and do not need structural changes for the demo. |
| W4.2 | Verify the frontend `AuthContext` OIDC flow reaches both services correctly in the demo environment. No code change required unless a concrete 401/403 failure is found. |
| W4.3 | Defer full enterprise auth UX polish (invite flows, role management UI, session expiry UX) to a future sprint. |

### W5 — Admin pages: graceful empty/error states

| ID | Requirement |
|---|---|
| W5.1 | `BenchmarkPolicies`, `VariableRegistry`, `FormulaGovernance`, and `ValuePacks` must render a visible, non-broken empty state when the API returns an empty list. Use the existing `EmptyState` component pattern. |
| W5.2 | Each page must render a visible error banner (not a blank screen) when the API call fails. Use the existing `QueryState` / `ErrorBoundary` pattern. |
| W5.3 | If verification against the demo backend reveals a hook calling a route that does not exist (e.g., `GET /graph/formulas/approvals/pending` returning 404), add a `"Data unavailable in this environment"` inline notice rather than wiring a new backend route. |
| W5.4 | No new backend routes are created as part of this work packet. |

### W6 — Playwright and test coverage

| ID | Requirement |
|---|---|
| W6.1 | Remove `test.fail()` from `e2e/contracts/harness-runs.spec.ts` only after W1.1–W1.3 are confirmed. |
| W6.2 | Add mocked Vitest unit tests for `BusinessCase.tsx` covering: degraded badge renders, pending-review badge renders, validated badge renders, internal-draft-only badge renders, export disabled when degraded/pending/failed, export enabled only when validated and `document_url` present. |
| W6.3 | Add mocked Vitest unit tests for `AIModel.tsx` status banner covering: queued/running/waiting-for-human/failed/cancelled/completed status rendering, loading state, error state, empty state (no run). |
| W6.4 | Add or update a Playwright spec covering: BusinessCase page shows degraded/pending-review/validated status row; export is blocked for degraded or pending-review; export is available for validated. |
| W6.5 | `j25-harness-run-lifecycle.spec.ts` must continue to pass (or remain correctly skipped). Backend-integrated j25 runs in CI when `PLAYWRIGHT_BACKEND_URL` is set. |
| W6.6 | The existing full regression suite count must not increase (no net-new failing tests). |

---

## Acceptance Criteria

1. `e2e/contracts/harness-runs.spec.ts` has no `test.fail()` guards and all AC-01 through AC-17 pass.
2. `AIModel.tsx` renders a live workflow status banner sourced from `useHarnessRun` or `useHarnessRuns`; static hypotheses and layout are unchanged.
3. `BusinessCase.tsx` renders a status row with correct badge and export state for degraded, pending-review, and validated cases.
4. `BenchmarkPolicies`, `VariableRegistry`, `FormulaGovernance`, and `ValuePacks` render non-broken empty and error states.
5. TypeScript passes (`pnpm --dir apps/web build` or `tsc --noEmit`).
6. All new Vitest unit tests pass (`pnpm --dir apps/web test`).
7. Playwright contract and regression suite does not gain new failures.
8. No mock-only production UI: every page that shows data either fetches it from a real API or clearly labels it as demo/unavailable.
9. Export/publish buttons respect validation state (disabled when degraded, pending, or evidence-insufficient).
10. Pending/failed/degraded statuses are visible to the user.

---

## Implementation Approach

Steps are ordered by dependency. Each step is independently verifiable.

1. **Audit harness gate-decision contract** — Read `harnessApi.decideGate()` in `apps/web/src/api/harness.ts` and compare the payload field name (`decision` vs `status`) against the backend `GateDecisionRequest` model in `services/layer4-agents/src/harness/api_models.py`. Fix any mismatch. Confirm `useDecideGate` in `useHarness.ts` awaits correctly.

2. **Verify harness polling** — Confirm `useHarnessRun` and `useHarnessGates` `refetchInterval` callbacks behave correctly for terminal vs non-terminal states. Fix if broken.

3. **Remove `test.fail()` from harness contract spec** — Only after steps 1–2 are confirmed. Run `pnpm --dir apps/web test` and the Playwright contract spec to verify AC-01 through AC-17 pass.

4. **Add `WorkflowStatusBanner` to `AIModel.tsx`** — Create a small component (or inline section) that accepts a `runId?: string` prop, calls `useHarnessRun(runId)` or `useHarnessRuns({ limit: 1 })` as fallback, and renders the status badge, current state, last-updated timestamp, and gate/validation state. Add loading/error/empty states. Add the demo annotation below the hypothesis list.

5. **Add trust status row to `BusinessCase.tsx`** — Derive `validationState` from the existing `businessCase` data (status, `case_metadata` enrichment flags, `degraded_reason`). Render the compact status row with the correct badge and export-gate behavior per W3.2–W3.5. Preserve all existing export logic.

6. **Harden admin pages** — For each of `BenchmarkPolicies`, `VariableRegistry`, `FormulaGovernance`, `ValuePacks`: verify the hook's API call against the demo backend. Add `EmptyState` for empty lists and an error banner for API failures. Add `"Data unavailable in this environment"` notices where routes are confirmed missing.

7. **Add Vitest unit tests for BusinessCase trust states** — Cover all badge/export combinations per W6.2. Mock `useBusinessCase` at the module boundary.

8. **Add Vitest unit tests for AIModel status banner** — Cover all status values and loading/error/empty states per W6.3. Mock `useHarnessRun` at the module boundary.

9. **Add/update Playwright spec for BusinessCase status row** — Cover degraded, pending-review, and validated end-to-end states per W6.4. Use mocked API routes (no backend required).

10. **Run full validation** — `pnpm --dir apps/web test`, `pnpm --dir apps/web build`, Playwright contract suite. Confirm regression count has not increased.

---

## Files Expected to Change

| File | Change |
|---|---|
| `apps/web/src/api/harness.ts` | Fix gate-decision payload field if mismatched |
| `apps/web/src/hooks/useHarness.ts` | Fix polling or mutation if broken |
| `apps/web/src/workflow/pages/AIModel.tsx` | Add `WorkflowStatusBanner` section + demo annotation |
| `apps/web/src/workflow/pages/AIModel.test.tsx` | Add status banner unit tests |
| `apps/web/src/pages/BusinessCase.tsx` | Add trust status row |
| `apps/web/src/pages/BusinessCase.test.tsx` | Add trust state unit tests |
| `apps/web/src/pages/admin/BenchmarkPolicies.tsx` | Add empty/error states |
| `apps/web/src/pages/admin/VariableRegistry.tsx` | Add empty/error states |
| `apps/web/src/pages/admin/FormulaGovernance.tsx` | Add empty/error states |
| `apps/web/src/pages/ValuePacks.tsx` | Add empty/error states |
| `apps/web/e2e/contracts/harness-runs.spec.ts` | Remove `test.fail()` guards |
| `apps/web/e2e/` (new or updated spec) | BusinessCase status row Playwright coverage |

---

## Out of Scope

- Full enterprise auth UX polish (invite flows, role management, session expiry UX)
- Replacing static Meridian/manufacturing hypotheses with real backend data
- New backend routes for admin pages
- Redesigning any existing page layout
- Expanding Playwright coverage beyond the gaps listed in W6
