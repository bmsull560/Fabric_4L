"""Relationship types for the Value Fabric ontology.

Defines all valid relationships between entities with provenance tracking.
"""

from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class PredicateType(str, Enum):
    """Valid relationship predicates in the Value Fabric ontology."""

    # Core relationship types
    ENABLES = "enables"  # Capability → UseCase
    REQUIRES = "requires"  # UseCase → Capability
    BENEFITS = "benefits"  # UseCase → Persona
    DRIVES = "drives"  # Persona → ValueDriver
    CONTRIBUTES_TO = "contributes_to"  # Capability → ValueDriver
    DEPENDS_ON = "depends_on"  # Capability → Capability
    ALTERNATIVE_TO = "alternative_to"  # Capability → Capability

    # Extended relationship types from spec
    CAPABILITY_SUBTYPE_OF = "capability_subtype_of"  # Capability → Capability (hierarchy)
    CAPABILITY_REQUIRES_CAPABILITY = (
        "capability_requires_capability"  # Capability → Capability (dependency)
    )
    SEMANTICALLY_EQUIVALENT = "semantically_equivalent"  # Entity → Entity (coreference)
    IMPLEMENTS = "implements"  # Feature → Capability
    DELIVERS = "delivers"  # UseCase → ValueDriver
    INVOLVES = "involves"  # UseCase → Persona


class ImpactLevel(str, Enum):
    """Impact level for relationship strength."""

    TRANSFORMATIONAL = "transformational"
    SIGNIFICANT = "significant"
    MODERATE = "moderate"
    MINOR = "minor"
    # Legacy values for backward compatibility
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EnablementType(str, Enum):
    """Type of enablement relationship between Capability and UseCase.

    Aligned with pack ontology enablement_type property values.
    """

    REQUIRED = "required"  # Capability is required for the use case
    ENHANCES = "enhances"  # Capability improves the use case but isn't required
    OPTIONAL = "optional"  # Capability can be used but not essential


class BenefitType(str, Enum):
    """Type of benefit delivered to a persona.

    Aligned with pack ontology benefit_type property values.
    """

    TIME_SAVINGS = "time_savings"
    ERROR_REDUCTION = "error_reduction"
    VISIBILITY = "visibility"
    EFFICIENCY = "efficiency"


class DriverType(str, Enum):
    """Type of value driver relationship.

    Aligned with pack ontology driver_type property values.
    """

    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"


class Relationship(BaseModel):
    """A relationship between two entities in the Knowledge Graph.

    Relationships are directional and carry confidence scores and
    provenance metadata for auditability.

    Attributes:
        id: Unique identifier for this relationship
        source_id: UUID of the source entity
        raw_predicate: Original predicate as extracted from text (preserves extraction richness)
        canonical_predicate: Normalized predicate aligned with ontology (enables, benefits, etc.)
        target_id: UUID of the target entity
        confidence: LLM confidence score (0.0-1.0)
        evidence_text: Direct quote from source supporting this relationship
        source_url: URL where this relationship was extracted
        impact_level: Business impact classification
        strength: Numerical relationship strength (0.0-1.0)
        enablement_type: Type of enablement (REQUIRED, ENHANCES, OPTIONAL) for ENABLES relationships
        benefit_type: Type of benefit (TIME_SAVINGS, ERROR_REDUCTION, etc.) for BENEFITS relationships
        driver_type: Type of driver (PRIMARY, SECONDARY, TERTIARY) for DRIVES relationships
        contribution_weight: Numerical weight (0.0-1.0) for contribution relationships
        influence_weight: Numerical weight (0.0-1.0) for influence relationships
        extracted_at: Timestamp of extraction
        extraction_job_id: Reference to extraction job
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: str = Field(..., description="UUID of source entity")
    raw_predicate: str = Field(..., description="Original predicate as extracted from text")
    canonical_predicate: PredicateType = Field(..., description="Normalized predicate aligned with ontology")
    target_id: str = Field(..., description="UUID of target entity")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_text: str = Field(..., min_length=1)
    source_url: str = Field(...)
    impact_level: ImpactLevel | None = None
    strength: float | None = Field(default=None, ge=0.0, le=1.0)
    enablement_type: EnablementType | None = None
    benefit_type: BenefitType | None = None
    driver_type: DriverType | None = None
    contribution_weight: float | None = Field(default=None, ge=0.0, le=1.0)
    influence_weight: float | None = Field(default=None, ge=0.0, le=1.0)
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    extraction_job_id: str | None = None

    @field_validator("source_id", "target_id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        """Validate that ID is a valid UUID."""
        try:
            from uuid import UUID

            UUID(v)
        except ValueError:
            raise ValueError(f"Invalid UUID: {v}")
        return v

    @field_validator("evidence_text")
    @classmethod
    def validate_evidence(cls, v: str) -> str:
        """Ensure evidence text is meaningful (not empty/whitespace)."""
        stripped = v.strip()
        if len(stripped) < 5:
            raise ValueError("Evidence text must be at least 5 characters")
        return stripped

    def get_inverse(self) -> "Relationship | None":
        """Create inverse relationship (if applicable).

        Not all relationships have meaningful inverses.
        Returns None if no inverse exists for this predicate type.
        """
        inverse_predicates = {
            PredicateType.ENABLES: PredicateType.REQUIRES,
            PredicateType.REQUIRES: PredicateType.ENABLES,
            PredicateType.CAPABILITY_REQUIRES_CAPABILITY: PredicateType.DEPENDS_ON,
            PredicateType.DEPENDS_ON: PredicateType.CAPABILITY_REQUIRES_CAPABILITY,
            PredicateType.IMPLEMENTS: PredicateType.ENABLES,  # Feature implements Capability
        }

        if self.canonical_predicate in inverse_predicates:
            return Relationship(
                source_id=self.target_id,
                raw_predicate=f"inverse_of_{self.raw_predicate}",
                canonical_predicate=inverse_predicates[self.canonical_predicate],
                target_id=self.source_id,
                confidence=self.confidence,
                evidence_text=f"Inverse of: {self.evidence_text}",
                source_url=self.source_url,
                impact_level=self.impact_level,
                strength=self.strength,
                extraction_job_id=self.extraction_job_id,
            )
        return None

    model_config = {"extra": "forbid"}


class RelationshipGraph(BaseModel):
    """Container for all relationships in an extraction result."""

    relationships: list[Relationship] = Field(default_factory=list)

    def add_relationship(self, rel: Relationship) -> None:
        """Add a relationship if it doesn't already exist."""
        if not self.has_relationship(rel.source_id, rel.canonical_predicate, rel.target_id):
            self.relationships.append(rel)

    def has_relationship(self, source_id: str, predicate: PredicateType, target_id: str) -> bool:
        """Check if a specific relationship already exists."""
        for rel in self.relationships:
            if (
                rel.source_id == source_id
                and rel.canonical_predicate == predicate
                and rel.target_id == target_id
            ):
                return True
        return False

    def get_outgoing(self, entity_id: str) -> list[Relationship]:
        """Get all relationships where entity is the source."""
        return [r for r in self.relationships if r.source_id == entity_id]

    def get_incoming(self, entity_id: str) -> list[Relationship]:
        """Get all relationships where entity is the target."""
        return [r for r in self.relationships if r.target_id == entity_id]

    def get_by_predicate(self, predicate: PredicateType) -> list[Relationship]:
        """Get all relationships of a specific type."""
        return [r for r in self.relationships if r.canonical_predicate == predicate]

    model_config = {"extra": "forbid"}
