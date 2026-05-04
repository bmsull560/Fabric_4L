# Governance & Compliance Implementation Reference (GDPR / CCPA / SOC 2)

## Purpose

This document is the audit-facing implementation reference that maps privacy/security controls to **implementation artifacts**, **tests**, and **CI evidence generation**.

- **Frameworks covered:** GDPR, CCPA/CPRA, SOC 2 (Common Criteria).
- **Audience:** Security Engineering, Privacy Operations, Internal Audit, and service owners.
- **Companion document:** `docs/compliance/control-matrix.md`.
- **Last updated:** 2026-04-29.

---

## 1) Control-to-Implementation Mapping

| Control Theme | GDPR / CCPA / SOC 2 | Implementation Artifacts (Code Paths) | Validation Tests | CI / Evidence Generation |
| --- | --- | --- | --- | --- |
| Identity, authn/authz, tenant boundary enforcement | GDPR Art. 5(1)(f), Art. 25, Art. 32; CCPA §1798.150; SOC 2 CC6.1/CC6.6/CC6.7 | `shared/identity/middleware.py`, `shared/identity/isolation.py`, `shared/identity/permissions.py` | `tests/integration/test_tenant_isolation_end_to_end.py`, `tests/integration/test_cross_layer_tenant_isolation.py` | `.github/workflows/pr-checks.yml`, `.github/workflows/security-gates.yml`, `make verify` |
| Audit immutability and accountability | GDPR Art. 5(2), Art. 30, Art. 33; CCPA accountability; SOC 2 CC7.2/CC7.3 | `shared/audit/models.py`, `shared/audit/emitter.py`, `value-fabric/layer4-agents/migrations/versions/003_add_audit_events.py` | `tests/integration/test_tenant_provisioning_audit.md` (procedure), migration-level verification during service tests | `make test-layer4`, PR checks with migration and test execution |
| Retention/deletion policy enforcement | GDPR Art. 5(1)(e), Art. 17; CCPA §1798.105; SOC 2 CC3.2/CC8.1 | `value-fabric/layer1-ingestion/src/shared/config.py`, `value-fabric/layer1-ingestion/src/shared/tasks.py` (`cleanup_old_content`) | `tests/contracts/test_retention_deletion_contract.py` | `make verify` (contract test stage), CI test artifacts |
| DSAR access/export/delete process control | GDPR Art. 15/17/20; CCPA §1798.100/105/110; SOC 2 CC2.3/CC8.1 | `value-fabric/layer4-agents/src/tenants/api/routes/tenants.py`, `value-fabric/layer4-agents/src/tenants/api/routes/users.py`, `value-fabric/layer4-agents/src/tenants/api/routes/api_keys.py`, `value-fabric/layer4-agents/src/api/routes/analysis.py` | Layer/service integration tests under `tests/integration/` (tenant provisioning/isolation paths) + operational DSAR workflow below | PR checks + release checklist runbooks in `docs/troubleshooting/runbooks/infrastructure/release-checklist.md` |
| Change governance and contract integrity | GDPR Art. 24; SOC 2 CC1.2/CC5.2 | `packages/platform-contract/CONTRACT.md`, `docs/platform-contract/DEPRECATION_MAP.md`, `contracts/` | `tests/contracts/` suite | `make verify`, contract gate tests in `tests/contracts/gate/` |

---

## 2) Data Classes and Retention/Deletion Policies by Subsystem

| Subsystem | Data Class | Examples | Default Retention | Deletion/Disposition Mechanism | Owner |
| --- | --- | --- | --- | --- | --- |
| Layer 1 Ingestion | Raw content and crawl metadata | Raw HTML, capture artifacts, extraction staging records | 30 days | `cleanup_old_content(days)` marks aged content as `DELETED`; default policy derived from `retention_days` setting | Layer 1 Engineering + Data Governance |
| Layer 2 Extraction | Intermediate extraction payloads | Ontology extraction results, transform intermediates | Environment/policy controlled; align to tenant contract | Job lifecycle cleanup and downstream persistence controls | Layer 2 Engineering |
| Layer 3 Knowledge | Knowledge graph + analytics operational records | Entity/relationship views, operational security telemetry | Service policy controlled; operational telemetry defaults to short-lived windows where configured | Service-level cleanup managers and tenancy controls | Layer 3 Engineering |
| Layer 4 Agents | Workflow state and tenant administration records | Agent workflow state, tenant/user/API-key lifecycle records | Lifecycle-bound + policy constrained | Deactivation/delete APIs; workflow state cleanup mechanisms | Layer 4 Engineering + Privacy Ops |
| Shared Audit | Immutable audit events | Security-relevant CRUD and governance actions | 7 years (baseline objective) | Append-only model + archival/retention process by operations | Security Engineering + SRE |
| Telemetry / Observability | Traces, metrics, logs | OpenTelemetry traces, app/service metrics | Per observability backend policy (short/medium-term) | Backend retention policies + log routing lifecycle | SRE |
| Backups / DR Artifacts | Database/object store snapshots | Postgres backups, object storage snapshots | As defined by DR policy and legal/compliance requirements | Backup expiry/rotation + documented recovery tests | Platform Engineering + SRE |

### Policy notes

1. Legal hold supersedes ordinary deletion windows.
2. Tenant-specific contractual obligations may require longer retention than defaults.
3. Deletion in one layer can require asynchronous downstream completion in dependent layers.

---

## 3) DSAR Workflow and Ownership

## 3.1 DSAR API Surfaces

- Tenant and user management: `value-fabric/layer4-agents/src/tenants/api/routes/tenants.py`, `users.py`, `api_keys.py`.
- Export-related routes: `value-fabric/layer4-agents/src/api/routes/analysis.py` and Layer 3 export surface in `value-fabric/layer3-knowledge/src/api/main.py`.

## 3.2 DSAR process flow

1. **Intake & identity verification** (Privacy Operations).
2. **Scope and lawful-basis/legal-hold determination** (Privacy Operations + Legal).
3. **Execution via APIs and approved operations** (Layer owners).
4. **Evidence collection and fulfillment log** (Security/SRE + Privacy Operations).
5. **Customer response and closure** (Privacy Operations).

## 3.3 RACI (condensed)

| DSAR Activity | Responsible | Accountable | Consulted | Informed |
| --- | --- | --- | --- | --- |
| Intake and identity verification | Privacy Operations | Privacy Lead | Support, Legal | Security |
| Access/export data retrieval | Layer Engineering owners | Product/Platform Engineering manager | Security, Privacy Ops | Support |
| Delete/deactivate execution | Layer Engineering owners | Privacy Lead | Legal, Security | Support |
| Audit evidence packaging | Security Engineering + SRE | Security Lead | Privacy Ops | Internal Audit |

---

## 4) Audit Evidence Generation Mapping

| Evidence Type | Script/Workflow | Output | Control Coverage |
| --- | --- | --- | --- |
| Full verification suite | `make verify` | Lint/type/test/contract/build logs | SOC 2 change management + control operation evidence |
| Agent behavior/eval evidence | `make evals` | Golden-trace evaluation output | Agent safety/quality governance support |
| Governance matrix change enforcement | `.github/scripts/check-control-matrix.sh` via PR checks | CI status + job logs | Documentation governance and control traceability |
| Security gate scans | `.github/workflows/security-gates.yml` | Security scan logs/artifacts | Vulnerability and secure SDLC controls |
| Release readiness checks | `docs/troubleshooting/runbooks/infrastructure/release-checklist.md` | Human-run checklist evidence | Production change governance |

---

## 5) Operational Review Cadence

- **Monthly:** retention/deletion exceptions, DSAR SLA attainment, authn/authz changes.
- **Quarterly:** full control mapping review and sampling of evidence artifacts.
- **Per material change:** update this document and `docs/compliance/control-matrix.md` in the same PR when control mappings shift.
