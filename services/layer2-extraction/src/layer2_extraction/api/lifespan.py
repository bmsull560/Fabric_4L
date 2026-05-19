"""Application lifespan management for Layer 2 API."""

import asyncio
import structlog
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from value_fabric.shared.identity.rate_limiter import RedisRateLimiter
from value_fabric.shared.identity.vault_check import is_vault_healthy

from ..shared_bootstrap import validate_production_safety

logger = structlog.get_logger()

redis_rate_limiter: RedisRateLimiter | None = None
_retry_task: asyncio.Task | None = None


async def _init_redis_rate_limiter(is_production_like, current_environment) -> RedisRateLimiter | None:
    try:
        import redis.asyncio as redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.from_url(redis_url, decode_responses=True)
        await redis_client.ping()
        limiter = RedisRateLimiter(redis_client)
        logger.info("L2: Redis rate limiter initialized")
        return limiter
    except Exception as e:
        if is_production_like():
            raise RuntimeError(f"Redis rate limiting is required in {current_environment()} but unavailable: {e}") from e
        logger.warning("L2: Redis not available for rate limiting: %s", e)
        return None


def create_lifespan(*, is_production_like, current_environment, pending_ingestion_retry_loop, ws_manager):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        global redis_rate_limiter, _retry_task
        validate_production_safety()

        redis = await _init_redis_rate_limiter(is_production_like, current_environment)
        redis_rate_limiter = redis
        app.state.redis_rate_limiter = redis

        if os.getenv("ENVIRONMENT", "development") == "production":
            vault_addr = os.getenv("VAULT_ADDR")
            if vault_addr and not await is_vault_healthy(vault_addr):
                raise RuntimeError("Vault unreachable — cannot start in production without secrets backend")

        if _retry_task is None:
            _retry_task = asyncio.create_task(pending_ingestion_retry_loop())

        await ws_manager.start()
        yield

        if _retry_task:
            _retry_task.cancel()
            try:
                await _retry_task
            except asyncio.CancelledError:
                pass
            _retry_task = None

        await ws_manager.stop()

        if getattr(app.state, "telemetry_provider", None) is not None:
            app.state.telemetry_provider.shutdown()
            app.state.telemetry_provider = None

    return lifespan
