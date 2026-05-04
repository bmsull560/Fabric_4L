"""Injectable ID-generation abstraction for deterministic unique identifiers.

**Problem:** Calling ``uuid.uuid4()`` directly inside business logic produces
random, non-reproducible identifiers that make snapshot testing and assertion
matching difficult.

**Solution:** Depend on the ``IDGenerator`` protocol and inject
``UUIDGenerator`` in production or ``SequentialIDGenerator`` in tests.

Example — production::

    from value_fabric.shared.testability import IDGenerator, UUIDGenerator

    class EventStore:
        def __init__(self, id_gen: IDGenerator = UUIDGenerator()) -> None:
            self._id_gen = id_gen

        def create_event(self, payload: dict) -> dict:
            return dict(id=self._id_gen.generate(), payload=payload)

Example — test::

    from value_fabric.shared.testability import SequentialIDGenerator

    gen = SequentialIDGenerator(prefix="evt")
    store = EventStore(id_gen=gen)
    e1 = store.create_event({"a": 1})
    e2 = store.create_event({"b": 2})
    assert e1["id"] == "evt-1"
    assert e2["id"] == "evt-2"
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import uuid4


@runtime_checkable
class IDGenerator(Protocol):
    """Abstract unique-ID factory."""

    def generate(self) -> str:
        """Return a new unique identifier string."""
        ...


class UUIDGenerator:
    """Production ID generator using ``uuid.uuid4()``."""

    __slots__ = ()

    def generate(self) -> str:
        """Return a new UUID4 hex string."""
        return uuid4().hex


class SequentialIDGenerator:
    """Test ID generator that produces predictable, incrementing identifiers.

    Args:
        prefix: String prepended to each ID (default ``"id"``).
        start: First counter value (default ``1``).
    """

    __slots__ = ("_prefix", "_counter")

    def __init__(self, prefix: str = "id", start: int = 1) -> None:
        self._prefix = prefix
        self._counter = start

    def generate(self) -> str:
        """Return ``"{prefix}-{n}"`` and increment the counter."""
        current = self._counter
        self._counter += 1
        return f"{self._prefix}-{current}"
