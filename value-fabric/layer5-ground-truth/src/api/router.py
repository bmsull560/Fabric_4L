"""
FastAPI router for Layer 5 Ground Truth API.

Endpoints:
  POST   /truths                    — Create a new TruthObject
  GET    /truths                    — List TruthObjects (paginated, filterable)
  GET    /truths/{id}               — Get a single TruthObject with full detail
  POST   /truths/{id}/validate      — Apply a validation state transition
  POST   /truths/{id}/sources       — Add an evidence source
  DELETE /truths/{id}               — Soft-delete a TruthObject
  GET    /truths/{id}/audit         — Get full validation event log
  POST   /truths/sync-kg            — Trigger Layer 3 KG sync for approved objects
  GET    /maturity-ladder           — Reference: full maturity ladder definition
  GET    /health                    — Health check
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database import get_db
from ..integration.layer3_client import get_layer3_client
from ..models.truth_object import ClaimType, TruthStatus
from ..services.state_machine import InsufficientEvidenceError, InvalidTransitionError
from ..services.truth_service import (
    add_source,
    create_truth_object,
    get_truth_object,
    list_truth_objects,
    soft_delete_truth_object,
    validate_truth_object,
)
from .auth import TokenClaims, get_current_user
from .schemas import (
    AddSourceRequest,
    HealthResponse,
    MaturityLadderResponse,
    MaturityLevelDetail,
    TruthObjectCreate,
    TruthObjectListResponse,
    TruthObjectResponse,
    TruthObjectSummary,
    TruthSourceResponse,
    ValidateRequest,
    ValidateResponse,
    ValidationEventResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["ground-truth"])


# ---------------------------------------------------------------------------
# POST /truths
# ---------------------------------------------------------------------------


@router.post(
    "/truths",
    response_model=TruthObjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new TruthObject",
    description=(
        "Create a new evidence-backed factual claim in EXTRACTED state. "
        "If sources are provided and confidence meets the threshold, the object "
        "will automatically advance to SUPPORTED or CORROBORATED."
    ),
    responses={
        201: {"description": "TruthObject created successfully"},
        422: {"description": "Validation error in request body"},
    },
)
async def create_truth(
    payload: TruthObjectCreate,
    caller: TokenClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TruthObjectResponse:
    organization_id = caller.organization_id
    sources_data = (
        [s.model_dump() for s in payload.sources] if payload.sources else None
    )

    truth = await create_truth_object(
        db=db,
        organization_id=organization_id,  # resolved from JWT
        claim=payload.claim,
        claim_type=payload.claim_type,
        confidence=payload.confidence,
        extraction_job_id=payload.extraction_job_id,
        extraction_model=payload.extraction_model,
        value=payload.value,
        applies_to=payload.applies_to,
        raw_extraction_data=payload.raw_extraction_data,
        sources=sources_data,
    )

    # Best-effort KG sync for high-confidence objects
    if truth.confidence >= 0.8 and truth.status in (
        "supported",
        "corroborated",
        "approved",
    ):
        client = get_layer3_client()
        node_id = await client.sync_truth_object(
            truth_object_id=truth.id,
            organization_id=organization_id,
            claim=truth.claim,
            claim_type=truth.claim_type,
            confidence=truth.confidence,
            status=truth.status,
            maturity_level=truth.maturity_level,
            value=truth.value,
            applies_to=truth.applies_to,
            source_count=len(truth.sources),
        )
        if node_id:
            truth.kg_node_id = node_id
            truth.kg_synced_at = datetime.now(UTC)

    return TruthObjectResponse.model_validate(truth)


# ---------------------------------------------------------------------------
# GET /truths
# ---------------------------------------------------------------------------


@router.get(
    "/truths",
    response_model=TruthObjectListResponse,
    summary="List TruthObjects",
    description="Paginated, filterable list of TruthObjects for the organization.",
)
async def list_truths(
    caller: TokenClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status_filter: TruthStatus | None = Query(
        default=None,
        alias="status",
        description="Filter by validation status",
    ),
    claim_type: ClaimType | None = Query(
        default=None,
        description="Filter by claim type",
    ),
    min_maturity: int | None = Query(
        default=None,
        ge=0,
        le=5,
        description="Minimum maturity level (0–5)",
    ),
    min_confidence: float | None = Query(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score",
    ),
    is_stale: bool | None = Query(
        default=None,
        description="Filter by staleness",
    ),
    applies_to_opportunity: str | None = Query(
        default=None,
        description="Filter by opportunity_id in applies_to",
    ),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> TruthObjectListResponse:
    organization_id = caller.organization_id
    items, total = await list_truth_objects(
        db=db,
        organization_id=organization_id,
        status=status_filter,
        claim_type=claim_type,
        min_maturity=min_maturity,
        min_confidence=min_confidence,
        is_stale=is_stale,
        applies_to_opportunity=applies_to_opportunity,
        limit=limit,
        offset=offset,
    )

    summaries = [
        TruthObjectSummary(
            id=t.id,
            claim=t.claim,
            claim_type=t.claim_type,
            confidence=t.confidence,
            status=t.status,
            maturity_level=t.maturity_level,
            is_stale=t.is_stale,
            source_count=len(t.sources),
            approved_by=t.approved_by,
            freshness=t.freshness,
            created_at=t.created_at,
        )
        for t in items
    ]

    return TruthObjectListResponse(
        items=summaries,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


# ---------------------------------------------------------------------------
# GET /truths/{id}
# ---------------------------------------------------------------------------


@router.get(
    "/truths/{truth_id}",
    response_model=TruthObjectResponse,
    summary="Get a TruthObject",
    description="Retrieve a single TruthObject with full detail, sources, and audit trail.",
    responses={
        200: {"description": "TruthObject found"},
        404: {"description": "TruthObject not found"},
    },
)
async def get_truth(
    truth_id: UUID,
    caller: TokenClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TruthObjectResponse:
    organization_id = caller.organization_id
    truth = await get_truth_object(db, truth_id, organization_id)
    if not truth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"TruthObject {truth_id} not found",
        )
    return TruthObjectResponse.model_validate(truth)


# ---------------------------------------------------------------------------
# POST /truths/{id}/validate
# ---------------------------------------------------------------------------


@router.post(
    "/truths/{truth_id}/validate",
    response_model=ValidateResponse,
    summary="Apply a validation state transition",
    description=(
        "Trigger a named validation action on a TruthObject. "
        "Actions: advance_supported | advance_corroborated | approve | "
        "dispute | resolve_dispute | operationalize"
    ),
    responses={
        200: {"description": "Transition applied successfully"},
        400: {"description": "Invalid transition or insufficient evidence"},
        404: {"description": "TruthObject not found"},
    },
)
async def validate_truth(
    truth_id: UUID,
    payload: ValidateRequest,
    caller: TokenClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ValidateResponse:
    organization_id = caller.organization_id
    truth = await get_truth_object(db, truth_id, organization_id)
    if not truth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"TruthObject {truth_id} not found",
        )

    previous_status = truth.status
    previous_maturity = truth.maturity_level

    try:
        truth = await validate_truth_object(
            db=db,
            truth_object=truth,
            action=payload.action,
            actor=payload.actor,
            actor_type=payload.actor_type,
            notes=payload.notes,
            dispute_reason=payload.dispute_reason.value
            if payload.dispute_reason
            else None,
        )
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except InsufficientEvidenceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Sync to Layer 3 after approval
    if truth.status == "approved":
        client = get_layer3_client()
        node_id = await client.sync_truth_object(
            truth_object_id=truth.id,
            organization_id=organization_id,
            claim=truth.claim,
            claim_type=truth.claim_type,
            confidence=truth.confidence,
            status=truth.status,
            maturity_level=truth.maturity_level,
            value=truth.value,
            applies_to=truth.applies_to,
            source_count=len(truth.sources),
        )
        if node_id:
            truth.kg_node_id = node_id
            truth.kg_synced_at = datetime.now(UTC)

    return ValidateResponse(
        truth_object_id=truth.id,
        previous_status=previous_status,
        new_status=truth.status,
        previous_maturity=previous_maturity,
        new_maturity=truth.maturity_level,
        actor=payload.actor,
        message=(
            f"Successfully applied '{payload.action}': "
            f"{previous_status} → {truth.status}"
        ),
    )


# ---------------------------------------------------------------------------
# POST /truths/{id}/sources
# ---------------------------------------------------------------------------


@router.post(
    "/truths/{truth_id}/sources",
    response_model=TruthSourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an evidence source",
    description=(
        "Attach a new evidence source to an existing TruthObject. "
        "Adding a source may trigger automatic status advancement."
    ),
    responses={
        201: {"description": "Source added successfully"},
        404: {"description": "TruthObject not found"},
    },
)
async def add_truth_source(
    truth_id: UUID,
    payload: AddSourceRequest,
    caller: TokenClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TruthSourceResponse:
    organization_id = caller.organization_id
    truth = await get_truth_object(db, truth_id, organization_id)
    if not truth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"TruthObject {truth_id} not found",
        )

    _, source = await add_source(
        db=db,
        truth_object=truth,
        organization_id=organization_id,
        source_data=payload.model_dump(),
    )

    return TruthSourceResponse.model_validate(source)


# ---------------------------------------------------------------------------
# GET /truths/{id}/audit
# ---------------------------------------------------------------------------


@router.get(
    "/truths/{truth_id}/audit",
    response_model=list[ValidationEventResponse],
    summary="Get validation audit trail",
    description="Returns the full immutable audit log of all state transitions for a TruthObject.",
)
async def get_audit_trail(
    truth_id: UUID,
    caller: TokenClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ValidationEventResponse]:
    organization_id = caller.organization_id
    truth = await get_truth_object(db, truth_id, organization_id)
    if not truth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"TruthObject {truth_id} not found",
        )
    return [ValidationEventResponse.model_validate(e) for e in truth.validation_events]


# ---------------------------------------------------------------------------
# DELETE /truths/{id}
# ---------------------------------------------------------------------------


@router.delete(
    "/truths/{truth_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a TruthObject",
    description="Marks a TruthObject as deleted. Records are never hard-deleted.",
)
async def delete_truth(
    truth_id: UUID,
    caller: TokenClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    deleted_by: str | None = Query(default=None),
) -> None:
    organization_id = caller.organization_id
    deleted_by = deleted_by or caller.user_id
    truth = await get_truth_object(db, truth_id, organization_id)
    if not truth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"TruthObject {truth_id} not found",
        )
    await soft_delete_truth_object(db, truth, deleted_by=deleted_by)


# ---------------------------------------------------------------------------
# POST /truths/sync-kg
# ---------------------------------------------------------------------------


@router.post(
    "/truths/sync-kg",
    summary="Sync approved TruthObjects to Layer 3 Knowledge Graph",
    description=(
        "Triggers a bulk sync of all APPROVED TruthObjects that have not yet "
        "been synced to the Layer 3 Knowledge Graph."
    ),
)
async def sync_to_kg(
    caller: TokenClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    organization_id = caller.organization_id
    from sqlalchemy import and_, select

    from ..models.truth_object import TruthObject

    result = await db.execute(
        select(TruthObject).where(
            and_(
                TruthObject.organization_id == organization_id,
                TruthObject.status == "approved",
                TruthObject.kg_node_id.is_(None),
                TruthObject.deleted_at.is_(None),
            )
        )
    )
    pending = result.scalars().all()

    client = get_layer3_client()
    synced = 0
    failed = 0
    for truth in pending:
        node_id = await client.sync_truth_object(
            truth_object_id=truth.id,
            organization_id=truth.organization_id,
            claim=truth.claim,
            claim_type=truth.claim_type,
            confidence=truth.confidence,
            status=truth.status,
            maturity_level=truth.maturity_level,
            value=truth.value,
            applies_to=truth.applies_to,
            source_count=len(truth.sources),
        )
        if node_id:
            truth.kg_node_id = node_id
            truth.kg_synced_at = datetime.now(UTC)
            synced += 1
        else:
            failed += 1

    return {
        "synced": synced,
        "failed": failed,
        "total_pending": len(pending),
    }


# ---------------------------------------------------------------------------
# GET /maturity-ladder
# ---------------------------------------------------------------------------


@router.get(
    "/maturity-ladder",
    response_model=MaturityLadderResponse,
    summary="Get maturity ladder definition",
    description="Returns the full 0–5 maturity ladder with descriptions and advancement criteria.",
)
async def get_maturity_ladder() -> MaturityLadderResponse:
    levels = [
        MaturityLevelDetail(
            level=0,
            name="Raw",
            description="Claim captured but not yet processed by any extraction model.",
            required_status="extracted",
            advancement_trigger="Extraction model processes the raw content",
        ),
        MaturityLevelDetail(
            level=1,
            name="Extracted",
            description="AI model has identified and structured the claim from source content.",
            required_status="extracted",
            advancement_trigger="At least 1 source attached AND confidence ≥ threshold",
        ),
        MaturityLevelDetail(
            level=2,
            name="Supported",
            description="Claim has at least one linked evidence source and meets confidence threshold.",
            required_status="supported",
            advancement_trigger="≥ 2 distinct independent sources corroborate the claim",
        ),
        MaturityLevelDetail(
            level=3,
            name="Corroborated",
            description="Multiple independent sources confirm the claim from different angles.",
            required_status="corroborated",
            advancement_trigger="Human reviewer explicitly approves the claim",
        ),
        MaturityLevelDetail(
            level=4,
            name="Approved",
            description="A qualified human reviewer has validated and approved the claim.",
            required_status="approved",
            advancement_trigger="Claim is referenced in an ROI model, board deck, or business case",
        ),
        MaturityLevelDetail(
            level=5,
            name="Operationalized",
            description=(
                "Claim has been used in board-level or CFO-facing decisions. "
                "This is the highest trust level — suitable for executive narratives."
            ),
            required_status="approved",
            advancement_trigger="Referenced in downstream business artefact (ROI model, deck, contract)",
        ),
    ]
    return MaturityLadderResponse(levels=levels)


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["system"],
)
async def health_check(
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> HealthResponse:
    import time

    settings = get_settings()
    start_time = time.time()

    # Check DB connectivity
    db_status = "ok"
    db_response_ms = None
    try:
        from sqlalchemy import text

        db_start = time.time()
        await db.execute(text("SELECT 1"))
        db_response_ms = round((time.time() - db_start) * 1000, 2)
    except Exception as e:
        db_status = "error"
        db_response_ms = None
        logger.error(f"Health check DB error: {e}")

    # Check Layer 3 connectivity
    l3_start = time.time()
    client = get_layer3_client()
    l3_connected = await client.ping()
    l3_response_ms = round((time.time() - l3_start) * 1000, 2)

    # Determine overall status
    overall_status = "ok"
    if db_status == "error":
        overall_status = "degraded"
    if not l3_connected:
        overall_status = "degraded"

    total_response_ms = round((time.time() - start_time) * 1000, 2)

    # Update Prometheus health metrics if available
    if request and hasattr(request.app.state, "metrics") and request.app.state.metrics:
        metrics = request.app.state.metrics
        metrics.set_health_status(overall_status == "ok", component="api")
        metrics.set_health_status(db_status == "ok", component="database")
        metrics.set_health_status(l3_connected, component="layer3")

    return HealthResponse(
        status=overall_status,
        version="0.1.0",
        timestamp=datetime.now(UTC),
        database=db_status,
        layer3_connected=l3_connected,
        layer3_url=settings.layer3_base_url,
        response_time_ms=total_response_ms,
        db_response_ms=db_response_ms,
        layer3_response_ms=l3_response_ms,
    )
