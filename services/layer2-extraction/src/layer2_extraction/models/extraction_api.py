"""API request/response models for Layer 2 extraction endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from value_fabric.layer2.models.ontology import Capability, Feature, Persona, UseCase, ValueDriver
from value_fabric.layer2.models.relationships import Relationship


class ExtractionRequest(BaseModel):
    """Request body for starting an extraction job."""

    model_config = ConfigDict(extra="forbid")

    content_id: str
    source_url: str
    markdown_content: str
    extraction_config: dict[str, Any] = Field(default_factory=dict)


class ExtractionResult(BaseModel):
    """Result of an extraction job."""

    model_config = ConfigDict(extra="forbid")

    source_url: str
    capabilities: list[Capability] = Field(default_factory=list)
    features: list[Feature] = Field(default_factory=list)
    use_cases: list[UseCase] = Field(default_factory=list)
    personas: list[Persona] = Field(default_factory=list)
    value_drivers: list[ValueDriver] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)

    def get_all_entities(self) -> list[Any]:
        """Return all extracted entities across types."""
        return (
            self.capabilities
            + self.features
            + self.use_cases
            + self.personas
            + self.value_drivers
        )
