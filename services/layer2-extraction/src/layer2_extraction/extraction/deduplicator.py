"""Entity deduplicator for Layer 2 extraction."""

from __future__ import annotations

import math
from typing import Any

from layer2_extraction.models.ontology import OntologyEntity


class EntityDeduplicator:
    """Deduplicate entities using embedding similarity and clustering."""

    def __init__(self, similarity_threshold: float = 0.85) -> None:
        self.similarity_threshold = similarity_threshold

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def compute_similarity_matrix(
        self, entities: list[OntologyEntity]
    ) -> list[list[float]]:
        """Compute pairwise cosine similarity matrix for entity embeddings."""
        n = len(entities)
        matrix: list[list[float]] = [[0.0 for _ in range(n)] for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 1.0
                elif j < i:
                    matrix[i][j] = matrix[j][i]
                else:
                    emb_i = getattr(entities[i], "embedding", [])
                    emb_j = getattr(entities[j], "embedding", [])
                    if emb_i and emb_j:
                        matrix[i][j] = self._cosine_similarity(emb_i, emb_j)
                    else:
                        matrix[i][j] = 0.0
        return matrix

    def _find_clusters(self, similarity_matrix: Any) -> list[list[int]]:
        """Cluster entity indices based on similarity matrix using BFS."""
        import numpy as np

        matrix = np.array(similarity_matrix)
        n = matrix.shape[0]
        visited = [False] * n
        clusters: list[list[int]] = []

        for i in range(n):
            if visited[i]:
                continue
            cluster: list[int] = []
            queue = [i]
            visited[i] = True
            while queue:
                curr = queue.pop(0)
                cluster.append(curr)
                for j in range(n):
                    if not visited[j] and matrix[curr, j] >= self.similarity_threshold:
                        visited[j] = True
                        queue.append(j)
            clusters.append(cluster)
        return clusters

    def cluster(self, similarity_matrix: list[list[float]]) -> list[list[int]]:
        """Cluster entity indices based on similarity matrix using BFS."""
        return self._find_clusters(similarity_matrix)

    def _select_canonical(self, entities: list[OntologyEntity]) -> OntologyEntity:
        """Select the canonical entity from a cluster (highest confidence)."""
        return max(entities, key=lambda e: e.confidence)

    def _merge_entities(self, entities: list[OntologyEntity]) -> OntologyEntity:
        """Merge a cluster of entities into a single canonical entity."""
        canonical = self._select_canonical(entities)
        merged = canonical.model_copy(deep=True)
        # Merge source refs
        all_refs: list[str] = []
        for e in entities:
            all_refs.extend(e.source_refs)
        merged.source_refs = list(dict.fromkeys(all_refs))
        return merged

    def deduplicate(self, entities: list[OntologyEntity]) -> list[OntologyEntity]:
        """Deduplicate a list of entities."""
        if not entities:
            return []
        sim_matrix = self.compute_similarity_matrix(entities)
        clusters = self.cluster(sim_matrix)
        result: list[OntologyEntity] = []
        for cluster in clusters:
            cluster_entities = [entities[i] for i in cluster]
            merged = self._merge_entities(cluster_entities)
            result.append(merged)
        return result
