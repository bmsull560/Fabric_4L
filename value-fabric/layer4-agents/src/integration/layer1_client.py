"""Layer 1 Ingestion API Client.

Provides hybrid integration where L4 DocumentIngestionAgent
calls L1 APIs for document processing.
"""

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class Layer1IngestionClient:
    """Client for Layer 1 Ingestion API.

    Used by DocumentIngestionAgent to:
    - Create ingestion jobs
    - Poll for completion
    - Retrieve extraction results

    Example:
        client = Layer1IngestionClient(
            base_url="http://layer1-ingestion:8000",
            api_key="secret"
        )

        job = await client.create_job(
            target_url="https://example.com/doc.pdf",
            document_type="pdf"
        )

        result = await client.wait_for_completion(job["job_id"])
    """

    def __init__(
        self,
        base_url: str = "http://layer1-ingestion:8000",
        api_key: str | None = None,
        timeout: float = 30.0,
    ):
        """Initialize Layer 1 client.

        Args:
            base_url: Layer 1 API base URL
            api_key: API key for authentication
            timeout: Request timeout
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
        )

    async def create_job(
        self,
        target_url: str,
        document_type: str = "auto",
        tenant_id: str | None = None,
        extraction_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a document ingestion job.

        Args:
            target_url: URL of document to ingest
            document_type: Type of document (pdf, html, etc.)
            tenant_id: Tenant context
            extraction_config: Extraction configuration

        Returns:
            Job creation result with job_id
        """
        payload = {
            "target": {
                "url": target_url,
                "type": "http",
            },
            "document_type": document_type,
            "extraction_config": extraction_config
            or {
                "structured_data": True,
                "metadata": True,
            },
        }

        if tenant_id:
            payload["tenant_id"] = tenant_id

        try:
            response = await self.client.post(
                "/v1/ingestion/jobs",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to create ingestion job: {e}")
            raise Layer1ClientError(f"Failed to create job: {e}") from e

    async def get_job_status(self, job_id: str) -> dict[str, Any]:
        """Get job status.

        Args:
            job_id: Job identifier

        Returns:
            Job status
        """
        try:
            response = await self.client.get(f"/v1/ingestion/jobs/{job_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get job status: {e}")
            raise Layer1ClientError(f"Failed to get status: {e}") from e

    async def wait_for_completion(
        self,
        job_id: str,
        timeout: float = 300.0,
        poll_interval: float = 2.0,
    ) -> dict[str, Any]:
        """Poll for job completion.

        Args:
            job_id: Job to wait for
            timeout: Maximum wait time
            poll_interval: Seconds between polls

        Returns:
            Completed job result
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            status = await self.get_job_status(job_id)

            job_status = status.get("status", "unknown")

            if job_status in ["completed", "failed", "cancelled"]:
                return status

            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise Layer1ClientError(f"Timeout waiting for job {job_id}")

            await asyncio.sleep(poll_interval)

    async def get_extraction_result(self, job_id: str) -> dict[str, Any]:
        """Get extraction result for completed job.

        Args:
            job_id: Completed job ID

        Returns:
            Extraction result
        """
        try:
            response = await self.client.get(f"/v1/ingestion/jobs/{job_id}/result")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get extraction result: {e}")
            raise Layer1ClientError(f"Failed to get result: {e}") from e

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()


class Layer1ClientError(Exception):
    """Error from Layer 1 client."""

    pass
