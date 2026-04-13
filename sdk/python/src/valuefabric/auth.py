"""Authentication helpers for the Value Fabric SDK."""

from __future__ import annotations

from typing import Callable


class APIKeyAuth:
    """Auth handler that injects an ``X-API-Key`` header."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def __call__(self, request: object) -> object:
        request.headers["X-API-Key"] = self.api_key  # type: ignore[attr-defined]
        return request


class JWTAuth:
    """Auth handler that injects an ``Authorization: Bearer`` header."""

    def __init__(self, token: str) -> None:
        self.token = token

    def __call__(self, request: object) -> object:
        request.headers["Authorization"] = f"Bearer {self.token}"  # type: ignore[attr-defined]
        return request


Auth = Callable[[object], object]
