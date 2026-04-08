"""Integration clients for Layer 4 to communicate with other layers.

Provides hybrid integration approach where L4 agents orchestrate
L1 (Ingestion) and L2 (Extraction) via API calls.
"""

from .layer1_client import Layer1IngestionClient
from .layer2_client import Layer2ExtractionClient

__all__ = [
    "Layer1IngestionClient",
    "Layer2ExtractionClient",
]
