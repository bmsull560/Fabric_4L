"""Playwright-based web crawler implementation.

This module provides async web crawling capabilities using Playwright
to render JavaScript-heavy pages and extract clean content.
"""

import asyncio
import hashlib
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import structlog

from ..shared.config import settings

logger = structlog.get_logger()


@dataclass
class CrawlResult:
    """Result of crawling a single URL."""
    url: str
    status_code: Optional[int]
    html_content: Optional[str]
    title: Optional[str]
    error: Optional[str]
    duration_ms: int
    headers: Dict[str, str]
    final_url: str  # In case of redirects


class PlaywrightCrawler:
    """Async web crawler using Playwright."""
    
    def __init__(
        self,
        max_concurrent: int = None,
        timeout_ms: int = None,
        navigation_timeout_ms: int = None,
        user_agent: str = None
    ):
        self.max_concurrent = max_concurrent or settings.max_concurrent_pages
        self.timeout_ms = timeout_ms or settings.page_timeout_ms
        self.navigation_timeout_ms = navigation_timeout_ms or settings.navigation_timeout_ms
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 "
            "ValueFabricBot/1.0"
        )
        
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._semaphore: Optional[asyncio.Semaphore] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
    
    async def start(self):
        """Initialize Playwright browser."""
        logger.info("Starting Playwright browser")
        self._playwright = await async_playwright().start()
        
        # Launch browser with security settings
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
            ]
        )
        
        # Create context with custom settings
        self._context = await self._browser.new_context(
            user_agent=self.user_agent,
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True,
            bypass_csp=True,
        )
        
        # Set default timeouts
        self._context.set_default_timeout(self.timeout_ms)
        self._context.set_default_navigation_timeout(self.navigation_timeout_ms)
        
        # Semaphore for concurrency control
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        
        logger.info("Playwright browser started successfully")
    
    async def stop(self):
        """Close Playwright browser."""
        logger.info("Stopping Playwright browser")
        
        if self._context:
            await self._context.close()
        
        if self._browser:
            await self._browser.close()
        
        if self._playwright:
            await self._playwright.stop()
        
        logger.info("Playwright browser stopped")
    
    async def crawl_url(
        self,
        url: str,
        wait_for_selector: Optional[str] = None,
        wait_for_timeout: int = 2000,
        scroll_page: bool = True
    ) -> CrawlResult:
        """Crawl a single URL and return the result.
        
        Args:
            url: URL to crawl
            wait_for_selector: Optional CSS selector to wait for
            wait_for_timeout: Time to wait after page load (ms)
            scroll_page: Whether to scroll to bottom to trigger lazy loading
            
        Returns:
            CrawlResult with HTML content and metadata
        """
        start_time = time.time()
        
        async with self._semaphore:
            page: Optional[Page] = None
            
            try:
                page = await self._context.new_page()
                
                # Block unnecessary resources
                await page.route(
                    "**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2,ttf}",
                    lambda route: route.abort()
                )
                
                # Navigate to URL
                response = await page.goto(
                    url,
                    wait_until='networkidle',
                    timeout=self.navigation_timeout_ms
                )
                
                # Wait for specific element if requested
                if wait_for_selector:
                    try:
                        await page.wait_for_selector(
                            wait_for_selector,
                            timeout=wait_for_timeout
                        )
                    except Exception as e:
                        logger.warning(
                            "Wait selector timeout",
                            url=url,
                            selector=wait_for_selector,
                            error=str(e)
                        )
                else:
                    # Default wait for dynamic content
                    await asyncio.sleep(wait_for_timeout / 1000)
                
                # Scroll to trigger lazy loading
                if scroll_page:
                    await self._scroll_page(page)
                
                # Get page content
                html_content = await page.content()
                title = await page.title()
                
                # Get final URL (after redirects)
                final_url = page.url
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                return CrawlResult(
                    url=url,
                    status_code=response.status if response else None,
                    html_content=html_content,
                    title=title,
                    error=None,
                    duration_ms=duration_ms,
                    headers=dict(response.headers) if response else {},
                    final_url=final_url
                )
                
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                logger.error(
                    "Crawl failed",
                    url=url,
                    error=str(e),
                    duration_ms=duration_ms
                )
                
                return CrawlResult(
                    url=url,
                    status_code=None,
                    html_content=None,
                    title=None,
                    error=str(e),
                    duration_ms=duration_ms,
                    headers={},
                    final_url=url
                )
                
            finally:
                if page:
                    await page.close()
    
    async def crawl_urls(
        self,
        urls: List[str],
        delay_seconds: float = None
    ) -> List[CrawlResult]:
        """Crawl multiple URLs with rate limiting.
        
        Args:
            urls: List of URLs to crawl
            delay_seconds: Delay between requests to same domain
            
        Returns:
            List of CrawlResult objects
        """
        results = []
        last_request_time: Dict[str, float] = {}
        
        for url in urls:
            domain = urlparse(url).netloc
            
            # Rate limiting
            if delay_seconds and domain in last_request_time:
                elapsed = time.time() - last_request_time[domain]
                if elapsed < delay_seconds:
                    wait_time = delay_seconds - elapsed
                    logger.debug(
                        "Rate limiting delay",
                        domain=domain,
                        wait_seconds=wait_time
                    )
                    await asyncio.sleep(wait_time)
            
            # Crawl the URL
            result = await self.crawl_url(url)
            results.append(result)
            
            last_request_time[domain] = time.time()
        
        return results
    
    async def _scroll_page(self, page: Page):
        """Scroll page to trigger lazy loading."""
        try:
            await page.evaluate("""
                async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 300;
                        const timer = setInterval(() => {
                            const scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;
                            
                            if (totalHeight >= scrollHeight) {
                                clearInterval(timer);
                                resolve();
                            }
                        }, 100);
                    });
                }
            """)
            # Small delay after scrolling
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning("Page scroll failed", error=str(e))
    
    async def extract_links(
        self,
        page: Page,
        base_url: str,
        same_domain_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Extract all links from a page.
        
        Args:
            page: Playwright page object
            base_url: Base URL for resolving relative links
            same_domain_only: Only return links from same domain
            
        Returns:
            List of link dictionaries with url, text, and is_external
        """
        base_domain = urlparse(base_url).netloc
        
        links = await page.evaluate("""
            () => Array.from(document.querySelectorAll('a[href]'))
                .map(a => ({
                    href: a.href,
                    text: a.textContent.trim(),
                    title: a.title
                }))
                .filter(a => a.href && !a.href.startsWith('javascript:') && !a.href.startsWith('#'))
        """)
        
        result = []
        for link in links:
            absolute_url = urljoin(base_url, link['href'])
            parsed = urlparse(absolute_url)
            
            # Skip non-HTTP(S) protocols
            if parsed.scheme not in ('http', 'https'):
                continue
            
            is_external = parsed.netloc != base_domain
            
            if same_domain_only and is_external:
                continue
            
            result.append({
                'url': absolute_url,
                'text': link['text'][:200],  # Limit text length
                'title': link.get('title', '')[:200],
                'is_external': is_external
            })
        
        return result
