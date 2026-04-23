"""Layer 4 Agents Service Configuration.

P0-29: Pydantic-settings with validation for required secrets.
Fails fast on startup if required configuration is missing or invalid.
"""

import secrets

try:
    from shared.secrets import load_infisical_secrets
    load_infisical_secrets()
except ImportError:
    pass  # shared package not available; env vars used directly

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Layer 4 Agents service settings with strict validation.

    All secrets must be provided via environment variables.
    Fails fast on startup if required configuration is missing.
    """

    model_config = SettingsConfigDict(
        env_prefix="LAYER4_",
        case_sensitive=False,
        extra="ignore",  # Allow extra env vars without error
    )

    # ==========================================================================
    # Application
    # ==========================================================================
    app_name: str = Field(default="layer4-agents", description="Service name")
    app_version: str = Field(default="1.0.0", description="Service version")
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    # ==========================================================================
    # Security (P0-29: Required secrets with minimum length validation)
    # ==========================================================================
    jwt_secret: str = Field(
        default="",
        description="JWT signing secret (min 32 characters required)"
    )
    api_key_hmac_secret: str = Field(
        default="",
        description="API key HMAC secret (min 32 characters required)"
    )

    # ==========================================================================
    # Database
    # ==========================================================================
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/layer4_agents",
        description="PostgreSQL connection URL"
    )
    database_pool_size: int = Field(default=10, description="Connection pool size")
    database_max_overflow: int = Field(default=20, description="Max pool overflow")

    # ==========================================================================
    # Redis
    # ==========================================================================
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    redis_pool_size: int = Field(default=10, description="Redis connection pool size")

    # ==========================================================================
    # External Services
    # ==========================================================================
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key for LLM operations"
    )
    openai_model: str = Field(default="gpt-4", description="Default OpenAI model")
    openai_timeout_seconds: int = Field(default=60, description="OpenAI API timeout")

    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")
    anthropic_model: str = Field(default="claude-3-sonnet-20240229", description="Default Anthropic model")
    anthropic_timeout_seconds: int = Field(default=60, description="Anthropic API timeout")

    # ==========================================================================
    # Layer Integration
    # ==========================================================================
    layer1_api_url: str = Field(
        default="http://layer1-ingestion:8000",
        description="Layer 1 Ingestion API URL"
    )
    layer2_api_url: str = Field(
        default="http://layer2-extraction:8000",
        description="Layer 2 Extraction API URL"
    )
    layer3_api_url: str = Field(
        default="http://layer3-knowledge:8001",
        description="Layer 3 Knowledge Graph API URL"
    )
    layer5_api_url: str = Field(
        default="http://layer5-ground-truth:8000",
        description="Layer 5 Ground Truth API URL"
    )

    # ==========================================================================
    # Workflow Engine
    # ==========================================================================
    max_concurrent_workflows: int = Field(
        default=10,
        description="Maximum concurrent workflows per replica (P1-42)"
    )
    workflow_timeout_seconds: int = Field(
        default=1800,  # 30 minutes (P1-25)
        description="Global workflow timeout"
    )
    workflow_state_ttl_seconds: int = Field(
        default=86400,  # 24 hours
        description="Workflow state TTL in Redis"
    )

    # ==========================================================================
    # Rate Limiting (P1-15)
    # ==========================================================================
    rate_limit_requests_per_minute: int = Field(
        default=100,
        description="Per-tenant rate limit (requests per minute)"
    )
    rate_limit_burst_size: int = Field(
        default=20,
        description="Rate limit burst size"
    )

    # ==========================================================================
    # Circuit Breaker (P1-18)
    # ==========================================================================
    circuit_breaker_failure_threshold: int = Field(
        default=5,
        description="Failures before opening circuit"
    )
    circuit_breaker_recovery_timeout_seconds: int = Field(
        default=60,
        description="Seconds before attempting recovery"
    )
    circuit_breaker_half_open_max_calls: int = Field(
        default=3,
        description="Max test calls in half-open state"
    )

    # ==========================================================================
    # CORS (P0-20)
    # ==========================================================================
    cors_origins: str = Field(
        default="",
        description="Comma-separated list of allowed CORS origins"
    )

    # ==========================================================================
    # Observability
    # ==========================================================================
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format: json or text")
    otel_exporter_endpoint: str | None = Field(
        default=None,
        description="OpenTelemetry exporter endpoint (P1-29)"
    )
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, description="Metrics server port")

    # ==========================================================================
    # Feature Flags (P2-05)
    # ==========================================================================
    feature_flag_provider: str = Field(
        default="redis",
        description="Feature flag backend: redis, config, or unleash"
    )

    # ==========================================================================
    # Billing (Stripe Integration)
    # ==========================================================================
    billing_enabled: bool = Field(
        default=False,
        description="Enable billing features and Stripe integration"
    )
    stripe_secret_key: str | None = Field(
        default=None,
        description="Stripe API secret key (sk_...)"
    )
    stripe_webhook_secret: str | None = Field(
        default=None,
        description="Stripe webhook endpoint secret (whsec_...)"
    )
    stripe_price_pro: str | None = Field(
        default=None,
        description="Stripe Price ID for Pro plan"
    )
    stripe_price_enterprise: str | None = Field(
        default=None,
        description="Stripe Price ID for Enterprise plan"
    )

    # ==========================================================================
    # Export Object Storage (S3/MinIO)
    # ==========================================================================
    export_storage_endpoint: str | None = Field(
        default=None,
        description="S3/MinIO endpoint URL for export package uploads"
    )
    export_storage_region: str = Field(
        default="us-east-1",
        description="S3 region for export object storage"
    )
    export_storage_bucket: str = Field(
        default="value-fabric-exports",
        description="Bucket for exported case artifacts"
    )
    export_storage_access_key: str = Field(
        default="",
        description="Access key for S3/MinIO export uploads"
    )
    export_storage_secret_key: str = Field(
        default="",
        description="Secret key for S3/MinIO export uploads"
    )
    export_storage_use_ssl: bool = Field(
        default=True,
        description="Whether to use TLS for object storage endpoint"
    )
    export_signed_url_ttl_seconds: int = Field(
        default=900,
        description="Signed URL TTL for export downloads in seconds"
    )

    @property
    def is_billing_configured(self) -> bool:
        """Check if Stripe billing is properly configured."""
        return self.billing_enabled and self.stripe_secret_key is not None

    # ==========================================================================
    # Validators (P0-29: Fail fast on invalid config)
    # ==========================================================================

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Normalize environment name."""
        v = v.lower()
        allowed = {"development", "staging", "production", "test"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}, got '{v}'")
        return v

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str, info: ValidationInfo) -> str:
        """Validate JWT secret meets minimum requirements."""
        environment = info.data.get("environment", "development")

        if environment == "production":
            if not v:
                raise ValueError(
                    "FATAL: JWT_SECRET is required in production. "
                    "Set a strong secret (min 32 characters)."
                )
            if len(v) < 32:
                raise ValueError(
                    f"FATAL: JWT_SECRET must be at least 32 characters in production, "
                    f"got {len(v)} characters."
                )

        # In non-production, generate a random secret if not provided
        if not v:
            if environment == "development":
                import warnings
                warnings.warn(
                    "JWT_SECRET not set in development. Using random secret (sessions will not persist across restarts).",
                    RuntimeWarning,
                    stacklevel=2,
                )
                return secrets.token_urlsafe(32)
            else:
                raise ValueError(f"JWT_SECRET is required in {environment} environment")

        if len(v) < 32:
            raise ValueError(f"JWT_SECRET must be at least 32 characters, got {len(v)}")

        return v

    @field_validator("api_key_hmac_secret")
    @classmethod
    def validate_api_key_hmac_secret(cls, v: str, info: ValidationInfo) -> str:
        """Validate API key HMAC secret meets minimum requirements."""
        environment = info.data.get("environment", "development")

        if environment == "production":
            if not v:
                raise ValueError(
                    "FATAL: API_KEY_HMAC_SECRET is required in production. "
                    "Set a strong secret (min 32 characters)."
                )
            if len(v) < 32:
                raise ValueError(
                    f"FATAL: API_KEY_HMAC_SECRET must be at least 32 characters in production, "
                    f"got {len(v)} characters."
                )

        # In non-production, generate a random secret if not provided
        if not v:
            if environment == "development":
                import warnings
                warnings.warn(
                    "API_KEY_HMAC_SECRET not set in development. Using random secret (API keys will not persist across restarts).",
                    RuntimeWarning,
                    stacklevel=2,
                )
                return secrets.token_urlsafe(32)
            else:
                raise ValueError(f"API_KEY_HMAC_SECRET is required in {environment} environment")

        if len(v) < 32:
            raise ValueError(f"API_KEY_HMAC_SECRET must be at least 32 characters, got {len(v)}")

        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str, info: ValidationInfo) -> str:
        """Validate database URL in production."""
        environment = info.data.get("environment", "development")

        if environment == "production":
            # Check for default/insecure credentials
            insecure_patterns = [
                ":postgres@",
                ":password@",
                ":admin@",
                ":secret@",
            ]
            for pattern in insecure_patterns:
                if pattern in v.lower():
                    raise ValueError(
                        f"FATAL: DATABASE_URL contains insecure default credentials '{pattern}'. "
                        "Use strong, unique passwords in production."
                    )

        return v

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: str, info: ValidationInfo) -> str:
        """Validate CORS origins in production (P0-20)."""
        environment = info.data.get("environment", "development")

        if environment == "production":
            if not v or v.strip() == "":
                raise ValueError(
                    "FATAL: CORS_ORIGINS is required in production. "
                    "Set to comma-separated list of allowed origins (e.g., 'https://app.valuefabric.io')."
                )

            origins = [o.strip() for o in v.split(",") if o.strip()]

            if "*" in origins:
                raise ValueError(
                    "FATAL: CORS_ORIGINS cannot contain '*' in production. "
                    "Specify exact allowed origins."
                )

            for origin in origins:
                if not origin.startswith(("https://", "http://")):
                    raise ValueError(
                        f"FATAL: CORS origin '{origin}' must start with http:// or https://"
                    )

        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str | None, info: ValidationInfo) -> str | None:
        """Validate OpenAI API key format if provided."""
        if v and not v.startswith(("sk-", "sk-proj-")):
            raise ValueError(
                "OPENAI_API_KEY appears invalid. Should start with 'sk-' or 'sk-proj-'."
            )
        return v

    # ==========================================================================
    # Computed Properties
    # ==========================================================================

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        if not self.cors_origins:
            return ["*"] if self.is_development else []
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def database_url_safe(self) -> str:
        """Get database URL with password masked for logging."""
        url = self.database_url
        # Simple masking - replace password with ***
        if "://" in url:
            parts = url.split("@")
            if len(parts) == 2:
                auth_part = parts[0].split(":")
                if len(auth_part) >= 3:
                    # postgresql://user:pass@host -> postgresql://user:***@host
                    return f"{auth_part[0]}:***@{parts[1]}"
        return url


# ==========================================================================
# Global Settings Instance
# ==========================================================================

# P0-29: This will fail fast on startup if required config is missing
settings = Settings()
