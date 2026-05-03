"""Durable job state persistence for Layer 2 extraction pipeline.

Provides Redis-backed storage for pipeline job state, replacing the in-memory
PIPELINE_JOBS dict to enable container restart tolerance and horizontal scaling.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)

PRODUCTION_LIKE_ENVIRONMENTS = {"production", "prod", "staging", "stage"}


def _current_environment() -> str:
    """Return the normalized runtime environment name for persistence policy checks."""
    return (
        os.getenv("ENVIRONMENT")
        or os.getenv("APP_ENV")
        or os.getenv("LAYER2_ENV")
        or "development"
    ).strip().lower()


def _is_production_like() -> bool:
    """Whether the current runtime must fail closed on non-durable persistence."""
    return _current_environment() in PRODUCTION_LIKE_ENVIRONMENTS


@dataclass
class PipelineJob:
    """Pipeline job state for external status contract."""

    job_id: str
    extraction_status: str
    ingestion_status: str
    created_at: str
    entities_extracted: int = 0
    relationships_extracted: int = 0
    retry_count: int = 0
    last_error: str | None = None
    next_retry_at: str | None = None
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize job to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineJob:
        """Deserialize job from dictionary."""
        return cls(**data)


class JobStore:
    """Storage abstraction for pipeline job state."""

    async def get(self, job_id: str) -> PipelineJob | None:
        """Get job by ID."""
        raise NotImplementedError

    async def set(self, job: PipelineJob) -> None:
        """Save or update job."""
        raise NotImplementedError

    async def delete(self, job_id: str) -> None:
        """Delete job."""
        raise NotImplementedError

    async def exists(self, job_id: str) -> bool:
        """Check if job exists."""
        raise NotImplementedError

    async def list_jobs(
        self, status: str | None = None, limit: int = 100
    ) -> list[PipelineJob]:
        """List jobs, optionally filtered by status."""
        raise NotImplementedError


class InMemoryJobStore(JobStore):
    """In-memory job store for development/testing."""

    def __init__(self) -> None:
        self._jobs: dict[str, PipelineJob] = {}

    async def get(self, job_id: str) -> PipelineJob | None:
        return self._jobs.get(job_id)

    async def set(self, job: PipelineJob) -> None:
        self._jobs[job.job_id] = job

    async def delete(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)

    async def exists(self, job_id: str) -> bool:
        return job_id in self._jobs

    async def list_jobs(
        self, status: str | None = None, limit: int = 100
    ) -> list[PipelineJob]:
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.extraction_status == status or j.ingestion_status == status]
        return jobs[:limit]


class RedisJobStore(JobStore):
    """Redis-backed durable job store for production.

    Provides persistence across container restarts and supports horizontal scaling.
    Jobs are stored as JSON with a TTL to prevent unbounded growth.
    """

    DEFAULT_TTL_SECONDS = 86400 * 7  # 7 days retention

    def __init__(
        self,
        redis_url: str | None = None,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        """Initialize Redis job store.

        Args:
            redis_url: Redis connection URL (or REDIS_URL env var)
            ttl_seconds: Job retention time (default 7 days)
        """
        import redis.asyncio as redis

        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._ttl_seconds = ttl_seconds
        self._client: redis.Redis | None = None

    async def _get_client(self) -> Any:
        """Lazy initialization of Redis client."""
        if self._client is None:
            import redis.asyncio as redis

            self._client = redis.from_url(self._redis_url, decode_responses=True)
        return self._client

    def _key(self, job_id: str) -> str:
        """Generate Redis key for job."""
        return f"layer2:job:{job_id}"

    async def get(self, job_id: str) -> PipelineJob | None:
        """Get job by ID from Redis."""
        try:
            client = await self._get_client()
            data = await client.get(self._key(job_id))
            if not data:
                return None
            return PipelineJob.from_dict(json.loads(data))
        except Exception as exc:
            logger.warning("Failed to get job %s from Redis: %s", job_id, exc)
            return None

    async def set(self, job: PipelineJob) -> None:
        """Save job to Redis with TTL."""
        client = await self._get_client()
        key = self._key(job.job_id)
        data = json.dumps(job.to_dict())
        await client.setex(key, self._ttl_seconds, data)

    async def delete(self, job_id: str) -> None:
        """Delete job from Redis."""
        client = await self._get_client()
        await client.delete(self._key(job_id))

    async def exists(self, job_id: str) -> bool:
        """Check if job exists in Redis."""
        client = await self._get_client()
        return await client.exists(self._key(job_id)) > 0

    async def list_jobs(
        self, status: str | None = None, limit: int = 100
    ) -> list[PipelineJob]:
        """List jobs from Redis.

        Note: This scans all job keys - for large deployments,
        consider maintaining a separate index or using Redis Search.
        """
        client = await self._get_client()
        jobs: list[PipelineJob] = []

        # Scan for job keys
        async for key in client.scan_iter(match="layer2:job:*", count=100):
            data = await client.get(key)
            if data:
                job = PipelineJob.from_dict(json.loads(data))
                if status is None or job.extraction_status == status or job.ingestion_status == status:
                    jobs.append(job)
                    if len(jobs) >= limit:
                        break

        return jobs

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None


def build_job_store() -> JobStore:
    """Factory function to build appropriate job store based on configuration.

    Production-like environments require an explicit Redis backing store and fail
    closed before constructing any in-memory fallback. Development and tests keep
    the historical in-memory fallback when Redis is not configured.
    """
    redis_url = os.getenv("REDIS_URL")

    if redis_url:
        try:
            return RedisJobStore(redis_url)
        except Exception as exc:
            if _is_production_like():
                raise RuntimeError(
                    "REDIS_URL is configured but the Layer 2 Redis job store could not be "
                    f"initialized in {_current_environment()}: {exc}"
                ) from exc
            logger.warning("Failed to initialize Redis job store, falling back to in-memory: %s", exc)

    if _is_production_like():
        raise RuntimeError(
            "REDIS_URL is required for Layer 2 job persistence in production-like "
            f"environment {_current_environment()!r}; refusing in-memory job store fallback."
        )

    return InMemoryJobStore()
