"""Shared protocol contracts for identity-bound providers and security hooks."""

from __future__ import annotations

from typing import Any, Awaitable, Protocol, runtime_checkable


class ProviderUnavailableError(RuntimeError):
    """Raised when an optional runtime provider is required but unavailable."""

    def __init__(self, *, provider: str, code: str, detail: str) -> None:
        self.provider = provider
        self.code = code
        self.detail = detail
        super().__init__(f"[{code}] {provider}: {detail}")

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "provider": self.provider, "detail": self.detail}


@runtime_checkable
class RequestContextProvider(Protocol):
    """Callable contract for resolving the active request context."""

    def __call__(self, request: Any | None = None) -> Awaitable[Any | None] | Any | None:
        ...


@runtime_checkable
class MetricsAccessHook(Protocol):
    """Callable contract for metrics endpoint access checks."""

    def __call__(self, request: Any) -> bool:
        ...

