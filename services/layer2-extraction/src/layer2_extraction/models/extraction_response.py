"""Extraction response models for structured LLM output."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from value_fabric.layer2.models.ontology import Capability, UseCase, Persona, ValueDriver
from value_fabric.layer2.models.relationships import Relationship


class CapabilityExtractionResponse(BaseModel):
    """Structured response for capability extraction."""

    model_config = ConfigDict(extra="forbid")

    capabilities: list[Capability] = []


class RelationshipExtractionResponse(BaseModel):
    """Structured response for relationship extraction."""

    model_config = ConfigDict(extra="forbid")

    relationships: list[Relationship] = []
