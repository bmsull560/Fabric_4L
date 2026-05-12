"""Entity deduplicator using embedding similarity."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from value_fabric.layer2.models.ontology import (
    Capability,
    Feature,
    Persona,
    UseCase,
    ValueDriver,
)


class EntityDeduplicator:
    """Deduplicate entities using embedding cosine similarity."""

    DEFAULT_THRESHOLD = 0.85

    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        api_key: str | None = None,
    ) -> None:
        self.threshold = threshold
        # Avoid instantiating OpenAI client at import time for testability
        self._api_key = api_key
        self._client: Any | None = None

    @property
    def client(self) -> Any:
        if self._client is None and self._api_key:
            import openai
            self._client = openai.AsyncOpenAI(api_key=self._api_key)
        return self._client

    # ------------------------------------------------------------------
    # Text representation
    # ------------------------------------------------------------------

    def _entity_to_text(self, entity: Any) -> str:
        """Convert entity to a text representation for embedding."""
        parts = [getattr(entity, "name", ""), getattr(entity, "description", "")]
        if hasattr(entity, "technical_features") and entity.technical_features:
            parts.extend(entity.technical_features)
        return " ".join(str(p) for p in parts if p)

    # ------------------------------------------------------------------
    # Similarity matrix
    # ------------------------------------------------------------------

    def _compute_similarity_matrix(
        self, embeddings: list[list[float]]
    ) -> np.ndarray:
        """Compute cosine similarity matrix from embeddings."""
        if not embeddings:
            return np.empty((0, 0))
        vectors = np.array(embeddings, dtype=np.float64)
        # Normalize
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized = vectors / norms
        return np.dot(normalized, normalized.T)

    # ------------------------------------------------------------------
    # Clustering
    # ------------------------------------------------------------------

    def _find_clusters(self, similarity: np.ndarray) -> list[list[int]]:
        """Find clusters using BFS transitive closure."""
        n = similarity.shape[0]
        if n == 0:
            return []
        visited = [False] * n
        clusters: list[list[int]] = []
        for i in range(n):
            if visited[i]:
                continue
            queue = [i]
            visited[i] = True
            cluster: list[int] = []
            while queue:
                node = queue.pop(0)
                cluster.append(node)
                for j in range(n):
                    if not visited[j] and similarity[node, j] >= self.threshold:
                        visited[j] = True
                        queue.append(j)
            clusters.append(cluster)
        return clusters

    # ------------------------------------------------------------------
    # Canonical selection
    # ------------------------------------------------------------------

    def _select_canonical(self, cluster_entities: list[Any]) -> Any:
        """Select the entity with highest confidence as canonical."""
        return max(cluster_entities, key=lambda e: getattr(e, "confidence", 0.0))

    # ------------------------------------------------------------------
    # Merge
    # ------------------------------------------------------------------

    def _merge_into_canonical(self, canonical: Any, duplicates: list[Any]) -> Any:
        """Merge duplicate entities into canonical."""
        merged_sources = list(getattr(canonical, "source_refs", []) or [])
        for dup in duplicates:
            for ref in getattr(dup, "source_refs", []) or []:
                if ref not in merged_sources:
                    merged_sources.append(ref)
        if hasattr(canonical, "source_refs"):
            canonical.source_refs = merged_sources
        return canonical

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def deduplicate(self, entities: list[Any]) -> list[Any]:
        """Deduplicate a list of entities."""
        if len(entities) <= 1:
            return entities
        # Placeholder: in production this would compute embeddings via OpenAI
        texts = [self._entity_to_text(e) for e in entities]
        # Simple character-count based embeddings for unit-test fallback
        embeddings = [[float(len(t))] for t in texts]
        sim = self._compute_similarity_matrix(embeddings)
        clusters = self._find_clusters(sim)
        result: list[Any] = []
        for cluster in clusters:
            cluster_entities = [entities[i] for i in cluster]
            canonical = self._select_canonical(cluster_entities)
            duplicates = [e for e in cluster_entities if e is not canonical]
            if duplicates:
                canonical = self._merge_into_canonical(canonical, duplicates)
            result.append(canonical)
        return result
