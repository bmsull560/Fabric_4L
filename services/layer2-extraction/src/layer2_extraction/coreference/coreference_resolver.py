"""Coreference resolver for Layer 2 extraction."""

from __future__ import annotations

from typing import Any


class CoreferenceResolver:
    """Resolve coreferences in extracted entities."""

    def __init__(self) -> None:
        pass

    def resolve(self, entities: list[Any]) -> list[Any]:
        """Resolve coreferences in a list of entities."""
        return entities

    def are_semantically_equivalent(self, entity1: Any, entity2: Any) -> bool:
        """Check if two entities are semantically equivalent."""
        return False
