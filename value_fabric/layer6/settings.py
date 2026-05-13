from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, ValidationInfo, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ALLOWED_PG_SSL_MODES = {"require", "verify-ca", "verify-full"}
_ALLOWED_NEO4J_SCHEMES = ("bolt+s://", "neo4j+s://")


class Layer6Settings(BaseSettings):
    """Layer 6 runtime settings with strict validation for security-sensitive env vars."""

    model_config = SettingsConfigDict(extra="ignore", case_sensitive=True)

    environment: Literal["development", "test", "staging", "production"] = Field(
        default="development", alias="ENVIRONMENT"
    )
    testing: bool = Field(default=False, alias="TESTING")

    database_url: str = Field(alias="DATABASE_URL")
    neo4j_uri: str = Field(alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER", min_length=1)
    neo4j_password: SecretStr = Field(alias="NEO4J_PASSWORD", min_length=12)

    jwt_secret: SecretStr = Field(alias="JWT_SECRET", min_length=32)
    api_key_hmac_secret: SecretStr = Field(alias="API_KEY_HMAC_SECRET", min_length=32)
    service_auth_secret: SecretStr = Field(alias="SERVICE_AUTH_SECRET", min_length=32)

    auth_required: bool = Field(default=True, alias="AUTH_REQUIRED")
    allow_insecure_dev_auth_bypass: bool = Field(default=False, alias="ALLOW_INSECURE_DEV_AUTH_BYPASS")
    dev_auth_bypass: bool = Field(default=False, alias="DEV_AUTH_BYPASS")
    auth_bypass_enabled: bool = Field(default=False, alias="AUTH_BYPASS_ENABLED")
    jwt_fallback_to_query_param: bool = Field(default=False, alias="JWT_FALLBACK_TO_QUERY_PARAM")
    allow_ephemeral_encryption: bool = Field(default=False, alias="ALLOW_EPHEMERAL_ENCRYPTION")
    allow_dev_auth_bypass: str | None = Field(default=None, alias="ALLOW_DEV_AUTH_BYPASS")

    @field_validator("database_url")
    @classmethod
    def _validate_database_url(cls, value: str, info: ValidationInfo) -> str:
        if not value.startswith(("postgresql://", "postgresql+")):
            raise ValueError("DATABASE_URL must target PostgreSQL")
        env = info.data.get("environment", "development")
        if env in {"staging", "production"}:
            if "sslmode=" not in value:
                raise ValueError("DATABASE_URL must include sslmode in staging/production")
            sslmode = value.split("sslmode=", 1)[1].split("&", 1)[0]
            if sslmode not in _ALLOWED_PG_SSL_MODES:
                raise ValueError("DATABASE_URL sslmode must be require, verify-ca, or verify-full")
        return value

    @field_validator("neo4j_uri")
    @classmethod
    def _validate_neo4j_uri(cls, value: str, info: ValidationInfo) -> str:
        env = info.data.get("environment", "development")
        if env in {"staging", "production"} and not value.startswith(_ALLOWED_NEO4J_SCHEMES):
            raise ValueError("NEO4J_URI must use neo4j+s:// or bolt+s:// in staging/production")
        return value

    @model_validator(mode="after")
    def _validate_bypass_flags(self) -> "Layer6Settings":
        if self.environment not in {"staging", "production"}:
            return self

        active_flags: list[str] = []
        if self.allow_insecure_dev_auth_bypass:
            active_flags.append("ALLOW_INSECURE_DEV_AUTH_BYPASS")
        if self.dev_auth_bypass:
            active_flags.append("DEV_AUTH_BYPASS")
        if self.auth_bypass_enabled:
            active_flags.append("AUTH_BYPASS_ENABLED")
        if self.jwt_fallback_to_query_param:
            active_flags.append("JWT_FALLBACK_TO_QUERY_PARAM")
        if self.allow_ephemeral_encryption:
            active_flags.append("ALLOW_EPHEMERAL_ENCRYPTION")
        if (self.allow_dev_auth_bypass or "").strip().lower() == "i_understand_risk":
            active_flags.append("ALLOW_DEV_AUTH_BYPASS")

        if active_flags:
            raise ValueError(
                "Production-like Layer 6 configuration cannot enable bypass flags: "
                + ", ".join(active_flags)
            )

        return self


@lru_cache(maxsize=1)
def get_layer6_settings() -> Layer6Settings:
    return Layer6Settings()


def validate_layer6_startup_settings() -> Layer6Settings:
    """Fail-fast startup hook for Layer 6 critical configuration."""

    return get_layer6_settings()
