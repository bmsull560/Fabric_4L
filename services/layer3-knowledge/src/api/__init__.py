"""API module for Layer 3 Knowledge Graph."""

# Dependencies and app require a full runtime environment (neo4j, agents, etc.)
# Wrap in try/except so that lightweight submodules (e.g. pack_loader) remain
# importable in test and CI environments without a running database.
try:
    from api.dependencies import (
        AppState,
        get_app_state,
        get_centrality_analyzer,
        get_community_detector,
        get_graph_rag,
        get_hybrid_search,
        get_neo4j_driver,
        get_schema_initializer,
        get_settings_from_state,
        get_similarity_analyzer,
        get_sync_manager,
        get_vector_store,
    )
    from api.main import app
    from api.models import (
        CentralityRequest,
        CentralityResponse,
        CommunityDetectionRequest,
        CommunityDetectionResponse,
        EntityComparisonRequest,
        EntityComparisonResponse,
        EntityContextResponse,
        GraphNodeWithLayout,
        GraphRAGQuery,
        GraphRAGResponse,
        HealthResponse,
        IngestRequest,
        IngestResponse,
        SchemaStatistics,
        SchemaStatus,
        SearchRequest,
        SearchResponse,
        SimilarityRequest,
        SimilarityResponse,
        SyncStatusResponse,
        ValueTreeResponse,
    )
    _RUNTIME_AVAILABLE = True
except (ImportError, Exception):
    _RUNTIME_AVAILABLE = False
    # Provide None stubs so callers can check _RUNTIME_AVAILABLE
    app = None

__all__ = [
    "app",
    "_RUNTIME_AVAILABLE",
    "AppState",
    "get_app_state",
    "get_centrality_analyzer",
    "get_community_detector",
    "get_graph_rag",
    "get_hybrid_search",
    "get_neo4j_driver",
    "get_schema_initializer",
    "get_settings_from_state",
    "get_similarity_analyzer",
    "get_sync_manager",
    "get_vector_store",
    # Models
    "CentralityRequest",
    "CentralityResponse",
    "CommunityDetectionRequest",
    "CommunityDetectionResponse",
    "EntityComparisonRequest",
    "EntityComparisonResponse",
    "EntityContextResponse",
    "GraphNodeWithLayout",
    "GraphRAGQuery",
    "GraphRAGResponse",
    "HealthResponse",
    "IngestRequest",
    "IngestResponse",
    "SchemaStatistics",
    "SchemaStatus",
    "SearchRequest",
    "SearchResponse",
    "SimilarityRequest",
    "SimilarityResponse",
    "SyncStatusResponse",
    "ValueTreeResponse",
]
