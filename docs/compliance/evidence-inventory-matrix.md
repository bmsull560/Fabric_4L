# Compliance Evidence Inventory Matrix

## Purpose

This matrix closes the execution gap between documented controls and auditable evidence by standardizing:
- control owner,
- authoritative data source,
- evidence generation frequency,
- retention period, and
- approval workflow.

Source baselines:
- `docs/compliance/control-matrix.md`
- `docs/governance/production-readiness-p0-foundations.md`
- `docs/governance/production-readiness-p1-operational-controls.md`
- `docs/governance/production-readiness-p2-governance-commercialization.md`

## Evidence Inventory

| Control ID | Control Domain | Owner | Data Source | Evidence Frequency | Retention | Approval Workflow |
|---|---|---|---|---|---|---|
| C-AC-01 | Access control + tenant auth integrity | Security Engineering | CI security gates, auth middleware tests, PR artifacts | Per PR + weekly scheduled scan | 7 years | Security reviewer + code owner sign-off in PR |
| C-TI-01 | Tenant isolation and least privilege | Platform Engineering | Tenant isolation tests, RLS migration evidence, architecture controls | Per PR + monthly spot-check | 7 years | Platform owner attestation + Security concurrence |
| C-AU-01 | Immutable audit trail | Security Engineering + SRE | Audit schema/migration evidence, runbook validation logs, audit-evidence artifacts | Monthly + post-incident | 7 years | Incident commander review + Security approval |
| C-DSAR-ACC | DSAR access fulfillment | Privacy Operations | DSAR ticket records, tenant/user API fulfillment logs | Monthly sample + quarterly tabletop | 7 years | Privacy lead approval + legal escalation for exceptions |
| C-DSAR-DEL | DSAR deletion fulfillment | Privacy Operations + App Engineering | Deletion API evidence + cleanup job outputs | Monthly | 7 years | Privacy lead sign-off + on-call escalation for SLA breaches |
| C-DSAR-EXP | DSAR export portability | Product Engineering + Privacy Operations | Export endpoint evidence + secure delivery checklist | Monthly | 7 years | Product owner + Privacy owner dual approval |
| C-RET-01 | Retention and deletion enforcement | Data Governance | Retention config snapshots + cleanup logs | Quarterly | 7 years | Data governance council review |
| C-RES-01 | Data residency and transfer controls | Platform Engineering + Legal/Privacy | Environment promotion artifacts, residency mapping records | Quarterly + before region launch | 7 years | Legal + Platform joint approval |
| C-SEC-03 | Secrets and third-party access governance | Security Engineering | Secret scanning outputs, secrets runbook checks, vendor review records | Per PR + monthly | 7 years | Security owner approval |
| P0-OIDC | Enterprise OIDC production gate | Identity Engineering | OIDC flow test artifacts, provider/JWKS validation logs | Per release + quarterly drill | 7 years | Identity owner + Security sign-off |
| P0-MODEL | Model governance production gate | ML Platform + Governance | Registry promotion logs, approval records, rollback drill artifacts | Per release + quarterly drill | 7 years | Model governance board approval |
| P1-FLAGS | Feature flag operational governance | Platform Engineering | Feature-flag API checks, kill-switch drill logs | Per PR + quarterly drill | 7 years | Platform owner + SRE sign-off |
| P1-QUOTA | Tenant quotas and rate limits | Platform Engineering | Load-test reports, rate-limit behavior artifacts | Per release + quarterly drill | 7 years | Platform owner approval |
| P2-SOC2 | SOC2/ISO control package readiness | Compliance Engineering | Control evidence bundles, access reviews, change samples, incident drill outputs | Quarterly | 7 years | Compliance officer attestation |

## Evidence Artifact Standards

Every generated artifact must include:
- `generated_at` (UTC timestamp),
- `control_id`,
- `owner`,
- `source_workflow` (or source system),
- `sanitized` flag,
- evidence period (`period_start`, `period_end`) when applicable.

## Review Cadence

- Quarterly: full evidence completeness review against this matrix.
- Monthly: freshness check for controls with monthly cadence.
- Per PR: automation-backed controls must publish machine-verifiable artifacts.
