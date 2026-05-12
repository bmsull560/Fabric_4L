"""Relationship models for Layer 2 extraction."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PredicateType(str, Enum):
    ENABLES = "enables"
    REQUIRES = "requires"
    PRODUCES = "produces"
    MEASURES = "measures"
    DEPENDS_ON = "depends_on"
    PART_OF = "part_of"
    ASSOCIATED_WITH = "associated_with"
    BENEFITS = "benefits"
    DRIVES = "drives"
    ALTERNATIVE_TO = "alternative_to"
    IMPLEMENTS = "implements"
    CAPABILITY_SUBTYPE_OF = "capability_subtype_of"


class Relationship(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = ""
    subject_id: str = ""
    predicate: PredicateType = PredicateType.ASSOCIATED_WITH
    object_id: str = ""
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    provenance: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)

    # Alias fields for test compatibility
    source_id: str = ""
    target_id: str = ""
    raw_predicate: str = ""
    canonical_predicate: PredicateType = PredicateType.ASSOCIATED_WITH
    evidence_text: str = ""
    source_url: str = ""
    extraction_job_id: str = ""

    @model_validator(mode="after")
    def _sync_alias_fields(self) -> "Relationship":
        if self.source_id and not self.subject_id:
            self.subject_id = self.source_id
        if self.target_id and not self.object_id:
            self.object_id = self.target_id
        if self.canonical_predicate and not self.predicate:
            self.predicate = self.canonical_predicate
        if self.subject_id and not self.source_id:
            self.source_id = self.subject_id
        if self.object_id and not self.target_id:
            self.target_id = self.object_id
        if self.predicate and not self.canonical_predicate:
            self.canonical_predicate = self.predicate
        return self

    def get_inverse(self) -> Relationship:
        return self.inverse()

    def inverse(self) -> Relationship:
        inverse_pred = {
            PredicateType.ENABLES: PredicateType.DEPENDS_ON,
            PredicateType.REQUIRES: PredicateType.ENABLES,
            PredicateType.DEPENDS_ON: PredicateType.ENABLES,
        }.get(self.predicate, self.predicate)
        return Relationship(
            id=f"{self.id}_inv" if self.id else "",
            subject_id=self.object_id,
            predicate=inverse_pred,
            object_id=self.subject_id,
            confidence=self.confidence,
            provenance=self.provenance,
            attributes=self.attributes.copy(),
            source_id=self.object_id,
            target_id=self.subject_id,
            canonical_predicate=inverse_pred,
        )

    @model_validator(mode="after")
    def _validate_relationship(self) -> "Relationship":
        if self.subject_id and self.object_id and self.subject_id == self.object_id:
            raise ValueError("subject_id and object_id cannot be the same")
        return self


class RelationshipGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationships: list[Relationship] = Field(default_factory=list)

    def add(self, rel: Relationship) -> None:
        self.relationships.append(rel)

    def get_by_subject(self, subject_id: str) -> list[Relationship]:
        return [r for r in self.relationships if r.subject_id == subject_id]

    def get_by_object(self, object_id: str) -> list[Relationship]:
        return [r for r in self.relationships if r.object_id == object_id]

    def get_by_predicate(self, predicate: PredicateType) -> list[Relationship]:
        return [r for r in self.relationships if r.predicate == predicate]

    def to_dict(self) -> dict[str, Any]:
        return {"relationships": [r.model_dump() for r in self.relationships]}
