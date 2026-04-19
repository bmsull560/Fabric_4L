"""Security middleware for FastAPI applications."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .config import SecurityConfig


def add_security_middleware(
    app: FastAPI,
    config: SecurityConfig | None = None,
) -> None:
    """Add security middleware to FastAPI app.

    Args:
        app: FastAPI application
        config: Security configuration
    """
    config = config or SecurityConfig()

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_methods=config.cors_methods,
        allow_headers=config.cors_headers,
        allow_credentials=True,
        max_age=600,
    )

    # Add trusted host middleware (if not allowing all)
    if "*" not in config.cors_origins:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=config.cors_origins,
        )

    # Add security headers middleware
    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)

        if config.enable_hsts:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        if config.enable_xframe:
            response.headers["X-Frame-Options"] = "DENY"

        if config.enable_xss_protection:
            response.headers["X-XSS-Protection"] = "1; mode=block"

        if config.enable_content_type_options:
            response.headers["X-Content-Type-Options"] = "nosniff"

        if config.enable_referrer_policy:
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if config.content_security_policy:
            response.headers["Content-Security-Policy"] = config.content_security_policy

        return response
