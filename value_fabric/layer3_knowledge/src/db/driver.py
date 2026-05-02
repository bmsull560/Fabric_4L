"""
Neo4j driver factory with retry logic, connection validation, and health check.

Design philosophy:
- Single source of truth for driver creation across all Layer 3 components
- Fail fast at startup with clear error messages
- Retry transient connection failures with exponential backoff
- Never return None — raise explicitly instead of silently failing
"""

import asyncio
import logging

from neo4j import AsyncDriver, AsyncGraphDatabase
from neo4j.exceptions import (
    AuthError,
    ConfigurationError,
    ServiceUnavailable,
    TransientError,
)

from ..config import Settings, get_settings
from shared.models.typed_dict import TypedDictModel


class health_checkResult(TypedDictModel):
    database: Any
    error: str | None = None
    status: str
    uri: Any

logger = logging.getLogger(__name__)

# Module-level singleton — shared across all components in the same process
_driver: AsyncDriver | None = None


async def create_driver(settings: Settings | None = None) -> AsyncDriver:
    """Create and verify a Neo4j async driver.

    Attempts to connect with exponential backoff.  Raises on permanent
    failures (bad credentials, wrong URI scheme) so callers know immediately
    rather than discovering the problem on the first query.

    Args:
        settings: Application settings.  Loaded from environment if None.

    Returns:
        A verified AsyncDriver instance.

    Raises:
        ConfigurationError: URI scheme is invalid or credentials are wrong.
        ServiceUnavailable: Neo4j is unreachable after all retries.
    """
    cfg = settings or get_settings()

    max_attempts = 5
    base_delay = 1.0  # seconds

    for attempt in range(1, max_attempts + 1):
        try:
            driver = AsyncGraphDatabase.driver(
                cfg.neo4j_uri,
                auth=(cfg.neo4j_user, cfg.neo4j_password),
                max_connection_pool_size=cfg.neo4j_max_pool_size,
                connection_timeout=10.0,
                max_transaction_retry_time=30.0,
            )
            # Verify the connection is actually usable
            await driver.verify_connectivity()
            logger.info(
                "Neo4j driver connected",
                extra={
                    "uri": cfg.neo4j_uri,
                    "database": cfg.neo4j_database,
                    "attempt": attempt,
                },
            )
            return driver

        except AuthError as exc:
            # Wrong credentials — no point retrying
            logger.error(
                "Neo4j authentication failed — check NEO4J_USER / NEO4J_PASSWORD: %s",
                exc,
            )
            raise ConfigurationError(f"Neo4j auth failed: {exc}") from exc

        except ConfigurationError as exc:
            # Bad URI scheme or other permanent config problem
            logger.error("Neo4j configuration error — check NEO4J_URI: %s", exc)
            raise

        except (ServiceUnavailable, TransientError) as exc:
            if attempt == max_attempts:
                logger.error(
                    "Neo4j unreachable after %d attempts: %s", max_attempts, exc
                )
                raise ServiceUnavailable(
                    f"Neo4j at {cfg.neo4j_uri} unreachable after {max_attempts} attempts"
                ) from exc

            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                "Neo4j connection attempt %d/%d failed, retrying in %.1fs: %s",
                attempt,
                max_attempts,
                delay,
                exc,
            )
            await asyncio.sleep(delay)

    # Should never reach here — kept for type-checker
    raise ServiceUnavailable("Neo4j driver could not be created")


async def get_driver(settings: Settings | None = None) -> AsyncDriver:
    """Return the module-level singleton driver, creating it if necessary.

    This is the preferred entry point for all Layer 3 components.
    The singleton is safe for concurrent async access because asyncio is
    single-threaded within a process.

    Args:
        settings: Application settings.  Only used on first call.

    Returns:
        Shared AsyncDriver instance.
    """
    global _driver
    if _driver is None:
        _driver = await create_driver(settings)
    return _driver


async def close_driver() -> None:
    """Close the module-level singleton driver.

    Should be called from the FastAPI lifespan shutdown handler.
    """
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")


async def reset_driver() -> None:
    """Backward-compatible alias for closing and resetting the singleton driver."""
    await close_driver()


async def health_check(settings: Settings | None = None) -> dict:
    """Check Neo4j connectivity without raising.

    Returns a dict with ``status`` (``"healthy"`` or ``"unhealthy"``) and
    optional ``error`` key.  Safe to call from FastAPI ``/health`` endpoints.
    """
    cfg = settings or get_settings()
    try:
        driver = await get_driver(cfg)
        async with driver.session(database=cfg.neo4j_database) as session:
            result = await session.run("RETURN 1 AS check")
            record = await result.single()
            if record and record["check"] == 1:
                return health_checkResult.model_validate({
                    "status": "healthy",
                    "uri": cfg.neo4j_uri,
                    "database": cfg.neo4j_database,
                })


        return health_checkResult.model_validate({"status": "unhealthy", "error": "Unexpected query result"})
    except (ServiceUnavailable, TransientError) as exc:
        return health_checkResult.model_validate({"status": "unhealthy", "error": f"Service unavailable: {exc}"})
    except ConfigurationError as exc:
        return health_checkResult.model_validate({"status": "unhealthy", "error": f"Configuration error: {exc}"})
    except Exception as exc:  # noqa: BLE001
        return health_checkResult.model_validate({"status": "unhealthy", "error": str(exc)})
