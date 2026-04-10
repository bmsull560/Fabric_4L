"""Integration layer for Layer 2 extraction pipeline.

Provides clients for connecting to downstream layers:
- Layer3KnowledgeClient: Push extraction results to Neo4j Knowledge Graph
"""

from .layer3_client import (
    IngestionResponse,
    IngestionStatus,
    Layer3KnowledgeClient,
    ingest_to_knowledge_graph,
)
from .pending_ingestion_store import (
    PendingIngestionStore,
    PendingIngestionRecord,
    PostgresPendingIngestionStore,
    SqlitePendingIngestionStore,
    build_pending_ingestion_store,
)

__all__ = [
    "IngestionResponse",
    "IngestionStatus",
    "Layer3KnowledgeClient",
    "ingest_to_knowledge_graph",
    "PendingIngestionStore",
    "PendingIngestionRecord",
    "PostgresPendingIngestionStore",
    "SqlitePendingIngestionStore",
    "build_pending_ingestion_store",
]
