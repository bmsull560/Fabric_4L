"""Cross-layer interface protocols for dependency injection.

These ``Protocol`` definitions formalize the implicit interfaces that exist
between layers.  Depending on a protocol rather than a concrete class:

* Allows unit tests to provide lightweight fakes.
* Decouples layers so they can evolve independently.
* Makes circular import problems impossible — protocols live in ``shared``.

Usage::

    from shared.testability import HTTPClientProtocol

    class Layer3Client:
        def __init__(self, http: HTTPClientProtocol) -> None:
            self._http = http

        async def get_entity(self, entity_id: str) -> dict:
            resp = await self._http.get(f"/entities/{entity_id}")
            return resp
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


# ─── HTTP Client ──────────────────────────────────────────────────────────


@runtime_checkable
class HTTPClientProtocol(Protocol):
    """Minimal async HTTP client interface (mirrors httpx.AsyncClient subset).

    Implement this protocol with ``httpx.AsyncClient`` in production and a
    simple dict-returning stub in tests.
    """

    async def get(self, url: str, **kwargs: Any) -> Any:
        """Send an HTTP GET request."""
        ...

    async def post(self, url: str, **kwargs: Any) -> Any:
        """Send an HTTP POST request."""
        ...

    async def put(self, url: str, **kwargs: Any) -> Any:
        """Send an HTTP PUT request."""
        ...

    async def delete(self, url: str, **kwargs: Any) -> Any:
        """Send an HTTP DELETE request."""
        ...


# ─── Cache Backend ────────────────────────────────────────────────────────


@runtime_checkable
class CacheBackendProtocol(Protocol):
    """Minimal async cache interface.

    Both ``MemoryCache`` (Layer 3) and ``RedisCacheStore`` satisfy this
    protocol.  Tests can supply a simple dict-backed fake.
    """

    async def get(self, key: str) -> Any | None:
        """Retrieve a cached value by key, or ``None`` if missing/expired."""
        ...

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        tags: set[str] | None = None,
    ) -> bool:
        """Store a value under *key*.  Returns ``True`` on success."""
        ...

    async def delete(self, key: str) -> bool:
        """Remove the entry for *key*.  Returns ``True`` if it existed."""
        ...
