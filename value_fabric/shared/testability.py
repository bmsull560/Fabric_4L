"""Deterministic testability helpers shared by compatibility models."""

from __future__ import annotations

import time as _time
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable
from uuid import uuid4


@runtime_checkable
class Clock(Protocol):
    """Protocol for injectable clocks used by security-sensitive models."""

    def now(self) -> datetime:
        """Return the current timezone-aware timestamp."""
        ...

    def monotonic(self) -> float:
        """Return a monotonic timestamp in seconds."""
        ...


class SystemClock:
    """System clock implementation returning UTC-aware datetimes."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def monotonic(self) -> float:
        return _time.monotonic()


class FixedClock:
    """Deterministic test clock used by shared compatibility modules."""

    def __init__(self, initial: datetime | None = None, mono_start: float = 0.0) -> None:
        self._current = initial or datetime(2025, 1, 1, tzinfo=timezone.utc)
        if self._current.tzinfo is None:
            self._current = self._current.replace(tzinfo=timezone.utc)
        self._mono = mono_start

    def now(self) -> datetime:
        return self._current

    def monotonic(self) -> float:
        return self._mono


@runtime_checkable
class IDGenerator(Protocol):
    """Abstract unique-ID factory."""

    def generate(self) -> str:
        """Return a new unique identifier string."""
        ...


class UUIDGenerator:
    """Production ID generator using UUID4 hex strings."""

    def generate(self) -> str:
        return uuid4().hex


class SequentialIDGenerator:
    """Predictable, incrementing ID generator for deterministic tests."""

    def __init__(self, prefix: str = "id", start: int = 1) -> None:
        self._prefix = prefix
        self._counter = start

    def generate(self) -> str:
        current = self._counter
        self._counter += 1
        return f"{self._prefix}-{current}"


__all__ = [
    "Clock",
    "FixedClock",
    "SystemClock",
    "IDGenerator",
    "SequentialIDGenerator",
    "UUIDGenerator",
]
