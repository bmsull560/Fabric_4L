"""Database configuration for Layer 2 Extraction."""

import os
from dataclasses import dataclass

import asyncpg


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

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load configuration from environment variables."""
        return cls(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "valuefabric"),
            user=os.getenv("POSTGRES_USER", "valuefabric"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            min_size=int(os.getenv("POSTGRES_MIN_CONNECTIONS", "5")),
            max_size=int(os.getenv("POSTGRES_MAX_CONNECTIONS", "20")),
        )


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
