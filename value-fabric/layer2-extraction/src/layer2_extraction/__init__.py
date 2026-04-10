"""Layer 2 Extraction package for Value Fabric.

Ontology-guided entity and relationship extraction pipeline.
"""

__version__ = "1.0.0"

# Models - these have no side effects
from layer2_extraction.models import (
    Capability,
    UseCase,
    Persona,
    ValueDriver,
    Feature,
    RoleType,
    ValueCategory,
    ExtractionResult,
    Relationship,
    RelationshipGraph,
    PredicateType,
    ImpactLevel,
    ExtractionCost,
    JobCostSummary,
)

__all__ = [
    "__version__",
    # Models
    "Capability",
    "UseCase",
    "Persona",
    "ValueDriver",
    "Feature",
    "RoleType",
    "ValueCategory",
    "ExtractionResult",
    "Relationship",
    "RelationshipGraph",
    "PredicateType",
    "ImpactLevel",
    "ExtractionCost",
    "JobCostSummary",
]
