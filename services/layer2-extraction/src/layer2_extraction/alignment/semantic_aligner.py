"""Semantic alignment utilities for Layer 2 entities."""

from __future__ import annotations

import hashlib
import re
from typing import Any


class SemanticAligner:
    """Align and normalize entity names for comparison."""

    _STOP_WORDS = frozenset(
        {
            "a", "an", "the", "and", "or", "of", "in", "on", "at", "to", "for",
            "with", "by", "from", "as", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "shall", "can", "need",
            "dare", "ought", "used", "system", "platform", "solution", "tool",
            "application", "app", "software", "service", "module", "component",
        }
    )

    def _compute_cache_key(self, entity: Any) -> str:
        """Generate a deterministic cache key for an entity."""
        name = getattr(entity, "name", "")
        desc = getattr(entity, "description", "")
        payload = f"{type(entity).__name__}:{name}:{desc}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _normalize_name(self, name: str) -> str:
        """Normalize a name by lowercasing, removing punctuation, and dropping stop words."""
        lowered = name.lower()
        # Replace hyphens with spaces
        cleaned = lowered.replace("-", " ")
        # Remove non-alphanumeric except spaces
        cleaned = re.sub(r"[^a-z0-9\s]", "", cleaned)
        tokens = cleaned.split()
        filtered = [t for t in tokens if t not in self._STOP_WORDS]
        return " ".join(filtered)
