"""
Validation State Machine for TruthObject lifecycle.

Implements the four-state forward-only machine:
  extracted → supported → corroborated → approved
                                       ↘ disputed (can revert to corroborated)

Rules
-----
EXTRACTED → SUPPORTED
  • confidence ≥ settings.min_confidence_for_supported
  • at least 1 TruthSource attached

SUPPORTED → CORROBORATED
  • ≥ settings.min_sources_for_corroborated distinct sources
  • sources must have different (source_type, source_url) pairs

CORROBORATED → APPROVED
  • requires human actor (actor_type == "human")
  • approved_by must be set

ANY → DISPUTED
  • can be triggered by any actor
  • requires dispute_reason

DISPUTED → CORROBORATED (revert)
  • human actor only
  • dispute is resolved

APPROVED → OPERATIONALIZED (maturity only, status stays APPROVED)
  • triggered when the truth object is referenced in an ROI model or deck
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..models.truth_object import (
    DisputeReason,
    MaturityHistory,
    MaturityLevel,
    TruthObject,
    TruthSource,
    TruthStatus,
    ValidationEvent,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class InvalidTransitionError(ValueError):
    """Raised when a requested state transition is not permitted."""

    pass


class InsufficientEvidenceError(ValueError):
    """Raised when the evidence requirements for a transition are not met."""

    pass


# ---------------------------------------------------------------------------
# Allowed transitions map
# ---------------------------------------------------------------------------

ALLOWED_TRANSITIONS: dict[TruthStatus, set[TruthStatus]] = {
    TruthStatus.EXTRACTED: {TruthStatus.SUPPORTED, TruthStatus.DISPUTED},
    TruthStatus.SUPPORTED: {TruthStatus.CORROBORATED, TruthStatus.DISPUTED},
    TruthStatus.CORROBORATED: {TruthStatus.APPROVED, TruthStatus.DISPUTED},
    TruthStatus.APPROVED: {TruthStatus.DISPUTED},
    TruthStatus.DISPUTED: {TruthStatus.CORROBORATED},  # revert after resolution
}

# Status → maturity level mapping (minimum maturity for a given status)
STATUS_TO_MATURITY: dict[TruthStatus, MaturityLevel] = {
    TruthStatus.EXTRACTED: MaturityLevel.EXTRACTED,
    TruthStatus.SUPPORTED: MaturityLevel.SUPPORTED,
    TruthStatus.CORROBORATED: MaturityLevel.CORROBORATED,
    TruthStatus.APPROVED: MaturityLevel.APPROVED,
    TruthStatus.DISPUTED: MaturityLevel.EXTRACTED,  # maturity does not advance on dispute
}


# ---------------------------------------------------------------------------
# State machine service
# ---------------------------------------------------------------------------


class ValidationStateMachine:
    """
    Encapsulates all state transition logic for TruthObject validation.

    All public methods accept an open AsyncSession and commit nothing —
    callers are responsible for committing the session. This keeps the
    service testable without needing a real database.
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    # ------------------------------------------------------------------
    # Public transition methods
    # ------------------------------------------------------------------

    async def advance_to_supported(
        self,
        db: AsyncSession,
        truth_object: TruthObject,
        actor: str | None = None,
        notes: str | None = None,
    ) -> TruthObject:
        """
        Advance a TruthObject from EXTRACTED → SUPPORTED.

        Requirements:
          - Current status must be EXTRACTED
          - confidence ≥ min_confidence_for_supported
          - At least 1 TruthSource attached
        """
        self._assert_transition(truth_object, TruthStatus.SUPPORTED)

        source_count = await self._count_sources(db, truth_object.id)
        if source_count < 1:
            raise InsufficientEvidenceError(
                "Cannot advance to SUPPORTED: at least 1 source is required."
            )
        if truth_object.confidence < self._settings.min_confidence_for_supported:
            raise InsufficientEvidenceError(
                f"Cannot advance to SUPPORTED: confidence {truth_object.confidence:.2f} "
                f"is below threshold {self._settings.min_confidence_for_supported:.2f}."
            )

        return await self._apply_transition(
            db=db,
            truth_object=truth_object,
            new_status=TruthStatus.SUPPORTED,
            actor=actor or "system",
            actor_type="system",
            source_count=source_count,
            notes=notes,
        )

    async def advance_to_corroborated(
        self,
        db: AsyncSession,
        truth_object: TruthObject,
        actor: str | None = None,
        notes: str | None = None,
    ) -> TruthObject:
        """
        Advance a TruthObject from SUPPORTED → CORROBORATED.

        Requirements:
          - Current status must be SUPPORTED
          - ≥ min_sources_for_corroborated distinct sources
          - Sources must have different (source_type, source_url) pairs
        """
        self._assert_transition(truth_object, TruthStatus.CORROBORATED)

        distinct_count = await self._count_distinct_sources(db, truth_object.id)
        if distinct_count < self._settings.min_sources_for_corroborated:
            raise InsufficientEvidenceError(
                f"Cannot advance to CORROBORATED: need "
                f"{self._settings.min_sources_for_corroborated} distinct sources, "
                f"found {distinct_count}."
            )

        return await self._apply_transition(
            db=db,
            truth_object=truth_object,
            new_status=TruthStatus.CORROBORATED,
            actor=actor or "system",
            actor_type="system",
            source_count=distinct_count,
            notes=notes,
        )

    async def approve(
        self,
        db: AsyncSession,
        truth_object: TruthObject,
        approved_by: str,
        notes: str | None = None,
    ) -> TruthObject:
        """
        Advance a TruthObject from CORROBORATED → APPROVED.

        Requirements:
          - Current status must be CORROBORATED
          - approved_by must be a non-empty string (human reviewer)
        """
        self._assert_transition(truth_object, TruthStatus.APPROVED)

        if not approved_by or not approved_by.strip():
            raise ValueError("approved_by is required for APPROVED transition.")

        source_count = await self._count_sources(db, truth_object.id)

        truth_object.approved_by = approved_by
        truth_object.approved_at = datetime.now(UTC)
        truth_object.approval_notes = notes

        return await self._apply_transition(
            db=db,
            truth_object=truth_object,
            new_status=TruthStatus.APPROVED,
            actor=approved_by,
            actor_type="human",
            source_count=source_count,
            notes=notes,
        )

    async def dispute(
        self,
        db: AsyncSession,
        truth_object: TruthObject,
        reason: DisputeReason,
        disputed_by: str,
        notes: str | None = None,
    ) -> TruthObject:
        """
        Mark a TruthObject as DISPUTED from any non-DISPUTED status.

        Requirements:
          - Current status must not already be DISPUTED
          - reason and disputed_by are required
        """
        self._assert_transition(truth_object, TruthStatus.DISPUTED)

        if not reason:
            raise ValueError("reason is required for DISPUTED transition.")
        if not disputed_by or not disputed_by.strip():
            raise ValueError("disputed_by is required for DISPUTED transition.")

        source_count = await self._count_sources(db, truth_object.id)

        truth_object.dispute_reason = reason.value
        truth_object.dispute_notes = notes
        truth_object.disputed_by = disputed_by
        truth_object.disputed_at = datetime.now(UTC)

        return await self._apply_transition(
            db=db,
            truth_object=truth_object,
            new_status=TruthStatus.DISPUTED,
            actor=disputed_by,
            actor_type="human",
            source_count=source_count,
            notes=notes,
        )

    async def resolve_dispute(
        self,
        db: AsyncSession,
        truth_object: TruthObject,
        resolved_by: str,
        notes: str | None = None,
    ) -> TruthObject:
        """
        Revert a DISPUTED TruthObject back to CORROBORATED after resolution.

        Requirements:
          - Current status must be DISPUTED
          - resolved_by is required (human actor)
        """
        self._assert_transition(truth_object, TruthStatus.CORROBORATED)

        source_count = await self._count_sources(db, truth_object.id)

        # Clear dispute fields
        truth_object.dispute_reason = None
        truth_object.dispute_notes = None
        truth_object.disputed_by = None
        truth_object.disputed_at = None

        return await self._apply_transition(
            db=db,
            truth_object=truth_object,
            new_status=TruthStatus.CORROBORATED,
            actor=resolved_by,
            actor_type="human",
            source_count=source_count,
            notes=notes or "Dispute resolved.",
        )

    async def mark_operationalized(
        self,
        db: AsyncSession,
        truth_object: TruthObject,
        trigger: str,
        triggered_by: str | None = None,
        context: dict | None = None,
    ) -> TruthObject:
        """
        Advance maturity to OPERATIONALIZED (level 5) without changing status.

        Called when a TruthObject is referenced in an ROI model, board deck,
        or other downstream business artefact.

        Requirements:
          - Current maturity must be APPROVED (4)
          - Current status must be APPROVED
        """
        if truth_object.status != TruthStatus.APPROVED.value:
            raise InvalidTransitionError(
                f"Only APPROVED truth objects can be operationalized, "
                f"current status: {truth_object.status}"
            )
        if truth_object.maturity_level >= MaturityLevel.OPERATIONALIZED.value:
            logger.debug(
                "TruthObject %s already at OPERATIONALIZED maturity", truth_object.id
            )
            return truth_object

        old_maturity = truth_object.maturity_level
        truth_object.maturity_level = MaturityLevel.OPERATIONALIZED.value
        truth_object.updated_at = datetime.now(UTC)

        history = MaturityHistory(
            truth_object_id=truth_object.id,
            organization_id=truth_object.organization_id,
            from_level=old_maturity,
            to_level=MaturityLevel.OPERATIONALIZED.value,
            trigger=trigger,
            triggered_by=triggered_by,
            context=context,
        )
        db.add(history)

        logger.info(
            "TruthObject %s advanced to OPERATIONALIZED via %s",
            truth_object.id,
            trigger,
        )
        return truth_object

    # ------------------------------------------------------------------
    # Auto-advance helper (called after source is added)
    # ------------------------------------------------------------------

    async def auto_advance(
        self,
        db: AsyncSession,
        truth_object: TruthObject,
    ) -> TruthObject:
        """
        Attempt automatic advancement based on current evidence.

        Called after a new TruthSource is added. Will advance through
        EXTRACTED → SUPPORTED → CORROBORATED if thresholds are met.
        Does NOT advance to APPROVED (requires human actor).
        """
        if not self._settings.auto_advance_to_supported:
            return truth_object

        current = TruthStatus(truth_object.status)

        if current == TruthStatus.EXTRACTED:
            try:
                truth_object = await self.advance_to_supported(
                    db, truth_object, actor="system:auto_advance"
                )
                current = TruthStatus.SUPPORTED
            except (InvalidTransitionError, InsufficientEvidenceError):
                return truth_object

        if current == TruthStatus.SUPPORTED:
            try:
                truth_object = await self.advance_to_corroborated(
                    db, truth_object, actor="system:auto_advance"
                )
            except (InvalidTransitionError, InsufficientEvidenceError):
                pass

        return truth_object

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _assert_transition(
        self,
        truth_object: TruthObject,
        target: TruthStatus,
    ) -> None:
        """Raise InvalidTransitionError if the transition is not permitted."""
        current = TruthStatus(truth_object.status)
        allowed = ALLOWED_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidTransitionError(
                f"Transition {current.value} → {target.value} is not permitted. "
                f"Allowed from {current.value}: "
                f"{[s.value for s in allowed] or 'none'}."
            )

    async def _count_sources(
        self,
        db: AsyncSession,
        truth_object_id: UUID,
    ) -> int:
        """Count the number of TruthSource records for a given TruthObject."""
        result = await db.execute(
            select(func.count()).where(TruthSource.truth_object_id == truth_object_id)
        )
        return result.scalar() or 0

    async def _count_distinct_sources(
        self,
        db: AsyncSession,
        truth_object_id: UUID,
    ) -> int:
        """Count distinct sources by (source_type, source_url) pairs.

        Two sources are considered distinct if they have different
        source_type values OR different source_url values.
        """
        # Use a subquery to count distinct (source_type, source_url) pairs
        subq = (
            select(
                TruthSource.source_type,
                TruthSource.source_url,
            )
            .where(TruthSource.truth_object_id == truth_object_id)
            .distinct()
            .subquery()
        )
        count_stmt = select(func.count()).select_from(subq)
        result = await db.execute(count_stmt)
        return result.scalar() or 0

    async def _apply_transition(
        self,
        db: AsyncSession,
        truth_object: TruthObject,
        new_status: TruthStatus,
        actor: str,
        actor_type: str,
        source_count: int,
        notes: str | None = None,
    ) -> TruthObject:
        """Apply a validated status transition and record audit events."""
        old_status = truth_object.status
        old_maturity = truth_object.maturity_level
        new_maturity = max(
            old_maturity,
            STATUS_TO_MATURITY[new_status].value,
        )

        # Update the truth object
        truth_object.status = new_status.value
        truth_object.maturity_level = new_maturity
        truth_object.updated_at = datetime.now(UTC)

        # Record validation event (immutable audit)
        event = ValidationEvent(
            truth_object_id=truth_object.id,
            organization_id=truth_object.organization_id,
            from_status=old_status,
            to_status=new_status.value,
            from_maturity=old_maturity,
            to_maturity=new_maturity,
            actor=actor,
            actor_type=actor_type,
            confidence_at_transition=truth_object.confidence,
            source_count_at_transition=source_count,
            notes=notes,
        )
        db.add(event)

        # Record maturity history if maturity changed
        if new_maturity != old_maturity:
            history = MaturityHistory(
                truth_object_id=truth_object.id,
                organization_id=truth_object.organization_id,
                from_level=old_maturity,
                to_level=new_maturity,
                trigger=f"status_transition:{new_status.value}",
                triggered_by=actor,
            )
            db.add(history)

        logger.info(
            "TruthObject %s transitioned %s → %s (maturity %d → %d) by %s",
            truth_object.id,
            old_status,
            new_status.value,
            old_maturity,
            new_maturity,
            actor,
        )
        await db.flush()  # Persist event and history before returning
        return truth_object
