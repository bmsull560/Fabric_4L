"""Configuration management for Layer 1 Ingestion Service."""

import os
from typing import List

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings

# Load secrets from Infisical if available (optional in dev, required in prod)
from shared.secrets import load_infisical_secrets
try:
    load_infisical_secrets()
except Exception:
    if os.getenv("ENVIRONMENT") == "production":
        raise RuntimeError("Failed to load Infisical secrets in production")


class Settings(BaseSettings):
    """Application settings loaded from environment variables with security validation."""

    # Application
    app_name: str = "layer1-ingestion"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, description="Enable debug mode")

    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/layer1_ingestion",
        description="PostgreSQL connection URL",
    )

    # JWT and Security
    jwt_secret: str = Field(default="changeme", description="JWT signing secret")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT secret is secure."""
        insecure_defaults = ["changeme", "changeme-in-production", "valuefabric", "postgres", "secret", "password"]
        if os.getenv("ENVIRONMENT") == "production":
            if v.lower() in insecure_defaults:
                raise ValueError(f"Insecure default JWT secret detected in production: {v}")
            if len(v) < 32:
                raise ValueError("JWT secret must be >= 32 characters in production")
        return v

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: List[str]) -> List[str]:
        """Validate CORS origins are secure."""
        if os.getenv("ENVIRONMENT") == "production":
            if "*" in v:
                raise ValueError("Wildcard CORS origin not allowed in production")
            if not v or all(not origin.strip() for origin in v):
                raise ValueError("At least one specific CORS origin must be configured in production")
        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL does not use default credentials in production."""
        if os.getenv("ENVIRONMENT") == "production":
            if "postgres:postgres@" in v or "password" in v.lower():
                raise ValueError("Database URL contains default/insecure credentials")
        return v

    # Redis (Celery broker and cache)
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")

    # Storage (MinIO/S3)
    s3_endpoint: str = Field(default="http://localhost:9000", description="S3/MinIO endpoint")
    s3_access_key: str = Field(default="minioadmin", description="S3 access key")
    s3_secret_key: str = Field(default="minioadmin", description="S3 secret key")
    s3_bucket: str = Field(default="layer1-raw-html", description="S3 bucket for raw HTML")
    s3_region: str = Field(default="us-east-1", description="S3 region")

    # Crawler settings
    max_concurrent_pages: int = Field(default=5, description="Max concurrent pages per worker")
    page_timeout_ms: int = Field(default=30000, description="Page load timeout in milliseconds")
    navigation_timeout_ms: int = Field(
        default=10000, description="Navigation timeout in milliseconds"
    )
    default_crawl_depth: int = Field(default=2, description="Default crawl depth")
    max_crawl_depth: int = Field(default=5, description="Maximum crawl depth")

    # Rate limiting
    global_requests_per_minute: int = Field(default=1000, description="Global rate limit")
    per_domain_delay_seconds: float = Field(
        default=1.0, description="Delay between requests to same domain"
    )
    jitter_percent: float = Field(default=20.0, description="Random jitter percentage for delays")

    # Queue settings
    queue_batch_size: int = Field(default=100, description="Number of URLs to process in batch")
    max_retries: int = Field(default=3, description="Max retries for failed URLs")
    retry_delay_seconds: int = Field(default=60, description="Base retry delay")

    # SEC EDGAR
    sec_edgar_rate_limit: int = Field(default=10, description="Requests per second (SEC limit)")
    sec_edgar_user_agent: str = Field(default="ValueFabric/1.0 (contact@valuefabric.io)")
    sec_edgar_cache_ttl_hours: int = Field(default=24)

    # USPTO Patents
    uspto_api_key: str | None = Field(default=None)
    uspto_rate_limit: int = Field(default=5, description="Requests per second")

    # News sources
    news_source: str = Field(default="gdelt", description="News source: 'gdelt' or 'newsapi'")
    newsapi_key: str | None = Field(default=None)

    # Compliance
    retention_days: int = Field(default=30, description="Raw HTML retention period")
    audit_log_retention_years: int = Field(default=7, description="Audit log retention")
    pii_threshold_flag: float = Field(
        default=0.3, description="PII detection threshold for flagging"
    )
    pii_threshold_quarantine: float = Field(
        default=0.7, description="PII detection threshold for quarantine"
    )
    robots_txt_cache_hours: int = Field(default=24, description="robots.txt cache TTL")

    # API settings
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")

    # Layer 2 integration
    layer2_api_url: str = Field(
        default="http://layer2-extraction:8000", description="Layer 2 extraction API URL"
    )

    # LLM Providers (for AI_LLM extraction method)
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4", description="OpenAI model for extraction")
    openai_timeout_seconds: int = Field(default=60, description="OpenAI API timeout")

    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")
    anthropic_model: str = Field(default="claude-3-sonnet-20240229", description="Anthropic model")
    anthropic_timeout_seconds: int = Field(default=60, description="Anthropic API timeout")

    azure_openai_api_key: str | None = Field(default=None, description="Azure OpenAI API key")
    azure_openai_endpoint: str | None = Field(default=None, description="Azure OpenAI endpoint")
    azure_openai_deployment: str | None = Field(
        default=None, description="Azure OpenAI deployment name"
    )

    # Pipeline settings
    pipeline_stage_timeout_seconds: int = Field(
        default=300, description="Timeout per pipeline stage"
    )
    max_pipeline_retries: int = Field(default=3, description="Max retries per pipeline stage")

    model_config = ConfigDict(case_sensitive=False)


# Global settings instance
settings = Settings()
