"""Database connection management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg

from .config import get_db_pool, close_db_pool


@asynccontextmanager
async def get_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get a database connection from the pool.

    Usage:
        async with get_connection() as conn:
            row = await conn.fetchrow("SELECT * FROM table WHERE id = $1", id)
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        yield conn


async def init_db_pool() -> None:
    """Initialize the database connection pool.

    Call this during application startup.
    """
    await get_db_pool()


async def close_db() -> None:
    """Close the database connection pool.

    Call this during application shutdown.
    """
    await close_db_pool()


async def check_db_health() -> bool:
    """Check database connectivity."""
    try:
        async with get_connection() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception:
        return False
