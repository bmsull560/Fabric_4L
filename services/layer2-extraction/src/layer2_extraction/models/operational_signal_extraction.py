"""Operational signal extraction models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OperationalSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal_type: str
    source_text: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SignalExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signals: list[OperationalSignal] = Field(default_factory=list)
    source_url: str = ""
    extraction_cost_usd: float = 0.0
