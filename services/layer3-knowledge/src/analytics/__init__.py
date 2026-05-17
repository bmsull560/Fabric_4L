"""Analytics package initialization."""

# Import existing analytics components
from ..analytics.centrality import CentralityAnalyzer
from ..analytics.communities import CommunityDetector
from ..analytics.manager import (
    AggregationType,
    AnalyticsConfig,
    AnalyticsEvent,
    AnalyticsManager,
    AnalyticsQuery,
    AnalyticsResult,
    AnalyticsStore,
    DashboardConfig,
    DashboardType,
    MetricDefinition,
    MetricsCollector,
    MetricType,
    TimeGranularity,
    get_analytics_manager,
    initialize_analytics,
)
from ..analytics.similarity import SimilarityAnalyzer

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
