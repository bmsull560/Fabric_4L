"""Database layer for Layer 2 Extraction.

Provides async PostgreSQL connection management and schema definitions
for ontology management.
"""

from .config import DatabaseConfig, get_db_config, get_db_pool, close_db_pool
from .connection import get_connection, init_db_pool

__all__ = [
    "DatabaseConfig",
    "get_db_config",
    "get_db_pool",
    "close_db_pool",
    "get_connection",
    "init_db_pool",
]
