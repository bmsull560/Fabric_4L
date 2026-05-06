# L4/L5 Governance Lineage Contract

## Canonical objects

All governance workflow objects are tenant-scoped and **immutable once written** for audit purposes. Each object carries:
- `lineage.business_case_id` or `lineage.value_model_id`
- `lineage.correlation_id` (shared cross-object correlation key)

Objects:
- `ReviewRequest`
- `ApprovalDecision`
- `VersionRecord`
- `VersionDiff`
- `AuditExportJob`

## Endpoints (Layer 4 canonical façade over L5 governance data)

- `POST /v1/governance/reviews` → create `ReviewRequest`
- `POST /v1/governance/reviews/{review_id}/decisions` → create immutable `ApprovalDecision`
- `POST /v1/governance/versions` → snapshot `VersionRecord`
- `GET /v1/governance/versions/{version_id}` → retrieve `VersionRecord`
- `GET /v1/governance/versions/{version_id}/diff?compare_to_version_id={id}` → compute `VersionDiff`
- `POST /v1/governance/audit/exports` → create `AuditExportJob` (approval-gated)
- `GET /v1/governance/lineage/{correlation_id}` → end-to-end lineage retrieval

## Approval-gated export invariant

`AuditExportJob` creation is blocked unless a corresponding `ApprovalDecision.decision == "approved"` exists for the `review_id`.

- blocked state: `status=blocked`, `reason=approval_required`
- allowed state: `status=pending`

## Frontend query-key mappings

- `QK.governance.review(reviewId)` ↔ `GET/POST /v1/governance/reviews`
- `QK.governance.reviewQueue(filters)` ↔ `GET /v1/governance/reviews` (queue projection)
- `QK.governance.auditExport(jobId)` ↔ `POST /v1/governance/audit/exports`
- `QK.governance.lineage(correlationId)` ↔ `GET /v1/governance/lineage/{correlation_id}`
- `QK.versions.detail(versionId)` ↔ `GET /v1/governance/versions/{version_id}`
- `QK.versions.compare(versionId, compareToVersionId)` ↔ `GET /v1/governance/versions/{version_id}/diff`
