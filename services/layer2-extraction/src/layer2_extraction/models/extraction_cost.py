"""Extraction cost tracking models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExtractionCost(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0


class JobCostSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_cost_usd: float = 0.0
    total_tokens: int = 0
    model_breakdown: dict[str, Any] = Field(default_factory=dict)
