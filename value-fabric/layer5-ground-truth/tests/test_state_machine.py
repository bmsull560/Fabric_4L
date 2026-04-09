"""
Unit tests for the ValidationStateMachine.

Tests are designed to FAIL initially if the state machine is not implemented
correctly. Each test verifies a specific invariant of the state machine.

Coverage:
  - All valid forward transitions
  - All invalid transitions (must raise InvalidTransitionError)
  - Insufficient evidence guard (InsufficientEvidenceError)
  - Dispute and resolve_dispute flow
  - Auto-advance behaviour
  - Maturity level advancement
  - Immutable audit event creation
"""

import uuid
from datetime import datetime, timezone

import pytest

from layer5_ground_truth.src.models.truth_object import (
    DisputeReason,
    MaturityLevel,
    TruthObject,
    TruthSource,
    TruthStatus,
    ValidationEvent,
)
from layer5_ground_truth.src.services.state_machine import (
    InsufficientEvidenceError,
    InvalidTransitionError,
    ValidationStateMachine,
)
from tests.conftest import TEST_ORG_ID


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_truth(
    status: TruthStatus = TruthStatus.EXTRACTED,
    confidence: float = 0.85,
    maturity: int = MaturityLevel.EXTRACTED.value,
) -> TruthObject:
    return TruthObject(
        id=uuid.uuid4(),
        organization_id=TEST_ORG_ID,
        claim="Test claim for unit testing",
        claim_type="efficiency_gain",
        confidence=confidence,
        status=status.value,
        maturity_level=maturity,
        freshness=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def make_source(truth_id: uuid.UUID) -> TruthSource:
    return TruthSource(
        id=uuid.uuid4(),
        truth_object_id=truth_id,
        organization_id=TEST_ORG_ID,
        source_type="call_transcript",
        confidence_contribution=0.8,
        created_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# EXTRACTED → SUPPORTED
# ---------------------------------------------------------------------------

class TestAdvanceToSupported:
    @pytest.mark.asyncio
    async def test_advances_when_conditions_met(self, db):
        """Should advance EXTRACTED → SUPPORTED when confidence ≥ 0.5 and 1+ source."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.EXTRACTED, confidence=0.85)
        db.add(truth)
        source = make_source(truth.id)
        db.add(source)
        await db.flush()

        result = await sm.advance_to_supported(db, truth, actor="test_user")

        assert result.status == TruthStatus.SUPPORTED.value
        assert result.maturity_level >= MaturityLevel.SUPPORTED.value

    @pytest.mark.asyncio
    async def test_fails_without_sources(self, db):
        """Should raise InsufficientEvidenceError when no sources attached."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.EXTRACTED, confidence=0.85)
        db.add(truth)
        await db.flush()

        with pytest.raises(InsufficientEvidenceError, match="at least 1 source"):
            await sm.advance_to_supported(db, truth)

    @pytest.mark.asyncio
    async def test_fails_with_low_confidence(self, db):
        """Should raise InsufficientEvidenceError when confidence < threshold."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.EXTRACTED, confidence=0.3)
        db.add(truth)
        source = make_source(truth.id)
        db.add(source)
        await db.flush()

        with pytest.raises(InsufficientEvidenceError, match="confidence"):
            await sm.advance_to_supported(db, truth)

    @pytest.mark.asyncio
    async def test_invalid_from_corroborated(self, db):
        """Cannot advance to SUPPORTED from CORROBORATED."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.CORROBORATED)
        db.add(truth)
        await db.flush()

        with pytest.raises(InvalidTransitionError):
            await sm.advance_to_supported(db, truth)

    @pytest.mark.asyncio
    async def test_creates_validation_event(self, db):
        """Transition must create an immutable ValidationEvent record."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.EXTRACTED, confidence=0.9)
        db.add(truth)
        source = make_source(truth.id)
        db.add(source)
        await db.flush()

        await sm.advance_to_supported(db, truth, actor="auditor")
        await db.flush()

        from sqlalchemy import select
        events = (await db.execute(
            select(ValidationEvent).where(
                ValidationEvent.truth_object_id == truth.id,
                ValidationEvent.to_status == TruthStatus.SUPPORTED.value,
            )
        )).scalars().all()

        assert len(events) == 1
        assert events[0].actor == "auditor"
        assert events[0].from_status == TruthStatus.EXTRACTED.value


# ---------------------------------------------------------------------------
# SUPPORTED → CORROBORATED
# ---------------------------------------------------------------------------

class TestAdvanceToCorroborated:
    @pytest.mark.asyncio
    async def test_advances_with_two_sources(self, db):
        """Should advance SUPPORTED → CORROBORATED with ≥ 2 sources."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.SUPPORTED, maturity=MaturityLevel.SUPPORTED.value)
        db.add(truth)
        db.add(make_source(truth.id))
        db.add(make_source(truth.id))
        await db.flush()

        result = await sm.advance_to_corroborated(db, truth)

        assert result.status == TruthStatus.CORROBORATED.value
        assert result.maturity_level >= MaturityLevel.CORROBORATED.value

    @pytest.mark.asyncio
    async def test_fails_with_one_source(self, db):
        """Should raise InsufficientEvidenceError with only 1 source."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.SUPPORTED, maturity=MaturityLevel.SUPPORTED.value)
        db.add(truth)
        db.add(make_source(truth.id))
        await db.flush()

        with pytest.raises(InsufficientEvidenceError, match="2 sources"):
            await sm.advance_to_corroborated(db, truth)

    @pytest.mark.asyncio
    async def test_invalid_from_extracted(self, db):
        """Cannot skip SUPPORTED and go directly to CORROBORATED."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.EXTRACTED)
        db.add(truth)
        await db.flush()

        with pytest.raises(InvalidTransitionError):
            await sm.advance_to_corroborated(db, truth)


# ---------------------------------------------------------------------------
# CORROBORATED → APPROVED
# ---------------------------------------------------------------------------

class TestApprove:
    @pytest.mark.asyncio
    async def test_approves_with_human_actor(self, db):
        """Should advance CORROBORATED → APPROVED with a valid approver."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.CORROBORATED, maturity=MaturityLevel.CORROBORATED.value)
        db.add(truth)
        await db.flush()

        result = await sm.approve(db, truth, approved_by="cfo@company.com")

        assert result.status == TruthStatus.APPROVED.value
        assert result.approved_by == "cfo@company.com"
        assert result.approved_at is not None
        assert result.maturity_level >= MaturityLevel.APPROVED.value

    @pytest.mark.asyncio
    async def test_fails_without_approver(self, db):
        """Should raise ValueError when approved_by is empty."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.CORROBORATED, maturity=MaturityLevel.CORROBORATED.value)
        db.add(truth)
        await db.flush()

        with pytest.raises(ValueError, match="approved_by is required"):
            await sm.approve(db, truth, approved_by="")

    @pytest.mark.asyncio
    async def test_invalid_from_extracted(self, db):
        """Cannot approve directly from EXTRACTED."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.EXTRACTED)
        db.add(truth)
        await db.flush()

        with pytest.raises(InvalidTransitionError):
            await sm.approve(db, truth, approved_by="cfo@company.com")


# ---------------------------------------------------------------------------
# Dispute flow
# ---------------------------------------------------------------------------

class TestDisputeFlow:
    @pytest.mark.asyncio
    async def test_dispute_from_supported(self, db):
        """Should mark SUPPORTED → DISPUTED."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.SUPPORTED, maturity=MaturityLevel.SUPPORTED.value)
        db.add(truth)
        await db.flush()

        result = await sm.dispute(
            db, truth,
            reason=DisputeReason.CONFLICTING_SOURCES,
            disputed_by="reviewer@company.com",
        )

        assert result.status == TruthStatus.DISPUTED.value
        assert result.dispute_reason == DisputeReason.CONFLICTING_SOURCES.value
        assert result.disputed_by == "reviewer@company.com"

    @pytest.mark.asyncio
    async def test_dispute_from_approved(self, db):
        """Should allow disputing an APPROVED truth object."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.APPROVED, maturity=MaturityLevel.APPROVED.value)
        db.add(truth)
        await db.flush()

        result = await sm.dispute(
            db, truth,
            reason=DisputeReason.STALE_DATA,
            disputed_by="analyst@company.com",
        )

        assert result.status == TruthStatus.DISPUTED.value

    @pytest.mark.asyncio
    async def test_cannot_dispute_already_disputed(self, db):
        """Cannot dispute a truth object that is already DISPUTED."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.DISPUTED)
        db.add(truth)
        await db.flush()

        with pytest.raises(InvalidTransitionError):
            await sm.dispute(
                db, truth,
                reason=DisputeReason.OTHER,
                disputed_by="reviewer@company.com",
            )

    @pytest.mark.asyncio
    async def test_resolve_dispute_reverts_to_corroborated(self, db):
        """Resolving a dispute should revert to CORROBORATED and clear dispute fields."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.DISPUTED, maturity=MaturityLevel.CORROBORATED.value)
        truth.dispute_reason = DisputeReason.CONFLICTING_SOURCES.value
        truth.disputed_by = "analyst@company.com"
        db.add(truth)
        await db.flush()

        result = await sm.resolve_dispute(db, truth, resolved_by="cfo@company.com")

        assert result.status == TruthStatus.CORROBORATED.value
        assert result.dispute_reason is None
        assert result.disputed_by is None


# ---------------------------------------------------------------------------
# Operationalize
# ---------------------------------------------------------------------------

class TestOperationalize:
    @pytest.mark.asyncio
    async def test_advances_maturity_to_5(self, db):
        """Should advance maturity to OPERATIONALIZED (5) for APPROVED objects."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.APPROVED, maturity=MaturityLevel.APPROVED.value)
        db.add(truth)
        await db.flush()

        result = await sm.mark_operationalized(
            db, truth,
            trigger="used_in_roi_model",
            triggered_by="system",
            context={"roi_model_id": "roi-001"},
        )

        assert result.maturity_level == MaturityLevel.OPERATIONALIZED.value
        assert result.status == TruthStatus.APPROVED.value  # status unchanged

    @pytest.mark.asyncio
    async def test_fails_for_non_approved(self, db):
        """Should raise InvalidTransitionError for non-APPROVED objects."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.CORROBORATED, maturity=MaturityLevel.CORROBORATED.value)
        db.add(truth)
        await db.flush()

        with pytest.raises(InvalidTransitionError, match="Only APPROVED"):
            await sm.mark_operationalized(db, truth, trigger="test")

    @pytest.mark.asyncio
    async def test_idempotent_if_already_operationalized(self, db):
        """Should not raise if already at OPERATIONALIZED maturity."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.APPROVED, maturity=MaturityLevel.OPERATIONALIZED.value)
        db.add(truth)
        await db.flush()

        result = await sm.mark_operationalized(db, truth, trigger="test")
        assert result.maturity_level == MaturityLevel.OPERATIONALIZED.value


# ---------------------------------------------------------------------------
# Auto-advance
# ---------------------------------------------------------------------------

class TestAutoAdvance:
    @pytest.mark.asyncio
    async def test_auto_advances_to_supported_with_one_source(self, db):
        """Auto-advance should reach SUPPORTED with 1 source + high confidence."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.EXTRACTED, confidence=0.9)
        db.add(truth)
        db.add(make_source(truth.id))
        await db.flush()

        result = await sm.auto_advance(db, truth)

        assert result.status == TruthStatus.SUPPORTED.value

    @pytest.mark.asyncio
    async def test_auto_advances_to_corroborated_with_two_sources(self, db):
        """Auto-advance should reach CORROBORATED with 2 sources + high confidence."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.EXTRACTED, confidence=0.9)
        db.add(truth)
        db.add(make_source(truth.id))
        db.add(make_source(truth.id))
        await db.flush()

        result = await sm.auto_advance(db, truth)

        assert result.status == TruthStatus.CORROBORATED.value

    @pytest.mark.asyncio
    async def test_does_not_auto_approve(self, db):
        """Auto-advance must never reach APPROVED — that requires human action."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.EXTRACTED, confidence=1.0)
        db.add(truth)
        for _ in range(5):
            db.add(make_source(truth.id))
        await db.flush()

        result = await sm.auto_advance(db, truth)

        assert result.status != TruthStatus.APPROVED.value

    @pytest.mark.asyncio
    async def test_stays_extracted_with_low_confidence(self, db):
        """Auto-advance should not advance if confidence is below threshold."""
        sm = ValidationStateMachine()
        truth = make_truth(TruthStatus.EXTRACTED, confidence=0.2)
        db.add(truth)
        db.add(make_source(truth.id))
        await db.flush()

        result = await sm.auto_advance(db, truth)

        assert result.status == TruthStatus.EXTRACTED.value
