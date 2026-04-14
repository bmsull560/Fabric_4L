# Compliance Control Matrix (GDPR / CCPA / SOC 2)

## Purpose

This matrix maps major GDPR, CCPA, and SOC 2 control themes to concrete **code**, **configuration**, and **operational process** evidence in Value Fabric.

- **Scope:** Current repository implementation.
- **Last reviewed:** 2026-04-14.
- **Update trigger:** Any PR that changes security/governance-sensitive files must also evaluate (and, when needed, update) this matrix.

---

## Control Matrix

| Framework / Control | Requirement Summary | Implementation & Configuration Evidence | Process / Operational Evidence | Owner | Review Cadence |
| --- | --- | --- | --- | --- | --- |
| GDPR Art. 5(1)(f), Art. 32 / CCPA §1798.150 / SOC 2 CC6.1, CC6.6 | Protect confidentiality and integrity of personal data in transit and at service boundaries. | Unified auth + tenant-resolution middleware in `shared/identity/middleware.py` enforces JWT/API key validation and resolves tenant context before protected requests proceed; `X-Tenant-ID` is mandatory for API access in docs. | Security controls are exercised in CI via PR and security workflows (`pr-checks.yml`, `security-gates.yml`) for lint/tests/scans and dependency checks. | Security Engineering | Monthly + per material auth change |
| GDPR Art. 5(1)(c), Art. 25 / CCPA data minimization principles / SOC 2 CC6.7 | Enforce tenant isolation and least data exposure across shared infrastructure. | Tenant isolation utilities in `shared/identity/isolation.py` (`TenantScopedMixin`, `TenantScopedCypher`, `tenant_cache_key`) plus PostgreSQL RLS migration `007_add_rls_policies.py` enforcing tenant filters at DB level. | Architecture and implementation plan document tenant isolation expectations and rollout baseline in `docs/phase3-implementation-plan.md`. | Platform Engineering | Monthly |
| GDPR Art. 30, Art. 5(2), Art. 33 / CCPA accountability / SOC 2 CC7.2, CC7.3 | Maintain immutable audit trail for security/compliance-relevant actions. | `003_add_audit_events.py` creates `audit_events` and DB trigger to block UPDATE/DELETE; shared audit models/emitter in `shared/audit/models.py` and `shared/audit/emitter.py` standardize action taxonomy and structured logging. | Incident/ops runbooks under `docs/runbooks/` + runbook index (`docs/runbooks/README.md`) provide investigation and response playbooks that rely on trace/audit data. | Security Engineering + SRE | Monthly + after incident |
| GDPR Art. 15 / CCPA §1798.100, §1798.110 / SOC 2 CC2.3 | DSAR **Access**: provide data subject access to data associated with an account/tenant. | Tenant/user read paths in Layer 4 tenant API (`src/tenants/api/routes/tenants.py`, `users.py`) provide controlled retrieval under role checks; API auth contract and tenant header requirements documented in `docs/API_REFERENCE.md`. | DSAR access request workflow: (1) verify requester identity, (2) retrieve scoped records via tenant/user APIs, (3) log fulfillment decision in audit trail. This procedural workflow is governed by this matrix and security review records. | Privacy Operations + Tenant Admin Support | Quarterly tabletop + monthly spot-check |
| GDPR Art. 17 / CCPA §1798.105 / SOC 2 CC8.1 | DSAR **Delete**: support deletion/deactivation and enforce downstream deletion windows. | Soft-delete/deactivation APIs for tenants/users/API keys in Layer 4 (`tenants.py`, `users.py`, `api_keys.py`) with service implementations in `tenants/service.py`; ingestion cleanup task `cleanup_old_content(days=30)` in `layer1-ingestion/src/shared/tasks.py` marks expired records deleted. | Deletion SLA: acknowledge request within 72h, complete application-level deletion/deactivation within 30 days unless legal hold applies; unresolved items escalated through on-call and runbook process. | Privacy Operations + Application Engineering | Monthly metrics review |
| GDPR Art. 20 / CCPA portability expectation / SOC 2 CC2.3 | DSAR **Export/Portability**: provide user-consumable export of subject-associated artifacts where supported. | Export paths exist in Layer 4 analysis/tooling (`src/api/routes/analysis.py` export endpoint, `src/tools/document_export.py`) and Layer 3 export proxy (`layer3-knowledge/src/api/main.py` `/v1/documents/export`). | Export SLA: deliver first export package or status update within 7 days of validated request; failures routed via workflow/incident runbooks (`docs/runbooks/workflow-stalled.md`, `high-error-rate.md`). | Product Engineering + Privacy Operations | Monthly |
| GDPR Art. 5(1)(e), Art. 24 / CCPA retention disclosures / SOC 2 CC3.2 | Define and enforce retention/deletion windows. | Layer 1 compliance settings include `retention_days=30` and `audit_log_retention_years=7` in `layer1-ingestion/src/shared/config.py`; model-level retention fields in `src/shared/models.py`; backup/security analytics cleanup use retention configs in Layer 3 managers. | Retention/deletion SLA baseline: 30-day default operational data retention unless overridden by policy; 7-year audit retention; changes require policy + matrix update in PR. | Data Governance | Quarterly |
| GDPR Chapter V (cross-border transfers) / CCPA service provider safeguards / SOC 2 CC9.2 | Control data residency and cross-region handling. | Deployment model supports environment-specific configuration (`docs/ENVIRONMENT.md`) and Kubernetes overlays (`k8s/overlays/*`) allowing region-specific cluster deployments and data-store pinning; S3 region is configurable via `LAYER1_S3_REGION`. | Data residency handling: tenant residency requirement captured at onboarding, mapped to deployment target/region, and validated during environment promotion review; exceptions require security + legal sign-off. | Platform Engineering + Legal/Privacy | Quarterly + before new region launch |
| GDPR Art. 28, Art. 32 / CCPA vendor safeguards / SOC 2 CC1.2, CC5.2 | Govern secrets and third-party access. | Secrets management guidance in `docs/secrets-management.md` and runbook `docs/runbooks/alertmanager-secret-management.md`; repo guardrails prohibit committed secrets (AGENTS + CI secret scans in `security-gates.yml`). | Rotational and incident procedures documented in secrets runbooks; periodic checks via CI security jobs and manual review. | Security Engineering | Monthly |

---

## DSAR Workflow Definitions

### 1) Access workflow

1. Validate requester identity and tenant association.
2. Determine scope (tenant-level, user-level, timeframe).
3. Retrieve records through tenant-scoped APIs and approved read models.
4. Capture decision + fulfillment metadata in audit logs.

### 2) Delete workflow

1. Validate legal basis and hold status.
2. Execute tenant/user/key deactivation or delete operations via approved APIs.
3. Trigger/verify scheduled cleanup paths (retention jobs, storage cleanup).
4. Confirm completion or partial completion with rationale.

### 3) Export workflow

1. Validate requester identity and export scope.
2. Generate export package via document/API export endpoints.
3. Deliver through approved secure channel.
4. Log completion, checksum/manifest reference, and operator.

---

## Retention and Deletion SLA Baseline

| Data Class | Baseline SLA | Evidence |
| --- | --- | --- |
| Raw ingestion content | 30-day retention default; deleted/marked deleted after expiry job window. | `layer1-ingestion/src/shared/config.py`, `layer1-ingestion/src/shared/tasks.py` |
| Audit events | 7-year retention objective (archival process externalized). | `layer4-agents/migrations/versions/003_add_audit_events.py`, `layer1-ingestion/src/shared/config.py` |
| Security/analytics operational telemetry | 30-day retention defaults in cleanup-capable managers. | `layer3-knowledge/src/security/monitor.py`, `layer3-knowledge/src/analytics/manager.py` |

---

## Control Ownership Model

- **Security Engineering:** authentication, authorization, audit integrity, security gates.
- **Platform Engineering:** tenancy isolation, deployment boundary controls, residency placement.
- **Privacy Operations:** DSAR intake/fulfillment governance and legal hold coordination.
- **Data Governance:** retention policy lifecycle and evidence review.
- **SRE:** runbook quality and incident response evidence continuity.

---

## PR / CI Enforcement

A CI policy check now enforces that PRs touching security/governance-sensitive paths also update this control matrix (or explicitly choose files outside the policy scope).

- Check script: `.github/scripts/check-control-matrix.sh`
- Workflow integration: `.github/workflows/pr-checks.yml` (`governance-docs-check` job)

