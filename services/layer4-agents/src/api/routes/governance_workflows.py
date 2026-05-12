"""Canonical governance workflow objects/endpoints for L4/L5 traceability."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, model_validator

router = APIRouter(prefix="/governance", tags=["governance-workflows"])


class LineageRef(BaseModel):
    """Shared immutable lineage carried by L4/L5 governance objects."""

    business_case_id: str | None = None
    value_model_id: str | None = None
    correlation_id: str
    trace_id: str | None = None

    @model_validator(mode="after")
    def validate_lineage(self) -> "LineageRef":
        if not self.business_case_id and not self.value_model_id:
            raise ValueError("lineage requires business_case_id or value_model_id")
        if self.trace_id is None:
            self.trace_id = self.correlation_id
        if self.trace_id != self.correlation_id:
            raise ValueError("trace_id must match correlation_id when both are present")
        return self


class ReviewRequest(BaseModel):
    review_id: str
    status: Literal["submitted", "in_review", "approved", "changes_requested", "rejected"]
    subject_type: Literal["business_case", "value_model"]
    submitted_at: datetime
    lineage: LineageRef
    immutable_audit_hash: str | None = None


class ApprovalDecision(BaseModel):
    decision_id: str
    review_id: str
    decision: Literal["approved", "changes_requested", "rejected"]
    immutable_audit_hash: str
    decided_at: datetime
    lineage: LineageRef


class VersionRecord(BaseModel):
    version_id: str
    version_status: Literal["active", "superseded"]
    lineage: LineageRef
    created_at: datetime
    object_type: Literal["business_case", "value_model"] = "business_case"
    snapshot: dict[str, Any] = Field(default_factory=dict)
    immutable_audit_hash: str | None = None


class VersionDiff(BaseModel):
    version_id: str
    compare_to_version_id: str
    changed_fields: list[str]
    change_count: int
    lineage: LineageRef


class AuditExportJob(BaseModel):
    audit_export_id: str
    review_id: str
    status: Literal["pending", "ready", "failed", "blocked"]
    reason: str | None = None
    lineage: LineageRef
    created_at: datetime
    immutable_audit_hash: str


class AuditExportCreateRequest(BaseModel):
    review_id: str
    correlation_id: str
    trace_id: str | None = None


_REVIEWS: dict[str, ReviewRequest] = {}
_DECISIONS: dict[str, ApprovalDecision] = {}
_VERSIONS: dict[str, VersionRecord] = {}
_EXPORTS: dict[str, AuditExportJob] = {}


def _ensure_absent(store: dict[str, BaseModel], object_id: str, object_name: str) -> None:
    if object_id in store:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{object_name} is immutable and already exists",
        )


def _hash_payload(kind: str, payload: BaseModel) -> str:
    serialized = payload.model_dump_json(exclude={"immutable_audit_hash"}, by_alias=True)
    return f"sha256:{sha256(f'{kind}:{serialized}'.encode('utf-8')).hexdigest()}"


def _same_origin(a: LineageRef, b: LineageRef) -> bool:
    return (
        a.business_case_id == b.business_case_id
        and a.value_model_id == b.value_model_id
        and a.correlation_id == b.correlation_id
    )


class LineageResponse(BaseModel):
    reviews: list[ReviewRequest]
    decisions: list[ApprovalDecision]
    versions: list[VersionRecord]
    exports: list[AuditExportJob]


@router.post("/reviews", response_model=ReviewRequest, status_code=status.HTTP_201_CREATED)
async def create_review(request: ReviewRequest) -> ReviewRequest:
    _ensure_absent(_REVIEWS, request.review_id, "ReviewRequest")
    request.immutable_audit_hash = _hash_payload("ReviewRequest", request)
    _REVIEWS[request.review_id] = request
    return request


@router.get("/reviews", response_model=list[ReviewRequest])
async def list_reviews(
    status_filter: str | None = Query(default=None, alias="status"),
    subject_type: str | None = None,
    correlation_id: str | None = None,
) -> list[ReviewRequest]:
    reviews = list(_REVIEWS.values())
    if status_filter:
        reviews = [item for item in reviews if item.status == status_filter]
    if subject_type:
        reviews = [item for item in reviews if item.subject_type == subject_type]
    if correlation_id:
        reviews = [item for item in reviews if item.lineage.correlation_id == correlation_id]
    return reviews


@router.get("/reviews/{review_id}", response_model=ReviewRequest)
async def get_review(review_id: str) -> ReviewRequest:
    if review_id not in _REVIEWS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="review not found")
    return _REVIEWS[review_id]


@router.post("/reviews/{review_id}/decisions", response_model=ApprovalDecision, status_code=status.HTTP_201_CREATED)
async def create_decision(review_id: str, decision: ApprovalDecision) -> ApprovalDecision:
    review = _REVIEWS.get(review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="review not found")
    if decision.review_id != review_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="decision review_id mismatch")
    if not _same_origin(review.lineage, decision.lineage):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="decision lineage mismatch")
    _ensure_absent(_DECISIONS, decision.decision_id, "ApprovalDecision")
    expected_hash = _hash_payload("ApprovalDecision", decision)
    if decision.immutable_audit_hash != expected_hash:
        decision.immutable_audit_hash = expected_hash
    _DECISIONS[decision.decision_id] = decision
    return decision


@router.get("/versions/{version_id}", response_model=VersionRecord)
async def get_version(version_id: str) -> VersionRecord:
    if version_id not in _VERSIONS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="version not found")
    return _VERSIONS[version_id]


@router.post("/versions", response_model=VersionRecord, status_code=status.HTTP_201_CREATED)
async def create_version(version: VersionRecord) -> VersionRecord:
    _ensure_absent(_VERSIONS, version.version_id, "VersionRecord")
    version.immutable_audit_hash = _hash_payload("VersionRecord", version)
    _VERSIONS[version.version_id] = version
    return version


@router.get("/versions/{version_id}/diff", response_model=VersionDiff)
async def get_version_diff(version_id: str, compare_to_version_id: str) -> VersionDiff:
    source = _VERSIONS.get(version_id)
    target = _VERSIONS.get(compare_to_version_id)
    if not source or not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="version not found")
    changed_fields = []
    if source.version_status != target.version_status:
        changed_fields.append("version_status")
    changed_fields.extend(
        sorted(
            field
            for field in set(source.snapshot) | set(target.snapshot)
            if source.snapshot.get(field) != target.snapshot.get(field)
        )
    )
    return VersionDiff(
        version_id=version_id,
        compare_to_version_id=compare_to_version_id,
        changed_fields=changed_fields,
        change_count=len(changed_fields),
        lineage=source.lineage,
    )


@router.post("/audit/exports", response_model=AuditExportJob, status_code=status.HTTP_201_CREATED)
async def create_audit_export(request: AuditExportCreateRequest) -> AuditExportJob:
    review = _REVIEWS.get(request.review_id)
    decisions = [item for item in _DECISIONS.values() if item.review_id == request.review_id]
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="review not found")
    if request.trace_id and request.trace_id != request.correlation_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="trace_id must match correlation_id")
    if review.lineage.correlation_id != request.correlation_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="export lineage mismatch")
    approved = any(decision.decision == "approved" for decision in decisions)
    export_id = str(uuid4())
    job = AuditExportJob(
        audit_export_id=export_id,
        review_id=request.review_id,
        status="pending" if approved else "blocked",
        reason=None if approved else "approval_required",
        created_at=datetime.now(timezone.utc),
        lineage=LineageRef(
            business_case_id=review.lineage.business_case_id,
            value_model_id=review.lineage.value_model_id,
            correlation_id=request.correlation_id,
            trace_id=request.trace_id or request.correlation_id,
        ),
        immutable_audit_hash="",
    )
    job.immutable_audit_hash = _hash_payload("AuditExportJob", job)
    _EXPORTS[export_id] = job
    return job


@router.get("/audit/exports/{audit_export_id}", response_model=AuditExportJob)
async def get_audit_export(audit_export_id: str) -> AuditExportJob:
    if audit_export_id not in _EXPORTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="audit export not found")
    return _EXPORTS[audit_export_id]


@router.get("/lineage/{correlation_id}", response_model=LineageResponse)
async def get_lineage(correlation_id: str) -> LineageResponse:
    reviews = [item for item in _REVIEWS.values() if item.lineage.correlation_id == correlation_id]
    decisions = [item for item in _DECISIONS.values() if item.lineage.correlation_id == correlation_id]
    versions = [item for item in _VERSIONS.values() if item.lineage.correlation_id == correlation_id]
    exports = [item for item in _EXPORTS.values() if item.lineage.correlation_id == correlation_id]
    return LineageResponse(reviews=reviews, decisions=decisions, versions=versions, exports=exports)
