"""Tests for hash-chained audit ledger handler.

Covers:
- Chain monotonicity (sequence numbers increase)
- Hash continuity (previous_hash links to prior event)
- Fork detection (different chain_ids are independent)
- Non-chained events pass through unchanged
- Emitter integration with chain_id parameter
"""

from __future__ import annotations

import pytest
from uuid import uuid4

from shared.audit.emitter import AuditEmitter, emit_audit_event, _create_audit_event
from shared.audit.ledger import LedgerCommitHandler
from shared.audit.models import AuditAction, AuditEvent, AuditOutcome


def _make_event(
    chain_id: str | None = None,
    action: AuditAction = AuditAction.TOOL_INVOCATION,
) -> AuditEvent:
    """Create a minimal AuditEvent for testing."""
    return AuditEvent(
        id=uuid4(),
        timestamp="2026-01-01T00:00:00Z",
        action=action,
        outcome=AuditOutcome.SUCCESS,
        resource_type="tool",
        resource_id="test_tool",
        chain_id=chain_id,
    )


# ═══════════════════════════════════════════════════════════════════════════
# LedgerCommitHandler unit tests
# ═══════════════════════════════════════════════════════════════════════════


class TestLedgerCommitHandler:
    """LedgerCommitHandler chain integrity."""

    @pytest.fixture
    def handler(self) -> LedgerCommitHandler:
        return LedgerCommitHandler()

    @pytest.mark.asyncio
    async def test_first_event_has_no_previous_hash(self, handler: LedgerCommitHandler) -> None:
        """First event in a chain must have previous_hash=None."""
        event = _make_event(chain_id="tenant-1:tool_a")
        await handler.handle(event)
        assert event.previous_hash is None
        assert event.event_hash is not None
        assert event.sequence_number == 1

    @pytest.mark.asyncio
    async def test_chain_monotonicity(self, handler: LedgerCommitHandler) -> None:
        """Sequence numbers must increase monotonically within a chain."""
        chain = "tenant-1:tool_a"
        for expected_seq in range(1, 6):
            event = _make_event(chain_id=chain)
            await handler.handle(event)
            assert event.sequence_number == expected_seq

    @pytest.mark.asyncio
    async def test_hash_continuity(self, handler: LedgerCommitHandler) -> None:
        """Each event's previous_hash must equal the prior event's event_hash."""
        chain = "tenant-1:tool_a"
        prev_hash = None
        for _ in range(5):
            event = _make_event(chain_id=chain)
            await handler.handle(event)
            assert event.previous_hash == prev_hash
            prev_hash = event.event_hash

    @pytest.mark.asyncio
    async def test_independent_chains(self, handler: LedgerCommitHandler) -> None:
        """Different chain_ids must maintain independent sequences."""
        e1 = _make_event(chain_id="chain-a")
        e2 = _make_event(chain_id="chain-b")
        e3 = _make_event(chain_id="chain-a")

        await handler.handle(e1)
        await handler.handle(e2)
        await handler.handle(e3)

        assert e1.sequence_number == 1
        assert e2.sequence_number == 1
        assert e3.sequence_number == 2
        assert e3.previous_hash == e1.event_hash

    @pytest.mark.asyncio
    async def test_non_chained_event_passthrough(self, handler: LedgerCommitHandler) -> None:
        """Events without chain_id must not be modified."""
        event = _make_event(chain_id=None)
        await handler.handle(event)
        assert event.previous_hash is None
        assert event.event_hash is None
        assert event.sequence_number is None

    @pytest.mark.asyncio
    async def test_canonical_payload_populated(self, handler: LedgerCommitHandler) -> None:
        """Handled events must have canonical_payload set."""
        event = _make_event(chain_id="test-chain")
        await handler.handle(event)
        assert event.canonical_payload is not None
        assert event.canonical_payload["chain_id"] == "test-chain"
        assert event.canonical_payload["sequence_number"] == 1

    @pytest.mark.asyncio
    async def test_hash_determinism(self, handler: LedgerCommitHandler) -> None:
        """Same event data must produce same hash."""
        e1 = AuditEvent(
            id=uuid4(),
            timestamp="2026-01-01T00:00:00Z",
            action=AuditAction.TOOL_INVOCATION,
            outcome=AuditOutcome.SUCCESS,
            resource_type="tool",
            resource_id="test_tool",
            chain_id="det-chain",
        )
        # Create identical event
        e2 = AuditEvent(
            id=e1.id,
            timestamp=e1.timestamp,
            action=e1.action,
            outcome=e1.outcome,
            resource_type=e1.resource_type,
            resource_id=e1.resource_id,
            chain_id=e1.chain_id,
        )

        handler2 = LedgerCommitHandler()
        await handler.handle(e1)
        await handler2.handle(e2)
        assert e1.event_hash == e2.event_hash

    @pytest.mark.asyncio
    async def test_100_event_chain_verifiable(self, handler: LedgerCommitHandler) -> None:
        """A 100-event chain must be end-to-end verifiable."""
        chain = "stress-chain"
        hashes: list[str] = []
        for _ in range(100):
            event = _make_event(chain_id=chain)
            await handler.handle(event)
            hashes.append(event.event_hash)

        # Verify chain integrity
        assert len(set(hashes)) == 100  # all unique
        seq, head_hash = handler.get_chain_state(chain)
        assert seq == 100
        assert head_hash == hashes[-1]


# ═══════════════════════════════════════════════════════════════════════════
# Emitter integration
# ═══════════════════════════════════════════════════════════════════════════


class TestEmitterIntegration:
    """Verify emitter passes chain_id through to events."""

    def test_create_audit_event_with_chain_id(self) -> None:
        """_create_audit_event must accept and set chain_id."""
        event = _create_audit_event(
            action=AuditAction.TOOL_INVOCATION,
            outcome=AuditOutcome.SUCCESS,
            resource_type="tool",
            resource_id="test",
            chain_id="my-chain",
        )
        assert event.chain_id == "my-chain"

    def test_create_audit_event_without_chain_id(self) -> None:
        """chain_id defaults to None."""
        event = _create_audit_event(
            action=AuditAction.CREATE,
            outcome=AuditOutcome.SUCCESS,
            resource_type="resource",
        )
        assert event.chain_id is None

    @pytest.mark.asyncio
    async def test_emitter_with_ledger_handler(self) -> None:
        """Full pipeline: emitter -> ledger handler -> chained event."""
        emitter = AuditEmitter()
        handler = LedgerCommitHandler()
        emitter.add_handler(handler)

        event = _create_audit_event(
            action=AuditAction.TOOL_INVOCATION,
            outcome=AuditOutcome.SUCCESS,
            resource_type="tool",
            resource_id="crm_sync",
            chain_id="t-1:crm_sync",
        )
        await emitter.emit(event)

        assert event.sequence_number == 1
        assert event.event_hash is not None
        assert event.previous_hash is None
