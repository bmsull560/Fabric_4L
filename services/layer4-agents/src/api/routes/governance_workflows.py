"""Canonical governance workflow objects/endpoints for L4/L5 traceability."""

from __future__ import annotations

<<<<<<< ours
<<<<<<< ours
from datetime import datetime, timezone
=======
from datetime import UTC, datetime
>>>>>>> theirs
=======
from datetime import UTC, datetime
>>>>>>> theirs
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/governance", tags=["governance-workflows"])


class LineageRef(BaseModel):
    business_case_id: str | None = None
    value_model_id: str | None = None
    correlation_id: str


class ReviewRequest(BaseModel):
    review_id: str
    status: Literal["submitted", "in_review", "approved", "changes_requested", "rejected"]
    subject_type: Literal["business_case", "value_model"]
    submitted_at: datetime
    lineage: LineageRef


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


class AuditExportCreateRequest(BaseModel):
    review_id: str
    correlation_id: str


_REVIEWS: dict[str, ReviewRequest] = {}
_DECISIONS: dict[str, ApprovalDecision] = {}
_VERSIONS: dict[str, VersionRecord] = {}
_EXPORTS: dict[str, AuditExportJob] = {}


@router.post("/reviews", response_model=ReviewRequest, status_code=status.HTTP_201_CREATED)
async def create_review(request: ReviewRequest) -> ReviewRequest:
    _REVIEWS[request.review_id] = request
    return request


@router.post("/reviews/{review_id}/decisions", response_model=ApprovalDecision, status_code=status.HTTP_201_CREATED)
async def create_decision(review_id: str, decision: ApprovalDecision) -> ApprovalDecision:
    if review_id not in _REVIEWS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="review not found")
    _DECISIONS[review_id] = decision
    return decision


@router.get("/versions/{version_id}", response_model=VersionRecord)
async def get_version(version_id: str) -> VersionRecord:
    if version_id not in _VERSIONS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="version not found")
    return _VERSIONS[version_id]


@router.post("/versions", response_model=VersionRecord, status_code=status.HTTP_201_CREATED)
async def create_version(version: VersionRecord) -> VersionRecord:
    _VERSIONS[version.version_id] = version
    return version


@router.get("/versions/{version_id}/diff", response_model=VersionDiff)
async def get_version_diff(version_id: str, compare_to_version_id: str) -> VersionDiff:
    source = _VERSIONS.get(version_id)
    target = _VERSIONS.get(compare_to_version_id)
    if not source or not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="version not found")
    changed_fields = ["status"] if source.version_status != target.version_status else []
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
    decision = _DECISIONS.get(request.review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="review not found")
    approved = bool(decision and decision.decision == "approved")
    export_id = str(uuid4())
    job = AuditExportJob(
        audit_export_id=export_id,
        review_id=request.review_id,
        status="pending" if approved else "blocked",
        reason=None if approved else "approval_required",
<<<<<<< ours
<<<<<<< ours
        created_at=datetime.now(timezone.utc),
=======
        created_at=datetime.now(UTC),
>>>>>>> theirs
=======
        created_at=datetime.now(UTC),
>>>>>>> theirs
        lineage=LineageRef(
            business_case_id=review.lineage.business_case_id,
            value_model_id=review.lineage.value_model_id,
            correlation_id=request.correlation_id,
        ),
    )
    _EXPORTS[export_id] = job
    return job


@router.get("/lineage/{correlation_id}")
async def get_lineage(correlation_id: str) -> dict[str, list[BaseModel]]:
    reviews = [item for item in _REVIEWS.values() if item.lineage.correlation_id == correlation_id]
    decisions = [item for item in _DECISIONS.values() if item.lineage.correlation_id == correlation_id]
    versions = [item for item in _VERSIONS.values() if item.lineage.correlation_id == correlation_id]
    exports = [item for item in _EXPORTS.values() if item.lineage.correlation_id == correlation_id]
    return {"reviews": reviews, "decisions": decisions, "versions": versions, "exports": exports}
