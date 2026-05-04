"""Deterministic testability helpers shared by compatibility models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol


class Clock(Protocol):
    """Protocol for injectable clocks used by security-sensitive models."""

    def now(self) -> datetime:
        """Return the current timezone-aware timestamp."""
        ...


class SystemClock:
    """System clock implementation returning UTC-aware datetimes."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


__all__ = ["Clock", "SystemClock"]
