"""Operational signal extraction models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class OperationalSignal(BaseModel):
    """An operational signal extracted from unstructured text."""

    model_config = ConfigDict(extra="forbid")

    signal_type: str
    text: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source_refs: list[str] = Field(default_factory=list)


class SignalExtractionResult(BaseModel):
    """Result of operational signal extraction."""

    model_config = ConfigDict(extra="forbid")

    signals: list[OperationalSignal] = Field(default_factory=list)
    source_url: str = ""
