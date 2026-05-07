"""Shared API dependencies for Layer 2 routes."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from value_fabric.shared.identity.context import RequestContext

try:
    from value_fabric.shared.identity.context import RequestContext
    from value_fabric.shared.identity.dependencies import require_authenticated
except ImportError:
    RequestContext = Any

    async def require_authenticated() -> Any:  # type: ignore[no-redef]
        """Stub that raises when shared.identity is not installed."""
        raise RuntimeError(
            "shared.identity package is required for Layer2 authentication. "
            "Install the shared package or set up the Python path correctly."
        )


__all__ = ["RequestContext", "require_authenticated"]
