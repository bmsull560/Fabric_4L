"""Injectable clock abstraction for deterministic time in production and tests.

**Problem:** Calling ``datetime.now()`` or ``time.time()`` directly inside
business logic creates hidden, non-deterministic dependencies that make unit
tests flaky, time-zone-sensitive, and impossible to fast-forward.

**Solution:** Depend on the ``Clock`` protocol and inject ``SystemClock`` in
production or ``FixedClock`` / ``SteppingClock`` in tests.

Example — production wiring::

    from shared.testability import Clock, SystemClock

    class AuditLogger:
        def __init__(self, clock: Clock = SystemClock()) -> None:
            self._clock = clock

        def log(self, action: str) -> dict:
            return {"action": action, "timestamp": self._clock.now()}

Example — test with frozen time::

    from shared.testability import FixedClock

    frozen = FixedClock(datetime(2025, 1, 1, tzinfo=timezone.utc))
    logger = AuditLogger(clock=frozen)
    event = logger.log("login")
    assert event["timestamp"] == datetime(2025, 1, 1, tzinfo=timezone.utc)

Example — test with advancing time::

    clock = FixedClock()
    t0 = clock.monotonic()
    clock.advance(5.0)
    assert clock.monotonic() - t0 == 5.0
"""

from __future__ import annotations

import time as _time
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Abstract wall-clock that can be replaced in tests.

    All implementations **must** return timezone-aware UTC datetimes from
    ``now()`` and monotonically non-decreasing values from ``monotonic()``.
    """

    def now(self) -> datetime:
        """Return the current UTC datetime (timezone-aware)."""
        ...

    def monotonic(self) -> float:
        """Return a monotonic timestamp in seconds (like ``time.monotonic()``)."""
        ...


class SystemClock:
    """Production clock backed by the OS wall-clock.

    This is the default used when no clock is injected.
    """

    __slots__ = ()

    def now(self) -> datetime:
        """Return ``datetime.now(timezone.utc)``."""
        return datetime.now(timezone.utc)

    def monotonic(self) -> float:
        """Return ``time.monotonic()``."""
        return _time.monotonic()


class FixedClock:
    """Test clock that returns a controllable, deterministic time.

    Starts at ``initial`` (defaults to ``2025-01-01T00:00:00Z``) and only
    advances when ``advance()`` is called explicitly.

    Attributes:
        _current: The frozen datetime.
        _mono: The frozen monotonic counter.
    """

    __slots__ = ("_current", "_mono")

    _EPOCH = datetime(2025, 1, 1, tzinfo=timezone.utc)

    def __init__(
        self,
        initial: datetime | None = None,
        mono_start: float = 0.0,
    ) -> None:
        self._current = initial or self._EPOCH
        if self._current.tzinfo is None:
            self._current = self._current.replace(tzinfo=timezone.utc)
        self._mono = mono_start

    def now(self) -> datetime:
        """Return the frozen datetime."""
        return self._current

    def monotonic(self) -> float:
        """Return the frozen monotonic counter."""
        return self._mono

    def advance(self, seconds: float) -> None:
        """Advance both ``now()`` and ``monotonic()`` by *seconds*.

        Args:
            seconds: Number of seconds to advance.  Must be non-negative.

        Raises:
            ValueError: If *seconds* is negative.
        """
        if seconds < 0:
            raise ValueError("Cannot advance clock by a negative amount")
        from datetime import timedelta

        self._current += timedelta(seconds=seconds)
        self._mono += seconds

    def set(self, dt: datetime) -> None:
        """Jump ``now()`` directly to *dt* (monotonic is unchanged).

        Args:
            dt: New datetime value.  Will be made tz-aware (UTC) if naive.
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        self._current = dt
