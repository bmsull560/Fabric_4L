# Spec: Codebase Audit & Roadmap to Shippable

## Status
Draft — pending user confirmation

---

## Problem Statement

Value Fabric has a well-designed six-layer architecture with strong governance patterns (tenant isolation, contract-first APIs, audit logging, security middleware). All six layers have substantive implementations — no layer is a stub. However, the platform is not yet shippable due to three categories of blockers:

1. **Test environment misconfiguration** — most test suites cannot run from the repo root due to missing global Python dependencies and service-venv fragmentation.
2. **Functional test failures** — Layer 4 has 3 confirmed harness test failures (tuple return type mismatch) and 3 confirmed langgraph execution test failures (stale mock patches, missing fixture fields, signal detection regression).
3. **Infrastructure gaps** — k8s manifests reference invalid local image paths, secret names are stale relative to the actual LLM provider (Together.ai), and the GHCR base image access pattern is unverified.

This spec defines the full five-phase roadmap to bring the platform to a shippable state.

---

## Scope

### In scope
- Phase 1: Test infrastructure — make all service test suites runnable
- Phase 2: Functional test failures — fix all confirmed Layer 4 failures
- Phase 3: Incomplete implementations — CoreferenceResolver, Pydantic v2 migration, Layer 3 route stubs
- Phase 4: Infrastructure hardening — k8s image paths, secret names, GHCR access
- Phase 5: Production readiness — E2E integration, Layer 3 tenant isolation audit, frontend test fixes, telemetry

### Out of scope
- Node 20 → 22 devcontainer upgrade (handled separately)
- New feature development
- Architectural refactors not required to unblock shippability
- Modifying `contracts/` directly (contract update workflow applies)

---

## Confirmed Findings (from live codebase, verified 2026-05-17)

| Finding | File / Location | Confirmed |
|---|---|---|
| `HarnessRunRepository.list()` returns `tuple[list, int]` but 3 tests iterate it as `list` | `services/layer4-agents/src/harness/repositories.py:291` | ✅ |
| `test_analyze_prospect_returns_complete_result` patches `get_openai_provider` (removed post-rewrite) | `services/layer4-agents/tests/test_langgraph_execution.py:107` | ✅ |
| `CoreferenceResolver.resolve()` returns input unchanged (no-op) | `services/layer2-extraction/src/layer2_extraction/coreference/coreference_resolver.py` | ✅ |
| `packages/platform-contract` uses `@validator` / `@root_validator` (Pydantic v1) | `packages/platform-contract/src/python/agent_contracts/models.py:16,106,126` | ✅ |
| `k8s/layer4-agents.yml` uses `image: services/layer4-agents:latest` (not a registry path) | `k8s/layer4-agents.yml:50` | ✅ |
| `k8s/base/` uses `image: services/<name>:main` (also not a registry path) | `k8s/base/` | ✅ |
| `k8s/layer4-agents.yml` references `openai-secret` and `anthropic-secret` | `k8s/layer4-agents.yml:66,71` | ✅ |
| `k8s/secrets.yml.template` has no `TOGETHER_API_KEY` entry | `k8s/secrets.yml.template` | ✅ |
| `structlog` not installed in global Python env | global env | ✅ |
| `prometheus_client` not installed in global Python env | global env | ✅ |
| `testcontainers` not installed in global Python env | global env | ✅ |
| `devcontainer.json` pins Node 20; `apps/web/package.json` requires `>=22.12.0` | `.devcontainer/devcontainer.json`, `apps/web/package.json` | ✅ |
| `formulas.py:579` has `pass  # All variables returned for now` (category filter unimplemented) | `services/layer3-knowledge/src/api/routes/formulas.py:579` | ✅ |
| `Makefile` `test-layer*` targets invoke `$(PYTEST)` without activating service venvs | `Makefile:260–277` | ✅ |

---

## Requirements

### Phase 1 — Test Infrastructure

**Goal:** All service test suites runnable without manual venv activation.

**R1.1** — The `Makefile` `test-layer1`, `test-layer4`, `test-layer5`, `test-layer6` targets must invoke pytest through each service's own virtual environment (or install deps into the global env). Currently they use `$(PYTEST)` which resolves to the global `python -m pytest`, missing service-specific deps.

**R1.2** — The root-level `pytest.ini` / `pyproject.toml` must not inject `--timeout` or `--randomly-seed` flags into service test runs that don't have those plugins installed. Either scope the root config to only the services that have those plugins, or remove the conflicting `addopts`.

**R1.3** — `structlog`, `prometheus_client`, and `testcontainers` must be available when running Layer 1, Layer 5, Layer 6, and Layer 4 tests respectively. Options (in order of preference):
  - Install them into each service's venv via `pip install -e ".[dev]"` in the Makefile targets
  - Or document a one-time `make setup` target that bootstraps all service venvs

**R1.4** — `services/layer4-agents/tests/conftest.py` imports `langgraph` at module level. The `test-layer4` Makefile target must `cd services/layer4-agents` before invoking pytest and must have `langgraph` available in the resolved Python environment.

**R1.5** — A `make setup` (or equivalent) target must exist that bootstraps all service venvs in one command, so a new contributor can run `make setup && make test` without manual steps.

---

### Phase 2 — Functional Test Failures

**Goal:** Layer 4 harness tests 226/226 passing; langgraph execution tests passing.

**R2.1 — HarnessRunRepository.list() tuple mismatch (P0)**

`HarnessRunRepository.list()` returns `tuple[list[HarnessRun], int]` (items, total_count). Three tests treat the return value as a plain `list`:

- `test_list_filters_by_tenant` (`test_harness_persistence.py:209`)
- `test_list_filters_by_status` (`test_harness_persistence.py:220`)
- `test_list_runs_tenant_scoped` (`test_harness_persistence.py:638`)

**Option A (recommended):** Fix the 3 failing tests to unpack the tuple: `items, _ = await repo.list(tenant_id)`. Preserves the pagination design; no production code change.

**Option B:** Change `list()` to return `list[HarnessRun]` and add a separate `count()` method. Simpler callers but requires updating all callers and the API layer.

The implementation must choose one option and apply it consistently to all callers (tests + API routes + any other consumers of `HarnessRunRepository.list()`).

**R2.2 — Stale mock patch target (P0)**

`test_analyze_prospect_returns_complete_result` patches `value_fabric.layer4.workflows.whitespace.get_openai_provider`, which no longer exists after the LLM provider rewrite. The test must be updated to patch the actual provider resolution path used post-rewrite (the governed LLM client or Together provider adapter).

**R2.3 — BusinessCaseInputData missing required field (P1)**

`test_business_case_handles_all_sections_failing` triggers a `ValidationError` because the test fixture is missing a required field added to `BusinessCaseInputData` after a model change. The fixture must be updated to include all required fields.

**R2.4 — SignalDetectionAgent returns 0 signals (P1)**

`test_detect_signals_returns_complete_result` expects 1 signal but `SignalDetectionAgent` returns an empty list. The root cause must be traced through `_execute_detect_signals()` — the mock LLM response is not being parsed into the signals list. Fix the parsing logic or the mock response shape to match the current extraction contract.

**R2.5 — 8 collection failures in Layer 4 full suite**

Eight test files fail collection due to missing `testcontainers` and tracing modules. Resolve by:
- Installing the missing deps in the service venv (preferred, covered by R1.3)
- Or adding `pytest.importorskip` guards in the affected files with a clear skip message

---

### Phase 3 — Incomplete Implementations

**Goal:** No functional no-ops in the critical path.

**R3.1 — CoreferenceResolver (P2)**

`CoreferenceResolver.resolve()` returns its input unchanged, silently producing duplicate entities in the knowledge graph. Implement basic entity deduplication by name + type matching:
- Deduplicate entities where `name` and `entity_type` match (case-insensitive)
- Merge provenance metadata from duplicates into the canonical entity
- Do not change the `resolve()` interface signature
- Unit tests must cover: no duplicates (passthrough), exact duplicates (merge), partial matches (no merge)

`are_semantically_equivalent()` may remain `False` for now (semantic equivalence requires embedding infrastructure) but must be documented as a known limitation.

**R3.2 — Pydantic v2 migration in platform-contract (P2)**

`packages/platform-contract/src/python/agent_contracts/models.py` uses `@validator` and `@root_validator` (Pydantic v1 compatibility layer). Migrate to:
- `@field_validator` (replaces `@validator`)
- `@model_validator` (replaces `@root_validator`)

The migration must not change validation semantics — only the decorator API. All existing contract tests must pass after migration. Zero Pydantic deprecation warnings in test output.

**R3.3 — Layer 3 formula category filter (P3)**

`services/layer3-knowledge/src/api/routes/formulas.py:579` has `pass  # All variables returned for now` — the category filter is unimplemented. Implement filtering by category using the implied name-pattern logic or by adding a `category` field to the variable registry entries. The endpoint must return only variables matching the requested category when `category` is provided.

---

### Phase 4 — Infrastructure Hardening

**Goal:** Deployable to a real cluster.

**R4.1 — k8s image paths (P1)**

All top-level k8s manifests and `k8s/base/` overlays use invalid local image paths (`services/<name>:latest` or `services/<name>:main`). Replace with configurable registry placeholders using the Kustomize `images` override pattern:

```yaml
# k8s/base/kustomization.yaml — add images block
images:
  - name: layer4-agents
    newName: ghcr.io/<org>/layer4-agents
    newTag: main
```

Environment-specific overlays (`k8s/overlays/`, `k8s/envs/`) must override `newName` and `newTag` with real values. The `<org>` placeholder must be documented in `k8s/README.md` with instructions for setting the real org at deploy time. Direct `image:` fields in deployment specs must reference the Kustomize image name so overlays can substitute correctly.

**R4.2 — k8s secret names for LLM provider (P3)**

`k8s/layer4-agents.yml` references `openai-secret` and `anthropic-secret` as env var sources. Layer 4's primary provider is Together.ai. Update:
- Rename `openai-secret` → `llm-provider-secret` (or `together-secret`) in the manifest
- Add `TOGETHER_API_KEY` to `k8s/secrets.yml.template`
- Remove or comment out stale `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` entries from the Layer 4 deployment (retain them if other layers still use them)
- Update `k8s/README.md` to document the secret naming convention

**R4.3 — GHCR base image access (P2)**

CI workflow `build-deploy.yml` checks `ghcr.io/value-fabric/base-images/` which may require a PAT for cross-org access. Verify:
- Whether the images are public (no auth needed) or private (PAT required)
- If private: add a `GHCR_PAT` secret to the repo and reference it in the workflow
- If public: document this in the workflow comments

---

### Phase 5 — Production Readiness

**Goal:** Meets the platform's own production-readiness checklist.

**R5.1 — End-to-end integration test (golden path J1)**

Run the golden path (J1) with a live Layer 4 backend and verify ROI calculation produces a valid result:
- A running Layer 4 service with Together.ai credentials
- A test account with valid input data
- Assertion that the ROI workflow completes and returns a structured result matching the contract
- Add to CI as a smoke test gated on `PLAYWRIGHT_BACKEND_URL` being set

**R5.2 — Layer 3 tenant isolation audit (P2)**

All Neo4j queries in `services/layer3-knowledge/src/` must filter by `tenant_id`. The audit must:
- Enumerate all Cypher queries in the codebase
- Verify each query includes a `tenant_id` filter (in `WHERE` or as a node property match)
- Add hostile cross-tenant tests for any query found to be missing the filter
- Document findings in `docs/` under the security reference section

**R5.3 — Frontend test fixes (P1)**

`apps/web` has ~100 failing tests (MSW handler mismatches, auth redirect issues). Fix:
- MSW handler mismatches: update mock handlers to match current API route shapes
- Auth redirect issues: update test fixtures to match current auth flow
- All frontend tests must pass (`pnpm --dir apps/web test`)

Note: Blocked by Node 20 in the current devcontainer (handled separately). Fixes must be ready to run once Node 22 is available.

**R5.4 — SqlTelemetryEmitter.get_events() (P3)**

`SqlTelemetryEmitter.get_events()` raises `NotImplementedError`. Either:
- Implement with a SQL query against the telemetry events table
- Or remove the method and update all callers

The choice must be documented.

**R5.5 — Layer 2 → Layer 3 pipeline integration test**

Verify that extracted entities flow correctly from Layer 2 into Neo4j (Layer 3):
- Correct tenant scoping on all created nodes
- Provenance metadata preserved
- No duplicate entities (validates CoreferenceResolver fix from R3.1)

---

## Acceptance Criteria

| ID | Phase | Criterion |
|---|---|---|
| AC-01 | 1 | `make test-layer1` runs without collection errors |
| AC-02 | 1 | `make test-layer4` runs without collection errors |
| AC-03 | 1 | `make test-layer5` runs without collection errors |
| AC-04 | 1 | `make test-layer6` runs without collection errors |
| AC-05 | 1 | `make setup` bootstraps all service venvs in one command |
| AC-06 | 2 | `test_list_filters_by_tenant` passes |
| AC-07 | 2 | `test_list_filters_by_status` passes |
| AC-08 | 2 | `test_list_runs_tenant_scoped` passes |
| AC-09 | 2 | `test_analyze_prospect_returns_complete_result` passes |
| AC-10 | 2 | `test_business_case_handles_all_sections_failing` passes |
| AC-11 | 2 | `test_detect_signals_returns_complete_result` passes |
| AC-12 | 2 | Layer 4 harness tests: 226/226 passing |
| AC-13 | 3 | `CoreferenceResolver.resolve()` deduplicates entities by name+type |
| AC-14 | 3 | `CoreferenceResolver` unit tests: passthrough, exact-dup merge, partial-match no-merge |
| AC-15 | 3 | `packages/platform-contract` uses `@field_validator` / `@model_validator`; zero Pydantic deprecation warnings |
| AC-16 | 3 | All existing contract tests pass after Pydantic v2 migration |
| AC-17 | 3 | `GET /formulas/variables?category=<x>` returns only variables matching the category |
| AC-18 | 4 | All `k8s/base/` and top-level manifests use Kustomize image placeholders (no `services/<name>:*` paths) |
| AC-19 | 4 | `k8s/secrets.yml.template` includes `TOGETHER_API_KEY`; stale `openai-secret`/`anthropic-secret` references updated in Layer 4 manifest |
| AC-20 | 4 | GHCR base image access documented (public or PAT-gated) |
| AC-21 | 5 | Golden path J1 ROI workflow completes end-to-end with live backend |
| AC-22 | 5 | All Layer 3 Neo4j queries verified to filter by `tenant_id`; hostile cross-tenant tests added |
| AC-23 | 5 | `SqlTelemetryEmitter.get_events()` implemented or removed with callers updated |
| AC-24 | 5 | Layer 2 → Layer 3 pipeline integration test passes with tenant scoping and provenance |

---

## Implementation Approach

Steps are ordered by risk and dependency. Each phase can be worked independently after Phase 1 unblocks test execution.

### Phase 1 — Test Infrastructure (1–2 days)

1. **Audit Makefile test targets** — Identify which targets use the global `$(PYTEST)` vs a service venv. Document the gap.
2. **Add `make setup` target** — For each service with a `pyproject.toml`, run `pip install -e ".[dev]"` inside the service directory. This installs `structlog`, `prometheus_client`, `testcontainers`, and other service-specific deps.
3. **Update `test-layer*` targets** — Each target must either: (a) activate the service venv before running pytest, or (b) rely on `make setup` having installed deps into the global env. Choose one approach and apply consistently.
4. **Scope root pytest config** — Audit `pyproject.toml` at repo root for `addopts` that inject plugins not available in all service venvs. Remove or scope them.
5. **Verify `make test` passes** — Run `make test-layer1 test-layer4 test-layer5 test-layer6` and confirm zero collection errors.

### Phase 2 — Functional Test Failures (2–3 days)

6. **Fix HarnessRunRepository.list() callers** — Choose Option A (fix 3 tests to unpack tuple) or Option B (change return type). Apply consistently to all callers. Run `make test-layer4` to confirm 226/226 passing.
7. **Fix stale mock patch in test_analyze_prospect** — Trace the current provider resolution path in `WhitespaceAnalysisWorkflow`. Update the `@patch` decorator to target the correct attribute. Verify the test passes with the real production class.
8. **Fix BusinessCaseInputData fixture** — Inspect `BusinessCaseInputData` model for required fields. Add the missing field to the test fixture. Confirm no `ValidationError`.
9. **Fix SignalDetectionAgent 0-signal output** — Trace `_execute_detect_signals()` to find why the mock LLM response isn't parsed into the signals list. Fix the parsing logic or mock response shape. Confirm `test_detect_signals_returns_complete_result` passes.
10. **Resolve 8 collection failures** — Install `testcontainers` via `make setup` (R1.3). For the tracing module (`value_fabric.layer3.tracing.middleware`), either install the layer3 package into the layer4 venv or add `pytest.importorskip` with a clear message.

### Phase 3 — Incomplete Implementations (3–5 days)

11. **Implement CoreferenceResolver** — Write unit tests first (TDD). Implement `resolve()` with name+type deduplication. Merge provenance from duplicates. Verify Layer 2 extraction pipeline tests still pass.
12. **Migrate platform-contract to Pydantic v2** — Replace `@validator` → `@field_validator`, `@root_validator` → `@model_validator`. Run all contract tests. Confirm zero deprecation warnings.
13. **Implement formula category filter** — Replace `pass  # All variables returned for now` with actual filtering logic. Add a test for `?category=Financial` returning only financial variables.

### Phase 4 — Infrastructure Hardening (2–3 days)

14. **Refactor k8s image references** — Add an `images:` block to `k8s/base/kustomization.yaml` for each service. Replace hardcoded `image:` fields in deployment specs with the Kustomize image name. Update `k8s/overlays/` and `k8s/envs/` to inject real registry values. Document `<org>` placeholder in `k8s/README.md`.
15. **Update Layer 4 secret names** — Rename `openai-secret` → `llm-provider-secret` in `k8s/layer4-agents.yml`. Add `TOGETHER_API_KEY` to `k8s/secrets.yml.template`. Update `k8s/README.md`.
16. **Verify GHCR base image access** — Attempt to pull `ghcr.io/value-fabric/base-images/python:3.11.13-slim-bookworm` without auth. If it fails, add `GHCR_PAT` secret to repo and update `build-deploy.yml`. Document the outcome.

### Phase 5 — Production Readiness (1 week)

17. **Layer 3 tenant isolation audit** — Write a script or test that enumerates all Cypher queries and checks for `tenant_id` filters. Fix any missing filters. Add hostile cross-tenant tests.
18. **Fix frontend tests** — Update MSW handlers to match current API shapes. Fix auth redirect test fixtures. Run `pnpm --dir apps/web test` to confirm all tests pass. (Requires Node 22 — coordinate with devcontainer upgrade.)
19. **Implement or remove SqlTelemetryEmitter.get_events()** — Decide based on whether any production code path calls it. Implement with a SQL query or remove and update callers.
20. **Layer 2 → Layer 3 integration test** — Write a test that runs the full extraction → graph ingestion pipeline with a synthetic document. Assert tenant scoping and provenance on created Neo4j nodes.
21. **Golden path J1 end-to-end test** — Run the ROI workflow with a live Layer 4 backend. Assert the result matches the contract shape. Add to CI as a smoke test.

---

## Priority Matrix

| Priority | Item | Requirement | Effort | Risk if skipped |
|---|---|---|---|---|
| P0 | Fix HarnessRunRepository.list() tuple mismatch | R2.1 | 30 min | Harness list endpoints broken at runtime |
| P0 | Fix stale mock patches (test_analyze_prospect) | R2.2 | 2 hours | False confidence in whitespace workflow |
| P0 | Fix test environment (venv/PYTHONPATH) | R1.1–R1.5 | 1 day | CI cannot validate any service |
| P1 | Fix k8s image paths | R4.1 | 2 hours | Cannot deploy to any cluster |
| P1 | Fix SignalDetectionAgent 0-signal output | R2.4 | 2–4 hours | Signal detection feature non-functional |
| P1 | Fix BusinessCaseInputData fixture | R2.3 | 1 hour | False negative in business case tests |
| P1 | Fix frontend tests | R5.3 | 2–3 days | Frontend CI always red |
| P2 | CoreferenceResolver implementation | R3.1 | 1–2 days | Duplicate entities in knowledge graph |
| P2 | Pydantic v2 migration in platform-contract | R3.2 | 1 day | Will break on Pydantic v3 |
| P2 | Layer 3 tenant isolation audit | R5.2 | 1–2 days | Cross-tenant data leakage risk |
| P2 | GHCR base image access | R4.3 | 2 hours | CI builds fail on base image pull |
| P3 | SqlTelemetryEmitter.get_events() | R5.4 | 4 hours | Telemetry query path broken at runtime |
| P3 | Together.ai secret in k8s template | R4.2 | 30 min | Ops confusion at deploy time |
| P3 | Formula category filter | R3.3 | 2 hours | Category filter silently returns all variables |

---

## Risk / Follow-up

- **Node 20 vs 22**: Frontend tests (R5.3) are blocked until the devcontainer is upgraded to Node 22. This is tracked separately. The frontend test fixes should be written and ready to run once Node 22 is available.
- **Together.ai as primary provider**: The k8s secret rename (R4.2) must be coordinated with any ops runbooks or deployment scripts that reference `openai-secret` for Layer 4. Check for references outside `k8s/` before renaming.
- **Layer 3 app_monolith migration**: `services/layer3-knowledge/src/api/main.py` notes that `app_monolith` is a compatibility shim in-progress. The tenant isolation audit (R5.2) must cover both the new route files and the monolith shim.
- **Pydantic v2 migration scope**: Only `packages/platform-contract` is in scope. Other services already use Pydantic v2 patterns. Do not migrate other packages unless they also show deprecation warnings.
- **HarnessRunRepository.list() option choice**: The spec documents both options (R2.1). The implementation must choose one and apply it consistently. Option A (fix tests) is lower risk; Option B (change return type) requires auditing all callers including API route handlers.
