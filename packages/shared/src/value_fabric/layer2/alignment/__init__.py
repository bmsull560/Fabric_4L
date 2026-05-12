"""Semantic alignment for Layer 2 extraction."""

from __future__ import annotations

from typing import Any


class SemanticAligner:
    """Aligns extracted entities to a canonical ontology using string normalization."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    def _normalize_name(self, name: str) -> str:
        result = name.lower().strip().replace("-", " ").replace("  ", " ")
        # Remove common trailing suffixes
        for suffix in (" system", " platform", " service", " tool", " suite"):
            if result.endswith(suffix):
                result = result[: -len(suffix)]
                break
        return result.strip()

    def normalize_name(self, name: str) -> str:
        return self._normalize_name(name)

    def compute_cache_key(self, entity: Any) -> str:
        name = getattr(entity, "name", getattr(entity, "title", ""))
        return self._normalize_name(str(name))

    _compute_cache_key = compute_cache_key

    def align(self, entity: Any, ontology: Any | None = None) -> Any:
        return entity
