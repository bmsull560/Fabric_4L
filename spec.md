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
