"""Semantic aligner for Layer 2 extraction."""

from __future__ import annotations

from typing import Any


class SemanticAligner:
    """Align extracted entities semantically."""

    def __init__(self) -> None:
        pass

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize an entity name for alignment."""
        return name.lower().strip()

    @staticmethod
    def alignment_cache_key(entity_type: str, name: str) -> str:
        """Generate a cache key for alignment."""
        return f"{entity_type}:{name.lower().strip()}"
