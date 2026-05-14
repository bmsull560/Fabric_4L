"""Coreference resolution for Layer 2 entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..models.relationships import PredicateType, Relationship


@dataclass
class CoreferenceCluster:
    member_entity_ids: list[str] = field(default_factory=list)


class CoreferenceResolver:
    """Resolve coreferences between entities using name matching and relationships."""

    def resolve_coreferences(
        self, entities: list[Any], relationships: list[Relationship]
    ) -> list[CoreferenceCluster]:
        if not entities:
            return []

        # Build union-find structure
        parent: dict[str, str] = {}

        def find(x: str) -> str:
            if x not in parent:
                parent[x] = x
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x: str, y: str) -> None:
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # Initialize all entity IDs
        for e in entities:
            eid = getattr(e, "id", "")
            if eid:
                parent[eid] = eid

        # Index entities by normalized name
        name_index: dict[str, list[str]] = {}
        for e in entities:
            name = getattr(e, "name", "")
            eid = getattr(e, "id", "")
            if name and eid:
                norm = self._normalize(name)
                name_index.setdefault(norm, []).append(eid)

        # Union exact name matches (case-insensitive)
        for eids in name_index.values():
            first = eids[0]
            for other in eids[1:]:
                union(first, other)

        # Union SEMANTICALLY_EQUIVALENT relationships
        for rel in relationships:
            if rel.canonical_predicate == PredicateType.SEMANTICALLY_EQUIVALENT:
                if rel.source_id and rel.target_id:
                    union(rel.source_id, rel.target_id)

        # Build clusters
        clusters: dict[str, list[str]] = {}
        for e in entities:
            eid = getattr(e, "id", "")
            if eid:
                root = find(eid)
                clusters.setdefault(root, []).append(eid)

        return [CoreferenceCluster(member_entity_ids=members) for members in clusters.values()]

    @staticmethod
    def _normalize(name: str) -> str:
        return " ".join(name.lower().split())
