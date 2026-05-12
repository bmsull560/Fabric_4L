"""Layer 3: Knowledge Graph & Semantic Layer for Value Fabric Platform."""

from .api import app
from .config import Settings, get_settings
from .services import (
    EvidenceSearchService,
    QuantificationResult,
    SignalPersistenceService,
    SignalQuantificationService,
)

try:  # Optional runtime deps (e.g. neo4j) may be absent in static contract test jobs.
    from .schema import (
        Constraint,
        Index,
        SchemaInitializer,
        get_all_constraints,
        get_all_indexes,
    )
    from .analytics import CentralityAnalyzer, CommunityDetector, SimilarityAnalyzer
    from .ingestion import Neo4jLoader, RDFLoadError, SyncConflictError, SyncManager
    from .retrieval import (
        GraphRAGEngine,
        GraphRAGResult,
        HybridSearch,
        HybridSearchResult,
        VectorStore,
        VectorStoreError,
    )
except ModuleNotFoundError:  # pragma: no cover - exercised in dependency-minimal CI collection
    Constraint = Index = SchemaInitializer = None
    get_all_constraints = get_all_indexes = None
    CentralityAnalyzer = CommunityDetector = SimilarityAnalyzer = None
    Neo4jLoader = RDFLoadError = SyncConflictError = SyncManager = None
    GraphRAGEngine = GraphRAGResult = HybridSearch = HybridSearchResult = None
    VectorStore = VectorStoreError = None

__version__ = "0.1.0"

__all__ = [
    # App
    "app",
    # Config
    "Settings",
    "get_settings",
    # Ingestion
    "Neo4jLoader",
    "RDFLoadError",
    "SyncManager",
    "SyncConflictError",
    # Schema
    "Constraint",
    "Index",
    "SchemaInitializer",
    "get_all_constraints",
    "get_all_indexes",
    # Retrieval
    "GraphRAGEngine",
    "GraphRAGResult",
    "HybridSearch",
    "HybridSearchResult",
    "VectorStore",
    "VectorStoreError",
    # Analytics
    "CentralityAnalyzer",
    "CommunityDetector",
    "SimilarityAnalyzer",
    # Signal Services (Phase 3)
    "SignalPersistenceService",
    "SignalQuantificationService",
    "EvidenceSearchService",
    "QuantificationResult",
]
