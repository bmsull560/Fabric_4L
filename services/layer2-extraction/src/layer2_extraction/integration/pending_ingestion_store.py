"""Compatibility re-export for pending ingestion persistence types and builders."""

from value_fabric.layer2.integration.pending_ingestion_store import (
    PendingIngestionRecord,
    PendingIngestionStore,
    PostgresPendingIngestionStore,
    SqlitePendingIngestionStore,
    build_pending_ingestion_store,
)

__all__ = [
    "PendingIngestionRecord",
    "PendingIngestionStore",
    "PostgresPendingIngestionStore",
    "SqlitePendingIngestionStore",
    "build_pending_ingestion_store",
]
