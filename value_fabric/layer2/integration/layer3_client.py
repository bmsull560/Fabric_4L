"""Layer 3 Knowledge Graph client for Layer 2 extraction pipeline."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class IngestionResponse(BaseModel):
    """Response from Layer 3 ingestion."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    ingestion_id: str
    entities_loaded: int = 0
    relationships_loaded: int = 0
    message: str = ""
    error: str | None = None


class IngestionStatus(BaseModel):
    """Status of an ongoing ingestion."""

    model_config = ConfigDict(extra="forbid")

    ingestion_id: str
    status: str = "unknown"
    progress_percent: float = 0.0
    entities_processed: int = 0
    entities_total: int = 0
    error_message: str | None = None


class Layer3KnowledgeClient:
    """Client for Layer 3 Knowledge Graph ingestion."""

    def __init__(self, base_url: str = "", api_key: str | None = None) -> None:
        self.base_url = base_url or "http://localhost:8003"
        self._api_key = api_key

    async def health_check(self) -> bool:
        """Check if Layer 3 is healthy."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health", timeout=5.0)
                return response.status_code == 200
        except Exception:
            return False

    async def ingest_rdf_data(
        self,
        *,
        rdf_data: str,
        source_url: str,
        extraction_job_id: str,
    ) -> IngestionResponse:
        """Ingest RDF data into Layer 3."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                payload = {
                    "rdf_data": rdf_data,
                    "source_url": source_url,
                    "extraction_job_id": extraction_job_id,
                }
                response = await client.post(
                    f"{self.base_url}/v1/ingest",
                    json=payload,
                    timeout=30.0,
                )
                data = response.json()
                return IngestionResponse(**data)
        except Exception as exc:
            return IngestionResponse(
                success=False,
                ingestion_id=extraction_job_id,
                error=str(exc),
            )

    async def get_ingestion_status(self, ingestion_id: str) -> IngestionStatus:
        """Get status of an ingestion."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v1/ingest/{ingestion_id}/status",
                    timeout=5.0,
                )
                data = response.json()
                return IngestionStatus(**data)
        except Exception as exc:
            return IngestionStatus(
                ingestion_id=ingestion_id,
                status="error",
                error_message=str(exc),
            )

    async def close(self) -> None:
        """Close any open connections."""
        pass
