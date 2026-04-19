"""Authentication helpers for the Value Fabric SDK."""

from __future__ import annotations

from collections.abc import Callable

import httpx


class APIKeyAuth:
    """Auth handler that injects an ``X-API-Key`` header."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def __call__(self, request: httpx.Request) -> httpx.Request:
        request.headers["X-API-Key"] = self.api_key
        return request


class JWTAuth:
    """Auth handler that injects an ``Authorization: Bearer`` header."""

    def __init__(self, token: str) -> None:
        self.token = token

    def __call__(self, request: httpx.Request) -> httpx.Request:
        request.headers["Authorization"] = f"Bearer {self.token}"
        return request


Auth = Callable[[httpx.Request], httpx.Request]
