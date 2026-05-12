"""Job store implementations for Layer 2 extraction pipeline."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PipelineJob(BaseModel):
    """State for a single extract-and-ingest pipeline job."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    source_url: str
    overall_status: str = "pending"
    extraction_status: str = "pending"
    ingestion_status: str = "pending"
    entities_extracted: int = 0
    relationships_extracted: int = 0
    retry_count: int = 0
    last_error: str | None = None
    next_retry_at: datetime | None = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    tenant_id: str | None = None


class ExtractionArtifacts(BaseModel):
    """Artifacts produced by an extraction run."""

    model_config = ConfigDict(extra="forbid")

    result: Any = None
    relationships: list[Any] = Field(default_factory=list)


class InMemoryJobStore:
    """In-memory job store for development and testing."""

    def __init__(self) -> None:
        self._jobs: dict[str, PipelineJob] = {}
        self._artifacts: dict[str, ExtractionArtifacts] = {}

    async def get_job(self, job_id: str, *, tenant_id: str | None = None) -> PipelineJob:
        job = self._jobs[job_id]
        if tenant_id is not None and job.tenant_id != tenant_id:
            raise KeyError(job_id)
        return job

    async def set_job(self, job: PipelineJob) -> None:
        self._jobs[job.job_id] = job

    async def get_artifacts(self, job_id: str, *, tenant_id: str | None = None) -> ExtractionArtifacts | None:
        return self._artifacts.get(job_id)

    async def set_artifacts(self, job_id: str, artifacts: ExtractionArtifacts) -> None:
        self._artifacts[job_id] = artifacts


def build_job_store() -> InMemoryJobStore:
    """Factory for job store based on environment."""
    return InMemoryJobStore()
