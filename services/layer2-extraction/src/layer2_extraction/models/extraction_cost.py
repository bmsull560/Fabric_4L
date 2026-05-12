"""Cost tracking models for Layer 2 extraction."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ExtractionCost(BaseModel):
    """Cost breakdown for an extraction job."""

    model_config = ConfigDict(extra="forbid")

    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    model: str = "gpt-4o"


class JobCostSummary(BaseModel):
    """Aggregated cost summary across extraction steps."""

    model_config = ConfigDict(extra="forbid")

    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_cost_usd: float = 0.0
    step_costs: list[ExtractionCost] = Field(default_factory=list)
