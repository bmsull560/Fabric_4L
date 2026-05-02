"""Integration layer for Layer 2 extraction pipeline.

Provides clients for connecting to downstream layers:
- Layer3KnowledgeClient: Push extraction results to Neo4j Knowledge Graph
- ModelRegistryClient: Resolve LLM models from Layer 4 Model Registry
"""

from .layer3_client import (
    IngestionResponse,
    IngestionStatus,
    Layer3KnowledgeClient,
    ingest_to_knowledge_graph,
)
from .model_registry_client import ModelRegistryClient
from .pending_ingestion_store import (
    PendingIngestionRecord,
    PendingIngestionStore,
    PostgresPendingIngestionStore,
    SqlitePendingIngestionStore,
    build_pending_ingestion_store,
)

__all__ = [
    "IngestionResponse",
    "IngestionStatus",
    "Layer3KnowledgeClient",
    "ingest_to_knowledge_graph",
    "ModelRegistryClient",
    "PendingIngestionStore",
    "PendingIngestionRecord",
    "PostgresPendingIngestionStore",
    "SqlitePendingIngestionStore",
    "build_pending_ingestion_store",
]
