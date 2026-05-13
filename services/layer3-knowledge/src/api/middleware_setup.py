"""Layer 3 middleware setup utilities."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from value_fabric.layer3.config import get_settings
from value_fabric.layer3.logging_config import get_logger
from value_fabric.shared.fastapi_framework import (
    add_governance_middleware,
    add_request_id_middleware,
    add_security_validation_middleware,
    resolve_cors_policy,
)

from api.rate_limiter import add_rate_limiting
from api.versioning import VersionMiddleware, get_version_compatibility

logger = get_logger(__name__)


def configure_foundation_middleware(app: FastAPI, *, shared_error_handling_available: bool) -> Any:
    cors_policy = resolve_cors_policy()
    app.add_middleware(CORSMiddleware, **cors_policy.as_kwargs())

    if shared_error_handling_available:
        add_request_id_middleware(app)
        logger.info("RequestIDMiddleware enabled for trace correlation")

    security_config = add_security_validation_middleware(
        app,
        skip_validation_paths={"/health", "/metrics"},
        strict_mode=True,
    )

    add_governance_middleware(app)

    try:
        settings: Any | None = get_settings()
    except Exception:
        logger.warning("Falling back to default rate-limit settings during import")
        settings = None

    add_rate_limiting(
        app,
        requests_per_minute=settings.rate_limit_requests_per_minute if settings else 100,
        burst_size=settings.rate_limit_burst_size if settings else 200,
        enabled=settings.rate_limit_enabled if settings else False,
    )

    app.middleware("http")(VersionMiddleware(get_version_compatibility()))
    return security_config
