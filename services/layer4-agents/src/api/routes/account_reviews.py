"""Account-scoped review and gate routes for L4.

Implements the endpoints that ReviewQueuePage and account-gate UIs expect:
  GET    /accounts/{account_id}/gates
  GET    /accounts/{account_id}/reviews
  POST   /accounts/{account_id}/reviews
  PATCH  /accounts/{account_id}/reviews/{review_id}
  POST   /accounts/{account_id}/reviews/{review_id}/comments
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from value_fabric.shared.identity.context import RequestContext
from value_fabric.shared.identity.dependencies import require_authenticated

from ...database import get_db_from_context
from ...harness.api_models import GateListResponse, GateResponse
from ...harness.registry import HarnessRegistry
from ...models.review_request import ReviewRequest, ReviewStatus

router = APIRouter(prefix="/v1/accounts", tags=["account-reviews"])
AuthDep = Annotated[RequestContext, Depends(require_authenticated)]


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class ReviewCommentPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    text: str
    author_id: str


class ReviewCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str | None = Field(default=None, description="Optional client-generated UUID")
    requester_id: str
    reviewer_id: str | None = None
    scope: str = "business_case"
    target_id: str | None = None


class ReviewUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str


class ReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    account_id: str
    tenant_id: str
    requester_id: str
    reviewer_id: str | None = None
    status: str
    scope: str
    target_id: str | None = None
    comments: list[dict[str, Any]]
    created_at: str
    updated_at: str
    resolved_at: str | None = None


class GateSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account_id: str
    all_passed: bool
    gates: list[dict[str, Any]]
    checked_at: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _review_to_response(review: ReviewRequest) -> ReviewResponse:
    return ReviewResponse(
        id=str(review.id),
        account_id=review.account_id,
        tenant_id=review.tenant_id,
        requester_id=review.requester_id,
        reviewer_id=review.reviewer_id,
        status=review.status,
        scope=review.scope,
        target_id=review.target_id,
        comments=review.comments,
        created_at=review.created_at.isoformat() if review.created_at else "",
        updated_at=review.updated_at.isoformat() if review.updated_at else "",
        resolved_at=review.resolved_at.isoformat() if review.resolved_at else None,
    )


# ---------------------------------------------------------------------------
# Routes — Gates
# ---------------------------------------------------------------------------


@router.get(
    "/{account_id}/gates",
    response_model=GateSummaryResponse,
    summary="Aggregate harness gates for an account",
)
async def get_account_gates(
    account_id: str,
    ctx: AuthDep,
    db: AsyncSession = Depends(get_db_from_context),
) -> GateSummaryResponse:
    """Return a summary of all harness-run gates associated with this account.

    Currently aggregates gates from harness runs that have an account_id
    matching the path parameter. In the future this may also include
    account-level compliance gates.
    """
    # NOTE: HarnessRegistry is sync-oriented; for an async endpoint we
    # construct it inline.  In production this should be injected.
    from ...harness.registry import HarnessRegistry
    from ...harness.models import RunStatus

    registry = HarnessRegistry(db)

    # Find all harness runs for this account + tenant
    runs = await registry.list_runs(
        tenant_id=ctx.tenant_id,
        status=None,
        limit=100,
    )
    account_runs = [r for r in runs if getattr(r, "account_id", None) == account_id]

    all_gates: list[dict[str, Any]] = []
    all_passed = True

    for run in account_runs:
        gates = registry.list_gates_for_run(run.run_id, ctx.tenant_id)
        for g in gates:
            gate_dict = {
                "id": g.id,
                "run_id": g.run_id,
                "type": g.gate_type.value if hasattr(g.gate_type, "value") else str(g.gate_type),
                "status": "closed" if g.status.value == "closed" else "open" if g.status.value == "open" else str(g.status),
                "reason": g.decision_reason,
            }
            all_gates.append(gate_dict)
            if gate_dict["status"] != "closed":
                all_passed = False

    return GateSummaryResponse(
        account_id=account_id,
        all_passed=all_passed,
        gates=all_gates,
        checked_at=datetime.now(UTC).isoformat(),
    )


# ---------------------------------------------------------------------------
# Routes — Reviews
# ---------------------------------------------------------------------------


@router.get(
    "/{account_id}/reviews",
    response_model=list[ReviewResponse],
    summary="List review requests for an account",
)
async def list_account_reviews(
    account_id: str,
    ctx: AuthDep,
    db: AsyncSession = Depends(get_db_from_context),
    status_filter: str | None = Query(None, alias="status"),
) -> list[ReviewResponse]:
    """Return all review requests scoped to the given account."""
    stmt = select(ReviewRequest).where(
        ReviewRequest.account_id == account_id,
        ReviewRequest.tenant_id == ctx.tenant_id,
    )
    if status_filter:
        stmt = stmt.where(ReviewRequest.status == status_filter)
    stmt = stmt.order_by(ReviewRequest.created_at.desc())

    result = await db.execute(stmt)
    reviews = result.scalars().all()
    return [_review_to_response(r) for r in reviews]


@router.post(
    "/{account_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a review request for an account",
)
async def create_account_review(
    account_id: str,
    body: ReviewCreateRequest,
    ctx: AuthDep,
    db: AsyncSession = Depends(get_db_from_context),
) -> ReviewResponse:
    """Create a new review request scoped to an account."""
    review = ReviewRequest(
        id=UUID(body.id) if body.id else uuid.uuid4(),
        account_id=account_id,
        tenant_id=ctx.tenant_id,
        requester_id=body.requester_id or ctx.user_id or "anonymous",
        reviewer_id=body.reviewer_id,
        status=ReviewStatus.PENDING.value,
        scope=body.scope,
        target_id=body.target_id,
        comments=[],
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return _review_to_response(review)


@router.patch(
    "/{account_id}/reviews/{review_id}",
    response_model=ReviewResponse,
    summary="Update review status",
)
async def update_account_review(
    account_id: str,
    review_id: UUID,
    body: ReviewUpdateRequest,
    ctx: AuthDep,
    db: AsyncSession = Depends(get_db_from_context),
) -> ReviewResponse:
    """Update the status of a review request."""
    stmt = select(ReviewRequest).where(
        ReviewRequest.id == review_id,
        ReviewRequest.account_id == account_id,
        ReviewRequest.tenant_id == ctx.tenant_id,
    )
    result = await db.execute(stmt)
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.status = body.status
    if body.status in (ReviewStatus.APPROVED.value, ReviewStatus.REJECTED.value):
        review.resolved_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(review)
    return _review_to_response(review)


@router.post(
    "/{account_id}/reviews/{review_id}/comments",
    response_model=ReviewResponse,
    summary="Add a comment to a review",
)
async def add_review_comment(
    account_id: str,
    review_id: UUID,
    body: ReviewCommentPayload,
    ctx: AuthDep,
    db: AsyncSession = Depends(get_db_from_context),
) -> ReviewResponse:
    """Append a comment to an existing review request."""
    stmt = select(ReviewRequest).where(
        ReviewRequest.id == review_id,
        ReviewRequest.account_id == account_id,
        ReviewRequest.tenant_id == ctx.tenant_id,
    )
    result = await db.execute(stmt)
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    comment = {
        "id": body.id,
        "review_id": str(review_id),
        "author_id": body.author_id or ctx.user_id or "anonymous",
        "text": body.text,
        "created_at": datetime.now(UTC).isoformat(),
    }
    # Append to existing comments list
    review.comments = review.comments + [comment]
    review.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(review)
    return _review_to_response(review)
