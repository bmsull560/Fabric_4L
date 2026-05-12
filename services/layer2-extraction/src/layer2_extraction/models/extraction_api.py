"""API request and response models for Layer 2 extraction."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from layer2_extraction.models.ontology import (
    Capability,
    Persona,
    UseCase,
    ValueDriver,
)
from layer2_extraction.models.relationships import Relationship


class ExtractionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    source_url: str
    content: str = ""
    config: dict[str, Any] = Field(default_factory=dict)
    content_id: str = ""
    markdown_content: str = ""
    extraction_config: dict[str, Any] = Field(default_factory=dict)


class ExtractionResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    source_url: str
    job_id: str = ""
    capabilities: list[Capability] = Field(default_factory=list)
    use_cases: list[UseCase] = Field(default_factory=list)
    personas: list[Persona] = Field(default_factory=list)
    value_drivers: list[ValueDriver] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    extraction_cost_usd: float = 0.0
    chunks_processed: int = 0

    def get_all_entities(self) -> list[Any]:
        return (
            self.capabilities
            + self.use_cases
            + self.personas
            + self.value_drivers
        )
