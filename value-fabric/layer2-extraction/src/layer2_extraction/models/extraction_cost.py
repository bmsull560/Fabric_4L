"""Cost tracking models for LLM extraction.

Tracks token usage and USD costs per extraction job for
budget management and cost optimization.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ExtractionCost(BaseModel):
    """Cost record for a single LLM API call.

    Tracks token usage, model pricing, and total USD cost
    for budget management and optimization analysis.

    Attributes:
        extraction_job_id: Reference to extraction job
        provider: LLM provider (openai, anthropic)
        model: Specific model used
        endpoint: Type of extraction (entity_extraction, relationship_extraction)
        input_tokens: Number of input/prompt tokens
        output_tokens: Number of output/completion tokens
        cost_usd: Total cost in USD
        timestamp: When the API call was made
    """

    extraction_job_id: str = Field(..., description="Reference to extraction job")
    provider: str = Field(..., pattern="^(openai|anthropic)$")
    model: str = Field(..., min_length=1)
    endpoint: str = Field(..., description="Type of extraction endpoint")
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0.0, ge=0.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ["openai", "anthropic"]:
            raise ValueError(f"Provider must be 'openai' or 'anthropic', got {v}")
        return v

    def total_tokens(self) -> int:
        """Get total token count."""
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "extraction_job_id": self.extraction_job_id,
            "provider": self.provider,
            "model": self.model,
            "endpoint": self.endpoint,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens(),
            "cost_usd": round(self.cost_usd, 6),
            "timestamp": self.timestamp.isoformat(),
        }


class JobCostSummary(BaseModel):
    """Aggregated cost summary for an extraction job.

    Provides total cost, token counts, and cost breakdown
    across all API calls within a single extraction job.
    """

    extraction_job_id: str
    total_cost_usd: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    api_calls: int = 0
    provider_breakdown: dict[str, float] = Field(default_factory=dict)
    endpoint_breakdown: dict[str, float] = Field(default_factory=dict)

    def add_cost_record(self, record: ExtractionCost) -> None:
        """Add a cost record to the summary."""
        self.total_cost_usd += record.cost_usd
        self.total_input_tokens += record.input_tokens
        self.total_output_tokens += record.output_tokens
        self.api_calls += 1

        # Update provider breakdown
        provider = record.provider
        self.provider_breakdown[provider] = (
            self.provider_breakdown.get(provider, 0.0) + record.cost_usd
        )

        # Update endpoint breakdown
        endpoint = record.endpoint
        self.endpoint_breakdown[endpoint] = (
            self.endpoint_breakdown.get(endpoint, 0.0) + record.cost_usd
        )

    def total_tokens(self) -> int:
        """Get total token count."""
        return self.total_input_tokens + self.total_output_tokens

    def avg_cost_per_call(self) -> float:
        """Get average cost per API call."""
        if self.api_calls == 0:
            return 0.0
        return self.total_cost_usd / self.api_calls
