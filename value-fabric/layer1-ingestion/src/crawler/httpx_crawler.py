"""HTTPX-based fast path crawler for static content ingestion.

Provides high-performance static page fetching with SPA detection,
content extraction, and execution metrics for Layer 1 ingestion.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
import structlog
import trafilatura
from selectolax.lexbor import LexborHTMLParser
from shared.models.typed_dict import TypedDictModel


class HttpxCrawler_get_statsResult(TypedDictModel):
    config: dict[str, Any]

logger = structlog.get_logger()


@dataclass(frozen=True)
class FastPathResult:
    """Result of a fast path HTTPX fetch.

    Contains fetched content, metadata, and quality signals for
    downstream routing decisions.
    """

    url: str
    status_code: int
    html: str
    title: str
    text_content: str
    content_hash: str
    links_found: list[str] = field(default_factory=list)
    is_spa_detected: bool = False
    fetch_time_ms: int = 0
    content_type: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    original_html_length: int = 0  # P1 Fix: Store original size before truncation


@dataclass
class HttpxCrawlerConfig:
    """Configuration for HttpxCrawler."""

    timeout_seconds: int = 15
    max_connections: int = 50
    max_keepalive: int = 20
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 "
        "ValueFabric-FastPath/1.0"
    )
    max_html_size: int = 1_000_000  # 1MB limit
    max_concurrent_requests: int = 20
    spa_script_threshold: int = 5  # Scripts to trigger SPA detection
    spa_content_ratio_threshold: float = 0.02


class HttpxCrawler:
    """High-performance static page scraper using HTTPX.

    Designed for fast path ingestion of static content with:
    - HTTP/2 multiplexing for efficiency
    - Concurrent request limiting
    - SPA shell detection
    - Clean text extraction via trafilatura
    - Link discovery for crawling

    Example:
        async with HttpxCrawler() as crawler:
            result = await crawler.fetch("https://example.com/page")
            if not result.is_spa_detected:
                print(f"Fetched {len(result.text_content)} chars in {result.fetch_time_ms}ms")
    """

    def __init__(self, config: HttpxCrawlerConfig | None = None) -> None:
        """Initialize crawler with configuration.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or HttpxCrawlerConfig()
        self._client: httpx.AsyncClient | None = None
        self._semaphore: asyncio.Semaphore | None = None
        self.logger = logger.bind(crawler="HttpxCrawler")

    async def __aenter__(self) -> HttpxCrawler:
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.stop()

    async def start(self) -> None:
        """Initialize HTTPX client with connection pooling."""
        limits = httpx.Limits(
            max_connections=self.config.max_connections,
            max_keepalive_connections=self.config.max_keepalive,
        )

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout_seconds),
            limits=limits,
            headers={
                "User-Agent": self.config.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
            },
            follow_redirects=True,
            http2=True,
        )

        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)

        self.logger.info(
            "HTTPX crawler started",
            max_connections=self.config.max_connections,
            timeout=self.config.timeout_seconds,
        )

    async def stop(self) -> None:
        """Close HTTPX client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None

        self.logger.info("HTTPX crawler stopped")

    async def fetch(self, url: str) -> FastPathResult:
        """Fetch a single URL via HTTPX with full processing.

        Args:
            url: URL to fetch

        Returns:
            FastPathResult with content and metadata
        """
        if not self._client:
            raise RuntimeError("Crawler not started. Use async context manager.")

        start_time = time.monotonic()

        try:
            async with self._semaphore:
                response = await self._client.get(url)

            fetch_time = int((time.monotonic() - start_time) * 1000)

            if response.status_code != 200:
                return self._create_error_result(
                    url=url,
                    status_code=response.status_code,
                    fetch_time_ms=fetch_time,
                    error_type="http_error",
                    headers=dict(response.headers),
                )

            # P1 Fix: Get full HTML first for link extraction
            full_html = response.text
            original_length = len(full_html)

            # Limit HTML size for processing (after extracting links)
            html = full_html[: self.config.max_html_size]
            content_type = response.headers.get("content-type", "")

            # Quick SPA detection
            is_spa = self._detect_spa_shell(html)

            # Extract structured content
            parsed = LexborHTMLParser(html)
            title_tag = parsed.css_first("title")
            title = title_tag.text() if title_tag else ""

            # Use trafilatura for clean text extraction
            text_content = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
            ) or ""

            # P1 Fix: Extract links from FULL HTML before truncation
            links = self._extract_links(full_html, url)

            # Content hash for deduplication
            content_hash = hashlib.sha256(text_content.encode()).hexdigest()[:16]

            return FastPathResult(
                url=url,
                status_code=response.status_code,
                html=html[:100000],  # Truncate for storage
                title=title,
                text_content=text_content,
                content_hash=content_hash,
                links_found=links,
                is_spa_detected=is_spa,
                fetch_time_ms=fetch_time,
                content_type=content_type,
                headers=dict(response.headers),
                original_html_length=original_length,  # P1 Fix: Store original length
            )

        except httpx.TimeoutException:
            fetch_time = int((time.monotonic() - start_time) * 1000)
            self.logger.warning("Fetch timeout", url=url, timeout=self.config.timeout_seconds)
            return self._create_error_result(
                url=url,
                status_code=504,
                fetch_time_ms=fetch_time,
                error_type="timeout",
            )

        except httpx.NetworkError as e:
            fetch_time = int((time.monotonic() - start_time) * 1000)
            self.logger.error("Network error", url=url, error=str(e))
            return self._create_error_result(
                url=url,
                status_code=0,
                fetch_time_ms=fetch_time,
                error_type=f"network_error:{type(e).__name__}",
            )

        except Exception as e:
            fetch_time = int((time.monotonic() - start_time) * 1000)
            self.logger.error("Fetch failed", url=url, error=str(e), exc_info=True)
            return self._create_error_result(
                url=url,
                status_code=0,
                fetch_time_ms=fetch_time,
                error_type=f"exception:{type(e).__name__}",
            )

    async def fetch_batch(
        self,
        urls: list[str],
        delay_seconds: float = 0,
    ) -> list[FastPathResult]:
        """Fetch multiple URLs concurrently with optional rate limiting.

        Args:
            urls: List of URLs to fetch
            delay_seconds: Optional delay between requests to same domain

        Returns:
            List of FastPathResult in same order as input
        """
        if delay_seconds > 0:
            return await self._fetch_batch_with_delay(urls, delay_seconds)

        # Fetch all concurrently
        tasks = [self.fetch(url) for url in urls]
        return await asyncio.gather(*tasks)

    async def _fetch_batch_with_delay(
        self,
        urls: list[str],
        delay_seconds: float,
    ) -> list[FastPathResult]:
        """Fetch URLs with per-domain rate limiting."""
        results: list[FastPathResult] = []
        last_request_time: dict[str, float] = {}

        for url in urls:
            domain = urlparse(url).netloc

            # Rate limiting
            if domain in last_request_time:
                elapsed = time.time() - last_request_time[domain]
                if elapsed < delay_seconds:
                    wait_time = delay_seconds - elapsed
                    self.logger.debug("Rate limiting", domain=domain, wait_seconds=wait_time)
                    await asyncio.sleep(wait_time)

            result = await self.fetch(url)
            results.append(result)
            last_request_time[domain] = time.time()

        return results

    def _detect_spa_shell(self, html: str) -> bool:
        """Detect if HTML appears to be a JS-rendered SPA shell.

        Lightweight heuristics optimized for speed:
        1. High script tag density (>5 scripts)
        2. Low content-to-HTML ratio
        3. Presence of common SPA markers
        4. Empty root/app containers

        Args:
            html: Raw HTML content

        Returns:
            True if SPA shell detected
        """
        if not html:
            return False

        html_lower = html.lower()

        # Indicator 1: High script density
        script_count = html_lower.count("<script")
        high_script_density = script_count > self.config.spa_script_threshold

        # Indicator 2: Low content ratio
        import re

        text_content = re.sub(r"<[^>]+>", "", html)
        content_ratio = len(text_content) / max(len(html), 1)
        low_content = content_ratio < self.config.spa_content_ratio_threshold

        # Indicator 3: SPA markers
        spa_markers = [
            '<div id="root"></div>',
            '<div id="app"></div>',
            '<div id="__next"></div>',
            'data-reactroot',
            'ng-version=',
        ]
        has_spa_markers = any(marker in html_lower for marker in spa_markers)

        # Indicator 4: Empty root containers
        has_empty_root = bool(
            re.search(r'<div\s+id=["\']root["\']\s*>\s*</div>', html, re.IGNORECASE)
        )

        indicators = [
            high_script_density,
            low_content,
            has_spa_markers,
            has_empty_root,
        ]

        # Require 2+ indicators to reduce false positives
        return sum(indicators) >= 2

    def _extract_links(self, html: str, base_url: str) -> list[str]:
        """Extract all links from HTML content.

        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative links

        Returns:
            List of absolute URLs
        """
        try:
            parsed = LexborHTMLParser(html)
            links = []

            for a_tag in parsed.css("a[href]"):
                href = a_tag.attrs.get("href", "").strip()
                if not href:
                    continue

                # Skip non-HTTP protocols and anchors
                if href.startswith(("javascript:", "mailto:", "tel:", "#")):
                    continue

                # Resolve relative URLs
                absolute_url = urljoin(base_url, href)

                # Only include HTTP(S) URLs
                parsed_url = urlparse(absolute_url)
                if parsed_url.scheme not in ("http", "https"):
                    continue

                links.append(absolute_url)

            # Deduplicate while preserving order
            seen = set()
            unique_links = []
            for link in links:
                if link not in seen:
                    seen.add(link)
                    unique_links.append(link)

            return unique_links

        except Exception as e:
            self.logger.warning("Link extraction failed", error=str(e))
            return []

    def _create_error_result(
        self,
        url: str,
        status_code: int,
        fetch_time_ms: int,
        error_type: str,
        headers: dict[str, str] | None = None,
    ) -> FastPathResult:
        """Create a FastPathResult for error cases."""
        return FastPathResult(
            url=url,
            status_code=status_code,
            html="",
            title="",
            text_content="",
            content_hash="",
            links_found=[],
            is_spa_detected=False,
            fetch_time_ms=fetch_time_ms,
            content_type=error_type,
            headers=headers or {},
            original_html_length=0,
        )

    def get_stats(self) -> dict[str, Any]:
        """Get crawler statistics (if implemented)."""
        # Placeholder for future metrics implementation
        return HttpxCrawler_get_statsResult.model_validate({
            "config": {
                "timeout_seconds": self.config.timeout_seconds,
                "max_connections": self.config.max_connections,
                "max_concurrent": self.config.max_concurrent_requests,
            }
        })


