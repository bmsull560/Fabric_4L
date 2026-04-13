"""
CRUD and business logic service for TruthObject management.

Separates database operations from the API layer, keeping routers thin.
All methods accept an open AsyncSession and do not commit — callers commit.
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import get_settings
from ..models.truth_object import (
    ClaimType,
    DisputeReason,
    MaturityLevel,
    TruthObject,
    TruthSource,
    TruthStatus,
    ValidationEvent,
)
from ..services.state_machine import ValidationStateMachine

logger = logging.getLogger(__name__)
_state_machine = ValidationStateMachine()


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


async def create_truth_object(
    db: AsyncSession,
    organization_id: UUID,
    claim: str,
    claim_type: ClaimType,
    confidence: float,
    extraction_job_id: str | None = None,
    extraction_model: str | None = None,
    value: dict | None = None,
    applies_to: dict | None = None,
    raw_extraction_data: dict | None = None,
    sources: list[dict] | None = None,
    created_by: str | None = None,
) -> TruthObject:
    """
    Create a new TruthObject in EXTRACTED state and optionally attach sources.

    If sources are provided and auto_advance is enabled, the state machine
    will attempt to advance the status automatically.
    """
    settings = get_settings()

    expires_at = datetime.now(UTC) + timedelta(days=settings.default_freshness_days)

    truth = TruthObject(
        organization_id=organization_id,
        claim=claim,
        claim_type=claim_type.value,
        confidence=confidence,
        value=value,
        applies_to=applies_to,
        extraction_job_id=extraction_job_id,
        extraction_model=extraction_model,
        raw_extraction_data=raw_extraction_data,
        status=TruthStatus.EXTRACTED.value,
        maturity_level=MaturityLevel.EXTRACTED.value,
        freshness=datetime.now(UTC),
        expires_at=expires_at,
    )
    db.add(truth)
    await db.flush()  # get the ID without committing

    # Record initial ValidationEvent
    initial_event = ValidationEvent(
        truth_object_id=truth.id,
        organization_id=organization_id,
        from_status=None,
        to_status=TruthStatus.EXTRACTED.value,
        from_maturity=None,
        to_maturity=MaturityLevel.EXTRACTED.value,
        actor=created_by or "system",
        actor_type="system" if not created_by else "human",
        confidence_at_transition=confidence,
        source_count_at_transition=len(sources) if sources else 0,
        notes="Initial extraction",
    )
    db.add(initial_event)
    await db.flush()  # Flush so the event has an ID and can be loaded by refresh

    # Attach sources if provided
    if sources:
        for src_data in sources:
            source = TruthSource(
                truth_object_id=truth.id,
                organization_id=organization_id,
                **src_data,
            )
            db.add(source)
        await db.flush()

        # Attempt auto-advance
        truth = await _state_machine.auto_advance(db, truth)

    # Refresh to populate the relationships needed for the response
    await db.refresh(
        truth, attribute_names=["sources", "validation_events", "maturity_history"]
    )

    logger.info(
        "Created TruthObject %s (org=%s, status=%s, confidence=%.2f)",
        truth.id,
        organization_id,
        truth.status,
        confidence,
    )
    return truth


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


async def get_truth_object(
    db: AsyncSession,
    truth_id: UUID,
    organization_id: UUID,
) -> TruthObject | None:
    """Fetch a single TruthObject by ID, scoped to the organization."""
    result = await db.execute(
        select(TruthObject)
        .options(
            selectinload(TruthObject.sources),
            selectinload(TruthObject.validation_events),
            selectinload(TruthObject.maturity_history),
        )
        .where(
            and_(
                TruthObject.id == truth_id,
                TruthObject.organization_id == organization_id,
                TruthObject.deleted_at.is_(None),
            )
        )
    )
    return result.scalar_one_or_none()


async def list_truth_objects(
    db: AsyncSession,
    organization_id: UUID,
    status: TruthStatus | None = None,
    claim_type: ClaimType | None = None,
    min_maturity: int | None = None,
    min_confidence: float | None = None,
    is_stale: bool | None = None,
    applies_to_opportunity: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[TruthObject], int]:
    """
    List TruthObjects with optional filters.

    Returns (items, total_count) for pagination.
    """
    base_filter = and_(
        TruthObject.organization_id == organization_id,
        TruthObject.deleted_at.is_(None),
    )

    conditions = [base_filter]
    if status:
        conditions.append(TruthObject.status == status.value)
    if claim_type:
        conditions.append(TruthObject.claim_type == claim_type.value)
    if min_maturity is not None:
        conditions.append(TruthObject.maturity_level >= min_maturity)
    if min_confidence is not None:
        conditions.append(TruthObject.confidence >= min_confidence)
    if is_stale is not None:
        conditions.append(TruthObject.is_stale == is_stale)
    if applies_to_opportunity:
        conditions.append(
            TruthObject.applies_to["opportunity_id"].astext == applies_to_opportunity
        )

    where_clause = and_(*conditions)

    # Count
    count_result = await db.execute(
        select(func.count()).select_from(TruthObject).where(where_clause)
    )
    total = count_result.scalar_one()

    # Items
    items_result = await db.execute(
        select(TruthObject)
        .options(selectinload(TruthObject.sources))
        .where(where_clause)
        .order_by(TruthObject.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = list(items_result.scalars().all())

    return items, total


# ---------------------------------------------------------------------------
# Add source
# ---------------------------------------------------------------------------


async def add_source(
    db: AsyncSession,
    truth_object: TruthObject,
    organization_id: UUID,
    source_data: dict,
    auto_advance: bool = True,
) -> tuple[TruthObject, TruthSource]:
    """
    Add a TruthSource to a TruthObject and optionally trigger auto-advance.
    """
    source = TruthSource(
        truth_object_id=truth_object.id,
        organization_id=organization_id,
        **source_data,
    )
    db.add(source)
    await db.flush()

    # Refresh to populate the relationships needed for the response
    await db.refresh(
        truth_object,
        attribute_names=["sources", "validation_events", "maturity_history"],
    )

    if auto_advance:
        truth_object = await _state_machine.auto_advance(db, truth_object)

    return truth_object, source


# ---------------------------------------------------------------------------
# Validate (state transitions via API)
# ---------------------------------------------------------------------------


async def validate_truth_object(
    db: AsyncSession,
    truth_object: TruthObject,
    action: str,
    actor: str,
    actor_type: str = "human",
    notes: str | None = None,
    dispute_reason: str | None = None,
) -> TruthObject:
    """
    Apply a named validation action to a TruthObject.

    Actions: advance_supported | advance_corroborated | approve |
             dispute | resolve_dispute
    """
    if action == "advance_supported":
        return await _state_machine.advance_to_supported(
            db, truth_object, actor=actor, notes=notes
        )
    elif action == "advance_corroborated":
        return await _state_machine.advance_to_corroborated(
            db, truth_object, actor=actor, notes=notes
        )
    elif action == "approve":
        return await _state_machine.approve(
            db, truth_object, approved_by=actor, notes=notes
        )
    elif action == "dispute":
        reason = (
            DisputeReason(dispute_reason) if dispute_reason else DisputeReason.OTHER
        )
        return await _state_machine.dispute(
            db, truth_object, reason=reason, disputed_by=actor, notes=notes
        )
    elif action == "resolve_dispute":
        return await _state_machine.resolve_dispute(
            db, truth_object, resolved_by=actor, notes=notes
        )
    elif action == "operationalize":
        return await _state_machine.mark_operationalized(
            db,
            truth_object,
            trigger="api_call",
            triggered_by=actor,
            context={"notes": notes},
        )
    else:
        raise ValueError(f"Unknown validation action: {action!r}")


# ---------------------------------------------------------------------------
# Freshness monitor
# ---------------------------------------------------------------------------


async def mark_stale_objects(db: AsyncSession, organization_id: UUID) -> int:
    """
    Mark all TruthObjects past their expires_at date as stale.

    Returns the number of objects marked stale.
    """
    now = datetime.now(UTC)
    result = await db.execute(
        select(TruthObject).where(
            and_(
                TruthObject.organization_id == organization_id,
                TruthObject.deleted_at.is_(None),
                TruthObject.is_stale.is_(False),
                TruthObject.expires_at <= now,
            )
        )
    )
    objects = result.scalars().all()
    for obj in objects:
        obj.is_stale = True
        obj.updated_at = now

    logger.info(
        "Marked %d TruthObjects as stale for org %s",
        len(objects),
        organization_id,
    )
    return len(objects)


# ---------------------------------------------------------------------------
# Soft delete
# ---------------------------------------------------------------------------


async def soft_delete_truth_object(
    db: AsyncSession,
    truth_object: TruthObject,
    deleted_by: str | None = None,
) -> TruthObject:
    """Soft-delete a TruthObject by setting deleted_at."""
    truth_object.deleted_at = datetime.now(UTC)
    truth_object.updated_at = datetime.now(UTC)
    await db.flush()  # Persist changes to DB immediately
    logger.info("Soft-deleted TruthObject %s by %s", truth_object.id, deleted_by)
    return truth_object
