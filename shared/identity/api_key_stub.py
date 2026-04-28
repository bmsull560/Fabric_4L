"""API key resolver stubs for layers without database access.

Provides explicit rejection of API key authentication in layers
where API key resolution is not wired to a database.
"""

import logging

logger = logging.getLogger(__name__)

# Key preview lengths for logging (security: don't log full keys)
_KEY_PREVIEW_LONG = 8
_KEY_PREVIEW_SHORT = 4
_KEY_PREVIEW_MINIMUM = 3  # Below this, show placeholder only


def reject_api_key_unsupported(raw_key: str) -> None:
    """Reject API key authentication with clear logging.

    This resolver is used in layers where API key authentication is not
    supported (no database access). It logs a warning and returns None,
    which causes the middleware to reject the request with 401.

    Args:
        raw_key: The API key presented by the client

    Returns:
        None (always rejects)
    """
    # Guard against non-string input (defense in depth)
    if not isinstance(raw_key, str):
        key_preview = "***"
    elif len(raw_key) >= _KEY_PREVIEW_LONG:
        key_preview = raw_key[:_KEY_PREVIEW_LONG]
    elif len(raw_key) >= _KEY_PREVIEW_SHORT:
        key_preview = raw_key[:_KEY_PREVIEW_SHORT]
    else:
        key_preview = "***"

    logger.warning(
        "API key '%s...' rejected: not supported in this layer. "
        "Use JWT Bearer tokens instead.",
        key_preview
    )
    return None


def reject_api_key_with_error(raw_key: str) -> None:
    """Reject API key authentication with explicit error.

    Use this in layers where API keys are explicitly disabled.

    Args:
        raw_key: The API key presented by the client

    Returns:
        None (always rejects)
    """
    # Guard against non-string input (defense in depth)
    if not isinstance(raw_key, str):
        key_preview = "***"
    elif len(raw_key) >= _KEY_PREVIEW_LONG:
        key_preview = raw_key[:_KEY_PREVIEW_LONG]
    elif len(raw_key) >= _KEY_PREVIEW_SHORT:
        key_preview = raw_key[:_KEY_PREVIEW_SHORT]
    else:
        key_preview = "***"
    logger.error(
        "API key '%s...' rejected: API key authentication is disabled in this layer. "
        "Use JWT Bearer tokens or configure API key support.",
        key_preview
    )
    return None
