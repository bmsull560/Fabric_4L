"""Configuration for Layer 5 Ground Truth Layer."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    from shared.secrets import load_infisical_secrets
    load_infisical_secrets()
except ImportError:
    pass  # shared package not available; env vars used directly


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8005, alias="API_PORT")
    api_workers: int = Field(default=1, alias="API_WORKERS")
    api_version: str = Field(default="v1", alias="API_VERSION")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    debug: bool = Field(default=False, alias="DEBUG")

    # PostgreSQL Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/value_fabric_ground_truth",
        alias="DATABASE_URL",
    )
    database_url_sync: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/value_fabric_ground_truth",
        alias="DATABASE_URL_SYNC",
    )
    db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    db_pool_pre_ping: bool = Field(default=True, alias="DB_POOL_PRE_PING")

    # Layer 3 Knowledge Graph Integration
    layer3_base_url: str = Field(
        default="http://localhost:8001",
        alias="LAYER3_BASE_URL",
    )
    layer3_api_key: str | None = Field(default=None, alias="LAYER3_API_KEY")
    layer3_timeout_seconds: int = Field(default=30, alias="LAYER3_TIMEOUT_SECONDS")
    layer3_sync_enabled: bool = Field(default=True, alias="LAYER3_SYNC_ENABLED")

    # Validation Configuration
    min_sources_for_corroborated: int = Field(
        default=2,
        alias="MIN_SOURCES_FOR_CORROBORATED",
        description="Minimum distinct sources required to advance to CORROBORATED status",
    )
    min_confidence_for_supported: float = Field(
        default=0.6,
        alias="MIN_CONFIDENCE_FOR_SUPPORTED",
        description="Minimum confidence score to advance from EXTRACTED to SUPPORTED",
    )
    auto_advance_to_supported: bool = Field(
        default=True,
        alias="AUTO_ADVANCE_TO_SUPPORTED",
        description="Automatically advance to SUPPORTED when confidence threshold is met",
    )

    # Freshness Configuration
    default_freshness_days: int = Field(
        default=90,
        alias="DEFAULT_FRESHNESS_DAYS",
        description="Default number of days before a truth object is considered stale",
    )
    stale_warning_days: int = Field(
        default=75,
        alias="STALE_WARNING_DAYS",
        description="Days before expiry to start emitting staleness warnings",
    )

    # Tenant Configuration
    default_tenant_id: str = Field(
        default="default",
        alias="DEFAULT_TENANT_ID",
    )

    # JWT / Auth Configuration
    jwt_secret: str = Field(
        default="changeme-in-production",
        alias="JWT_SECRET",
        description="HMAC secret for signing/verifying JWTs",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        alias="JWT_ALGORITHM",
    )
    jwt_tenant_claim: str = Field(
        default="tenant_id",
        alias="JWT_TENANT_CLAIM",
        description="JWT claim key that holds the tenant/organization UUID",
    )
    jwt_user_claim: str = Field(
        default="sub",
        alias="JWT_USER_CLAIM",
        description="JWT claim key that holds the user identity",
    )
    jwt_roles_claim: str = Field(
        default="roles",
        alias="JWT_ROLES_CLAIM",
        description="JWT claim key that holds the user roles list",
    )
    # When true, a missing/invalid JWT falls back to the organization_id query param
    # (useful for local dev and integration tests). Set false in production.
    jwt_fallback_to_query_param: bool = Field(
        default=True,
        alias="JWT_FALLBACK_TO_QUERY_PARAM",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL uses asyncpg driver."""
        if "postgresql://" in v and "asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://")
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
