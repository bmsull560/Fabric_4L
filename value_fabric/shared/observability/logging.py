"""Shared structured logging compatibility helpers."""

from __future__ import annotations

import structlog


def get_logger(name: str | None = None):
    """Return a structlog logger using the repository-standard logging facade."""
    return structlog.get_logger(name) if name else structlog.get_logger()
