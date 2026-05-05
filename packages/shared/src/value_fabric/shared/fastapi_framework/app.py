"""Reusable FastAPI application assembly helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI

from value_fabric.shared.error_handling import register_exception_handlers

from .middleware import CorsPolicy, add_cors_middleware, add_request_id_middleware


def create_fabric_app(
    *,
    service_name: str,
    title: str,
    version: str,
    description: str,
    lifespan: Callable[..., Any] | None = None,
    cors_policy: CorsPolicy | dict[str, Any] | None = None,
    register_default_exception_handlers: bool = True,
    include_request_id_middleware: bool = True,
) -> FastAPI:
    """Create a FastAPI application with Value Fabric defaults.

    This factory centralizes the common bootstrap concerns that are repeated
    across service entrypoints without constraining service-specific startup
    dependencies or router composition.
    """

    app = FastAPI(
        title=title,
        version=version,
        description=description,
        lifespan=lifespan,
    )
    app.state.service_name = service_name

    if cors_policy is not None:
        policy = cors_policy if isinstance(cors_policy, CorsPolicy) else CorsPolicy(**cors_policy)
        add_cors_middleware(app, policy)

    if include_request_id_middleware:
        add_request_id_middleware(app)

    if register_default_exception_handlers:
        register_exception_handlers(app)

    return app