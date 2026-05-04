"""Shared API-key rejection helpers for JWT-only layers.

Layers that do not implement API-key lookup can import these helpers and pass
them to ``GovernanceMiddleware`` to keep API-key auth disabled.  The helpers are
intentionally synchronous and always return ``None`` so unsupported API-key
authentication fails closed without introducing a database lookup path.
"""

from __future__ import annotations

import logging
from typing import Any

__all__ = ["reject_api_key_unsupported", "reject_api_key_with_error"]

_LOGGER = logging.getLogger(__name__)
_KEY_PREVIEW_LENGTH = 8
_KEY_PREVIEW_SHORT = 4


def _key_preview(raw_key: Any) -> str:
    """Return an audit-safe preview for an API key-like value."""

    if not isinstance(raw_key, str) or len(raw_key) < _KEY_PREVIEW_SHORT:
        return "***"
    return f"{raw_key[:_KEY_PREVIEW_LENGTH]}..."


def reject_api_key_unsupported(raw_key: str) -> dict | None:
    """Reject API-key authentication for JWT-only layers.

    The key is never used for authentication and only a short redacted preview is
    logged for operational diagnostics.
    """

    _LOGGER.warning(
        "API key authentication rejected for key preview %s. Use JWT Bearer tokens instead.",
        _key_preview(raw_key),
    )
    return None


def reject_api_key_with_error(raw_key: str) -> dict | None:
    """Reject API-key authentication with an error-level operational log."""

    _LOGGER.error(
        "API key authentication rejected for key preview %s; API keys are disabled in this layer.",
        _key_preview(raw_key),
    )
    return None
