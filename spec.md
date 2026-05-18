# Spec: Test Suite Remediation & Coverage Improvement

## Status
Extended — pending user confirmation

> **Scope note:** This spec extends the original Workflow Test Coverage initiative (§ Workflow Coverage — 7-Step Value Pilot, below) with a broader test remediation effort covering Python backend failures, shared-package contract drift, CI gate failures, and frontend Vitest failures. The workflow coverage work is preserved unchanged as Phase 4.

---

## Part 1 — Test Suite Remediation & Coverage Improvement

### Problem Statement

The Fabric_4L monorepo has two test stacks (Python/pytest and TypeScript/Vitest) with a combined 8,064+ tests. A live audit (2026-05-17) found 954 failures and 396 errors across all suites. The failures fall into four priority tiers:

- **P0 — Backend contract/security/workflow failures**: Missing `validate_jwt_config` export blocks the entire `shared.identity` import chain, cascading into 16+ security test collection errors, 6 shared-package collection errors, and 2 integration test collection errors. Arch tests expose a stale AST assertion against `require_authenticated`. Layer 3 shim drift and Layer 5 shim integrity failures indicate canonical-path governance regressions.
- **P1 — CI/runtime stability failures**: 24 CI gate tests fail due to missing files (`app_monolith.py`, `entity_compat.py`), a YAML parse error in workflow permission tests, Layer 3 source mirror governance docstring gaps, and a mirrored-files drift guard failure.
- **P2 — Frontend functional failures**: 100 Vitest tests fail across 16 files due to missing MSW handlers, a missing `QK.targets` query key, a temporal dead zone (TDZ) bug in `useAuth`, and stale `navSchema` breadcrumb assertions. Frontend suite is also blocked by Node 20 (requires ≥22).
- **P3 — Test quality cleanup**: Contract tests (382) are all skipped without live services; collection errors in `tests/layer3/` (14 files) due to `sys.path` topology under `importlib` mode.

---

### Current Baseline

| Suite | Passed | Failed | Errors | Skipped | Coverage |
|---|---:|---:|---:|---:|---:|
| `tests/arch` + `tests/ci` | 182 | 27 | 0 | 0 | — |
| `tests/contract` | 0 | 0 | 0 | 382 | — |
| `tests/security` | — | — | 16 (collection) | — | — |
| `tests/shared` | — | — | 6 (collection) | — | — |
| `tests/integration` | — | — | 2 (collection) | — | — |
| Layer 1 service | 509 | 117 | 99 | 32 | 58.3% |
| Layer 2 service | 289 | 31 | 0 | 1 | 61.1% |
| Layer 3 service | 395 | 41 | 3 | 1 | 43.7% |
| Layer 4 service | 1,401 | 231 | 98 | 8 | 59.7% |
| Layer 5 service | 92 | 21 | 101 | 3 | 59.5% |
| Layer 6 service | 79 | 0 | 0 | 0 | **83.9%** |
| API service | 60 | 29 | 0 | 0 | 70.7% |
| Frontend (Vitest, last run) | 1,515 | **100** | 0 | 0 | 83.2% stmts (`src/`) |

**Coverage targets:** 80% per layer (enforced per-service). Only Layer 6 meets the target. Frontend `src/` meets the target on statements/branches but has 100 failing tests.

---

### Scope

**In scope:**
- `packages/shared/src/value_fabric/shared/security/config.py` — add missing `validate_jwt_config` export
- `packages/shared/src/value_fabric/shared/identity/dependencies.py` — verify import resolves after fix
- `tests/arch/test_tenant_architecture.py` — fix stale AST assertion for `require_authenticated`
- `tests/arch/test_layer3_models_shim_contract.py` — fix or document shim re-export assertion
- `tests/arch/test_layer3_runtime_shim_drift.py` — document drift; fix or quarantine
- `tests/arch/test_canonical_module_sentinels.py` — fix Layer 5 sentinel import (missing `sqlalchemy`)
- `tests/ci/test_workflow_permissions.py` — fix YAML parse error in workflow permission scanner
- `tests/ci/test_layer3_route_compat_shims.py` — fix missing file references (`app_monolith.py`, `entity_compat.py`)
- `tests/ci/test_layer3_source_mirror_gate.py` — add governance docstrings to Layer 3 service-local files
- `tests/ci/test_check_layer5_shim_integrity.py` — fix `CANONICAL_ROOT` attribute missing from contract module
- `tests/ci/test_mirrored_files_drift_guard.py` — fix mirrored-files drift (shared identity isolation)
- `tests/ci/test_unscoped_tenant_match_lint.py` — cascades from `validate_jwt_config`; resolves after P0 fix
- `tests/ci/test_build_promotion_artifact_contract.py` — fix missing `published_tag` marker in CI workflow
- `tests/ci/test_route_auth_gate.py` — investigate route count assertion (expected vs actual)
- `tests/ci/test_env_contract_validator_i01.py` — fix env schema compile failure
- `tests/ci/test_layer6_service_src_presence.py` — fix Layer 6 conftest import error (`validate_jwt_config` cascade)
- `.nvmrc` — add/update to Node 22 LTS
- `.devcontainer/devcontainer.json` — update Node version to ≥22.12.0
- `apps/web/src/hooks/queryKeys.ts` — add missing `QK.targets` namespace
- `apps/web/src/hooks/useAuth.ts` — fix TDZ bug (`Cannot access 'data' before initialization`)
- `apps/web/src/navigation/navSchema.ts` — fix stale breadcrumb label assertions
- `apps/web/src/test/mocks/handlers.ts` — add missing MSW handlers for failing hook/page tests

**Out of scope:**
- Tests requiring live infrastructure (PostgreSQL, Redis, Neo4j, Docker) — counted and noted, not fixed
- `tests/contract/` — all 382 skipped tests require live services; not addressed here
- `tests/layer3/` collection errors under `importlib` mode — documented as known topology issue
- Per-service coverage improvement beyond fixing existing failures (separate initiative)
- New test authoring beyond what is needed to fix existing failures (covered in Part 2 / Phase 4)

---

### Requirements

#### R-P0: Shared package — missing `validate_jwt_config` export

**R-P0.1** — `validate_jwt_config` must be exported from `value_fabric.shared.security.config`. The function should validate that JWT configuration is safe for the current environment (wrapping or aliasing the existing `validate_jwt_secret_strength` logic, or adding a new function if the semantics differ).

**R-P0.2** — After the fix, `from value_fabric.shared.security.config import validate_jwt_config` must succeed without `ImportError`.

**R-P0.3** — `tests/shared/`, `tests/security/`, `tests/integration/`, and `tests/ci/test_unscoped_tenant_match_lint.py` must no longer produce collection errors caused by this import chain.

---

#### R-P0: Arch test — stale `require_authenticated` AST assertion

**R-P0.4** — `tests/arch/test_tenant_architecture.py::test_tenant_required_api_dependencies_reject_missing_and_invalid_tenant` currently fails because `require_authenticated` delegates to `_unauthorized()` helper rather than directly naming `HTTPException` and `status`. The test assertion must be updated to reflect the actual pattern: either check that `_unauthorized` is called (which itself raises `HTTPException`), or check that the function body raises an exception type that is a subclass of `HTTPException`. The invariant being tested (that unauthenticated requests are rejected with an HTTP error) must be preserved.

---

#### R-P0: Layer 3 shim drift

**R-P0.5** — `tests/arch/test_layer3_runtime_shim_drift.py` fails because `services/layer3-knowledge/src/api/models.py`, `api/app_monolith.py`, and `services/product_service.py` have drifted from the canonical runtime. Either: (a) resolve the drift by aligning the service wrappers back to thin forwarders, or (b) if the drift is intentional, update the drift-check script and document the exception in `docs/governance/compatibility-debt-registry.md`.

**R-P0.6** — `tests/arch/test_layer3_models_shim_contract.py` fails because `services/layer3-knowledge/src/api/models.py` no longer contains `from value_fabric.layer3.api.models import *`. Either restore the re-export or update the test to reflect the new canonical pattern and document the change.

---

#### R-P1: CI gate failures

**R-P1.1** — `tests/ci/test_workflow_permissions.py` fails with a YAML `ScannerError` on line 46 of a workflow file (`DATABASE_URL: sqlite:///:memory:`). The offending workflow file must be fixed so its YAML is valid.

**R-P1.2** — `tests/ci/test_layer3_route_compat_shims.py` fails because `value_fabric/layer3/api/app_monolith.py` and `value_fabric/layer3/api/routes/entity_compat.py` do not exist. Either create these files (as shims) or update the test to reflect the current canonical file layout.

**R-P1.3** — `tests/ci/test_layer3_source_mirror_gate.py` fails because 13 Layer 3 service-local files are missing required governance docstrings. Add the required docstrings to each flagged file.

**R-P1.4** — `tests/ci/test_check_layer5_shim_integrity.py` fails because the `layer5_source_contract` module (resolved to `services/layer5-ground-truth/scripts/check_no_duplicate_modules.py`) does not expose `CANONICAL_ROOT`. Either add the attribute to the script or update the test to use the correct attribute name.

**R-P1.5** — `tests/ci/test_mirrored_files_drift_guard.py` fails because `scripts/check_mirrored_files.py` reports missing files in the shared identity isolation mirror. Identify and create the missing mirror files.

**R-P1.6** — `tests/ci/test_build_promotion_artifact_contract.py` fails because `.github/workflows/build-deploy.yml` does not contain the `published_tag` build artifact contract marker. Add the marker.

**R-P1.7** — `tests/ci/test_route_auth_gate.py` fails with an assertion about route count (scanned 80 routes). Investigate whether the expected count in the test is stale and update it, or fix the route inventory if routes are missing auth annotations.

**R-P1.8** — `tests/ci/test_env_contract_validator_i01.py` fails on env schema compilation. Identify the failing schema and fix the compilation error.

**R-P1.9** — `tests/arch/test_canonical_module_sentinels.py::test_layer5_models_imports_directly` fails because `layer5_ground_truth/models/model_registry.py` imports `sqlalchemy` which is not installed in the test environment. Install `sqlalchemy` as a test dependency (it is already a production dependency of Layer 5) and verify the sentinel test passes.

---

#### R-P2: Frontend runtime prerequisite

**R-P2.1** — Add or update `.nvmrc` at the repo root to specify Node 22 LTS (≥22.12.0).

**R-P2.2** — Update `.devcontainer/devcontainer.json` to use a Node ≥22.12.0 base image or feature.

**R-P2.3** — After Node upgrade, `pnpm --dir apps/web install --frozen-lockfile` must succeed.

**R-P2.4** — After Node upgrade, `pnpm --dir apps/web exec vitest run` must start without a runtime-version error.

---

#### R-P2: Frontend functional failures

**R-P2.5** — Add `QK.targets` namespace to `apps/web/src/hooks/queryKeys.ts` with the same factory pattern used by other namespaces (`all`, `list(filters)`, `detail(id)`, `stats`). The `useTargets.test.ts` assertions about `QK.targets.all`, `QK.targets.stats`, and `QK.targets.list(filters)` must pass.

**R-P2.6** — Fix the TDZ (`Cannot access 'data' before initialization`) bug in `apps/web/src/hooks/useAuth.ts`. The `useAuth.test.ts` suite must pass with zero failures.

**R-P2.7** — Add missing MSW handlers to `apps/web/src/test/mocks/handlers.ts` for the following routes that produce "unmatched request" failures:
  - Accounts API routes (used by `useAccounts.test.tsx`)
  - Competitive intel API routes (used by `useCompetitiveIntel.test.ts`)
  - Models API routes (used by `useModels.test.tsx`)
  - ROI Calculator API routes (used by `useROICalculator.test.ts`)
  - Value Packs API routes (used by `useValuePacks.test.tsx`)
  - Targets admin page routes (used by `TargetsAdmin.test.tsx` and variants)
  - Ingestion Jobs routes (used by `IngestionJobs.test.tsx`)
  - Account Picker Modal routes (used by `AccountPickerModal.test.tsx`)
  - Signals tab routes (used by `SignalsTab.test.tsx`)
  - Hypothesis validation flow routes (used by `HypothesisValidationToDriverFlow.test.tsx`)

**R-P2.8** — Fix the `navSchema.test.ts` assertion failures. Either update `resolveBreadcrumbs` in `apps/web/src/navigation/navSchema.ts` to return the expected labels, or update the test assertions to match the current schema behavior. The invariant (breadcrumbs resolve correctly for all workflow paths) must be preserved.

---

### Acceptance Criteria

| ID | Criterion |
|---|---|
| AC-01 | `pytest tests/arch tests/ci --ignore=tests/ci/test_check_no_nul_bytes.py` passes with 0 failures |
| AC-02 | `pytest tests/shared tests/integration` collects without errors |
| AC-03 | `pytest tests/security --ignore=tests/security/test_neo4j_cross_tenant_write_isolation.py --ignore=tests/security/test_layer3_similarity_roi_tenant_isolation.py` collects without errors |
| AC-04 | `from value_fabric.shared.security.config import validate_jwt_config` succeeds |
| AC-05 | `node --version` reports ≥22.12.0 after devcontainer rebuild |
| AC-06 | `pnpm --dir apps/web install --frozen-lockfile` succeeds |
| AC-07 | `pnpm --dir apps/web exec vitest run` reports 0 failures (or documents any remaining failures with root cause) |
| AC-08 | `QK.targets` is defined in `queryKeys.ts` with `all`, `list`, `detail`, `stats` factories |
| AC-09 | `useAuth.test.ts` passes with 0 failures |
| AC-10 | No source file is modified solely to suppress a test — every source change must fix a real defect |
| AC-11 | Every test fix that changes an assertion documents why the old assertion was stale |
| AC-12 | All P0 fixes are accompanied by a regression test or an explanation of why the existing test is sufficient |

---

### Implementation Approach (Phase 1–3)

**Phase 1 — P0: Shared package contract fix (unblocks ~24 downstream failures)**

1. Read `packages/shared/src/value_fabric/shared/security/config.py` to understand the existing `validate_jwt_secret_strength` function and determine whether `validate_jwt_config` should alias it or be a new function.
2. Add `validate_jwt_config` to `security/config.py` — either as an alias or a new function that validates JWT configuration holistically (secret strength + algorithm + expiry settings).
3. Verify `from value_fabric.shared.security.config import validate_jwt_config` resolves.
4. Run `pytest tests/shared tests/integration tests/ci/test_unscoped_tenant_match_lint.py -q` to confirm collection errors are resolved.

**Phase 1 — P0: Arch test fixes**

5. Fix `tests/arch/test_tenant_architecture.py` — update `_function_mentions_names` check for `require_authenticated` to match the helper-delegation pattern (`_unauthorized` is called, which raises `HTTPException`).
6. Investigate Layer 3 shim drift (`test_layer3_runtime_shim_drift.py`, `test_layer3_models_shim_contract.py`). If drift is unintentional, restore the shim re-export in `services/layer3-knowledge/src/api/models.py`. If intentional, update the drift-check script and register in the compatibility debt registry.

**Phase 2 — P1: CI gate fixes**

7. Fix the YAML syntax error in the workflow file flagged by `test_workflow_permissions.py` (line 46, `DATABASE_URL: sqlite:///:memory:`).
8. Fix `test_layer3_route_compat_shims.py` — create the missing shim files or update the test to the current file layout.
9. Add governance docstrings to the 13 Layer 3 service-local files flagged by `test_layer3_source_mirror_gate.py`.
10. Fix `test_check_layer5_shim_integrity.py` — add `CANONICAL_ROOT` to `check_no_duplicate_modules.py` or update the test to use the correct attribute.
11. Fix `test_mirrored_files_drift_guard.py` — identify and create the missing shared identity isolation mirror files.
12. Add `published_tag` marker to `.github/workflows/build-deploy.yml` (`test_build_promotion_artifact_contract.py`).
13. Fix `test_route_auth_gate.py` — update the expected route count or fix missing auth annotations.
14. Fix `test_env_contract_validator_i01.py` — identify and fix the failing env schema.
15. Install `sqlalchemy` in `tests/requirements-test.txt` and verify `test_canonical_module_sentinels.py` passes.

**Phase 3 — P2: Frontend runtime + functional fixes**

16. Add/update `.nvmrc` to `22` (Node 22 LTS).
17. Update `.devcontainer/devcontainer.json` to use Node ≥22.12.0.
18. Run `nvm install 22 && nvm use 22` locally; run `pnpm --dir apps/web install --frozen-lockfile`.
19. Add `QK.targets` namespace to `queryKeys.ts`.
20. Fix TDZ bug in `useAuth.ts`.
21. Add missing MSW handlers to `handlers.ts` for all 10 failing route groups.
22. Fix `navSchema.ts` or `navSchema.test.ts` breadcrumb assertions.
23. Run `pnpm --dir apps/web exec vitest run` and verify 0 failures (or document residual failures).

**Phase 4 — Workflow page coverage (original spec, unchanged)**
*(See § Workflow Coverage — 7-Step Value Pilot below)*

---

### Risk / Follow-up

| Risk | Mitigation |
|---|---|
| `validate_jwt_config` semantics unclear — aliasing `validate_jwt_secret_strength` may not be correct | Read all call sites before aliasing; add a docstring explaining the intended contract |
| Layer 3 shim drift fix may break service-local tests | Run `pytest services/layer3-knowledge/tests/` after any shim change |
| MSW handler additions may over-mock and hide real API contract drift | Use typed response shapes matching the OpenAPI contract; add a comment linking to the contract |
| Node upgrade may break other tooling in the devcontainer | Test `pnpm install` and `pnpm build` after upgrade before committing devcontainer change |
| Layer 5 shim integrity fix requires understanding `check_no_duplicate_modules.py` contract | Read the script fully before adding `CANONICAL_ROOT` |

---

---

## Part 2 — Workflow Test Coverage — 7-Step Value Pilot

*(Original spec content preserved below)*
# Spec: FE-C1 + FE-C2 — Imperative Navigation & URL Concatenation Remediation

**Contract:** §2.6 UI State Management  
**Deadline:** 2026-05-30  
**Deprecation IDs:** DEP-IMPERATIVE-NAV-009, DEP-URL-CONCAT-010  
**ESLint rules:** `fabric-contracts/no-imperative-navigation`, `fabric-contracts/no-url-concatenation`

<!-- ARCHIVED: Security Audit spec (F-01 through F-25) superseded 2026-05-18. Implemented in PR #398. -->

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

