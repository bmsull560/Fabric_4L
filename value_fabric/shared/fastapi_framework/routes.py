"""Small route registration helpers for FastAPI services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, FastAPI


@dataclass(frozen=True)
class RouterMount:
    router: APIRouter
    prefix: str = ""
    kwargs: dict[str, Any] | None = None


def include_router_mounts(app: FastAPI, mounts: list[RouterMount]) -> None:
    for mount in mounts:
        app.include_router(mount.router, prefix=mount.prefix, **(mount.kwargs or {}))
