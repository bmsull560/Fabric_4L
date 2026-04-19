"""Security configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field


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
