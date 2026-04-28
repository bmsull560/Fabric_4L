"""API key resolver stubs for layers without database access.

P0-5 FIX: Provides explicit rejection of API key authentication in layers
where API key resolution is not wired to a database.
"""

import logging

logger = logging.getLogger(__name__)


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
    logger.warning(
        "API key authentication rejected: not supported in this layer. "
        "Use JWT Bearer tokens instead."
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
    logger.error(
        "API key '%s...' rejected: API key authentication is disabled in this layer. "
        "Use JWT Bearer tokens or configure API key support.",
        raw_key[:8] if len(raw_key) > 8 else raw_key[:4]
    )
    return None
