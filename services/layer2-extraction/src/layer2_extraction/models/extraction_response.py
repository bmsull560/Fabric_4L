"""Extraction response models for Layer 2."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CapabilityExtractionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capabilities: list[Any] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class UseCaseExtractionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_cases: list[Any] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class PersonaExtractionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    personas: list[Any] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ValueDriverExtractionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value_drivers: list[Any] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class FeatureExtractionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    features: list[Any] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class UnifiedExtractionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capabilities: list[Any] = Field(default_factory=list)
    use_cases: list[Any] = Field(default_factory=list)
    personas: list[Any] = Field(default_factory=list)
    value_drivers: list[Any] = Field(default_factory=list)
    features: list[Any] = Field(default_factory=list)
    relationships: list[Any] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class RelationshipExtractionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationships: list[Any] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
