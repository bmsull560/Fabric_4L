"""Coreference resolution for Layer 2 extraction."""

from __future__ import annotations

from typing import Any


class CoreferenceResolver:
    """Resolves coreferent entities using simple union-find clustering."""

    def __init__(self, threshold: float = 0.85) -> None:
        self.threshold = threshold

    def resolve_coreferences(self, entities: list[Any]) -> list[Any]:
        """Cluster entities that refer to the same real-world object."""
        if not entities:
            return []

        parent = list(range(len(entities)))

        def find(i: int) -> int:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        def union(i: int, j: int) -> None:
            ri, rj = find(i), find(j)
            if ri != rj:
                parent[ri] = rj

        def _name_similarity(a: Any, b: Any) -> float:
            name_a = getattr(a, "name", getattr(a, "title", "")).lower()
            name_b = getattr(b, "name", getattr(b, "title", "")).lower()
            if name_a == name_b:
                return 1.0
            if name_a in name_b or name_b in name_a:
                return 0.9
            return 0.0

        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                if _name_similarity(entities[i], entities[j]) >= self.threshold:
                    union(i, j)

        clusters: dict[int, list[int]] = {}
        for i in range(len(entities)):
            root = find(i)
            clusters.setdefault(root, []).append(i)

        result: list[Any] = []
        for indices in clusters.values():
            canonical = entities[indices[0]]
            for idx in indices[1:]:
                other = entities[idx]
                for field in ("name", "title", "description"):
                    val = getattr(other, field, None)
                    if val and len(str(val)) > len(str(getattr(canonical, field, ""))):
                        setattr(canonical, field, val)
            result.append(canonical)
        return result
