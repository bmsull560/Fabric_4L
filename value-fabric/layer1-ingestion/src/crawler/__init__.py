"""Crawler package for web scraping.

Exports:
- PlaywrightCrawler: Main crawler with OpenTelemetry tracing
- CrawlerConfig: Configuration dataclass with YAML support
- CrawlResult: Result dataclass with metrics
"""

from .playwright_crawler import PlaywrightCrawler, CrawlResult
from .crawler_config import CrawlerConfig, load_config
from .telemetry import init_telemetry, CrawlMetrics

__all__ = [
    "PlaywrightCrawler",
    "CrawlResult",
    "CrawlerConfig",
    "load_config",
    "init_telemetry",
    "CrawlMetrics",
]
