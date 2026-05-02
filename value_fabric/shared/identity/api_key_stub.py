"""Stub for API-key resolver when API-key authentication is not supported.

Layers that do not implement API-key lookup can import ``reject_api_key_unsupported``
and pass it to ``GovernanceMiddleware`` to keep API-key auth disabled.
"""

__all__ = ["reject_api_key_unsupported"]


async def reject_api_key_unsupported(raw_key: str) -> dict | None:
    """Always returns ``None`` — API-key authentication is not supported.

    Args:
        raw_key: The raw API key from the ``X-API-Key`` header.

    Returns:
        ``None`` unconditionally.
    """
    return None
