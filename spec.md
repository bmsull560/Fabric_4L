# Spec: Sprint 5 — Auth, Tenant Isolation, and Security Audit
# + Sprint 6 — Infra, Deployment, and Release Gates

## Status
Ready for implementation

---

## Problem Statement

Two sprints of work close the primary launch-risk categories:

**Sprint 5** addresses cross-tenant leakage, duplicated auth stacks, and unclear security boundaries:
- `governance_workflows.py` routes (reviews, versions, audit exports, lineage) have **no auth dependency** — any unauthenticated caller can create review decisions and read audit exports.
- Gate decisions (approve/reject) use `ctx.user_id` for `decision_by` but have **no role check** — any authenticated user can approve a gate regardless of role.
- `services/api` (JWT+bcrypt, no OIDC) is a separate auth stack from Layer 4 (`GovernanceMiddleware` + OIDC/PKCE). The dual-stack creates silent drift risk with no cross-contract test.
- Tenant-isolation tests exist but harness runs, gates, checkpoints, validation calls, and L5 org mapping lack dedicated cross-tenant hostile tests.
- Billing routes exist but Stripe env vars must not crash the app; missing config must return `billing_not_configured`.
- Anthropic adapter raises a bare `NotImplementedError`; needs a typed `ProviderNotImplementedError`.
- Apollo/NewsAPI enrichment returns placeholder data in all modes; must fail closed unless explicit mock mode is set.

**Sprint 6** makes deployment honest and repeatable (extends the existing 3-item spec below):
- LLM cost telemetry is partially wired (commented out in executor, active in whitespace workflow) with an empty Grafana dashboard.
- Harness trace event structured log fields need a contract test.
- Validation outcome and failed/degraded workflow telemetry need structured log field verification.
- Rollback procedure exists at `docs/runbooks/deployment-rollout-and-rollback.md` but needs a release-gate report entry.

---

## Sprint 5 Requirements

### S5-R1 — governance_workflows.py route protection

| ID | Requirement |
|---|---|
| S5-R1.1 | All read routes (`GET /governance/reviews`, `GET /governance/reviews/{id}`, `GET /governance/versions/{id}`, `GET /governance/versions/{id}/diff`, `GET /governance/audit/exports/{id}`, `GET /governance/lineage/{id}`) must require `require_authenticated`. |
| S5-R1.2 | All write routes (`POST /governance/reviews`, `POST /governance/reviews/{id}/decisions`, `POST /governance/versions`, `POST /governance/audit/exports`) must require `require_content_admin` (covers `content_admin`, `tenant_admin`, `super_admin`). |
| S5-R1.3 | Auth dependency must use `value_fabric.shared.identity.dependencies` — not a local implementation. |
| S5-R1.4 | Routes must extract `tenant_id` from the authenticated `RequestContext`, not from request body. |

### S5-R2 — Gate decision RBAC

| ID | Requirement |
|---|---|
| S5-R2.1 | `POST /v1/harness/gates/{gate_id}/decisions` must require `require_content_admin` (reviewer or admin role). |
| S5-R2.2 | `decision_by` must be set from `ctx.user_id` (server-derived); body-supplied `decision_by` must be ignored. |
| S5-R2.3 | A caller with `read_only` or `analyst` role must receive HTTP 403 when attempting a gate decision. |
| S5-R2.4 | A caller with `content_admin`, `tenant_admin`, or `super_admin` role must be permitted. |

### S5-R3 — services/api auth stack risk classification

| ID | Requirement |
|---|---|
| S5-R3.1 | Add a cross-contract test proving a JWT minted by `services/api/app/core/security.py` (`create_access_token`) is accepted by `services/layer4-agents` `decode_jwt` (shared identity). |
| S5-R3.2 | Document the dual-stack in `reports/SECURITY_AUDIT_SPRINT5.md`: Layer 4 (`GovernanceMiddleware` + OIDC/PKCE) is the production path; `services/api` (JWT+bcrypt) is classified as a standalone risk with no OIDC, no PKCE, no CSRF protection. |
| S5-R3.3 | Document cross-stack drift: `services/api` uses `python-jose` (legacy); Layer 4 shared identity uses `PyJWT`. |
| S5-R3.4 | No migration of `services/api` auth this sprint — classification and cross-contract test only. |

### S5-R4 — Tenant-isolation tests

| ID | Requirement |
|---|---|
| S5-R4.1 | Add a test: Tenant A cannot read Tenant B's harness runs (`GET /v1/harness/runs/{run_id}` with wrong tenant → 404). |
| S5-R4.2 | Add a test: Tenant A cannot read Tenant B's gates (`GET /v1/harness/gates/{gate_id}` with wrong tenant → 404). |
| S5-R4.3 | Add a test: Tenant A cannot read Tenant B's checkpoints (`GET /v1/harness/runs/{run_id}/checkpoints` with wrong tenant → 404). |
| S5-R4.4 | Add a test: Tenant A cannot submit a validation call against Tenant B's run → 403 or 404. |
| S5-R4.5 | Add a test: L5 org mapping — `GET /v1/ground-truth/truth-objects` with Tenant B token returns only Tenant B objects (no Tenant A leakage). |
| S5-R4.6 | Add a test: frontend cannot fetch cross-tenant resources — `X-Tenant-ID` header mismatch against JWT claim → 403. |
| S5-R4.7 | All new tests must be in `tests/security/` or `tests/layer4/` and carry `pytest.mark.security` + `pytest.mark.tenant_boundary`. |

### S5-R5 — Security smoke tests

| ID | Requirement |
|---|---|
| S5-R5.1 | Missing tenant context (no JWT, no header) → 422 or 401 (not 200, not 500). |
| S5-R5.2 | Wrong tenant in JWT → 404 on resource lookup (not 200 with other tenant's data). |
| S5-R5.3 | Body `tenant_id` is ignored; authenticated tenant from JWT is used. |
| S5-R5.4 | `decision_by` is server-derived from `ctx.user_id`; body-supplied value is ignored. |
| S5-R5.5 | No secrets (JWT secret, API keys, Stripe keys) appear in structured log output. |
| S5-R5.6 | These checks must be runnable via `make security-smoke` (add to `tests/security/test_security_smoke.py` or a new file in `tests/security/`). |

### S5-R6 — Billing posture

| ID | Requirement |
|---|---|
| S5-R6.1 | Missing `STRIPE_SECRET_KEY` env var must not crash the app on startup. |
| S5-R6.2 | All billing routes must return HTTP 402 with `{"error": "billing_not_configured"}` when Stripe is not configured. |
| S5-R6.3 | `StripeNotConfiguredError` (already exists in `stripe_client.py`) must be caught at the route layer and translated to the above response. |
| S5-R6.4 | Stripe code must remain disabled by default; no Stripe import at module load time unless `STRIPE_SECRET_KEY` is set. |
| S5-R6.5 | Add a test asserting billing routes return 402 with `billing_not_configured` when env var is absent. |

### S5-R7 — Optional provider posture

| ID | Requirement |
|---|---|
| S5-R7.1 | Anthropic adapter must raise a typed `ProviderNotImplementedError` (not bare `NotImplementedError`) when `LAYER4_LLM_PROVIDER=anthropic`. |
| S5-R7.2 | `ProviderNotImplementedError` must be a subclass of `AdapterError` (already defined in `llm_adapter_interfaces.py`). |
| S5-R7.3 | Apollo/NewsAPI enrichment must fail closed (return an error result, not placeholder data) unless `ENRICHMENT_MOCK_MODE=true` is explicitly set. |
| S5-R7.4 | When `ENRICHMENT_MOCK_MODE=true`, placeholder data is permitted and must be clearly tagged with `"mock": true` in the response. |
| S5-R7.5 | Add tests: Anthropic raises `ProviderNotImplementedError`; enrichment fails closed without mock mode; enrichment returns mock-tagged data with mock mode. |

### S5-R8 — Security audit report

| ID | Requirement |
|---|---|
| S5-R8.1 | Create `reports/SECURITY_AUDIT_SPRINT5.md` covering: auth stack comparison, Layer 4 as production path, `services/api` risk classification, cross-stack drift, governance_workflows gap (now fixed), gate RBAC gap (now fixed), billing posture, provider posture. |
| S5-R8.2 | Report must include a "Definition of Done" checklist matching the sprint brief. |

---

## Sprint 6 Requirements (New Items)

### S6-R4 — LLM cost telemetry

| ID | Requirement |
|---|---|
| S6-R4.1 | Uncomment and wire `LLMCostCalculator` in `services/layer4-agents/src/engine/executor.py` so every LLM call records cost via `metrics.record_llm_cost(...)`. |
| S6-R4.2 | Structured log fields emitted per LLM call must include: `tenant_id`, `workflow_id`, `model`, `prompt_tokens`, `completion_tokens`, `cost_usd`. |
| S6-R4.3 | Add a contract test asserting these fields are present in the structured log output for a mocked LLM call. |
| S6-R4.4 | Populate `monitoring/grafana/dashboards/llm-costs.json` with at minimum: total cost by tenant (time series), cost by model (bar), token usage by workflow (table). |

### S6-R5 — Harness trace event and validation outcome telemetry

| ID | Requirement |
|---|---|
| S6-R5.1 | Structured log fields for harness trace events must include: `tenant_id`, `run_id`, `workflow_type`, `stage`, `trace_id`. Verify these are emitted by `Layer4LifecycleLogger`. |
| S6-R5.2 | Validation outcome events must emit: `tenant_id`, `run_id`, `gate_id`, `outcome` (`approved`/`rejected`/`pending`), `decision_by`. |
| S6-R5.3 | Failed/degraded workflow events must emit: `tenant_id`, `run_id`, `error_class`, `error_code`, `stage`. |
| S6-R5.4 | Add contract tests for each structured log schema (harness trace, validation outcome, failed workflow). |

### S6-R6 — Release gate report

| ID | Requirement |
|---|---|
| S6-R6.1 | Create `reports/RELEASE_GATE_SPRINT6.md` stating: no P0 blockers after Sprint 5+6 work, deployment path (kubectl apply / Kustomize), GitOps claims accurate (ArgoCD non-operational, documented), placeholder digest guard passes, K8s manifests render, rollback procedure at `docs/runbooks/deployment-rollout-and-rollback.md`. |

---

## Sprint 6 Requirements (Carried from Previous Spec)

### R1 — Fix `manager.py`: define `VaultSourceNotSupportedError` and raise it

| ID | Requirement |
|---|---|
| R1.1 | Define `class VaultSourceNotSupportedError(RuntimeError)` in `services/layer3-knowledge/src/config/manager.py`. |
| R1.2 | `_load_from_vault()` must raise `VaultSourceNotSupportedError` with a message that names the source and references ESO/environment-backed config as the migration path. It must not return `{}`. |
| R1.3 | The existing test `services/layer3-knowledge/tests/test_vault_config_source.py` must pass without modification. |
| R1.4 | Add a regression test only if the existing test does not verify both the exception type and the message content. (Audit first; add only if needed.) |
| R1.5 | `docs/governance/compatibility-debt-registry.md` already documents this as intentional v1 behavior — confirm the entry is accurate and update only if the implementation diverges from what is documented. |

### R2 — Wire digest guard into environment-promotion CI

| ID | Requirement |
|---|---|
| R2.1 | Add a `Block placeholder image digests` step in `.github/workflows/environment-promotion.yml` before the staging deploy step. |
| R2.2 | Add the same step before the production deploy step. |
| R2.3 | The step must run `bash scripts/check-no-placeholder-digests.sh k8s/envs/<env>/kustomization.yaml` where `<env>` is `staging` or `prod` respectively. |
| R2.4 | The step must fail the job (exit non-zero) if placeholder digests are found, blocking the deploy. |

### R3 — Sprint 0 launch-readiness report

| ID | Requirement |
|---|---|
| R3.1 | Create `reports/launch-readiness-sprint0.md`. |
| R3.2 | Report must include: commands run, test pass/fail counts per suite (from the 2026-05-17 test report or a fresh run), known failures classified as: implementation failure / environment issue / pre-existing unrelated failure. |
| R3.3 | Report must include per-layer coverage figures. |
| R3.4 | Report must state whether release gates are green or blocked, with evidence. |
| R3.5 | Report must include a "Sprint 0 Blockers Snapshot" section with P0/P1/P2 open counts and a link to `docs/readiness/blockers.md`. |
| R3.6 | Report must not claim gates are green unless `make verify` (or the closest available subset) was actually run and passed. |

### R4 — Launch blocker board

| ID | Requirement |
|---|---|
| R4.1 | Create `docs/readiness/blockers.md`. |
| R4.2 | Board must have three sections: **P0 — Release blockers**, **P1 — Must fix before external demo**, **P2 — Post-launch hardening**. |
| R4.3 | Each section must use a table with columns: ID, Area, Blocker/Item, Owner, Status, Evidence/Link. |
| R4.4 | Populate from existing audit evidence: `reports/RELEASE_READINESS_AUDIT_2026-05-12.md` is the primary source for known P0/P1/P2 items. |
| R4.5 | Include a `_Last updated:` datestamp at the top. |
| R4.6 | P0 definition: release-blocking (pilot cannot launch). P1 definition: must fix before external demo. P2 definition: post-launch hardening. |

### R5 — ROADMAP.md canonical-source note

| ID | Requirement |
|---|---|
| R5.1 | Add or strengthen a note near the top of ROADMAP.md (within the first 20 lines or immediately after the executive summary header) stating that `docs/readiness/current.md` is the canonical source for launch readiness and that any percentage in ROADMAP.md is historical/contextual. |
| R5.2 | Do not change the 95% figure in ROADMAP.md. |
| R5.3 | Do not change the 97% figure in `docs/readiness/current.md`. |

---

## Acceptance Criteria

### Sprint 5

1. `governance_workflows.py` — all GET routes return 401 with no credentials; all POST routes return 403 for `analyst` role and 201/200 for `content_admin`.
2. Gate decision endpoint returns 403 for `analyst`/`read_only` callers; `decision_by` in response equals `ctx.user_id`, not any body-supplied value.
3. `reports/SECURITY_AUDIT_SPRINT5.md` exists and classifies Layer 4 as production auth path, `services/api` as standalone risk, and documents cross-stack drift.
4. Cross-contract JWT test passes: token minted by `services/api` `create_access_token` is accepted by shared identity `decode_jwt`.
5. All 6 tenant-isolation tests (S5-R4.1–R4.6) pass under `pytest -m "security and tenant_boundary"`.
6. Security smoke tests (S5-R5.1–R5.5) pass under `make security-smoke`.
7. Billing routes return HTTP 402 `{"error": "billing_not_configured"}` when `STRIPE_SECRET_KEY` is absent; app starts without crashing.
8. Anthropic adapter raises `ProviderNotImplementedError` (subclass of `AdapterError`).
9. Enrichment fails closed without `ENRICHMENT_MOCK_MODE=true`; returns mock-tagged data when set.

### Sprint 6 (New Items)

10. `executor.py` records LLM cost on every call; structured log includes `tenant_id`, `workflow_id`, `model`, `prompt_tokens`, `completion_tokens`, `cost_usd`.
11. `monitoring/grafana/dashboards/llm-costs.json` has ≥3 panels (cost by tenant, cost by model, token usage by workflow).
12. Contract tests pass for harness trace, validation outcome, and failed workflow log schemas.
13. `reports/RELEASE_GATE_SPRINT6.md` exists with no P0 blockers declared.

### Sprint 6 (Carried Items)

14. `k8s/envs/prod/kustomization.yaml` contains no `sha256:1111...7777` values.
15. `k8s/envs/prod/kustomization.yaml.template` exists with `<resolved-by-ci>` markers.
16. `scripts/check-no-placeholder-digests.sh` exits 1 on placeholder digests, 0 otherwise.
17. The check script is referenced in `.github/workflows/environment-promotion.yml`.
18. `pytest services/layer3-knowledge/tests/test_vault_config.py` passes.
19. `docs/governance/compatibility-debt-registry.md` contains a Vault v1 release note.
20. `get_tiered_db_session()` emits `DeprecationWarning` and raises `HTTPException(status_code=422)` for unsupported tiers.
21. No production caller of `get_tiered_db_session()` remains outside of tests.

---

## Implementation Approach

Steps are ordered by dependency. Each step is independently verifiable.

### Sprint 5

1. **Protect `governance_workflows.py` read routes** — Add `Depends(require_authenticated)` to all GET handlers. Import from `value_fabric.shared.identity.dependencies`. Extract `tenant_id` from `RequestContext`.

2. **Protect `governance_workflows.py` write routes** — Add `Depends(require_content_admin)` to all POST handlers. Ensures `content_admin`, `tenant_admin`, and `super_admin` can write; `analyst` and `read_only` get 403.

3. **Add gate decision RBAC** — In `services/layer4-agents/src/api/routes/harness.py`, change the gate decision endpoint to use `Depends(require_content_admin)`. Remove any body-supplied `decision_by`; always set from `ctx.user_id`.

4. **Add `ProviderNotImplementedError`** — In `services/layer4-agents/src/services/llm_adapter_interfaces.py`, add `ProviderNotImplementedError(AdapterError)`. Update the Anthropic branch in `llm_provider.py` to raise it.

5. **Fix enrichment mock-mode guard** — In `enrichment_orchestrator.py`, check `os.environ.get("ENRICHMENT_MOCK_MODE") == "true"` before returning placeholder data. If not set, return a structured error result with `success=False`.

6. **Fix billing fail-closed** — In `services/layer4-agents/src/api/routes/billing.py`, catch `StripeNotConfiguredError` at the route layer and return HTTP 402 `{"error": "billing_not_configured"}`. Verify no Stripe import at module load time.

7. **Write tenant-isolation tests** — Create `tests/security/test_harness_tenant_isolation.py` with tests S5-R4.1–R4.6. Use existing `tenant_a_token`/`tenant_b_token` fixtures.

8. **Write security smoke additions** — Add S5-R5.1–R5.5 checks to `tests/security/test_security_smoke.py` or a new `tests/security/test_sprint5_smoke.py`.

9. **Write cross-contract JWT test** — Create `tests/security/test_cross_stack_jwt_contract.py`. Mint a token with `services/api` `create_access_token`, decode with shared identity `decode_jwt`, assert `tenant_id` and `sub` match.

10. **Write provider and billing tests** — Add to `services/layer4-agents/tests/`: Anthropic raises `ProviderNotImplementedError`; billing returns 402 without `STRIPE_SECRET_KEY`; enrichment fails closed; enrichment returns mock-tagged data with `ENRICHMENT_MOCK_MODE=true`.

11. **Write security audit report** — Create `reports/SECURITY_AUDIT_SPRINT5.md` covering all S5-R8 items.

### Sprint 6 (New Items)

12. **Wire LLM cost in executor** — Uncomment `LLMCostCalculator` import and `metrics.record_llm_cost(...)` call in `engine/executor.py`. Ensure `tenant_id`, `workflow_id`, `model`, token counts, and `cost_usd` are passed.

13. **Add LLM cost log contract test** — Create `tests/contract/test_llm_cost_log_schema.py` asserting required fields are present in structured log output for a mocked LLM call.

14. **Populate Grafana LLM cost dashboard** — Edit `monitoring/grafana/dashboards/llm-costs.json` to add: (a) time-series panel for total cost by tenant, (b) bar panel for cost by model, (c) table panel for token usage by workflow.

15. **Add harness/validation/workflow log contract tests** — Create `tests/contract/test_layer4_log_schemas.py` asserting structured log fields for harness trace events, validation outcomes, and failed/degraded workflows.

16. **Write release gate report** — Create `reports/RELEASE_GATE_SPRINT6.md`.

### Sprint 6 (Carried Items)

17. **Strip placeholder digests from `kustomization.yaml`** — Remove the 7 `digest:` lines with placeholder values.

18. **Create `kustomization.yaml.template`** — Copy structure, replace each `digest:` value with `digest: <resolved-by-ci>`.

19. **Create `scripts/check-no-placeholder-digests.sh`** — Grep for sequential placeholder pattern; exit 1 with a clear message if found.

20. **Wire check into CI** — Add a step in `environment-promotion.yml` before any `kubectl apply`.

21. **Add Vault unit test** — Create `services/layer3-knowledge/tests/test_vault_config.py` asserting `VaultSourceNotSupportedError` is raised for `type: vault`.

22. **Add compatibility-debt-registry entry** — Document `VaultSourceNotSupportedError` as intentional v1 behavior with ESO migration path.

23. **Fix `get_tiered_db_session()`** — Add `warnings.warn(...)`, change `status_code=501` → `422`, verify no production callers remain.

---

## Files Touched

### Sprint 5

| File | Change |
|---|---|
| `services/layer4-agents/src/api/routes/governance_workflows.py` | Add `require_authenticated` (reads) + `require_content_admin` (writes) |
| `services/layer4-agents/src/api/routes/harness.py` | Add `require_content_admin` to gate decision; enforce server-derived `decision_by` |
| `services/layer4-agents/src/services/llm_adapter_interfaces.py` | Add `ProviderNotImplementedError` |
| `services/layer4-agents/src/services/llm_provider.py` | Raise `ProviderNotImplementedError` for Anthropic |
| `services/layer4-agents/src/services/enrichment_orchestrator.py` | Fail closed without `ENRICHMENT_MOCK_MODE=true`; tag mock responses |
| `services/layer4-agents/src/api/routes/billing.py` | Catch `StripeNotConfiguredError` → HTTP 402 `billing_not_configured` |
| `tests/security/test_harness_tenant_isolation.py` | New — harness/gate/checkpoint/validation/L5/frontend cross-tenant tests |
| `tests/security/test_security_smoke.py` | Add S5-R5 smoke checks |
| `tests/security/test_cross_stack_jwt_contract.py` | New — cross-stack JWT acceptance test |
| `services/layer4-agents/tests/test_provider_posture.py` | New — Anthropic, enrichment, billing posture tests |
| `reports/SECURITY_AUDIT_SPRINT5.md` | New — security audit report |

### Sprint 6 (New Items)

| File | Change |
|---|---|
| `services/layer4-agents/src/engine/executor.py` | Uncomment LLM cost recording |
| `monitoring/grafana/dashboards/llm-costs.json` | Add 3 panels |
| `tests/contract/test_llm_cost_log_schema.py` | New — LLM cost log field contract test |
| `tests/contract/test_layer4_log_schemas.py` | New — harness/validation/workflow log schema tests |
| `reports/RELEASE_GATE_SPRINT6.md` | New — release gate report |

### Sprint 6 (Carried Items)

| File | Change |
|---|---|
| `services/layer3-knowledge/src/config/manager.py` | Add `VaultSourceNotSupportedError`; change `_load_from_vault()` to raise it |
| `.github/workflows/environment-promotion.yml` | Add digest guard step before staging + prod deploy steps |
| `docs/readiness/blockers.md` | New — P0/P1/P2 launch blocker board |
| `reports/launch-readiness-sprint0.md` | New — Sprint 0 evidence artifact |
| `ROADMAP.md` | Add canonical-source note (no percentage change) |

### Files confirmed already done — no changes needed

| File | Status |
|---|---|
| `k8s/envs/prod/kustomization.yaml` | ✅ Placeholder digests already removed |
| `k8s/envs/prod/kustomization.yaml.template` | ✅ Already exists with `<resolved-by-ci>` markers |
| `scripts/check-no-placeholder-digests.sh` | ✅ Already exists and correct |
| `docs/governance/compatibility-debt-registry.md` | ✅ Vault v1 release note already present |
| `services/layer4-agents/src/database.py` | ✅ Already uses 422 + DeprecationWarning |
| `services/layer4-agents/tests/test_isolation_tier_provisioning.py` | ✅ Tests already cover 422 + deprecation |

---

## Known Pre-existing Failures (not Sprint 0 scope)

From the 2026-05-17 test report — these are pre-existing and must be classified in the sprint report but not fixed in Sprint 0:

- 17 test collection errors (import topology, missing modules, f-string syntax error)
- Layer 1: 117 failures, 99 errors (mostly testcontainers/Docker unavailable)
- Layer 3: 41 failures, 3 errors (Prometheus registry collision, graph alias export missing)
- Layer 4: 231 failures, 98 errors (infrastructure unavailable)
- Layer 5: 21 failures, 101 errors (testcontainers)
- Frontend: 100 failures (Vitest)

These are environment issues or pre-existing implementation gaps, not regressions introduced by Sprint 0 work.
