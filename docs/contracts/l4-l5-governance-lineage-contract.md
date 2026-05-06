# L4/L5 Governance Lineage Contract

## Canonical objects

All governance workflow objects are tenant-scoped and **immutable once written** for audit purposes. Each object carries:
- `lineage.business_case_id` or `lineage.value_model_id`
- `lineage.correlation_id` (shared cross-object correlation key)
- `lineage.trace_id` (compatibility alias that must equal `correlation_id` when present)
- `immutable_audit_hash` for every persisted governance/audit object

Objects:
- `ReviewRequest`: submitted review envelope for a business case or value model.
- `ApprovalDecision`: append-only approval, rejection, or change request decision tied to a review.
- `VersionRecord`: immutable snapshot of a business case or value model version.
- `VersionDiff`: deterministic comparison of two `VersionRecord.snapshot` payloads and status.
- `AuditExportJob`: immutable audit export request, including blocked attempts.

## Immutable audit requirements

- Create endpoints are append-only. Reusing `review_id`, `decision_id`, or `version_id` returns `409 Conflict`.
- Decisions must reference an existing review and must carry the same originating business case/value model and correlation identifier.
- Export jobs are recorded even when blocked so attempted exports are auditable.
- `trace_id` and `correlation_id` are immutable lineage values and must match when both are supplied.
- Any object without either `business_case_id` or `value_model_id` is invalid.

## Endpoints (Layer 4 canonical façade over L5 governance data)

- `POST /v1/governance/reviews` → create `ReviewRequest`
- `GET /v1/governance/reviews/{review_id}` → retrieve `ReviewRequest`
- `GET /v1/governance/reviews?status={status}&subject_type={type}&correlation_id={id}` → queue projection for `ReviewRequest`
- `POST /v1/governance/reviews/{review_id}/decisions` → create immutable `ApprovalDecision`
- `POST /v1/governance/versions` → snapshot `VersionRecord`
- `GET /v1/governance/versions/{version_id}` → retrieve `VersionRecord`
- `GET /v1/governance/versions/{version_id}/diff?compare_to_version_id={id}` → compute `VersionDiff`
- `POST /v1/governance/audit/exports` → create `AuditExportJob` (approval-gated)
- `GET /v1/governance/audit/exports/{audit_export_id}` → retrieve `AuditExportJob`
- `GET /v1/governance/lineage/{correlation_id}` → end-to-end lineage retrieval

## Approval-gated export invariant

`AuditExportJob` creation is blocked unless a corresponding immutable `ApprovalDecision.decision == "approved"` exists for the `review_id`.

- blocked state: `status=blocked`, `reason=approval_required`
- allowed state: `status=pending`
- lineage mismatch: `400 Bad Request`
- missing review: `404 Not Found`

## Frontend query-key mappings

- `QK.governance.review(reviewId)` ↔ `GET /v1/governance/reviews/{review_id}` and mutations through `POST /v1/governance/reviews`
- `QK.governance.reviewQueue(filters)` ↔ `GET /v1/governance/reviews`
- `QK.governance.auditExport(jobId)` ↔ `GET /v1/governance/audit/exports/{audit_export_id}` and mutation through `POST /v1/governance/audit/exports`
- `QK.governance.lineage(correlationId)` ↔ `GET /v1/governance/lineage/{correlation_id}`
- `QK.versions.detail(versionId)` ↔ `GET /v1/governance/versions/{version_id}`
- `QK.versions.compare(versionId, compareToVersionId)` ↔ `GET /v1/governance/versions/{version_id}/diff`

## Lineage response contract

`GET /v1/governance/lineage/{correlation_id}` returns:

```json
{
  "reviews": ["ReviewRequest"],
  "decisions": ["ApprovalDecision"],
  "versions": ["VersionRecord"],
  "exports": ["AuditExportJob"]
}
```

Clients must treat the returned arrays as immutable event/history projections, not mutable current-state records.
