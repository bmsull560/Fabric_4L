import os
import warnings
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_DEFAULT_DEV_SECRET = "fabric-4l-dev-secret-key-change-in-production"
_DEV_ENVIRONMENTS = {"local", "dev", "development", "test", "testing", "ci"}
_PRODUCTION_ENVS = {"production", "prod", "staging"}


def _detect_environment() -> str:
    for key in ("ENVIRONMENT", "ENV", "APP_ENV"):
        val = os.getenv(key, "").strip().lower()
        if val:
            return val
    return "development"


class Settings(BaseSettings):
    app_name: str = "Fabric_4L API"
    app_env: str = Field(default_factory=_detect_environment, alias="APP_ENV")
    debug: bool = False
    secret_key: str = _DEFAULT_DEV_SECRET
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    mock_persistence: bool = True
    database_url: str | None = None
    llm_provider: str = "mock"
    allow_mock_llm: bool = False
    # Empty list = no cross-origin requests allowed by default (fail-closed).
    # Development get_settings() supplies localhost defaults only after warning.
    cors_origins: list[str] = []

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    @property
    def is_production_like(self) -> bool:
        env = self.app_env.lower()
        return env in _PRODUCTION_ENVS or env not in _DEV_ENVIRONMENTS

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        """Accept a comma-separated string or a list of exact allowed origins."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_production_safety(self) -> "Settings":
        if not self.is_production_like:
            return self

        errors: list[str] = []
        if self.mock_persistence:
            errors.append("mock_persistence must be false in production-like environments")
        if not self.database_url:
            errors.append("database_url must be configured in production-like environments")
        if self.llm_provider.lower() == "mock" and not self.allow_mock_llm:
            errors.append("llm_provider=mock is disabled in production-like environments")
        if self.secret_key == _DEFAULT_DEV_SECRET or len(self.secret_key) < 32:
            errors.append("secret_key must be replaced with a strong production secret")
        if not self.cors_origins:
            errors.append("cors_origins must be configured in production-like environments")
        if "*" in self.cors_origins:
            errors.append("cors_origins cannot include '*' in production-like environments")

        if errors:
            raise ValueError("Unsafe production configuration: " + "; ".join(errors))
        return self


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()

    if settings.is_production_like:
        return settings

    if not settings.cors_origins:
        warnings.warn(
            "CORS_ORIGINS not set — defaulting to localhost dev origins. "
            "Set CORS_ORIGINS explicitly before deploying.",
            RuntimeWarning,
            stacklevel=2,
        )
        settings.cors_origins = ["http://localhost:5173", "http://localhost:3000"]

    return settings
