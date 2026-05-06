"""Integration interfaces for Layer 2 durable stores."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from value_fabric.layer2.integration.job_store import PipelineJob
    from value_fabric.layer2.integration.pending_ingestion_store import PendingIngestionRecord


class JobStorePort(ABC):
    """Port contract for pipeline job persistence."""

    @abstractmethod
    async def get(self, job_id: str) -> PipelineJob | None: ...

    @abstractmethod
    async def set(self, job: PipelineJob) -> None: ...

    @abstractmethod
    async def delete(self, job_id: str) -> None: ...

    @abstractmethod
    async def exists(self, job_id: str) -> bool: ...

    @abstractmethod
    async def list_jobs(
        self, status: str | None = None, limit: int = 100
    ) -> list[PipelineJob]: ...


class PendingIngestionStorePort(ABC):
    """Port contract for pending ingestion retry persistence."""

    @abstractmethod
    async def enqueue(
        self,
        job_id: str,
        source_url: str,
        extraction_result_json: str,
        relationships_json: str,
        retry_count: int,
        next_retry_at: datetime,
        max_retries: int,
        last_error: str | None,
    ) -> None: ...

    @abstractmethod
    async def get_due(self, now: datetime, limit: int = 25) -> list[PendingIngestionRecord]: ...

    @abstractmethod
    async def complete(self, job_id: str) -> None: ...

    @abstractmethod
    async def reschedule(
        self,
        job_id: str,
        retry_count: int,
        last_error: str,
        next_retry_at: datetime,
    ) -> None: ...

    @abstractmethod
    async def get_retry_metadata(self, job_id: str) -> dict | None: ...
