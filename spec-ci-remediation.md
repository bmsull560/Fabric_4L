# Spec: CI Remediation — Restore CI to Green

## Status
Ready for implementation

---

## Problem Statement

CI is at 12.8% pass rate (51/400 runs) over the past 7 days. Three structural root causes account for the majority of failures, and 14 P0 Critical Gates are failing against real security and governance violations. The goal is to restore CI to a passing state by fixing root causes in priority order — not by suppressing or skipping checks.

---

## Failure Inventory (Priority Order)

### Priority 1 — Merge Conflict Markers (blocks all PR pipelines)

**Impact:** 15/15 Preflight runs fail before any test executes. Every PR is blocked.

**Root cause:** Unresolved `<<<<<<<`/`=======`/`>>>>>>>` markers committed into 37 files across the tree (from merge commit `315e84c14c9306363c718c22c8cb7a292d514eee`).

**Affected files (confirmed via `git grep`):**
- `tests/contract/conftest.py`
- `apps/web/src/api/workflows.ts`
- `apps/web/src/api/generated/l4/index.ts`
- `apps/web/src/api/generated/l5/index.ts`
- `packages/platform-contract/src/typescript/generated/layer4_agents.ts`
- `packages/platform-contract/src/typescript/generated/layer5_ground_truth.ts`
- `scripts/export_openapi.py`
- `services/layer2-extraction/src/layer2_extraction/extraction/cache.py`
- `services/layer3-knowledge/src/agents/provenance_tracking.py`
- `services/layer3-knowledge/src/agents/roi_calculation.py`
- `services/layer3-knowledge/src/agents/value_tree_projection.py`
- `services/layer3-knowledge/src/agents/whitespace_analysis.py`
- `services/layer3-knowledge/src/analytics/centrality.py`
- `services/layer3-knowledge/src/analytics/communities.py`
- `services/layer3-knowledge/src/analytics/similarity.py`
- `services/layer3-knowledge/src/api/dependencies_tenant.py`
- `services/layer3-knowledge/src/api/routes/calculators.py`
- `services/layer3-knowledge/src/api/routes/entities.py`
- `services/layer3-knowledge/src/api/routes/signals.py`
- `services/layer3-knowledge/src/api/routes/value_packs.py`
- `services/layer3-knowledge/src/db/query_execution.py`
- `services/layer3-knowledge/tests/test_query_execution_boundary.py`
- `services/layer4-agents/src/api/routes/workflows.py`
- `services/layer4-agents/src/services/context_gatherer.py`
- `services/layer4-agents/tests/test_context_gatherer.py`
- `services/layer5-ground-truth/src/layer5_ground_truth/api/main.py`
- `services/layer5-ground-truth/src/layer5_ground_truth/api/router.py`
- `services/layer5-ground-truth/src/layer5_ground_truth/api/schemas.py`
- `services/layer5-ground-truth/src/layer5_ground_truth/integration/layer3_client.py`
- `services/layer5-ground-truth/src/layer5_ground_truth/services/freshness_monitor.py`
- `services/layer5-ground-truth/src/layer5_ground_truth/shared_bootstrap.py`
- `services/layer5-ground-truth/tests/test_layer3_failure_modes.py`
- `specs/value_fabric_api_interfaces.py`
- `specs/value_fabric_extraction_pipeline.py`
- `specs/value_fabric_ontology_schema.py`
- `specs/value_fabric_rdf_serialization.py`
- `specs/value_fabric_reference_models.py`

**Resolution approach:**
- Review each file individually — choose the semantically correct version for each conflict.
- For generated TypeScript files (`apps/web/src/api/generated/`, `packages/platform-contract/src/typescript/generated/`): regenerate from source rather than manually resolving.
- For `specs/` files: the `=======` lines are section dividers in docstrings, not conflict markers — verify before touching.
- Verify with `bash scripts/ci/check_conflict_markers.sh` (exits 0 = clean).

---

### Priority 2 — Broken Workflow Configurations (80 phantom failures)

**Impact:** `supply-chain.yml` and `contract-compliance.yml` together account for 80 failures (26% of total) but represent zero test execution — they fail before any job starts.

#### 2a. `supply-chain.yml` — Placeholder `CI_TOOLS_IMAGE`

**Root cause:** `env.CI_TOOLS_IMAGE` on line 24 references `ghcr.io/value-fabric/ci-tools/security-suite@sha256:a4c5f6e7...` — a placeholder digest that does not exist. Four jobs use `container: image: ${{ env.CI_TOOLS_IMAGE }}`:
- `sbom-scan` (line 89)
- `provenance` (line 193)
- `verify-signatures` (line 221)
- `dependency-audit` (line 280)
- `license-check` (line ~283)

**Fix:** Remove the `CI_TOOLS_IMAGE` env var and the `container:` block from each affected job. Replace with inline tool installation using pinned GitHub Actions or direct binary downloads:
- `syft` / `grype` → `anchore/sbom-action` + `anchore/scan-action` (already used in `source-sbom-scan`)
- `cosign` → `sigstore/cosign-installer`
- `pip-audit` → `pip install pip-audit`
- `pip-licenses` → `pip install pip-licenses`

Note: `source-sbom-scan` (runs on every PR/push) already uses GitHub Actions correctly and is unaffected.

#### 2b. `contract-compliance.yml` — Copilot actor failure

**Root cause:** Workflow fails in 0 seconds when triggered by the Copilot actor. The workflow has `permissions: contents: read, issues: write`. The failure before any job starts indicates a missing secret or OIDC permission unavailable to the Copilot actor context.

**Fix:** Add `if: github.actor != 'copilot[bot]'` at the workflow or job level, OR ensure required permissions are available to the Copilot actor. Audit `env:` and `secrets:` blocks to identify the missing credential.

---

### Priority 3 — Docker Compose Ephemeral Stack Failures (~29 runs, 5 workflows)

**Impact:** Smoke Gate, Integration Tests, PR Performance Gate, DAST (Security Gates), and Performance Load Tests all fail at stack startup.

**Root cause:** Services build from `Dockerfile` / `Dockerfile.full` using base image `ghcr.io/value-fabric/base-images/python:3.11.13-slim-bookworm@sha256:86adf8db...`. If this image is in a private registry that CI runners cannot pull without credentials, every `docker compose up --build` fails at the pull step.

**Fix steps:**
1. Determine whether `ghcr.io/value-fabric/base-images/python` requires `packages: read` permission.
2. If private: add a `docker/login-action` step (using `GITHUB_TOKEN`) before `docker compose up` in each affected workflow, OR switch the base image to the public `python:3.11.13-slim-bookworm`.
3. Validate locally: `docker compose -f docker-compose.full.yml config` (no missing env vars).
4. Confirm all required env vars are set in the workflow `env:` block or have safe defaults in the compose file.

**Affected workflows:** `smoke-gate.yml`, `integration-tests.yml`, `pr-performance-gate.yml`, `security-gates.yml` (DAST job), `performance-load-tests.yml`.

---

### Priority 4 — 14 Critical Gates (P0 Policy Violations)

All 14 gates must pass. No waivers. Each fix must address the underlying violation — not the gate definition — unless the gate itself is demonstrably incorrect, in which case fix the gate with a documented rationale.

| Gate ID | Gate Command | Violation Category |
|---|---|---|
| `auth-coverage` | `pytest tests/security/test_sensitive_route_audit_coverage.py` | Routes missing auth coverage |
| `tenant-isolation-hostile` | `pytest tests/security/test_tenant_isolation.py tests/security/test_graph_tenant_hostile_regression.py` | Tenant isolation violations in L3/L4 |
| `openapi-drift` | `python scripts/export_openapi.py && git diff --exit-code contracts/openapi/` | OpenAPI contracts out of sync |
| `production-config-policy` | `make gate-config` → `pytest tests/config/` | Config policy violations (L5) |
| `production-config-policy-layer6` | `pytest tests/k8s/test_production_blockers.py` | Production blockers (L6) |
| `correlation-log-contract` | `pytest tests/security/test_correlation_logging_contract.py` | Correlation logging contract violations |
| `adr027-layer3-imports` | `python scripts/ci/check_layer3_imports.py --strict` | L3 import path violations (ADR-027) |
| `layer3-tenant-dependency-imports` | `python scripts/ci/check_layer3_legacy_tenant_dependency_imports.py` | Legacy tenant dependency imports in L3 |
| `env-contract-structure` | (gate script per `critical-gates.yml`) | Env contract structure violations |
| `p0-auth-boundaries` | `pytest tests/security/test_auth_boundaries.py` | Auth boundary violations |
| `p0-auth-source` | `pytest tests/security/test_auth_source_validation.py` | Auth source validation failures |
| `p0-rate-limit-safety` | `pytest tests/security/test_rate_limit_safety.py` | Rate limit safety violations |
| `p0-jwt-config` | `pytest tests/security/test_jwt_config_validation.py` | JWT config violations |
| `p0-cross-tenant-write` | `pytest tests/security/test_cross_tenant_write.py` | Cross-tenant write violations |

**Approach for each gate:**
1. Run the gate command locally to get specific violation output.
2. Fix the underlying code violation (not the test or gate).
3. Re-run the gate to confirm it passes.
4. If the gate is invalid/noisy, fix the gate definition with a documented rationale.

---

### Priority 5 — Secondary Failures (after P1–P4 are green)

| Workflow | Root Cause | Fix |
|---|---|---|
| Security Validation — JWT_SECRET on feature branches | `TEST_JWT_SECRET` scoped to `main` only | Make secret available to all branches, or add `if: secrets.TEST_JWT_SECRET != ''` guard with explicit skip message |
| `layer4-route-contract-matrix-check` | L4 route matrix out of sync | Update matrix in `scripts/ci/check_layer4_route_contract_matrix.py` to match current routes |
| Contract Drift Check — deprecation drift | Deprecated fields not annotated | Annotate per `scripts/ci/check_deprecation_drift.py` expectations |
| Build and Deploy — layer6-benchmarks | Docker build failure | Debug `services/layer6-benchmarks/Dockerfile`; likely broken `uv.lock` or missing dep |
| Kubernetes Manifest Validation — dev overlay | `k8s/envs/dev/kustomization.yaml` invalid | Fix missing resource reference or invalid field in dev overlay |
| K8s Readiness — kustomize install | SHA256 checksum stale | Verify checksum against kustomize v5.4.3 release |
| OpenAPI Drift Check — export script | `scripts/export_openapi.py` has conflict markers | Resolved by Priority 1 |
| Prod Readiness Gates — policy schema | `.fabric/prod-gates.policy.yaml` invalid | Fix schema; verify with `make gates-validate-policy` |
| Launch Readiness Pipeline — repo verification | Repo verification script fails | Debug and fix the verification script |
| Verify Gate — shim divergence | Shim out of sync | Run `make verify` locally; identify and fix the specific shim |
| Mandatory Test Profile — Python failures | Real test failures | Run mandatory profile locally; fix each failure |
| CodeQL Analysis | Analysis errors (both language packs) | Check GitHub Advanced Security quota; fix CodeQL config |
| Generated API Freshness — Node.js setup | Node.js toolchain setup fails | Verify Node version pin matches available runner images |

---

## Requirements

1. **No test suppression.** Do not add `continue-on-error: true`, skip markers, or `if: false` conditions to make gates pass.
2. **No P0 waivers.** All 14 Critical Gates must pass with real code fixes.
3. **Per-file conflict resolution.** Each conflicted file reviewed individually; generated files regenerated from source.
4. **Self-contained workflows.** After removing `CI_TOOLS_IMAGE`, each job installs its own tools via pinned actions or verified binary downloads.
5. **Gate fixes require regression verification.** Each Critical Gate fix verified by re-running the gate command locally.
6. **Tenant isolation must not be weakened.** Any fix touching tenant-scoped code must preserve `tenant_id` filtering in all queries and writes.
7. **Contract alignment required.** If a gate fix changes an API response shape, the OpenAPI contract, TypeScript types, and TanStack Query hooks must be updated in sync.

---

## Acceptance Criteria

- [ ] `bash scripts/ci/check_conflict_markers.sh` exits 0
- [ ] `supply-chain.yml` completes on PR/push without referencing `CI_TOOLS_IMAGE`
- [ ] `contract-compliance.yml` does not fail in 0 seconds for any actor
- [ ] Docker Compose ephemeral stack starts successfully in CI (Smoke Gate passes)
- [ ] All 14 Critical Gates pass locally:
  ```
  pytest -q tests/security/test_auth_boundaries.py \
             tests/security/test_jwt_config_validation.py \
             tests/security/test_cross_tenant_write.py \
             tests/security/test_auth_source_validation.py \
             tests/security/test_rate_limit_safety.py \
             tests/security/test_sensitive_route_audit_coverage.py \
             tests/security/test_tenant_isolation.py \
             tests/security/test_graph_tenant_hostile_regression.py \
             tests/security/test_correlation_logging_contract.py
  ```
- [ ] `python scripts/export_openapi.py && git diff --exit-code contracts/openapi/` exits 0
- [ ] `make gate-config` exits 0
- [ ] `python scripts/ci/check_layer3_imports.py --strict` exits 0
- [ ] `python scripts/ci/check_layer3_legacy_tenant_dependency_imports.py` exits 0
- [ ] Overall CI pass rate recovers to ≥ 70% (from 12.8%)

---

## Implementation Steps (Ordered)

1. **Resolve conflict markers** — Review and fix all 37 conflicted files individually. Regenerate generated TypeScript files from source. Verify with `bash scripts/ci/check_conflict_markers.sh`.

2. **Fix `supply-chain.yml`** — Remove `CI_TOOLS_IMAGE` env var and all `container: image:` blocks. Replace with inline tool installation using pinned GitHub Actions and `pip install`.

3. **Fix `contract-compliance.yml`** — Identify the missing secret/permission for the Copilot actor. Add actor guard or fix permission scope.

4. **Fix Docker Compose stack startup** — Determine base image auth requirements. Add registry login step or switch to public base image. Validate with `docker compose -f docker-compose.full.yml config`.

5. **Run each Critical Gate locally** — Execute each gate command to capture specific violation output before writing any fixes.

6. **Fix P0 security gate violations** — Address `p0-auth-boundaries`, `p0-jwt-config`, `p0-cross-tenant-write`, `p0-auth-source`, `p0-rate-limit-safety` in the underlying code. Re-run each gate to confirm.

7. **Fix tenant isolation and auth coverage gates** — Address `auth-coverage`, `tenant-isolation-hostile`, `correlation-log-contract`, `adr027-layer3-imports`, `layer3-tenant-dependency-imports`.

8. **Fix OpenAPI drift and config policy gates** — Sync `contracts/openapi/` via `scripts/export_openapi.py`. Fix `production-config-policy` and `production-config-policy-layer6`.

9. **Fix `env-contract-structure` gate** — Identify and fix the env contract structure violation.

10. **Address secondary failures** — JWT_SECRET branch scoping, L4 route matrix, deprecation drift, layer6 Docker build, k8s dev overlay, kustomize checksum, prod readiness policy schema.

11. **Validate end-to-end** — Run `make verify` locally. Confirm `bash scripts/ci/check_conflict_markers.sh` exits 0. Push to a feature branch and verify CI pass rate.
