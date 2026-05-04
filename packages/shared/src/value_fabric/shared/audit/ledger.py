"""Hash-chained audit ledger handler.

Implements per-chain_id monotonic sequencing and hash chaining for audit
events.  Registered as an ``AuditEmitter`` handler when
``AUDIT_LEDGER_MODE=enabled``.

GATE Framework §1.3 — Hash-Chained Audit Emitter
"""

from __future__ import annotations

import logging
from typing import Any

from value_fabric.shared.crypto.canonical import canonical_hash

from .models import AuditEvent

logger = logging.getLogger(__name__)


class LedgerCommitHandler:
    """Audit handler that enforces hash chaining and emits ledger commits.

    Maintains a per-chain_id monotonic sequence and previous_hash.
    In multi-instance deployments, chain state MUST be backed by Redis
    (or the audit sink itself) to prevent hash forks.
    """

    def __init__(self, redis_client: Any | None = None) -> None:
        self._redis = redis_client
        self._local_heads: dict[str, tuple[int, str]] = {}  # chain_id -> (seq, hash)

    async def handle(self, event: AuditEvent) -> None:
        """Process an audit event through the ledger chain.

        If the event has a ``chain_id``, compute its canonical hash and
        link it to the previous event in the same chain.  Events without
        a ``chain_id`` are passed through unchanged.
        """
        if not event.chain_id:
            return

        chain_id = event.chain_id
        seq, prev_hash = await self._get_chain_head(chain_id)
        next_seq = seq + 1

        # Build canonical payload (excluding mutable/hash fields)
        payload = {
            "id": str(event.id),
            "timestamp": event.timestamp,
            "action": event.action.value,
            "outcome": event.outcome.value,
            "actor_id": str(event.actor_id) if event.actor_id else None,
            "tenant_id": str(event.tenant_id) if event.tenant_id else None,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "request_id": event.request_id,
            "details": event.details,
            "previous_hash": prev_hash,
            "sequence_number": next_seq,
            "chain_id": chain_id,
        }

        event_hash = canonical_hash(payload)
        event.previous_hash = prev_hash
        event.event_hash = event_hash
        event.canonical_payload = payload
        event.sequence_number = next_seq

        await self._set_chain_head(chain_id, next_seq, event_hash)

        logger.debug(
            "Ledger commit: chain=%s seq=%d hash=%s",
            chain_id,
            next_seq,
            event_hash[:12],
        )

    async def _get_chain_head(self, chain_id: str) -> tuple[int, str | None]:
        """Retrieve the current head (sequence, hash) for a chain."""
        if self._redis:
            # Redis-backed chain lookup not yet implemented; falling back to local.
            # In production multi-instance deployments, this MUST be implemented
            # to prevent hash chain forks.
            raise NotImplementedError(
                "Redis-backed audit ledger chain lookup is not implemented. "
                "Use local_heads only for single-instance deployments."
            )
        return self._local_heads.get(chain_id, (0, None))

    async def _set_chain_head(self, chain_id: str, seq: int, hash_: str) -> None:
        """Update the chain head after a successful commit."""
        if self._redis:
            # See _get_chain_head for Redis implementation requirements.
            raise NotImplementedError(
                "Redis-backed audit ledger chain update is not implemented. "
                "Use local_heads only for single-instance deployments."
            )
        self._local_heads[chain_id] = (seq, hash_)

    def get_chain_state(self, chain_id: str) -> tuple[int, str | None]:
        """Return current (sequence, hash) for a chain (sync, for testing)."""
        return self._local_heads.get(chain_id, (0, None))
