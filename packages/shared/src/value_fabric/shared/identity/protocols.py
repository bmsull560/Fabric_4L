"""Shared identity provider protocols used by Layer service dependencies.

This module keeps Layer-specific dependency wiring independent from concrete
FastAPI dependency implementations while preserving a typed fail-closed error
when a required provider is unavailable.
"""

from __future__ import annotations

from typing import Any, Protocol


class ProviderUnavailableError(RuntimeError):
    """Raised when a required cross-layer provider has not been wired."""

    def __init__(self, *, provider: str, code: str, detail: str) -> None:
        self.provider = provider
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail} ({provider})")


class RequestContextProvider(Protocol):
    """Callable contract for request-context provider dependencies."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Return the current request context or an awaitable resolving to one."""
