"""Crawler package for web scraping with hybrid HTTPX/Browser routing.

Components:
- PlaywrightCrawler: Browser-based crawling (existing)
- HttpxCrawler: Fast HTTP-only crawling (new)
- SmartRouter: Per-URL routing decisions (new)
- QualityGate: Fast path validation (new)
- ExecutionLogger: Path and metrics logging (new)

Usage:
    from src.crawler.playwright_crawler import PlaywrightCrawler
    from src.crawler.httpx_crawler import HttpxCrawler
    from src.crawler.smart_router import SmartRouter, RouteType
    from src.crawler.quality_gate import QualityGate
    from src.crawler.execution_logger import ExecutionLogger
    from src.crawler.telemetry import ExecutionMetrics

Note: Use direct submodule imports to avoid relative import issues in tests.
"""

# Exports removed to prevent relative import errors when imported directly.
# Import from submodules directly as shown above.
