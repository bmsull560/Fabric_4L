"""Shared API dependencies for Layer 2 routes."""

try:
    from shared.identity.context import RequestContext
    from shared.identity.dependencies import require_authenticated
except ImportError:
    RequestContext = None  # type: ignore[assignment,misc]

    async def require_authenticated():  # type: ignore[misc]
        """Stub that raises when shared.identity is not installed."""
        raise RuntimeError(
            "shared.identity package is required for Layer2 authentication. "
            "Install the shared package or set up the Python path correctly."
        )

__all__ = ["RequestContext", "require_authenticated"]
