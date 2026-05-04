"""Database configuration for Layer 2 Extraction."""

import os
from dataclasses import dataclass

import asyncpg

PRODUCTION_LIKE_ENVIRONMENTS = {"production", "prod", "staging", "stage"}
LOCALHOST_HOSTS = {"localhost", "127.0.0.1", "::1"}
DEFAULT_DATABASE_NAMES = {"valuefabric", "value_fabric", "postgres"}
DEFAULT_DATABASE_USERS = {"valuefabric", "postgres"}


def _current_environment() -> str:
    """Return the normalized runtime environment name for fail-closed policy checks."""
    return (
        os.getenv("ENVIRONMENT")
        or os.getenv("APP_ENV")
        or os.getenv("LAYER2_ENV")
        or "development"
    ).strip().lower()


def _is_production_like(environment: str | None = None) -> bool:
    """Whether persistence settings must be production-grade."""
    return (environment or _current_environment()).strip().lower() in PRODUCTION_LIKE_ENVIRONMENTS


@dataclass
class DatabaseConfig:
    """PostgreSQL database configuration."""

    host: str = "localhost"
    port: int = 5432
    database: str = "valuefabric"
    user: str = "valuefabric"
    password: str = ""
    min_size: int = 5
    max_size: int = 20

    @property
    def dsn(self) -> str:
        """Build connection DSN."""
        if self.password:
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        return f"postgresql://{self.user}@{self.host}:{self.port}/{self.database}"

    def validate_for_environment(self, environment: str | None = None) -> None:
        """Fail closed on insecure database settings in production-like runtimes."""
        env = (environment or _current_environment()).strip().lower()
        if not _is_production_like(env):
            return

        errors: list[str] = []
        if not self.password:
            errors.append("POSTGRES_PASSWORD must be set")
        if self.host.strip().lower() in LOCALHOST_HOSTS:
            errors.append("POSTGRES_HOST must not point at localhost")
        if self.user.strip().lower() in DEFAULT_DATABASE_USERS:
            errors.append("POSTGRES_USER must not use a default service account")
        if self.database.strip().lower() in DEFAULT_DATABASE_NAMES:
            errors.append("POSTGRES_DB must not use a default database name")
        if self.min_size < 1 or self.max_size < self.min_size:
            errors.append("PostgreSQL pool sizes must be positive and internally consistent")

        if errors:
            raise RuntimeError(
                f"Layer 2 database configuration is not production-safe for {env}: "
                + "; ".join(errors)
            )

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load configuration from environment variables."""
        config = cls(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "valuefabric"),
            user=os.getenv("POSTGRES_USER", "valuefabric"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            min_size=int(os.getenv("POSTGRES_MIN_CONNECTIONS", "5")),
            max_size=int(os.getenv("POSTGRES_MAX_CONNECTIONS", "20")),
        )
        config.validate_for_environment()
        return config


# Global connection pool
_pool: asyncpg.Pool | None = None


def get_db_config() -> DatabaseConfig:
    """Get database configuration from environment."""
    return DatabaseConfig.from_env()


async def get_db_pool() -> asyncpg.Pool:
    """Get or create the database connection pool."""
    global _pool
    if _pool is None:
        config = get_db_config()
        _pool = await asyncpg.create_pool(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.user,
            password=config.password,
            min_size=config.min_size,
            max_size=config.max_size,
        )
    return _pool


async def close_db_pool() -> None:
    """Close the database connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
