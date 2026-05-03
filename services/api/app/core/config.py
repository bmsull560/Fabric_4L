import os
import warnings
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings

_DEV_SECRET = "fabric-4l-dev-secret-key-change-in-production"
_DEV_ENVIRONMENTS = {"local", "dev", "development", "test", "testing", "ci"}


def _detect_environment() -> str:
    for key in ("ENVIRONMENT", "ENV", "APP_ENV"):
        val = os.getenv(key, "").strip().lower()
        if val:
            return val
    return "development"


class Settings(BaseSettings):
    app_name: str = "Fabric_4L API"
    debug: bool = False
    secret_key: str = _DEV_SECRET
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    mock_persistence: bool = True
    # Empty list = no cross-origin requests allowed by default (fail-closed).
    # Set CORS_ORIGINS to a comma-separated list of allowed origins.
    cors_origins: list[str] = []

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        """Accept a comma-separated string or a list."""
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v  # type: ignore[return-value]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    env = _detect_environment()

    if env not in _DEV_ENVIRONMENTS:
        # Fail-closed: require an explicit secret in non-dev environments.
        if not settings.secret_key or settings.secret_key == _DEV_SECRET:
            raise RuntimeError(
                f"SECRET_KEY must be set to a non-default value in '{env}' environment. "
                "Set the SECRET_KEY environment variable before starting the service."
            )
        # Fail-closed: require explicit CORS origins in non-dev environments.
        if not settings.cors_origins:
            raise RuntimeError(
                f"CORS_ORIGINS must be set in '{env}' environment. "
                "Set CORS_ORIGINS to a comma-separated list of allowed origins "
                "(e.g. 'https://app.example.com')."
            )
        if "*" in settings.cors_origins:
            raise RuntimeError(
                f"CORS_ORIGINS cannot contain '*' in '{env}' environment. "
                "Specify exact allowed origins."
            )
    else:
        # Development: warn and fall back to localhost defaults when unset.
        if not settings.cors_origins:
            warnings.warn(
                "CORS_ORIGINS not set — defaulting to localhost dev origins. "
                "Set CORS_ORIGINS explicitly before deploying.",
                RuntimeWarning,
                stacklevel=2,
            )
            settings.cors_origins = ["http://localhost:5173", "http://localhost:3000"]

    return settings
