"""Operational signal extraction models for Layer 2.

These models define the structured output for extracting Operational
category pain signals from prospect setup data.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OperationalSignal(BaseModel):
    """Single operational pain signal extracted from prospect data.

    This is the raw extraction output before Layer 3 enrichment adds
    evidence matching and impact quantification.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ..., min_length=5, max_length=200,
        description="Specific operational pain name (e.g., 'Production Downtime', 'Changeover Inefficiency')"
    )
    category: Literal["Operational"] = Field(
        default="Operational",
        description="Fixed category for this extraction lane"
    )
    description: str = Field(
        ..., min_length=20,
        description="Detailed explanation of the operational pain, its root causes, and business impact"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Confidence in this signal extraction (0.0-1.0). Higher when pain is explicitly stated."
    )
    confidence_explanation: str = Field(
        ..., min_length=20,
        description="Rationale for confidence score: what evidence supports this signal, what might be uncertain"
    )
    impact_indicators: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Specific clues from the input that indicate quantifiable impact (e.g., '3-5 day delays', '$2M annual loss')"
    )
    trend_direction: Literal["increasing", "decreasing", "stable", "new"] = Field(
        ..., description="Observed trend based on prospect description"
    )
    trend_explanation: str | None = Field(
        default=None,
        description="Rationale for trend assessment"
    )
    stakeholder_quotes: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="Direct quotes from prospect input that evidence this pain"
    )
    likely_value_drivers: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="Value driver names this signal likely maps to (for L3 quantification)"
    )

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is within valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return round(v, 2)

    @field_validator("impact_indicators")
    @classmethod
    def validate_indicators(cls, v: list[str]) -> list[str]:
        """Ensure indicators are specific and non-empty."""
        return [ind.strip() for ind in v if ind.strip()]


class ExtractionMetadata(BaseModel):
    """Metadata about the extraction process."""

    model_config = ConfigDict(extra="forbid")

    source_text_length: int = Field(
        ..., ge=0, description="Character count of input text processed"
    )
    extraction_duration_ms: int | None = Field(
        default=None, ge=0, description="Time taken for extraction"
    )
    model_version: str = Field(
        default="gpt-4o-2024-08-06", description="LLM model used"
    )
    prompt_version: str = Field(
        default="1.0.0", description="Extraction prompt version"
    )
    source_references: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Locations in source text where signals were found"
    )


class OperationalSignalExtractionResponse(BaseModel):
    """Structured response for operational signal extraction.

    Expected as response_format parameter to OpenAI structured output API.
    Returns 0-3 operational signals to limit scope for the vertical slice.
    """

    model_config = ConfigDict(extra="forbid")

    signals: list[OperationalSignal] = Field(
        default_factory=list,
        max_length=3,
        description="Extracted operational pain signals from prospect setup. Maximum 3 for vertical slice scope."
    )
    extraction_metadata: ExtractionMetadata = Field(
        default_factory=lambda: ExtractionMetadata(source_text_length=0),
        description="Metadata about the extraction process"
    )
    no_signals_reason: str | None = Field(
        default=None,
        description="Explanation if no operational signals were found"
    )

    @field_validator("signals")
    @classmethod
    def validate_signals(cls, v: list[OperationalSignal]) -> list[OperationalSignal]:
        """Ensure signals are high quality."""
        if len(v) > 3:
            raise ValueError("Maximum 3 signals allowed for vertical slice")
        # Sort by confidence descending
        return sorted(v, key=lambda s: s.confidence_score, reverse=True)
