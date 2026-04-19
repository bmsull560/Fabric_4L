"""Layer 2 Extraction API Client.

Provides hybrid integration where L4 FinancialExtractionAgent
calls L2 APIs for financial document processing.
"""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class Layer2ExtractionClient:
    """Client for Layer 2 Extraction Pipeline API.

    Used by FinancialExtractionAgent to:
    - Extract from SEC filings
    - Transcribe earnings calls
    - Extract financial metrics

    Example:
        client = Layer2ExtractionClient(
            base_url="http://layer2-extraction:8000"
        )

        filing = await client.extract_filing(
            url="https://sec.gov/.../10-k.pdf",
            filing_type="10-K",
            ticker="AAPL"
        )
    """

    def __init__(
        self,
        base_url: str = "http://layer2-extraction:8000",
        api_key: str | None = None,
        timeout: float = 60.0,
    ):
        """Initialize Layer 2 client.

        Args:
            base_url: Layer 2 API base URL
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

    async def extract_filing(
        self,
        url: str,
        filing_type: str,
        ticker: str | None = None,
        extraction_prompts: list[str] | None = None,
    ) -> dict[str, Any]:
        """Extract data from SEC filing.

        Args:
            url: URL of filing document
            filing_type: 10-K, 10-Q, 8-K, etc.
            ticker: Company ticker symbol
            extraction_prompts: Custom extraction prompts

        Returns:
            Extracted financial data
        """
        payload = {
            "document_url": url,
            "filing_type": filing_type,
            "extraction_type": "sec_filing",
        }

        if ticker:
            payload["ticker"] = ticker
        if extraction_prompts:
            payload["prompts"] = extraction_prompts

        try:
            response = await self.client.post(
                "/v1/extract",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to extract filing: {e}")
            raise Layer2ClientError(f"Failed to extract filing: {e}") from e

    async def transcribe_earnings_call(
        self,
        audio_url: str,
        company: str,
        quarter: str,
        year: int,
    ) -> dict[str, Any]:
        """Transcribe earnings call audio.

        Args:
            audio_url: URL of audio file
            company: Company name
            quarter: Quarter (Q1, Q2, Q3, Q4)
            year: Year

        Returns:
            Transcription result
        """
        payload = {
            "audio_url": audio_url,
            "company": company,
            "quarter": quarter,
            "year": year,
        }

        try:
            response = await self.client.post(
                "/v1/transcribe/earnings",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to transcribe earnings call: {e}")
            raise Layer2ClientError(f"Failed to transcribe: {e}") from e

    async def extract_financial_metrics(
        self,
        document_text: str,
        metrics: list[str] | None = None,
        ticker: str | None = None,
    ) -> dict[str, Any]:
        """Extract financial metrics from text.

        Args:
            document_text: Text to analyze
            metrics: Specific metrics to extract
            ticker: Company ticker for context

        Returns:
            Extracted metrics
        """
        payload = {
            "text": document_text,
            "extraction_type": "financial_metrics",
        }

        if metrics:
            payload["metrics"] = metrics
        if ticker:
            payload["ticker"] = ticker

        try:
            response = await self.client.post(
                "/v1/extract/metrics",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to extract metrics: {e}")
            raise Layer2ClientError(f"Failed to extract metrics: {e}") from e

    async def identify_risk_factors(
        self,
        document_text: str,
        categories: list[str] | None = None,
    ) -> dict[str, Any]:
        """Identify risk factors from text.

        Args:
            document_text: Text to analyze
            categories: Risk categories to identify

        Returns:
            Identified risks
        """
        payload = {
            "text": document_text,
            "extraction_type": "risk_factors",
        }

        if categories:
            payload["categories"] = categories

        try:
            response = await self.client.post(
                "/v1/extract/risks",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to identify risks: {e}")
            raise Layer2ClientError(f"Failed to identify risks: {e}") from e

    async def extract_and_ingest(
        self,
        url: str,
        filing_type: str,
        ticker: str | None = None,
    ) -> dict[str, Any]:
        """Extract from filing and auto-ingest to knowledge graph.

        Args:
            url: URL of filing document
            filing_type: 10-K, 10-Q, 8-K, etc.
            ticker: Company ticker symbol

        Returns:
            Extraction and ingestion result
        """
        payload = {
            "document_url": url,
            "filing_type": filing_type,
            "extraction_type": "sec_filing",
            "auto_ingest": True,
        }

        if ticker:
            payload["ticker"] = ticker

        try:
            response = await self.client.post(
                "/v1/extract-and-ingest",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to extract and ingest: {e}")
            raise Layer2ClientError(f"Failed to extract and ingest: {e}") from e

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()


class Layer2ClientError(Exception):
    """Error from Layer 2 client."""

    pass
