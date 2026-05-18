# Spec: FE-C1 + FE-C2 — Imperative Navigation & URL Concatenation Remediation

**Contract:** §2.6 UI State Management  
**Deadline:** 2026-05-30  
**Deprecation IDs:** DEP-IMPERATIVE-NAV-009, DEP-URL-CONCAT-010  
**ESLint rules:** `fabric-contracts/no-imperative-navigation`, `fabric-contracts/no-url-concatenation`

---

## Problem Statement

Two contract clusters remain open against the frontend:

- **FE-C1:** `HypothesesTab.tsx` uses `useNavigate()` directly (bypassing the canonical `useNavigation()` abstraction) to navigate with router `location.state`.
- **FE-C2:** Nine sites across six files construct UI route strings via template-literal concatenation instead of using centralized route helpers.

Both patterns are flagged as `error` by the `eslint-plugin-fabric-contracts` rules. The canonical infrastructure (`navigationService.ts`, `useNavigation()`, `navHelpers.ts`, `workspaceRoutes.ts`) already exists — this work closes the remaining violations by migrating call sites and filling the one gap in the abstraction (router state support).

---

## Violation Inventory

### FE-C1 — Imperative Navigation

| File | Line | Violation |
|---|---|---|
| `apps/web/src/pages/intelligence/HypothesesTab.tsx` | 160, 427 | `useNavigate()` + `navigate({ pathname, search }, { state: {...} })` |

### FE-C2 — URL Concatenation

| File | Lines | Pattern |
|---|---|---|
| `apps/web/src/shell/router.tsx` | 150 | `` navigateTo(`/accounts/${accountId}/intelligence/signals`) `` |
| `apps/web/src/shell/router.tsx` | 165 | `` <Navigate to={`/studio/${selectedAccountId}/${targetTab}`} /> `` |
| `apps/web/src/components/workspace/DriverTreeShell.tsx` | 19 | `` to:`/drivers/${accountId}/${t.key}` `` |
| `apps/web/src/components/workspace/CalculatorShell.tsx` | 14 | `` to:`/calculator/${accountId}/${t.key}` `` |
| `apps/web/src/pages/deliverables/ExecutiveView.tsx` | 51, 56 | `` href/to:`/deliverables/cases/${bc.case_id}` `` |
| `apps/web/src/pages/deliverables/TechnicalView.tsx` | 54, 59 | same |
| `apps/web/src/pages/deliverables/CFOView.tsx` | 77, 82 | same |
| `apps/web/src/features/intelligence-workspace/IntelligenceWorkspaceTabs.tsx` | 19 | `` to:`/accounts/${accountId}/intelligence/${tab.id}` `` |
| `apps/web/src/components/layout/Layout.tsx` | 324, 351 | `resolvedPath + "/"` (active-state detection) |

---

## Requirements

### R1 — Extend `useNavigation()` with typed router state support

`useNavigation()` must expose a `navigateTo(path, options?)` signature where `options` accepts a `state` field typed as `Record<string, unknown>`. Existing callers that pass no options must continue to work unchanged.

```ts
navigateTo(path: string, options?: { state?: Record<string, unknown> }): void
```

### R2 — Migrate `HypothesesTab.tsx` to `useNavigation()`

Replace `useNavigate()` + direct `navigate()` call with `useNavigation()` + `navigateTo(path, { state })`. The router state payload (`hypothesisId`, `accountId`, `tenantId`, `evidenceIds`, `valueModelId`, `treeId`, `createdId`, `conversionStatus`) must be passed via the `state` option. Search params (`tree_id`, `value_model_id`) are constructed via `URLSearchParams` and appended to the path string before calling `navigateTo`.

### R3 — Fix `shell/router.tsx` URL concatenation (2 sites)

- Line 150: Replace `` `/accounts/${accountId}/intelligence/signals` `` with `workspacePath(accountId, 'signals')` from `workspaceRoutes.ts`.
- Line 165: Replace `` `/studio/${selectedAccountId}/${targetTab}` `` with `getStatePath('studio', { accountId: selectedAccountId })` + tab segment via `buildPath`, or add a `studioPath(accountId, tab)` helper to `accountRouting.ts`.

### R4 — Fix `DriverTreeShell.tsx` and `CalculatorShell.tsx`

Replace inline tab `to` template literals with `buildPath` from `navigationService.ts`:

```ts
// DriverTreeShell
to: buildPath('/drivers/:accountId/:tab', { accountId, tab: t.key })

// CalculatorShell
to: buildPath('/calculator/:accountId/:tab', { accountId, tab: t.key })
```

### R5 — Create `deliverableRoutes.ts` and migrate three view files

Create `apps/web/src/navigation/deliverableRoutes.ts`:

```ts
import { getStatePath } from "@/navigation/navigationService";

export const deliverableRoutes = {
  businessCaseDetail: (caseId: string) =>
    getStatePath("business-case-detail", { caseId }),
  businessCaseList: () =>
    getStatePath("business-cases"),
};
```

Replace all `` `/deliverables/cases/${bc.case_id}` `` and `"/deliverables/cases"` literals in `ExecutiveView.tsx`, `TechnicalView.tsx`, and `CFOView.tsx` with `deliverableRoutes.businessCaseDetail(bc.case_id)` and `deliverableRoutes.businessCaseList()`.

### R6 — Fix `IntelligenceWorkspaceTabs.tsx`

Replace `` `/accounts/${accountId}/intelligence/${tab.id}` `` with `workspacePath(accountId, tab.id)` from `workspaceRoutes.ts`.

### R7 — Fix `Layout.tsx` active-state detection

Replace the two `resolvedPath + "/"` BinaryExpressions with `isRouteActive(currentPath, resolvedPath)` from `navHelpers.ts`. The helper already implements the same `location === resolvedPath || location.startsWith(resolvedPath + "/")` logic.

### R8 — `workspaceRoutes.ts` internal alignment (optional)

`workspaceRoutes.ts` is the canonical workspace route helper; callers must not be migrated away from it. Its internals may optionally use `buildPath` / `getStatePath` from `navigationService.ts` if doing so removes duplication or fixes path correctness. No caller changes required.

---

## Acceptance Criteria

- [ ] `HypothesesTab.tsx` imports `useNavigation()`, not `useNavigate()`.
- [ ] `useNavigation()` accepts an optional `state` param; existing callers unchanged.
- [ ] No `useNavigate()` direct calls remain outside `apps/web/src/navigation/`.
- [ ] No UI route template-literal concatenation remains in the 6 affected files.
- [ ] `deliverableRoutes.ts` exists and is the sole source of deliverable route strings.
- [ ] `Layout.tsx` uses `isRouteActive()` for active-state checks; no `+ "/"` BinaryExpression.
- [ ] `DriverTreeShell.tsx` and `CalculatorShell.tsx` use `buildPath` for tab `to` props.
- [ ] `IntelligenceWorkspaceTabs.tsx` uses `workspacePath()`.
- [ ] `shell/router.tsx` URL concatenation sites replaced with canonical helpers.
- [ ] ESLint `no-imperative-navigation` and `no-url-concatenation` rules pass with 0 errors on changed files (verified by static grep since Node 22 is unavailable in this environment).
- [ ] Tests cover: `useNavigation()` with and without state; `isRouteActive()` with/without trailing slash; `deliverableRoutes` helpers; workspace tab path construction.
- [ ] No Zustand/global store introduced for route transition state.
- [ ] `make lint` and `make typecheck` pass.

---

## Implementation Tasks (ordered)

1. **Extend `useNavigation()` hook** — add optional `state` param to `navigateTo()`; update TypeScript signature; keep existing callers working.
2. **Migrate `HypothesesTab.tsx`** — replace `useNavigate()` + `navigate()` with `useNavigation()` + `navigateTo(path, { state })`.
3. **Create `deliverableRoutes.ts`** — `businessCaseDetail(caseId)` and `businessCaseList()` using `getStatePath`.
4. **Fix `ExecutiveView.tsx`, `TechnicalView.tsx`, `CFOView.tsx`** — replace template literals with `deliverableRoutes.*`.
5. **Fix `IntelligenceWorkspaceTabs.tsx`** — replace template literal with `workspacePath()`.
6. **Fix `DriverTreeShell.tsx` and `CalculatorShell.tsx`** — replace tab `to` template literals with `buildPath`.
7. **Fix `shell/router.tsx`** — replace 2 URL concatenation sites with canonical helpers.
8. **Fix `Layout.tsx`** — replace `resolvedPath + "/"` with `isRouteActive()`.
9. **Add/update tests** — `useNavigation` state, `isRouteActive`, `deliverableRoutes`, workspace path construction.
10. **Run `make lint` and `make typecheck`** — confirm 0 errors.
11. **Update `contract-remediation-queue-by-layer.md`** — mark FE-C1 and FE-C2 closed.

---

## Out of Scope

- `ExportMenu.tsx` — uses template literals for API endpoint paths, not UI routes. Not a §2.6 violation.
- `workspaceRoutes.ts` caller migration — callers stay on `workspaceRoutes.ts`; internal refactor only if there is a correctness benefit.
- DEP-WOUTER-ROUTER-011 (direct wouter imports) — separate deprecation, not in this sprint.
- Node 22 / full ESLint run — environment constraint; static grep + typecheck used as proxy.

---

<!-- ARCHIVED SPRINT PLAN BELOW — superseded 2026-05-18 -->
---

## Audit Basis (archived)

Full `make verify` run + per-layer mypy, platform_contract_lint, launch blocker register, security test coverage, and RLS gap analysis. Completed 2026-05-18.

**Environment-only failures excluded** (ruff not in PATH, pytest not in PATH for check-workflow-matrix — not code issues):

| Gate | Current state |
|---|---|
| `make verify` → `lint` | FAIL — ruff not in PATH (env) |
| `make verify` → `typecheck` | FAIL — L1:641, L2:70, L3:1740, L4:841, L5:259, L6:31 errors |
| `make verify` → `security-smoke` | FAIL — PyJWT missing from `tests/requirements.txt` |
| `make verify` → `contract-tests` | FAIL — PyJWT missing from `tests/requirements.txt` |
| `platform_contract_lint` | 0 errors, 15 warnings (1 deadline 2026-06-01, 12 deadline 2026-06-30) |
| P1-006 | OPEN — frontend test report artifact not retained |
| P1-007 | OPEN — security suite CI artifact not attached |
| P1-008 | OPEN — journey SLO report not generated |
| RLS test coverage | GAP — migration 033's 8 tables have no enforcement test |

---

## Sprint 1 — Unblock `make verify` (Days 1–2)

These three tasks are tightly coupled: fixing PyJWT unblocks security-smoke and contract-tests; the typecheck triage determines whether errors are suppressible or require fixes. Together they restore `make verify` to a state where every gate either passes or has a documented suppression.

---

### Task 1 — Add PyJWT to `tests/requirements.txt`

**Why first:** `tests/conftest.py` imports `jwt as pyjwt` at module load. This causes `ModuleNotFoundError` on every pytest collection, which means `security-smoke`, `contract-tests`, and any local test run all fail before a single test executes. One line fix, maximum unblock.

**Files:**
- `tests/requirements.txt` — add `PyJWT>=2.8.0`

**Acceptance criteria:**
- `make security-smoke` no longer fails on `ModuleNotFoundError: No module named 'jwt'`
- `make contract-tests` no longer fails on import
- `python3 -c "import jwt"` succeeds after `pip install -r tests/requirements.txt`

**Effort:** ~5 minutes.

---

### Task 2 — Triage and suppress mypy errors across all 6 layers

**Why second:** `make verify` fails on `typecheck` with 3,582 total mypy errors across 6 layers. The dominant categories are:

| Layer | Errors | Dominant types |
|---|---|---|
| L1 | 641 | `Column[T]` assignment (SQLAlchemy ORM), read-only property, `no-any-return` |
| L2 | 70 | `no-untyped-def`, `no-any-return` |
| L3 | 1,740 | `no-any-return` (283), `no-untyped-def` (240+128), `TypedDictModel` subclass |
| L4 | 841 | `no-untyped-def` (240), `no-any-return` (108+), `TypedDictModel` subclass |
| L5 | 259 | `Column[T]` assignment, `no-untyped-def`, `TokenClaims.email` attr |
| L6 | 31 | `no-any-return`, `no-untyped-def` |

Most errors are pre-existing annotation gaps, not runtime bugs. The correct approach is a per-layer `mypy.ini` or `pyproject.toml` suppression of the categories that are noise (`no-untyped-def`, `no-any-return` where the function is not a contract boundary), while fixing the small set of genuine type errors (`call-arg` mismatches, `attr-defined` on wrong types).

**Files:**
- `services/layer*/mypy.ini` or `services/layer*/pyproject.toml` — add per-layer mypy config with targeted `disable_error_code` for noise categories
- Fix genuine `call-arg` errors in L3 (`EconomicRelationship`, `VariableMetadata` missing required args — ~22+13 occurrences)
- Fix `TokenClaims.email` attr error in L5 (5 occurrences)

**Acceptance criteria:**
- `make typecheck` exits 0
- No genuine contract-boundary type errors suppressed
- `call-arg` and `attr-defined` errors resolved, not suppressed

**Effort:** 1–2 days (L3 call-arg fixes are the bulk).

---

### Task 3 — Fix `get_db_with_tenant` → `get_db_from_context` in Layer 1 (deadline 2026-06-01)

**Why in Sprint 1:** Deadline is 2026-06-01 — 14 days away. Single occurrence in `services/layer1-ingestion/src/shared/database.py` line 275 (docstring example). The function itself is the deprecated one; its callers in `app_monolith.py` need to be migrated to `get_db_from_context`.

**Files:**
- `services/layer1-ingestion/src/shared/database.py` — migrate `get_db_with_tenant` usages to `get_db_from_context`
- `services/layer1-ingestion/src/api/app_monolith.py` — update any `Depends(get_db_with_tenant)` call sites

**Acceptance criteria:**
- `platform_contract_lint` warning `get_db_with_tenant_usage` is gone
- `make platform-contract-lint` shows 0 errors, 14 warnings (one fewer)

**Effort:** ~1 hour.

---

## Sprint 2 — Security Coverage and Launch Blockers (Days 3–5)

---

### Task 4 — Add `test_rls_enforcement.py` coverage for migration 033

**Why:** Migration 033 introduced RLS policies on 8 tables (`billing_charges`, `billing_invoice_items`, `billing_invoices`, `billing_usage_events`, `company_knowledge_profiles`, `icp_profiles`, `knowledge_sources`, `value_extraction_records`) and `admin_bypass_policy` on 4 of them. `test_rls_enforcement.py` has a hardcoded test for migration 032 but nothing for 033. A regression in 033's upgrade would be invisible to the test suite.

**Files:**
- `tests/security/test_rls_enforcement.py` — add `test_033_remaining_tables_have_strict_rls()` mirroring the existing `test_crm_and_billing_tables_have_strict_rls()` pattern; assert 033 exists, covers all 8 tables, upgrade uses strict matching, and the 4 billing tables have `admin_bypass_policy`

**Acceptance criteria:**
- New test asserts `033_fix_rls_null_tenant_policy_remaining.py` exists
- Asserts all 8 tables are referenced in the file
- Asserts `tenant_id IS NULL` does not appear in `upgrade()`
- Asserts `admin_bypass_policy` is created for the 4 billing-only tables
- Asserts `downgrade()` does NOT contain `tenant_id IS NULL` (safe downgrade)

**Effort:** ~1 hour.

---

### Task 5 — Produce P1-007 security suite CI artifact

**Why:** P1-007 blocks Core GA sign-off. The security suite (`pytest tests/security`) is written and passing locally but no CI artifact exists. After Task 1 (PyJWT fix), the suite can be run and its output captured as a retained artifact.

**Files:**
- `.github/workflows/` — add or extend a CI workflow step to run `pytest tests/security -v --tb=short` and upload the JUnit XML as a workflow artifact
- `docs/launch/launch-blocker-register.md` — update P1-007 status from `OPEN` to `REQUIRED_PASS` once artifact is attached

**Acceptance criteria:**
- CI workflow runs `pytest tests/security` and uploads artifact on every push to `main` and release branches
- P1-007 evidence requirement is satisfied by the retained artifact
- No new test failures introduced

**Effort:** ~2 hours.

---

### Task 6 — Produce P1-008 journey SLO report

**Why:** P1-008 blocks Core GA go/no-go. The gate script (`assert-journey-launch-slos.mjs`) is written and reads `tmp/journey-slo-report.json`. The file doesn't exist. With live staging available, the report can be generated from the Playwright journey run and committed as evidence.

**Files:**
- `apps/web/tmp/journey-slo-report.json` — generate from Playwright journey run against staging (or produce a seed file from the existing passing journey evidence)
- `.github/workflows/` — wire `pnpm --dir apps/web run test:journey-slo-gate` into CI after the Playwright journey step
- `docs/launch/launch-blocker-register.md` — update P1-008 status

**Acceptance criteria:**
- `pnpm --dir apps/web run test:journey-slo-gate` exits 0
- Report contains `account_signals_evidence_driver_calculator_business_case` key with `successRate >= 0.99`, `p95LatencySeconds <= 12`, `nonEmptyRatio >= 1`
- P1-008 evidence requirement satisfied

**Effort:** ~2 hours (staging run + wiring).

---

## Sprint 3 — Contract Compliance and Agent Output Contracts (Days 6–8)

---

### Task 7 — Migrate L4 test fixtures from raw dict to `AgentResultEnvelope` (deadline 2026-06-30)

**Why:** 12 `raw_dict_agent_return` warnings across 4 Layer 4 test files. `AgentResultEnvelope` exists in `packages/platform-contract/src/python/canonical/agent_output.py`. The warnings are in test files, not production code, but they represent the test suite asserting against the wrong contract shape — if production agents switch to `AgentResultEnvelope`, these tests will silently pass against the wrong structure.

**Files:**
- `services/layer4-agents/tests/test_agent_tenant_isolation.py` (2 occurrences)
- `services/layer4-agents/tests/test_agent_grounding_and_refusal.py` (3 occurrences)
- `services/layer4-agents/tests/test_tool_result_contract.py` (5 occurrences)
- `services/layer4-agents/tests/test_tools_authorization.py` (1 occurrence)

**Acceptance criteria:**
- All 12 `raw_dict_agent_return` warnings resolved
- `platform_contract_lint` shows 0 errors, 3 warnings (only `test_agent_tool_result_contracts.py` remains, which is the contract test file itself)
- Test assertions updated to use `AgentResultEnvelope` fields

**Effort:** ~3 hours.

---

### Task 8 — Produce P1-006 frontend test report artifact

**Why:** P1-006 blocks Core GA sign-off. The frontend test suite passes locally but no retained artifact exists. Requires Node 22 (Docker container). The fix is to run `pnpm --dir apps/web run test` inside the Docker build and upload the Vitest JSON report.

**Files:**
- `.github/workflows/` — add frontend test step running `pnpm --dir apps/web run test --reporter=json --outputFile=apps/web/tmp/frontend-test-report.json` and uploading as artifact
- `docs/launch/launch-blocker-register.md` — update P1-006 status

**Acceptance criteria:**
- CI produces a retained `frontend-test-report.json` artifact on every push
- P1-006 evidence requirement satisfied
- All existing tests continue to pass

**Effort:** ~2 hours.

---

## Sprint 4 — Typecheck Hardening and Remaining Debt (Days 9–12)

---

### Task 9 — Fix genuine `call-arg` type errors in Layer 3 (`EconomicRelationship`, `VariableMetadata`)

**Why:** After Sprint 1's mypy suppression pass, the remaining `call-arg` errors in L3 are genuine — `EconomicRelationship` and `VariableMetadata` constructors are called without required arguments (`formula`, `max_value`, `category`). These are contract-boundary models; suppressing them would hide real bugs. 22 + 13 + 13 occurrences across L3.

**Files:**
- `services/layer3-knowledge/src/` — fix call sites for `EconomicRelationship` (add `formula=`) and `VariableMetadata` (add `max_value=`, `category=`)

**Acceptance criteria:**
- `make typecheck-layer3` exits 0 after suppression config is applied
- No `call-arg` errors remain for `EconomicRelationship` or `VariableMetadata`
- No runtime behaviour changed

**Effort:** ~4 hours.

---

### Task 10 — Fix `TokenClaims.email` attr errors in Layer 5 (5 occurrences)

**Why:** `TokenClaims` does not have an `email` attribute according to mypy, but 5 call sites in L5 access `.email`. This is either a missing field on the model or a wrong attribute name. If it's a missing field, it's a silent `AttributeError` at runtime for any code path that hits these routes without an email claim.

**Files:**
- `packages/shared/src/value_fabric/shared/identity/` — check `TokenClaims` definition; add `email: str | None = None` if missing
- `services/layer5-ground-truth/src/` — fix the 5 call sites if the attribute name is wrong

**Acceptance criteria:**
- `make typecheck-layer5` exits 0
- `TokenClaims.email` is either defined on the model or all 5 call sites use the correct attribute
- No runtime `AttributeError` possible on the affected code paths

**Effort:** ~1 hour.

---

## Summary Table

| # | Task | Sprint | Gate unblocked | Effort |
|---|---|---|---|---|
| 1 | Add PyJWT to `tests/requirements.txt` | 1 | `security-smoke`, `contract-tests` | 5 min |
| 2 | Triage + suppress mypy noise, fix genuine errors | 1 | `typecheck` | 1–2 days |
| 3 | Migrate `get_db_with_tenant` → `get_db_from_context` in L1 | 1 | `platform_contract_lint` warning (deadline 2026-06-01) | 1 hr |
| 4 | Add 033 RLS enforcement tests | 2 | Security coverage gap | 1 hr |
| 5 | P1-007: Security suite CI artifact | 2 | Launch blocker P1-007 | 2 hr |
| 6 | P1-008: Journey SLO report | 2 | Launch blocker P1-008 | 2 hr |
| 7 | Migrate L4 test fixtures to `AgentResultEnvelope` | 3 | `platform_contract_lint` warnings (deadline 2026-06-30) | 3 hr |
| 8 | P1-006: Frontend test report artifact | 3 | Launch blocker P1-006 | 2 hr |
| 9 | Fix L3 `call-arg` errors (`EconomicRelationship`, `VariableMetadata`) | 4 | `typecheck-layer3` | 4 hr |
| 10 | Fix L5 `TokenClaims.email` attr errors | 4 | `typecheck-layer5` | 1 hr |

---

<!-- ARCHIVED: Previous spec (Restore make verify) superseded 2026-05-18. PR #393 merged. -->
<!-- ARCHIVED: Previous spec (Clear Repository-Owned Launch Gate) superseded 2026-05-18. PR #384 merged. -->
<!-- ARCHIVED: Previous spec (Workflow Test Coverage) superseded 2026-05-17. Tests were already implemented. -->

