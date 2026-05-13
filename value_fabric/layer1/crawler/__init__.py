"""Canonical Layer 1 crawler import surface.

Runtime callers should import crawler modules through ``value_fabric.layer1``.
Concrete implementations still resolve via the Layer 1 package path shim until
the remaining service-local modules are migrated.
"""

from __future__ import annotations

from pathlib import Path

_repo_root = Path(__file__).resolve().parents[3]
_compatibility_path = str(_repo_root / "services" / "layer1-ingestion" / "src" / "crawler")

if _compatibility_path not in __path__:
    __path__.append(_compatibility_path)

from .decision_store import CrawlDecisionRecord, CrawlDecisionRepository, FallbackStats, RouterQualityReport
from .httpx_crawler import FastPathResult, HttpxCrawler, HttpxCrawlerConfig, SSRFProtectionError
from .playwright_crawler import CrawlResult, PlaywrightCrawler
from .quality_gate import AdaptiveQualityGate, QualityGate, QualityThresholds
from .smart_router import QualityDecision, RouteType, RoutingDecision, SmartRouter

__all__ = [
    "AdaptiveQualityGate",
    "CrawlDecisionRecord",
    "CrawlDecisionRepository",
    "CrawlResult",
    "FallbackStats",
    "FastPathResult",
    "HttpxCrawler",
    "HttpxCrawlerConfig",
    "PlaywrightCrawler",
    "QualityDecision",
    "QualityGate",
    "QualityThresholds",
    "RouteType",
    "RouterQualityReport",
    "RoutingDecision",
    "SSRFProtectionError",
    "SmartRouter",
]
