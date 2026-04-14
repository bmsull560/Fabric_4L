# Compliance Control Matrix

This matrix maps SOC 2 Common Criteria (CC-series) and relevant FedRAMP Moderate control families to implementation assets in Value Fabric.

## Control Coverage

| Control ID(s) | Implementation location | Verification mechanism | Evidence source | Control owner | Review frequency |
|---|---|---|---|---|---|
| **SOC 2 CC1.1, CC1.2** / **FedRAMP AT, PM** | Governance and operational policies in `docs/SECRETS.md`, `docs/ENVIRONMENT.md`, and incident processes under `docs/runbooks/`. | Quarterly policy walkthrough + annual leadership control attestation. | `docs/SECRETS.md`, `docs/ENVIRONMENT.md`, runbook git history in `docs/runbooks/`. | Security & Compliance Lead | Quarterly |
| **SOC 2 CC2.1, CC2.2** / **FedRAMP CA-2, CA-7** | Required quality gates in `Makefile` (`verify`, `contract-tests`, `evals`) and CI workflows in `.github/workflows/`. | Per-PR CI checks + weekly compliance dashboard review. | GitHub Actions run history, `artifacts/testing/` quality audits. | Engineering Manager | Weekly |
| **SOC 2 CC3.2, CC3.4** / **FedRAMP RA-3, RA-5, SI-2** | Risk mitigation and readiness planning in `LAUNCH_READINESS_REPORT.md`, `Phase2_Readiness_Status.md`, and `.windsurf/plans/launch-readiness-2026-04-11.md`. | Monthly risk review meeting with tracked remediation owners. | Launch/readiness artifacts and plan updates under `.windsurf/plans/`. | Program Management + Security | Monthly |
| **SOC 2 CC5.2, CC5.3** / **FedRAMP CM-2, CM-3, CM-6** | Controlled infrastructure-as-code in `k8s/`, schema contracts in `contracts/`, and deployment composition in `value-fabric/docker-compose.yml`. | Change-control PR approval + contract regression tests (`pytest tests/contract/`). | Git history for `k8s/` + `contracts/`, CI logs for contract tests. | Platform Engineering | Per release |
| **SOC 2 CC6.1, CC6.2** / **FedRAMP AC-2, AC-3, AC-6** | Authentication/authorization controls in `value-fabric/shared/identity/` (JWT, RBAC, middleware, rate limits). | Automated unit tests in `value-fabric/shared/identity/tests/` + semiannual access review. | Test results and role/permission configuration evidence in `shared/identity` code + review records. | IAM Owner | Semiannual |
| **SOC 2 CC6.6, CC6.7** / **FedRAMP SC-7, SC-8, SC-13** | Secret handling and transport controls in `docs/SECRETS.md`, `docs/secrets-management.md`, `k8s/secrets.yml.template`, and env validators in `scripts/ci/validate-env-contract.ts`. | CI env contract validation + quarterly secrets rotation drills. | CI logs for `validate-env-contract`, Infisical/Vault audit dashboards, secrets rotation tickets. | Security Engineering | Quarterly |
| **SOC 2 CC7.2, CC7.3** / **FedRAMP AU-2, AU-6, IR-5, SI-4** | Monitoring and alerting in `monitoring/prometheus/`, `monitoring/alerting/rules.yml`, and incident runbooks in `docs/runbooks/`. | Continuous monitoring + on-call alert review + monthly incident trend review. | Grafana/Prometheus dashboards, Alertmanager history, incident tickets. | SRE Lead | Continuous + Monthly review |
| **SOC 2 CC7.4, CC7.5** / **FedRAMP IR-4, CP-2, CP-4** | Operational recovery procedures and smoke validation in `scripts/smoke/production_smoke.py`, `scripts/smoke/vault_smoke.py`, and runbooks under `docs/runbooks/`. | Pre-release smoke tests + quarterly tabletop incident exercises. | Smoke-test artifacts in `artifacts/`, runbook update logs, exercise notes. | SRE + Incident Commander | Per release + Quarterly |
| **SOC 2 CC8.1** / **FedRAMP SA-11, SA-10** | SDLC and release validation controls in `Makefile`, `tests/contract/`, `tests/evals/`, and `.github/workflows/`. | Release checklist sign-off requiring `make verify` (and `make evals` for agent changes). | CI/CD pipeline status, release checklist records, test output artifacts. | Release Manager | Per release |
| **SOC 2 CC9.2** / **FedRAMP CP-9, CP-10** | Backup/recovery posture captured in operational docs (`k8s/README.md`, runbooks, and platform deployment artifacts). | Quarterly restore simulation + post-exercise review. | Restore drill records, runbook evidence, infrastructure change records. | Platform Operations | Quarterly |

## Audit Query Reference

Use this query as baseline evidence for audit log completeness checks (AU family / CC7):

```sql
SELECT tenant_id,
       action,
       outcome,
       COUNT(*) AS event_count,
       MIN(timestamp) AS first_seen,
       MAX(timestamp) AS last_seen
FROM audit_events
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY tenant_id, action, outcome
ORDER BY last_seen DESC;
```

Primary schema references:
- `value-fabric/layer4-agents/migrations/versions/003_add_audit_events.py`
- `value-fabric/shared/audit/models.py`
