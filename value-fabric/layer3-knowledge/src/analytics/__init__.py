"""Analytics package initialization."""

from .manager import (
    MetricType,
    AggregationType,
    TimeGranularity,
    DashboardType,
    AnalyticsEvent,
    MetricDefinition,
    AnalyticsQuery,
    AnalyticsResult,
    DashboardConfig,
    AnalyticsConfig,
    MetricsCollector,
    AnalyticsStore,
    AnalyticsManager,
    get_analytics_manager,
    initialize_analytics,
)

# Import existing analytics components
from .centrality import CentralityAnalyzer
from .communities import CommunityDetector
from .similarity import SimilarityAnalyzer

__all__ = [
    # Existing analytics components
    "CommunityDetector", 
    "CentralityAnalyzer", 
    "SimilarityAnalyzer",
    # New analytics system
    "MetricType",
    "AggregationType",
    "TimeGranularity",
    "DashboardType",
    "AnalyticsEvent",
    "MetricDefinition",
    "AnalyticsQuery",
    "AnalyticsResult",
    "DashboardConfig",
    "AnalyticsConfig",
    "MetricsCollector",
    "AnalyticsStore",
    "AnalyticsManager",
    "get_analytics_manager",
    "initialize_analytics",
]
