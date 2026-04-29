"""Testability primitives for dependency injection and deterministic testing.

This package provides injectable abstractions that replace hard-coded calls to
``datetime.now()``, ``uuid.uuid4()``, ``time.time()`` and similar non-deterministic
functions.  Using these protocols throughout the codebase makes every downstream
testing decision easier:

* **Clock** – injectable wall-clock; swap with ``FixedClock`` in tests.
* **IDGenerator** – injectable unique-ID factory; swap with ``SequentialIDGenerator``.
* **Protocols** – ``HTTPClientProtocol``, ``CacheBackendProtocol`` for cross-layer DI.

Quick-start
-----------

Production code::

    from shared.testability import Clock, SystemClock

    class MyService:
        def __init__(self, clock: Clock = SystemClock()) -> None:
            self._clock = clock

        def record(self) -> dict:
            return dict(ts=self._clock.now().isoformat())

Test code::

    from shared.testability import FixedClock

    clock = FixedClock()
    svc = MyService(clock=clock)
    result = svc.record()
    assert result["ts"] == clock.now().isoformat()
"""

from .clock import Clock, FixedClock, SystemClock
from .id_generator import IDGenerator, SequentialIDGenerator, UUIDGenerator
from .interfaces import CacheBackendProtocol, HTTPClientProtocol

__all__ = [
    # Clock
    "Clock",
    "FixedClock",
    "SystemClock",
    # ID generation
    "IDGenerator",
    "SequentialIDGenerator",
    "UUIDGenerator",
    # Cross-layer protocols
    "CacheBackendProtocol",
    "HTTPClientProtocol",
]
