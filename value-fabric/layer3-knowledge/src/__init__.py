"""Layer 3: Knowledge Graph & Semantic Layer for Value Fabric Platform."""

from .analytics import CentralityAnalyzer, CommunityDetector, SimilarityAnalyzer
from .api import app
from .config import Settings, get_settings
from .ingestion import Neo4jLoader, RDFLoadError, SyncConflictError, SyncManager
from .retrieval import (
    GraphRAGEngine,
    GraphRAGResult,
    HybridSearch,
    HybridSearchResult,
    VectorStore,
    VectorStoreError,
)
from .schema import (
    Constraint,
    Index,
    SchemaInitializer,
    get_all_constraints,
    get_all_indexes,
)

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
]
