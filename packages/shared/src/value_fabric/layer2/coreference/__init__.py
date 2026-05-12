"""Coreference resolution for Layer 2 extraction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Cluster:
    member_entity_ids: list[str]
    canonical_entity: Any


class CoreferenceResolver:
    """Resolves coreferent entities using simple union-find clustering."""

    def __init__(self, threshold: float = 0.85) -> None:
        self.threshold = threshold

    def resolve_coreferences(self, entities: list[Any], relationships: list[Any] | None = None) -> list[Cluster]:
        """Cluster entities that refer to the same real-world object."""
        if not entities:
            return []

        entity_index = {getattr(e, "id", None): i for i, e in enumerate(entities) if getattr(e, "id", None)}
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

        # Union-find by name similarity
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                if _name_similarity(entities[i], entities[j]) >= self.threshold:
                    union(i, j)

        # Union-find by semantically_equivalent relationships
        for rel in relationships or []:
            pred = getattr(rel, "canonical_predicate", None) or getattr(rel, "predicate", None)
            if getattr(pred, "value", str(pred)) == "semantically_equivalent":
                src = getattr(rel, "source_id", None)
                tgt = getattr(rel, "target_id", None)
                if src in entity_index and tgt in entity_index:
                    union(entity_index[src], entity_index[tgt])

        clusters: dict[int, list[int]] = {}
        for i in range(len(entities)):
            root = find(i)
            clusters.setdefault(root, []).append(i)

        result: list[Cluster] = []
        for indices in clusters.values():
            canonical = entities[indices[0]]
            for idx in indices[1:]:
                other = entities[idx]
                for field in ("name", "title", "description"):
                    val = getattr(other, field, None)
                    if val and len(str(val)) > len(str(getattr(canonical, field, ""))):
                        setattr(canonical, field, val)
            result.append(
                Cluster(
                    member_entity_ids=[getattr(entities[i], "id", "") for i in indices],
                    canonical_entity=canonical,
                )
            )
        return result
