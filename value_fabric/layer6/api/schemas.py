"""Pydantic request/response schemas for Layer 6 Benchmark API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DatasetSummary(BaseModel):
    """Summary of benchmark dataset."""

    dataset_id: str
    name: str
    description: str
    industry: str
    segment: str | None
    geography: str | None
    metrics: list[str]
    metric_count: int
    version: str
    data_source: str | None


class DatasetDetail(BaseModel):
    """Detailed benchmark dataset."""

    dataset_id: str
    name: str
    description: str
    industry: str
    segment: str | None
    geography: str | None
    metrics: dict[str, dict]
    version: str
    data_source: str | None


class ComparisonRequestPayload(BaseModel):
    """Payload for comparison request."""

    dataset_id: str
    metric: str
    company_value: str = Field(..., description="Company value as string (Decimal)")
    industry: str
    segment: str | None = None


class ComparisonResponse(BaseModel):
    """Response from comparison."""

    percentile: int
    peer_median: str
    peer_range: tuple[str, str]
    sample_size: int
    confidence: str
    assessment: str


class ValidationRequestPayload(BaseModel):
    """Payload for validation request."""

    dataset_id: str
    metric: str
    value: str = Field(..., description="Value as string (Decimal)")
    tolerance_percent: int = 10


class ValidationResponse(BaseModel):
    """Response from validation."""

    is_valid: bool
    expected_range: tuple[str, str]
    actual_value: str
    deviation_percent: float | None
    severity: str
    message: str
