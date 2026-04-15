"""Structured output response models for LLM extraction.

These models define the exact schema expected from structured output LLM calls.
They wrap the ontology models for use with OpenAI's structured outputs API.
"""

from pydantic import BaseModel, Field

from .ontology import Capability, Feature, Persona, UseCase, ValueDriver
from .relationships import Relationship


class CapabilityExtractionResponse(BaseModel):
    """Structured response for capability extraction.

    Expected as response_format parameter to OpenAI structured output API.
    """

    capabilities: list[Capability] = Field(
        default_factory=list,
        description="Extracted product/technical capabilities from the source text. "
        "Include confidence scores (0.0-1.0) and source evidence for each.",
    )


class UseCaseExtractionResponse(BaseModel):
    """Structured response for use case extraction.

    Expected as response_format parameter to OpenAI structured output API.
    """

    use_cases: list[UseCase] = Field(
        default_factory=list,
        description="Extracted business use cases from the source text. "
        "Include workflow steps, KPIs, and industry context where available.",
    )


class PersonaExtractionResponse(BaseModel):
    """Structured response for persona extraction.

    Expected as response_format parameter to OpenAI structured output API.
    """

    personas: list[Persona] = Field(
        default_factory=list,
        description="Extracted stakeholder personas from the source text. "
        "Include role types, pain points, and success metrics.",
    )


class ValueDriverExtractionResponse(BaseModel):
    """Structured response for value driver extraction.

    Expected as response_format parameter to OpenAI structured output API.
    """

    value_drivers: list[ValueDriver] = Field(
        default_factory=list,
        description="Extracted quantifiable business value drivers from the source text. "
        "Include formulas, metrics, and units of measurement where specified.",
    )


class FeatureExtractionResponse(BaseModel):
    """Structured response for feature extraction.

    Expected as response_format parameter to OpenAI structured output API.
    """

    features: list[Feature] = Field(
        default_factory=list,
        description="Extracted product features from the source text. "
        "Features are concrete product functionality that implements capabilities.",
    )


class RelationshipExtractionResponse(BaseModel):
    """Structured response for relationship extraction.

    Expected as response_format parameter to OpenAI structured output API.
    """

    relationships: list[Relationship] = Field(
        default_factory=list,
        description="Extracted relationships between entities. "
        "Only create relationships with explicit evidence in the source text.",
    )
