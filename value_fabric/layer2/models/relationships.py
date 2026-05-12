"""Relationship models for Layer 2 extraction."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PredicateType(str, Enum):
    """Canonical relationship predicate types."""

    ENABLES = "enables"
    REQUIRES = "requires"
    INVOLVES = "involves"
    DELIVERS = "delivers"
    IMPLEMENTED_BY = "implemented_by"
    MEASURED_BY = "measured_by"
    MAPS_TO_APQC = "maps_to_apqc"
    BENEFITS = "benefits"
    DRIVES = "drives"
    DEPENDS_ON = "depends_on"
    ALTERNATIVE_TO = "alternative_to"
    CAPABILITY_SUBTYPE_OF = "capability_subtype_of"
    SEMANTICALLY_EQUIVALENT = "semantically_equivalent"


class Relationship(BaseModel):
    """Entity relationship with evidence and confidence."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    target_id: str
    raw_predicate: str
    canonical_predicate: PredicateType
    evidence_text: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source_url: str = ""
    impact_level: Any = None
    strength: float | None = None
    enablement_type: Any = None
    contribution_weight: float | None = None
    extraction_job_id: str | None = None

    @field_validator("source_id", "target_id")
    @classmethod
    def _validate_uuid(cls, v: str) -> str:
        from uuid import UUID
        try:
            UUID(v)
        except ValueError:
            raise ValueError(f"Invalid UUID format: {v}")
        return v

    def get_inverse(self) -> Relationship | None:
        """Return the inverse relationship if one is defined."""
        inverse_map = {
            PredicateType.ENABLES: PredicateType.REQUIRES,
            PredicateType.REQUIRES: PredicateType.ENABLES,
            PredicateType.INVOLVES: None,
            PredicateType.DELIVERS: None,
            PredicateType.IMPLEMENTED_BY: None,
            PredicateType.MEASURED_BY: None,
            PredicateType.MAPS_TO_APQC: None,
            PredicateType.BENEFITS: None,
            PredicateType.DRIVES: None,
            PredicateType.DEPENDS_ON: None,
            PredicateType.ALTERNATIVE_TO: PredicateType.ALTERNATIVE_TO,
            PredicateType.CAPABILITY_SUBTYPE_OF: None,
            PredicateType.SEMANTICALLY_EQUIVALENT: PredicateType.SEMANTICALLY_EQUIVALENT,
        }
        inverse = inverse_map.get(self.canonical_predicate)
        if inverse is None:
            return None
        return Relationship(
            source_id=self.target_id,
            target_id=self.source_id,
            raw_predicate=f"inverse of {self.raw_predicate}",
            canonical_predicate=inverse,
            evidence_text=self.evidence_text,
            confidence=self.confidence,
            source_url=self.source_url,
        )


class RelationshipGraph:
    """In-memory graph of relationships."""

    def __init__(self) -> None:
        self.relationships: list[Relationship] = []
        self._index: dict[str, list[Relationship]] = {}

    def add_relationship(self, rel: Relationship) -> None:
        """Add a relationship if not already present."""
        for existing in self.relationships:
            if (
                existing.source_id == rel.source_id
                and existing.target_id == rel.target_id
                and existing.canonical_predicate == rel.canonical_predicate
            ):
                return
        self.relationships.append(rel)
        self._index.setdefault(rel.source_id, []).append(rel)

    def get_outgoing(self, entity_id: str) -> list[Relationship]:
        """Get all outgoing relationships for an entity."""
        return [r for r in self.relationships if r.source_id == entity_id]

    def get_incoming(self, entity_id: str) -> list[Relationship]:
        """Get all incoming relationships for an entity."""
        return [r for r in self.relationships if r.target_id == entity_id]
