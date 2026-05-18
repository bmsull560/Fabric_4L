# Launch Decision Artifact (Canonical)

- **Owner:** Release Management (Engineering)
- **Last Updated (UTC):** 2026-05-18
- **Scope:** Production launch go/no-go decision package for Value Fabric.
- **Aligned Runbook:** `docs/runbooks/deployment-rollout-and-rollback.md`
- **Primary Readiness Criteria Source:** `docs/readiness/current.md`

## 1) Consolidated Evidence Ledger

This table maps each launch criterion in `docs/readiness/current.md` to objective, auditable evidence.

| Launch criterion (`docs/readiness/current.md`) | Objective evidence artifact(s) | Verification command or source | Status owner |
|---|---|---|---|
| 1. `make verify` passes with no failing gate | `artifacts/release/gate-result.json`, CI job log for verify gate | `make verify` | Engineering |
| 2. Contract lint + tool contract checks pass | `artifacts/release/gate-result.json`, contract-check step logs | `python scripts/ci/platform_contract_lint.py` + `python scripts/ci/check_tool_contracts.py` | Engineering |
| 3. Security smoke tests pass | Security smoke-test CI logs, release summary | `scripts/ops/release-gate.sh` (security checks section) | Security |
| 4. Graph Query module gate passes on PR + release branches | `.github/workflows/graph-module-tests.yml` run summaries and coverage artifacts | GitHub Actions workflow execution on PR + release branch | Engineering |
| 5. Release gate report indicates no P0 blockers | `artifacts/release/gate-result.json`, `artifacts/release/summary.md` | `scripts/ops/release-gate.sh` + `scripts/ops/render-release-summary.sh` | Engineering + Product |
| 6. Launch readiness percentage aligned across canonical docs | `docs/readiness/current.md` and launch docs consistency checks | Docs review + release checklist validation | Product + Operations |
| Tenant isolation regression-free | Tenant isolation test reports and targeted logs | `pytest tests/security -k tenant` (or equivalent service-specific tenant suites) | Security + Engineering |
| Live workflow validation passes | End-to-end workflow run outputs (L1→L6 critical path) and smoke logs | Release smoke checks after staged deploy | Operations |
| Security regression suite stable | Security regression test artifacts | `pytest tests/security` | Security |

## 2) Go / No-Go Thresholds

Thresholds below are release-blocking unless explicitly waived by Engineering + Security + Operations.

### Mandatory pass/fail gates

- `make verify` = **PASS**.
- Contract lint and tool contract checks = **PASS**.
- Security smoke/regression checks = **PASS**.
- No unresolved **P0** blockers in release gate output.
- Tenant isolation tests = **PASS** (no cross-tenant read/write leak).
- Live workflow validation = **PASS** for critical launch journeys.

### SLO / burn-rate launch guardrails

During staged rollout and first post-release window:

- Error budget burn-rate must remain within predefined SRE alert thresholds for the release window.
- Any sustained high-severity burn-rate alert or sustained 5xx regression beyond agreed threshold is an automatic rollback trigger.
- Readiness/liveness probe failures that breach rollout SLOs are rollback triggers.

## 3) Rollback Triggers (Aligned to Deployment Runbook)

Rollback triggers are aligned to `docs/runbooks/deployment-rollout-and-rollback.md`.

Immediate rollback (or blue-green traffic switch-back) when any occurs:

1. Smoke checks fail post-deploy for any critical Layer 1–Layer 5 or frontend path.
2. Readiness or liveness probe instability persists after remediation window.
3. Error-rate/SLO dashboards show sustained regression above release threshold.
4. Security regression indicates authz/tenant isolation regression.
5. Contract drift causes client-facing response incompatibility.

Operational steps (runbook-consistent):

1. Freeze rollout.
2. Identify failing component via deployment/pod events and dashboards.
3. Execute rollback (`kubectl rollout undo ...`) or blue-green traffic switch-back.
4. Re-run smoke checks.
5. Escalate incident if issue persists.

## 4) Required Multi-Function Sign-Off

Launch cannot proceed without explicit sign-off from:

- Engineering owner
- Security owner
- Product owner
- Operations owner

| Function | Owner | Sign-off status | Timestamp (UTC) | Notes |
|---|---|---|---|---|
| Engineering | _TBD_ | Pending | _TBD_ |  |
| Security | _TBD_ | Pending | _TBD_ |  |
| Product | _TBD_ | Pending | _TBD_ |  |
| Operations | _TBD_ | Pending | _TBD_ |  |

## 5) Launch Execution Controls

### Branch freeze

- Freeze launch branch before production promotion.
- Permit only release-manager-approved fixes with traceable change control.

### Staged rollout

- Execute canary or blue-green strategy per runbook criteria.
- Validate post-stage health before increasing traffic.
- Keep rollback path pre-validated before each traffic step.

### Post-release monitoring

- Monitor predefined burn-rate/error-budget thresholds for the release watch window.
- Monitor probes, latency, error rate, and security anomaly signals.
- Declare launch complete only after watch window exits without rollback triggers.
