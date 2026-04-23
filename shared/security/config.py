"""Security configuration and startup validation."""

from __future__ import annotations

import logging
import os
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SecurityConfig(BaseModel):
    """Security middleware configuration."""

    # CORS
    cors_origins: list[str] = Field(default=["*"], description="Allowed CORS origins")
    cors_methods: list[str] = Field(default=["*"], description="Allowed CORS methods")
    cors_headers: list[str] = Field(default=["*"], description="Allowed CORS headers")
    
    # Security headers
    enable_hsts: bool = Field(default=True, description="Enable HSTS header")
    enable_xframe: bool = Field(default=True, description="Enable X-Frame-Options")
    enable_xss_protection: bool = Field(default=True, description="Enable XSS protection")
    enable_content_type_options: bool = Field(default=True, description="Enable X-Content-Type-Options")
    enable_referrer_policy: bool = Field(default=True, description="Enable Referrer-Policy")
    
    # CSP
    content_security_policy: str | None = Field(
        default="default-src 'self'",
        description="Content-Security-Policy header"
    )
    
    # Request limits
    max_body_size: int = Field(default=10 * 1024 * 1024, description="Max request body size (bytes)")
    max_body_size_bytes: int = Field(default=1_048_576, description="Max body size for validation (bytes)")
    
    # Validation settings
    skip_validation_paths: frozenset[str] = Field(default=frozenset(), description="Paths to skip validation")
    strict_mode: bool = Field(default=True, description="Strict validation mode")
    validate_json_bodies: bool = Field(default=True, description="Validate JSON request bodies")
    
    class Config:
        extra = "allow"


# ═══════════════════════════════════════════════════════════════════════════
# Startup Validation Functions
# ═══════════════════════════════════════════════════════════════════════════


def is_production() -> bool:
    """Check if running in production environment."""
    return os.getenv("ENVIRONMENT", "").lower() == "production"


def is_development() -> bool:
    """Check if running in development environment."""
    return os.getenv("ENVIRONMENT", "").lower() == "development"


def validate_cors_config() -> None:
    """Validate CORS configuration for production safety.
    
    Raises:
        ValueError: If CORS is misconfigured in production
    """
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    
    if is_production():
        # Wildcard CORS is not allowed in production
        if cors_origins == "*":
            raise ValueError(
                "CORS wildcard (*) is not allowed in production. "
                "Specify explicit HTTPS origins."
            )
        
        # HTTP origins are not allowed in production
        if "http://" in cors_origins.lower():
            raise ValueError(
                "HTTP CORS origins are not allowed in production. "
                "Use HTTPS only."
            )
    elif is_development() and cors_origins == "*":
        logger.warning(
            "CORS is set to wildcard (*) in development mode. "
            "This is insecure and should not be used in production."
        )


def validate_database_config() -> None:
    """Validate database configuration for production safety.
    
    Raises:
        ValueError: If database is misconfigured in production
    """
    database_url = os.getenv("DATABASE_URL", "")
    
    if not database_url:
        raise ValueError("DATABASE_URL is required")
    
    if is_production():
        # SQLite is not allowed in production
        if database_url.startswith("sqlite"):
            raise ValueError(
                "SQLite is not supported in production. "
                "Use PostgreSQL with RLS for multi-tenant isolation."
            )
        
        # Warn if connection is not encrypted
        if "sslmode" not in database_url.lower():
            logger.warning(
                "DATABASE_URL does not specify sslmode. "
                "Unencrypted database connections expose tenant data in transit. "
                "Add ?sslmode=require to the connection string."
            )


def validate_environment_config() -> None:
    """Validate environment configuration for conflicts.
    
    Raises:
        ValueError: If environment variables conflict
    """
    if is_production() and os.getenv("DEBUG", "").lower() == "true":
        raise ValueError(
            "DEBUG mode cannot be enabled in production. "
            "Set DEBUG=false or remove the variable."
        )


def validate_all_controls() -> None:
    """Validate that not all security controls are disabled.
    
    Raises:
        ValueError: If all controls are disabled in production
    """
    if not is_production():
        return
    
    redis_url = os.getenv("REDIS_URL", "")
    audit_sink = os.getenv("AUDIT_SINK_URL", "")
    jwt_secret = os.getenv("JWT_SECRET", "")
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    
    if not redis_url and not audit_sink and not jwt_secret and cors_origins == "*":
        raise ValueError(
            "All security controls are disabled in production. "
            "This indicates a catastrophic misconfiguration."
        )


def get_startup_summary() -> dict[str, Any]:
    """Get startup summary with active control modes.
    
    Returns:
        Dictionary with environment info and control status
    """
    environment = os.getenv("ENVIRONMENT", "development")
    redis_url = os.getenv("REDIS_URL", "")
    audit_sink = os.getenv("AUDIT_SINK_URL", "")
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    
    summary = {
        "environment": environment,
        "redis_enabled": bool(redis_url),
        "audit_enabled": bool(audit_sink),
        "cors_mode": "restricted" if cors_origins != "*" else "permissive",
        "jwt_validation": "strict" if is_production() else "relaxed",
        "warnings": [],
        "degraded_controls": [],
    }
    
    # Check for degraded controls
    if not redis_url:
        summary["degraded_controls"].extend(["redis", "rate_limiting"])
        if not is_development():
            summary["warnings"].append("Redis is not configured - rate limiting disabled")
    
    if not audit_sink:
        summary["degraded_controls"].append("audit")
        if not is_development():
            summary["warnings"].append("Audit sink is not configured - audit events will be lost")
    
    if cors_origins == "*":
        summary["degraded_controls"].append("cors")
        if not is_development():
            summary["warnings"].append("CORS is set to wildcard - security risk")
    
    if summary["warnings"]:
        summary["warnings"].insert(0, "WARNING: Some security controls are degraded")
    
    return summary
