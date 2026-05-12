"""Extraction response models for Layer 2."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CapabilityExtractionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capabilities: list[Any] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class RelationshipExtractionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationships: list[Any] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
