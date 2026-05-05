"""Reusable FastAPI middleware assembly helpers.

These helpers keep service entrypoints focused on composition while preserving
the established middleware ordering choices in each layer.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Iterable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from value_fabric.shared.error_handling import RequestIDMiddleware
from value_fabric.shared.identity.api_key_stub import reject_api_key_unsupported
from value_fabric.shared.identity.middleware import GovernanceMiddleware
from value_fabric.shared.security import SecurityConfig, add_security_middleware


@dataclass(frozen=True)
class CorsPolicy:
    """Normalized CORS settings for service entrypoints."""

    allow_origins: list[str]
    allow_credentials: bool
    allow_methods: list[str]
    allow_headers: list[str]

    def as_kwargs(self) -> dict[str, Any]:
        return {
            "allow_origins": self.allow_origins,
            "allow_credentials": self.allow_credentials,
            "allow_methods": self.allow_methods,
            "allow_headers": self.allow_headers,
        }


def resolve_cors_policy(
    *,
    environment: str | None = None,
    origins_env: str | None = None,
    production_environments: Iterable[str] = ("production",),
) -> CorsPolicy:
    """Resolve a safe CORS policy from environment variables."""

    environment_name = environment or os.getenv("ENVIRONMENT", "development")
    raw_origins = origins_env if origins_env is not None else os.getenv("CORS_ORIGINS", "")
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

    if environment_name in set(production_environments) and not origins:
        raise RuntimeError(
            "FATAL: CORS_ORIGINS environment variable must be set in production. "
            "Use 'https://yourdomain.com' or comma-separated list of allowed origins."
        )

    allow_origins = origins or ["*"]
    return CorsPolicy(
        allow_origins=allow_origins,
        allow_credentials="*" not in allow_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def add_request_id_middleware(app: FastAPI, *, enabled: bool = True) -> None:
    if enabled:
        app.add_middleware(RequestIDMiddleware)


def add_security_validation_middleware(
    app: FastAPI,
    *,
    skip_validation_paths: Iterable[str],
    strict_mode: bool = True,
) -> SecurityConfig:
    config = SecurityConfig.from_env(
        skip_validation_paths=frozenset(skip_validation_paths),
        strict_mode=strict_mode,
    )
    add_security_middleware(app, config=config)
    return config


def add_governance_middleware(app: FastAPI, *, rate_limiter: Any | None = None) -> None:
    app.add_middleware(
        GovernanceMiddleware,
        api_key_resolver=reject_api_key_unsupported,
        rate_limiter=rate_limiter,
    )


def add_cors_middleware(app: FastAPI, policy: CorsPolicy) -> None:
    app.add_middleware(CORSMiddleware, **policy.as_kwargs())
