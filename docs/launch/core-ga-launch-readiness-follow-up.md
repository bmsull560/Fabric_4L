# Core GA Launch Readiness Follow-Up

**Date:** 2026-05-08  
**Scope:** Core GA deterministic path: `account -> signals -> evidence -> driver -> calculator -> business case`  
**Status:** Local deterministic-path evidence is green. Production readiness is not complete until live/environment evidence is attached.

This document converts the remaining Core GA launch-readiness gaps into executable closure items. It does not replace the launch blocker register or the environment-dependent evidence matrix.

## 1. Locally Closed Items

| Item | Status | Evidence | Notes |
|---|---|---|---|
| Repository final-testing launch gate | PASS | `python scripts/ci/validate_final_testing_launch_gate.py` | Repository-owned launch package is valid; live evidence is still required. |
| Frontend typecheck | PASS | `pnpm --dir apps/web run check` | TypeScript passed after Core GA path hardening. |
| Frontend production build | PASS | `pnpm --dir apps/web run build` | Build passed with existing circular chunk warning tracked below. |
| Full frontend Vitest suite | PASS | `pnpm --dir apps/web run test` | Completed locally on 2026-05-08 after shard-4 isolation; attach CI timing artifact to release evidence if required by release policy. |
| Journey 24 deterministic launch path | PASS | `pnpm --dir apps/web run test:e2e:journey-launch` | Covers local deterministic `account -> signals -> evidence -> driver -> calculator -> business case` path. |
| Account provider drift regression | PASS | `cmd /c node_modules\\.bin\\vitest.cmd run src/pages/Accounts.test.tsx --reporter=verbose --pool=forks --poolOptions.forks.singleFork=true` from `apps/web` | Confirms runtime provider drift fails closed instead of crashing the account page. |
| Targeted Layer 4 agent/workflow tests | PASS | `python -m pytest services/layer4-agents/tests/test_agent_grounding_and_refusal.py services/layer4-agents/tests/test_agent_tool_result_contracts.py services/layer4-agents/tests/test_workflow_canonical_contract.py services/layer4-agents/tests/test_workflow_tenant_isolation.py -q -n 0 -p no:cacheprovider` | 45 tests passed locally with test secrets and SQLite temp DB. |

## 2. CI-Only / Environment-Dependent Items

| Gap | Current Status | Owner | Closure Command Or Job | Required Evidence |
|---|---|---|---|---|
| Broad security suite | OPEN - local broad run timed out or requires intended CI profile | Security owner | CI job running `pytest tests/security` in the supported Python/dependency environment | Security test report, environment descriptor, and any P0/P1 failures entered into `docs/launch/launch-blocker-register.md`. |
| Journey SLO gate | OPEN - requires synthetic monitor output | Test owner / Observability owner | `pnpm --dir apps/web run test:journey-slo-gate` after producing `apps/web/tmp/journey-slo-report.json` or setting `JOURNEY_SLO_REPORT_PATH` | SLO report proving success rate `>= 99%`, p95 latency `<= 12s`, and non-empty response ratio `100%` over 15 minutes. |
| Live LLM provider validation | REQUIRES_ENVIRONMENT | AI platform owner | Staging/live provider E2E job for launch workflows with mock fallback disabled | Redacted run logs proving grounded citations, fact/assumption labeling, refusal for unsupported claims, prompt-injection resistance, cost tracking, and traceability to workflow/account/tenant. |
| SSO/OIDC validation | REQUIRES_ENVIRONMENT | Identity owner | Staging identity validation run against configured provider | Login/logout proof, failed-login mapping, role/group mapping, tenant mapping, and redacted audit event. |
| Billing and metering | REQUIRES_ENVIRONMENT | Billing owner | Provider sandbox/live billing validation job | Meter event sample, idempotency proof, reconciliation result, invoice/usage aggregation sample, and owner sign-off. |
| Rollback / restore drill | REQUIRES_ENVIRONMENT | SRE owner | Release-candidate rollback and restore drill in production-like environment | Redacted rollback transcript, restore proof, data-integrity check, timing result, and approval record. |
| Telemetry dashboards | REQUIRES_ENVIRONMENT | Observability owner | Staging dashboard validation and alert-rule test | Dashboard URLs, metric/log/trace samples, alert rule evidence, threshold rationale, and redaction sample. |
| Alert receiver | REQUIRES_ENVIRONMENT | SRE owner | Alert receiver provider test | Provider delivery proof, escalation route, acknowledgement record, and backup receiver proof. |
| Performance smoke | REQUIRES_ENVIRONMENT | Performance owner | Production-like smoke/performance job | Command output, environment shape, release-candidate SHA, latency/error-rate output, and saturation notes. |
| Production-like E2E rehearsal | REQUIRES_ENVIRONMENT | Test owner | Browser E2E rehearsal with real auth, services, persisted stores, and release candidate SHA | Screenshots/transcript, logs, release-candidate SHA, and blocker classification for any failures. |

## 3. Known Warnings That Are Not Current Launch Blockers

| Warning | Classification | Rationale | Follow-Up |
|---|---|---|---|
| Vite circular chunk warning: `vendor-radix -> vendor-react -> vendor-radix` | P2 Follow-Up unless bundle/performance gates fail | The production build completes and no current Core GA deterministic-path failure is tied to this chunk warning. | Track as bundle hygiene. Escalate to P1 only if bundle budget, startup timing, or performance smoke fails. |
| Prior local full frontend test timeout | RESOLVED_LOCAL | Shard 4 was isolated and `pnpm --dir apps/web run test` now completes successfully locally. | Keep CI timing artifact as release traceability if required by release policy; reopen only if CI fails. |
| Broad security suite timeout | P1 validation gap until CI profile runs | Local host did not complete the intended broad profile. This cannot be counted as pass or fail without CI evidence. | Security owner should run the supported CI profile and classify failures. |

## 4. Required Evidence Artifacts

| Artifact | Expected Location | Producer | Required Before |
|---|---|---|---|
| Repository launch gate output | Release notes or final-testing evidence bundle | Release captain | Final testing entry. |
| Full frontend test report with timing | Local command transcript from `pnpm --dir apps/web run test`; CI artifact attached to release candidate if required by release policy | Frontend/CI owner | Closed locally; keep as release traceability if CI artifact retention is required. |
| Security suite report | CI artifact attached to release candidate | Security owner | Core GA sign-off or explicit waiver. |
| Journey SLO report | `apps/web/tmp/journey-slo-report.json` locally, or CI/staging artifact referenced by `JOURNEY_SLO_REPORT_PATH` | Test/Observability owner | Core GA go/no-go. |
| Live LLM provider validation bundle | Redacted staging/live evidence bundle | AI platform owner | Core GA go/no-go. |
| SSO/OIDC validation evidence | Redacted staging/live evidence bundle | Identity owner | Enterprise Core GA go/no-go. |
| Billing validation evidence | Provider sandbox/live evidence bundle | Billing owner | Paid GA go/no-go. |
| Rollback/restore transcript | Redacted SRE evidence bundle | SRE owner | Core GA go/no-go. |
| Telemetry dashboard and alert evidence | Dashboard links plus redacted samples | Observability/SRE owners | Core GA go/no-go. |
| Performance smoke artifact | CI/staging performance bundle | Performance owner | Core GA go/no-go. |

## 5. Exact Commands To Close Remaining Items

Run from the repository root unless noted.

```bash
# Repository-owned launch package
python scripts/ci/validate_final_testing_launch_gate.py

# Core GA evidence claim guard
python scripts/ci/validate_core_ga_launch_evidence.py

# Frontend full suite, expected in CI if local execution times out
pnpm --dir apps/web run test

# Frontend production build
pnpm --dir apps/web run build

# Core deterministic launch journey
pnpm --dir apps/web run test:e2e:journey-launch

# Journey SLO gate after a synthetic monitor writes the report
pnpm --dir apps/web run test:journey-slo-gate

# Broad security profile in the intended CI environment
pytest tests/security
```

Layer 4 targeted regression command with local test environment:

```powershell
$env:TMP='C:\Users\BBB\Fabric_4L\.tmp'
$env:TEMP='C:\Users\BBB\Fabric_4L\.tmp'
$env:API_KEY_HMAC_SECRET='test-hmac-secret-00000000000000000000000000000000'
$env:DATABASE_URL='sqlite+aiosqlite:///./.tmp/layer4-test.db'
$env:JWT_SECRET='test-jwt-secret-00000000000000000000000000000000'
$env:SERVICE_AUTH_SECRET='test-service-secret-00000000000000000000000000000000'
python -m pytest services/layer4-agents/tests/test_agent_grounding_and_refusal.py services/layer4-agents/tests/test_agent_tool_result_contracts.py services/layer4-agents/tests/test_workflow_canonical_contract.py services/layer4-agents/tests/test_workflow_tenant_isolation.py -q -n 0 -p no:cacheprovider
```

## Go/No-Go Rule

Core GA cannot be marked production-ready until the open environment-dependent evidence is attached or explicitly waived with owner, expiration, monitoring, rollback plan, and scope impact. Paid GA remains blocked unless billing evidence passes or paid launch is removed from scope.
