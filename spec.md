# Spec: Sprint 4 — Frontend Launch Paths and Demo-Grade UX
# Spec: Sprint 5 — Auth, Tenant Isolation, and Security Audit
# + Sprint 6 — Infra, Deployment, and Release Gates

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

## Files Expected to Change

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
| `k8s/envs/prod/kustomization.yaml` | Remove placeholder digests |
| `k8s/envs/prod/kustomization.yaml.template` | New — template with `<resolved-by-ci>` markers |
| `scripts/check-no-placeholder-digests.sh` | New — CI guard script |
| `.github/workflows/environment-promotion.yml` | Add pre-deploy check step |
| `services/layer3-knowledge/tests/test_vault_config.py` | New — unit test for `_load_from_vault()` |
| `docs/governance/compatibility-debt-registry.md` | Add Vault v1 release note |
| `services/layer4-agents/src/database.py` | Fix 501→422, add `DeprecationWarning` |
| `services/layer4-agents/tests/` | Add/update test for deprecation + 422 |

---

---

# Spec: Repo Cleanup Audit — Technical Debt Reduction Pass

## Status
Ready for implementation

---

## Problem Statement

A production-minded audit of the Fabric_4L repository identified concrete maintainability, safety, and DX issues across six categories. This spec covers the agreed scope: **quick wins** (low-risk, high-leverage) plus two higher-effort items explicitly requested — full WfPrimitives caller migration and CI security workflow consolidation.

The audit was constrained by the churn guard: no broad renames, no style-only diffs, no new dependencies, no touching unrelated files.

---

## Repo Cleanup Audit

### Category 1 — Dead / Orphaned Root-Level Scripts

**Issue:** Three root-level Python scripts are one-time migration artifacts with no ongoing purpose.
- `cleanup_pytest_cache.py` — hardcoded Windows path `c:/Users/BBB/Fabric_4L`; does nothing on Linux CI.
- `fix_all_relative_imports.py` — bulk-fixed Layer 3 relative imports; migration complete, no remaining `from ...X` patterns in `services/layer3-knowledge/src/`.
- `fix_test_imports.py` — bulk-fixed legacy `from shared.X` imports; migration complete, zero remaining `from shared.` in `services/` or `tests/`.

**Why it matters:** Orphaned scripts at the repo root create confusion about what's canonical tooling vs. one-off fixers. The Windows-path script silently does nothing in CI.
**Severity:** Low
**Recommended fix:** Delete all three files.
**Estimated effort:** Small

---

**Issue:** `compose-resolved.yml` (784 lines, generated Docker Compose artifact) is committed to the repo but not in `.gitignore`.
**Why it matters:** Generated artifacts in version control create merge conflicts and mislead readers about the canonical compose definition.
**Severity:** Low
**Recommended fix:** Add `compose-resolved.yml` to `.gitignore`.
**Estimated effort:** Small

---

**Issue:** `pyrightconfig.json` `strict` array references three files that no longer exist (`value_fabric/layer3/security/query_validator.py`, `value_fabric/layer3/security/monitor.py`, `value_fabric/layer3/analytics/manager.py`). The `value_fabric/` directory is deprecated and these paths resolve to nothing.
**Why it matters:** Pyright silently ignores missing strict paths, so the strict-mode enforcement is a no-op for those three entries. Misleads engineers into thinking those modules are type-checked strictly.
**Severity:** Low
**Recommended fix:** Remove the three dead paths from `pyrightconfig.json` `strict` array. Keep `tests/layer3/test_typed_payloads.py` (exists).
**Estimated effort:** Small

---

**Issue:** Three root-level spec files (`spec-oidc-audit.md`, `spec-test-report.md`) are committed alongside canonical docs. They are working documents, not reference documentation.
**Why it matters:** Root-level clutter; readers can't distinguish canonical docs from working notes.
**Severity:** Low
**Recommended fix:** Move to `specs/` directory (which already exists and contains similar working documents).
**Estimated effort:** Small

---

### Category 2 — Stale Contracts

**Issue:** All three `review_by` dates in `contracts/drift-allowlist.yaml` are `2026-05-15`, which is now past (today: 2026-05-18).
**Why it matters:** Stale allowlist entries mean known contract drift is no longer being actively reviewed. The drift check script reads this file; stale entries silently suppress failures.
**Severity:** Medium
**Recommended fix:** Update all three `review_by` dates to a future date (e.g., `2026-08-15`) and add a comment documenting the review outcome.
**Estimated effort:** Small

---

### Category 3 — Frontend: WfPrimitives Shim Migration

**Issue:** 81 production files import from `@/components/WfPrimitives`, a deprecated compatibility shim explicitly frozen against new additions. The shim re-exports from canonical Fabric/shadcn primitives. Callers import: `Btn`, `SectionCard`, `MetricCard`, `StatusBadge`, `DataTable`, `PageHeader`, `EntityBadge`, `EntityType`.

**Why it matters:** The shim is a maintenance liability — any change to the underlying primitives must be verified against the shim's re-export surface. New engineers don't know which import path is canonical. The shim's own JSDoc says "migrate callers to direct imports."
**Severity:** Medium
**Recommended fix:** Replace all `WfPrimitives` imports with direct imports from canonical locations:

| WfPrimitives export | Canonical import |
|---|---|
| `Btn` | `@/components/ui/button` → `Button` (aliased as `Btn` where needed, or rename) |
| `SectionCard` | `@/components/ui/fabric/FabricCard` |
| `MetricCard` | `@/components/blocks` |
| `StatusBadge` | `@/components/blocks` |
| `DataTable` | `@/components/ui/fabric` |
| `PageHeader` | `@/components/ui/fabric/PageHeader` |
| `EntityBadge` | `@/components/ui/fabric` |
| `EntityType` | `@/components/ui/fabric` (type import) |

After migration, delete `WfPrimitives.tsx` and remove its export from `components/index.ts`.
**Estimated effort:** Medium

---

### Category 4 — Frontend: Noise / Minor Issues

**Issue:** 10 files contain `"use client"` directives. This is a Next.js RSC directive — it is a no-op in Vite/React but creates confusion about the framework.
**Why it matters:** Engineers unfamiliar with the codebase may assume Next.js patterns apply. The directive is harmless but misleading.
**Severity:** Low
**Recommended fix:** Remove `"use client"` from all files in `apps/web/src/`. The shadcn/ui files (`form.tsx`, `sheet.tsx`, `toggle-group.tsx`, `command.tsx`, `sidebar.tsx`) were likely copied from a Next.js template — strip the directive.
**Estimated effort:** Small

---

**Issue:** `components/layout/Layout.tsx` (783 lines) is exported from `components/index.ts` but is not imported anywhere in the application. The router uses `GlobalLayout` exclusively.
**Why it matters:** Dead code at 783 lines is significant noise. It also contains a duplicate `vp-theme` localStorage write that conflicts with `ThemeContext`.
**Severity:** Low
**Recommended fix:** Verify no external consumers, then delete `Layout.tsx` and remove its export from `components/index.ts`.
**Estimated effort:** Small

---

### Category 5 — CI: Security Workflow Consolidation

**Issue:** Three overlapping security CI workflows run on PRs to `main`:
- `security-gate.yml` (77 lines) — runs `pytest tests/security/` on every PR
- `security-gates.yml` (653 lines) — comprehensive: Bandit, Semgrep, CodeQL, secret scanning, OWASP, tenant isolation
- `security-gates-merged.yml` (241 lines) — subset of `security-gates.yml` targeting `main`, `staging`, `production`

`security-gate.yml` is a strict subset of what `security-gates.yml` already does. `security-gates-merged.yml` overlaps with `security-gates.yml` on the `main` branch trigger.

**Why it matters:** Duplicate CI jobs waste runner minutes, slow PR feedback, and create confusion about which workflow is authoritative when one passes and another fails.
**Severity:** Medium
**Recommended fix:** 
1. Delete `security-gate.yml` — its `pytest tests/security/` step is already covered by `security-gates.yml`.
2. Merge `security-gates-merged.yml`'s unique jobs (if any) into `security-gates.yml` under a branch filter, then delete `security-gates-merged.yml`.
3. `security-gates.yml` becomes the single authoritative security workflow.
**Estimated effort:** Medium

---

### Category 6 — Backend: `print()` in Production Crawler Code

**Issue:** `services/layer1-ingestion/src/crawler/httpx_crawler.py` and `quality_gate.py` contain `print()` statements in production code paths (not migrations, not scripts).
**Why it matters:** `print()` bypasses structured logging (`structlog`), is invisible to log aggregators, and pollutes stdout in production containers.
**Severity:** Low
**Recommended fix:** Replace with `logger.debug(...)` using the existing `structlog` logger pattern already present in the same files.
**Estimated effort:** Small

---

### Category 7 — Config: Layer 6 Auth Bypass Flag Proliferation

**Issue:** `services/layer6-benchmarks/src/settings.py` defines **four** separate auth bypass flags (`ALLOW_INSECURE_DEV_AUTH_BYPASS`, `DEV_AUTH_BYPASS`, `AUTH_BYPASS_ENABLED`, `ALLOW_DEV_AUTH_BYPASS`) where other services use one (`ALLOW_INSECURE_DEV_AUTH_BYPASS`). All four are checked independently.
**Why it matters:** Four flags for the same concern means a security reviewer must check all four. Any one of them can enable bypass. This is a security surface expansion with no documented rationale.
**Severity:** Medium
**Recommended fix:** Consolidate to `ALLOW_INSECURE_DEV_AUTH_BYPASS` (the canonical flag used by Layer 5 and the shared package). Deprecate the other three with a startup warning. Update `.env.example` and `.env.dev.example`.
**Estimated effort:** Small

---

## Priority Plan

### Quick Wins (implement first — all low-risk, independently verifiable)

1. Delete `cleanup_pytest_cache.py`, `fix_all_relative_imports.py`, `fix_test_imports.py`
2. Add `compose-resolved.yml` to `.gitignore`
3. Remove dead paths from `pyrightconfig.json` `strict` array
4. Move `spec-oidc-audit.md` and `spec-test-report.md` to `specs/`
5. Update stale `contracts/drift-allowlist.yaml` `review_by` dates
6. Remove `"use client"` directives from `apps/web/src/`
7. Delete `components/layout/Layout.tsx` (dead code, 783 lines)
8. Replace `print()` with `logger.debug()` in Layer 1 crawler files
9. Consolidate Layer 6 auth bypass flags to single canonical flag

### Medium-Effort Structural Fixes (higher value, more files touched)

10. Migrate all 81 WfPrimitives callers to canonical imports, delete shim
11. Consolidate 3 security CI workflows into 1

### High-Risk / High-Value Refactors (deferred — see below)

- `app_monolith.py` splits (Layer 1: 3071 lines, Layer 3: 3836 lines)
- Layer 2.5 Signal Refinery architecture clarification (not in six-layer docs)
- `from src.` import pattern in Layer 4 tests (requires pytest pythonpath audit)
- Coverage floor gaps for Layers 1, 3, 5, 6

---

## Acceptance Criteria

1. `cleanup_pytest_cache.py`, `fix_all_relative_imports.py`, `fix_test_imports.py` do not exist in the repo root.
2. `compose-resolved.yml` is listed in `.gitignore`.
3. `pyrightconfig.json` `strict` array contains only `tests/layer3/test_typed_payloads.py`.
4. `spec-oidc-audit.md` and `spec-test-report.md` exist under `specs/`, not at repo root.
5. All `review_by` dates in `contracts/drift-allowlist.yaml` are in the future.
6. No `"use client"` directive exists in any file under `apps/web/src/`.
7. `apps/web/src/components/layout/Layout.tsx` does not exist; its export is removed from `components/index.ts`.
8. `services/layer1-ingestion/src/crawler/httpx_crawler.py` and `quality_gate.py` contain no bare `print()` calls.
9. `services/layer6-benchmarks/src/settings.py` defines only `ALLOW_INSECURE_DEV_AUTH_BYPASS`; the other three flags emit `DeprecationWarning` at startup if set.
10. No file under `apps/web/src/` imports from `@/components/WfPrimitives` (except `WfPrimitives.tsx` itself, which is then deleted).
11. `apps/web/src/components/WfPrimitives.tsx` does not exist.
12. `.github/workflows/security-gate.yml` and `.github/workflows/security-gates-merged.yml` do not exist; their coverage is absorbed into `security-gates.yml`.
13. `pnpm --dir apps/web build` passes with no TypeScript errors.
14. `pytest tests/ -x -q` passes (or fails only on pre-existing infra-gated tests).

---

## Implementation Approach

Steps are ordered by risk (lowest first) and independence (each step is verifiable on its own).

1. **Delete orphaned root scripts** — Remove `cleanup_pytest_cache.py`, `fix_all_relative_imports.py`, `fix_test_imports.py`. Verify no CI workflow references them.

2. **Gitignore compose-resolved.yml** — Add single line to `.gitignore`.

3. **Fix pyrightconfig.json** — Remove three dead `strict` paths. Keep `tests/layer3/test_typed_payloads.py`.

4. **Move working spec files** — `git mv spec-oidc-audit.md specs/` and `git mv spec-test-report.md specs/`. Update any internal links.

5. **Update drift-allowlist review dates** — Set all three `review_by` to `2026-08-18`. Add a comment noting the review outcome (SSE representation gap is accepted).

6. **Remove `"use client"` directives** — Strip from all 10 files. No behavior change in Vite.

7. **Delete Layout.tsx** — Confirm zero non-test imports, delete file, remove export from `components/index.ts`.

8. **Replace print() with logger.debug()** — In `httpx_crawler.py` and `quality_gate.py`, use the existing `structlog` logger.

9. **Consolidate Layer 6 auth bypass flags** — Keep `ALLOW_INSECURE_DEV_AUTH_BYPASS`. Add `DeprecationWarning` to the three legacy flag checks. Update `.env.dev.example` comment.

10. **Migrate WfPrimitives callers** — For each of the 81 importing files, replace `WfPrimitives` imports with canonical equivalents. Key mappings: `Btn` → `Button` from `@/components/ui/button`; `SectionCard` → `FabricCard` from `@/components/ui/fabric`; `MetricCard`, `StatusBadge`, `DataTable`, `PageHeader`, `EntityBadge` → `@/components/ui/fabric` or `@/components/blocks`. After all callers are migrated, delete `WfPrimitives.tsx` and remove its export from `components/index.ts`. Run `pnpm --dir apps/web build` to verify.

11. **Consolidate security CI workflows** — Audit `security-gates-merged.yml` for any jobs not in `security-gates.yml`. Merge unique jobs into `security-gates.yml` under appropriate branch filters. Delete `security-gate.yml` and `security-gates-merged.yml`. Verify the remaining workflow covers all previous triggers.

---

## Files Touched

| File | Change |
|---|---|
| `cleanup_pytest_cache.py` | Delete |
| `fix_all_relative_imports.py` | Delete |
| `fix_test_imports.py` | Delete |
| `.gitignore` | Add `compose-resolved.yml` |
| `pyrightconfig.json` | Remove 3 dead strict paths |
| `spec-oidc-audit.md` | Move to `specs/spec-oidc-audit.md` |
| `spec-test-report.md` | Move to `specs/spec-test-report.md` |
| `contracts/drift-allowlist.yaml` | Update 3 stale `review_by` dates |
| `apps/web/src/components/layout/GlobalLayout.tsx` | Remove `"use client"` |
| `apps/web/src/components/layout/AppHeader.tsx` | Remove `"use client"` |
| `apps/web/src/components/layout/LeftNavigation.tsx` | Remove `"use client"` |
| `apps/web/src/workflow/pages/ProspectSetup.tsx` | Remove `"use client"` |
| `apps/web/src/components/workspace/ProspectPromptBuilder.tsx` | Remove `"use client"` |
| `apps/web/src/components/ui/form.tsx` | Remove `"use client"` |
| `apps/web/src/components/ui/sheet.tsx` | Remove `"use client"` |
| `apps/web/src/components/ui/toggle-group.tsx` | Remove `"use client"` |
| `apps/web/src/components/ui/command.tsx` | Remove `"use client"` |
| `apps/web/src/components/ui/sidebar.tsx` | Remove `"use client"` |
| `apps/web/src/components/layout/Layout.tsx` | Delete |
| `apps/web/src/components/index.ts` | Remove `Layout` export; remove `WfPrimitives` export after migration |
| `services/layer1-ingestion/src/crawler/httpx_crawler.py` | Replace `print()` with `logger.debug()` |
| `services/layer1-ingestion/src/crawler/quality_gate.py` | Replace `print()` with `logger.debug()` |
| `services/layer6-benchmarks/src/settings.py` | Consolidate auth bypass flags |
| `.env.dev.example` | Update auth bypass flag comment |
| `apps/web/src/components/WfPrimitives.tsx` | Delete (after all callers migrated) |
| 81 files importing `WfPrimitives` | Migrate to canonical imports |
| `.github/workflows/security-gate.yml` | Delete |
| `.github/workflows/security-gates-merged.yml` | Delete (after merging unique jobs) |
| `.github/workflows/security-gates.yml` | Absorb coverage from deleted workflows |

---

## Deferred / Needs Decision

| Item | Why deferred | Decision needed | Recommended next step |
|---|---|---|---|
| `app_monolith.py` splits (L1: 3071 lines, L3: 3836 lines) | High churn, cross-cutting; splitting requires route ownership decisions | Which route groups move first? Who owns the split? | Create a dedicated spec per layer; start with L3 which already has a migration ledger |
| Layer 2.5 Signal Refinery (`services/layer2-5-signal-refinery/`) | Not documented in the six-layer architecture, not in k8s manifests, but present in `docker-compose.dev.yml` | Is this a permanent layer or a prototype? Should it be in the architecture docs? | Clarify ownership; add to ARCHITECTURE.md or mark as experimental |
| `from src.` imports in Layer 4 tests | Requires pytest `pythonpath` audit; could break test collection if changed naively | Is `pythonpath = ["src"]` in `pyproject.toml` the intended resolution? | Audit Layer 4 test collection with `pytest --collect-only`; fix import style in a dedicated pass |
| Coverage floors for Layers 1, 3, 5, 6 | Adding `fail_under` without knowing current coverage could immediately break CI | What is the current coverage for each layer? | Run `pytest --cov=src --cov-report=term-missing` per layer; set floors at current - 5% |
| `xfail(strict=False)` on cross-tenant write tests | These are security tests that are allowed to pass unexpectedly — masking regressions | Should cross-tenant write tests be `strict=True`? | Review each `xfail` reason; promote to `strict=True` where the underlying behavior is now implemented |
| Layer 6 `DEV_AUTH_BYPASS` / `AUTH_BYPASS_ENABLED` full removal | Removing env vars could break existing deployment configs silently | Are these flags set in any deployment environment? | Audit k8s secrets and `.env` files in deployment environments before removing |
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
