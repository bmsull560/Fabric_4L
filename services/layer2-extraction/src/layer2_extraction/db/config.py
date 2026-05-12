"""Database configuration for Layer 2 extraction."""

from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, ConfigDict


class DatabaseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str = "localhost"
    port: int = 5432
    database: str = "layer2"
    user: str = "layer2"
    password: str = ""
    min_connections: int = 1
    max_connections: int = 10

    @classmethod
    def from_env(cls) -> DatabaseConfig:
        """Load database config from environment variables."""
        env = os.environ.get("ENVIRONMENT", os.environ.get("APP_ENV", "development")).lower()
        host = os.environ.get("POSTGRES_HOST", "localhost")
        port = int(os.environ.get("POSTGRES_PORT", "5432"))
        database = os.environ.get("POSTGRES_DB", "layer2")
        user = os.environ.get("POSTGRES_USER", "layer2")
        password = os.environ.get("POSTGRES_PASSWORD", "")
        min_conn = int(os.environ.get("POSTGRES_MIN_CONNECTIONS", "1"))
        max_conn = int(os.environ.get("POSTGRES_MAX_CONNECTIONS", "10"))

        if env == "production":
            errors: list[str] = []
            if not password:
                errors.append("POSTGRES_PASSWORD must be set in production")
            if host in ("localhost", "127.0.0.1", "::1"):
                errors.append("POSTGRES_HOST must not point at localhost in production")
            if user in ("postgres", "admin", "root"):
                errors.append("POSTGRES_USER must not use a default service account in production")
            if database in ("postgres", "layer2", "default"):
                errors.append("POSTGRES_DB must not use a default database name in production")
            if errors:
                raise RuntimeError("; ".join(errors))

        return cls(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            min_connections=min_conn,
            max_connections=max_conn,
        )
