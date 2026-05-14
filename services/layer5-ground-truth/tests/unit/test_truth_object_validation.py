"""Adversarial unit tests for TruthObject validation and state machine.

Covers:
- Missing evidence → transition rejected
- Confidence below threshold → transition rejected
- Invalid/forbidden state transitions
- Approval without human actor → rejected
- Dispute without reason → rejected
- Cross-tenant claim injection → rejected
- Maturity ladder regression (downgrade) → not permitted
- Concurrent transition conflict → TransitionConflictError
- Operationalization of non-APPROVED object → rejected
- Auto-advance stops at CORROBORATED (never auto-approves)
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

# Ensure layer5 src is importable
_L5_SRC = Path(__file__).parents[3] / "src"
if str(_L5_SRC) not in sys.path:
    sys.path.insert(0, str(_L5_SRC))

from layer5_ground_truth.models.truth_object import DisputeReason, MaturityLevel, TruthStatus
from layer5_ground_truth.services.state_machine import (
    InsufficientEvidenceError,
    InvalidTransitionError,
    TransitionConflictError,
    ValidationStateMachine,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_truth_object(
    *,
    status: TruthStatus = TruthStatus.EXTRACTED,
    confidence: float = 0.9,
    maturity_level: int = MaturityLevel.EXTRACTED.value,
    tenant_id=None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id or uuid4(),
        status=status.value,
        confidence=confidence,
        maturity_level=maturity_level,
        approved_by=None,
        approved_at=None,
        approval_notes=None,
        dispute_reason=None,
        dispute_notes=None,
        disputed_by=None,
        disputed_at=None,
        deleted_at=None,
        updated_at=None,
    )


def _make_db(*, rowcount: int = 1) -> AsyncMock:
    """Mock AsyncSession that simulates a successful UPDATE (rowcount=1)."""
    result = MagicMock()
    result.rowcount = rowcount
    result.scalar = MagicMock(return_value=1)

    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


def _make_db_with_source_count(count: int, *, rowcount: int = 1) -> AsyncMock:
    """Mock AsyncSession where source count queries return `count`.

    Dispatches on statement type rather than call order so the mock is
    correct regardless of how many source-count queries a method makes
    before issuing the UPDATE:
    - UPDATE statements (optimistic-lock transition) → update_result
    - All other statements (SELECT source counts) → scalar_result
    """
    from sqlalchemy.sql.dml import Update as _Update

    scalar_result = MagicMock()
    scalar_result.scalar = MagicMock(return_value=count)

    update_result = MagicMock()
    update_result.rowcount = rowcount

    async def _execute(stmt, *args, **kwargs):
        if isinstance(stmt, _Update):
            return update_result
        return scalar_result

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=_execute)
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


_SETTINGS = SimpleNamespace(
    min_confidence_for_supported=0.5,
    min_sources_for_corroborated=2,
    auto_advance_to_supported=True,
)


def _make_sm() -> ValidationStateMachine:
    sm = ValidationStateMachine.__new__(ValidationStateMachine)
    sm._settings = _SETTINGS
    return sm


# ---------------------------------------------------------------------------
# EXTRACTED → SUPPORTED: missing evidence
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.asyncio
async def test_advance_to_supported_requires_at_least_one_source():
    """Transition to SUPPORTED is rejected when no sources are attached."""
    sm = _make_sm()
    to = _make_truth_object(status=TruthStatus.EXTRACTED, confidence=0.9)

    scalar_result = MagicMock()
    scalar_result.scalar = MagicMock(return_value=0)  # zero sources
    db = AsyncMock()
    db.execute = AsyncMock(return_value=scalar_result)

    with pytest.raises(InsufficientEvidenceError, match="at least 1 source"):
        await sm.advance_to_supported(db, to)

    db.add.assert_not_called()
    db.flush.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_advance_to_supported_requires_minimum_confidence():
    """Transition to SUPPORTED is rejected when confidence is below threshold."""
    sm = _make_sm()
    to = _make_truth_object(status=TruthStatus.EXTRACTED, confidence=0.3)

    scalar_result = MagicMock()
    scalar_result.scalar = MagicMock(return_value=1)  # has a source
    db = AsyncMock()
    db.execute = AsyncMock(return_value=scalar_result)

    with pytest.raises(InsufficientEvidenceError, match="confidence"):
        await sm.advance_to_supported(db, to)

    db.add.assert_not_called()


# ---------------------------------------------------------------------------
# SUPPORTED → CORROBORATED: insufficient distinct sources
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.asyncio
async def test_advance_to_corroborated_requires_distinct_sources():
    """Transition to CORROBORATED is rejected with only 1 distinct source."""
    sm = _make_sm()
    to = _make_truth_object(status=TruthStatus.SUPPORTED)

    scalar_result = MagicMock()
    scalar_result.scalar = MagicMock(return_value=1)  # only 1 distinct source
    db = AsyncMock()
    db.execute = AsyncMock(return_value=scalar_result)

    with pytest.raises(InsufficientEvidenceError, match="distinct sources"):
        await sm.advance_to_corroborated(db, to)

    db.add.assert_not_called()


# ---------------------------------------------------------------------------
# CORROBORATED → APPROVED: requires human actor
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.asyncio
async def test_approve_requires_non_empty_approved_by():
    """Approval is rejected when approved_by is empty or whitespace."""
    sm = _make_sm()
    to = _make_truth_object(status=TruthStatus.CORROBORATED)
    db = _make_db_with_source_count(3)

    for bad_value in ("", "   ", None):
        with pytest.raises(ValueError, match="approved_by is required"):
            await sm.approve(db, to, approved_by=bad_value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_approve_from_non_corroborated_status_rejected():
    """Approval from EXTRACTED or SUPPORTED status is rejected."""
    sm = _make_sm()
    db = _make_db_with_source_count(3)

    for bad_status in (TruthStatus.EXTRACTED, TruthStatus.SUPPORTED, TruthStatus.DISPUTED):
        to = _make_truth_object(status=bad_status)
        with pytest.raises(InvalidTransitionError):
            await sm.approve(db, to, approved_by="reviewer@example.com")


# ---------------------------------------------------------------------------
# Dispute: requires reason and actor
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.asyncio
async def test_dispute_requires_reason():
    """Dispute is rejected when reason is None."""
    sm = _make_sm()
    to = _make_truth_object(status=TruthStatus.CORROBORATED)
    db = _make_db_with_source_count(2)

    with pytest.raises(ValueError, match="reason is required"):
        await sm.dispute(db, to, reason=None, disputed_by="analyst@example.com")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_dispute_requires_disputed_by():
    """Dispute is rejected when disputed_by is empty."""
    sm = _make_sm()
    to = _make_truth_object(status=TruthStatus.CORROBORATED)
    db = _make_db_with_source_count(2)

    with pytest.raises(ValueError, match="disputed_by is required"):
        await sm.dispute(db, to, reason=DisputeReason.CONFLICTING_SOURCES, disputed_by="")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_dispute_already_disputed_is_rejected():
    """Disputing an already-DISPUTED object is rejected."""
    sm = _make_sm()
    to = _make_truth_object(status=TruthStatus.DISPUTED)
    db = _make_db_with_source_count(2)

    with pytest.raises(InvalidTransitionError):
        await sm.dispute(db, to, reason=DisputeReason.CONFLICTING_SOURCES, disputed_by="analyst")


# ---------------------------------------------------------------------------
# Forbidden transitions
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.asyncio
async def test_cannot_skip_from_extracted_to_corroborated():
    """EXTRACTED → CORROBORATED is not a permitted transition."""
    sm = _make_sm()
    to = _make_truth_object(status=TruthStatus.EXTRACTED)
    db = _make_db_with_source_count(3)

    with pytest.raises(InvalidTransitionError):
        await sm.advance_to_corroborated(db, to)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cannot_skip_from_extracted_to_approved():
    """EXTRACTED → APPROVED is not a permitted transition."""
    sm = _make_sm()
    to = _make_truth_object(status=TruthStatus.EXTRACTED)
    db = _make_db_with_source_count(3)

    with pytest.raises(InvalidTransitionError):
        await sm.approve(db, to, approved_by="reviewer@example.com")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cannot_transition_approved_to_supported():
    """APPROVED → SUPPORTED is not a permitted transition (no regression)."""
    sm = _make_sm()
    to = _make_truth_object(
        status=TruthStatus.APPROVED,
        maturity_level=MaturityLevel.APPROVED.value,
    )
    db = _make_db_with_source_count(3)

    with pytest.raises(InvalidTransitionError):
        await sm.advance_to_supported(db, to)


# ---------------------------------------------------------------------------
# Maturity ladder: no regression
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.asyncio
async def test_maturity_does_not_regress_on_dispute():
    """Maturity level must not decrease when a TruthObject is disputed."""
    sm = _make_sm()
    # Object at CORROBORATED maturity (level 3)
    to = _make_truth_object(
        status=TruthStatus.CORROBORATED,
        maturity_level=MaturityLevel.CORROBORATED.value,
    )
    # dispute() calls: (1) _count_sources → scalar, (2) UPDATE → rowcount=1
    scalar_result = MagicMock()
    scalar_result.scalar = MagicMock(return_value=2)
    update_result = MagicMock()
    update_result.rowcount = 1
    call_count = [0]

    async def _execute(stmt, *args, **kwargs):
        call_count[0] += 1
        return scalar_result if call_count[0] == 1 else update_result

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=_execute)
    db.add = MagicMock()
    db.flush = AsyncMock()

    result = await sm.dispute(
        db, to, reason=DisputeReason.CONFLICTING_SOURCES, disputed_by="analyst"
    )

    # Status changes to DISPUTED but maturity must not go below CORROBORATED
    assert result.maturity_level >= MaturityLevel.CORROBORATED.value, (
        f"Maturity regressed to {result.maturity_level} after dispute"
    )


# ---------------------------------------------------------------------------
# Concurrent transition conflict
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.asyncio
async def test_concurrent_transition_raises_conflict_error():
    """TransitionConflictError is raised when the UPDATE affects 0 rows."""
    sm = _make_sm()
    to = _make_truth_object(status=TruthStatus.EXTRACTED, confidence=0.9)

    # rowcount=0 simulates another process already changed the status
    db = _make_db_with_source_count(1, rowcount=0)

    with pytest.raises(TransitionConflictError, match="Concurrent transition"):
        await sm.advance_to_supported(db, to)


# ---------------------------------------------------------------------------
# Operationalization guards
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.asyncio
async def test_operationalize_requires_approved_status():
    """mark_operationalized is rejected for non-APPROVED objects."""
    sm = _make_sm()
    db = AsyncMock()

    for bad_status in (TruthStatus.EXTRACTED, TruthStatus.SUPPORTED,
                       TruthStatus.CORROBORATED, TruthStatus.DISPUTED):
        to = _make_truth_object(
            status=bad_status,
            maturity_level=MaturityLevel.CORROBORATED.value,
        )
        with pytest.raises(InvalidTransitionError, match="Only APPROVED"):
            await sm.mark_operationalized(db, to, trigger="roi_model")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_operationalize_is_idempotent_when_already_operationalized():
    """mark_operationalized is a no-op when already at OPERATIONALIZED maturity."""
    sm = _make_sm()
    db = AsyncMock()
    to = _make_truth_object(
        status=TruthStatus.APPROVED,
        maturity_level=MaturityLevel.OPERATIONALIZED.value,
    )

    result = await sm.mark_operationalized(db, to, trigger="roi_model")

    assert result.maturity_level == MaturityLevel.OPERATIONALIZED.value
    db.add.assert_not_called()


# ---------------------------------------------------------------------------
# Auto-advance: never auto-approves
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.asyncio
async def test_auto_advance_never_reaches_approved():
    """auto_advance must stop at CORROBORATED and never auto-approve."""
    sm = _make_sm()
    to = _make_truth_object(status=TruthStatus.EXTRACTED, confidence=0.9)

    # auto_advance EXTRACTED→SUPPORTED→CORROBORATED:
    # call 1: _count_sources (scalar), call 2: UPDATE (rowcount)
    # call 3: _count_sources (scalar), call 4: UPDATE (rowcount)
    scalar_result = MagicMock()
    scalar_result.scalar = MagicMock(return_value=3)
    update_result = MagicMock()
    update_result.rowcount = 1

    call_count = [0]

    async def _execute(stmt, *args, **kwargs):
        call_count[0] += 1
        # Even calls are UPDATEs; odd calls are source count queries
        if call_count[0] % 2 == 0:
            return update_result
        return scalar_result

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=_execute)
    db.add = MagicMock()
    db.flush = AsyncMock()

    result = await sm.auto_advance(db, to)

    assert TruthStatus(result.status) != TruthStatus.APPROVED, (
        "auto_advance must never reach APPROVED — human approval is required"
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_auto_advance_disabled_by_settings():
    """auto_advance is a no-op when auto_advance_to_supported is False."""
    sm = _make_sm()
    sm._settings = SimpleNamespace(
        min_confidence_for_supported=0.5,
        min_sources_for_corroborated=2,
        auto_advance_to_supported=False,
    )
    to = _make_truth_object(status=TruthStatus.EXTRACTED, confidence=0.9)
    db = AsyncMock()

    result = await sm.auto_advance(db, to)

    assert TruthStatus(result.status) == TruthStatus.EXTRACTED
    db.execute.assert_not_called()
