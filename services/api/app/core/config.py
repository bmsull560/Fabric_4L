import os
from functools import lru_cache

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
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    env = _detect_environment()
    if env not in _DEV_ENVIRONMENTS:
        if not settings.secret_key or settings.secret_key == _DEV_SECRET:
            raise RuntimeError(
                f"SECRET_KEY must be set to a non-default value in '{env}' environment. "
                "Set the SECRET_KEY environment variable before starting the service."
            )
    return settings
