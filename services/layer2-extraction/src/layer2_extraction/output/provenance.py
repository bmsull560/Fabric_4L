"""Provenance tracking for Layer 2 extraction."""

from __future__ import annotations

import uuid
import datetime as _datetime_module
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExtractionActivityStatus(str, Enum):
    """Status of an extraction activity."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SourceDocument(BaseModel):
    """Reference to a source document."""

    model_config = ConfigDict(extra="forbid")

    url: str
    content_hash: str
    content_type: str | None = None
    size_bytes: int = 0
    http_status: int = 200
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LLMCall(BaseModel):
    """Record of a single LLM API call."""

    model_config = ConfigDict(extra="forbid")

    call_id: str
    model: str
    prompt_hash: str
    prompt_version: str
    temperature: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExtractionStep(BaseModel):
    """A single step in an extraction activity."""

    model_config = ConfigDict(extra="forbid")

    step_name: str
    started_at: datetime
    completed_at: datetime | None = None
    entities_extracted: int = 0
    llm_calls: list[LLMCall] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    @property
    def duration_ms(self) -> int | None:
        if self.started_at is None or self.completed_at is None:
            return None
        return int((self.completed_at - self.started_at).total_seconds() * 1000)


class ExtractionActivity(BaseModel):
    """Top-level provenance record for an extraction job."""

    model_config = ConfigDict(extra="forbid")

    activity_id: str
    status: ExtractionActivityStatus = ExtractionActivityStatus.RUNNING
    source_document: SourceDocument
    steps: list[ExtractionStep] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    output_entities: list[str] = Field(default_factory=list)
    output_relationships: list[str] = Field(default_factory=list)
    rdf_output_path: str | None = None

    def add_step(self, step: ExtractionStep) -> None:
        self.steps.append(step)

    def complete(self, rdf_output_path: str | None = None) -> None:
        self.status = ExtractionActivityStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        if rdf_output_path is not None:
            self.rdf_output_path = rdf_output_path

    def fail(self, message: str) -> None:
        self.status = ExtractionActivityStatus.FAILED
        self.completed_at = datetime.now(UTC)
        if self.steps:
            self.steps[-1].errors.append(message)

    @property
    def total_duration_ms(self) -> int | None:
        if self.started_at is None or self.completed_at is None:
            return None
        return int((self.completed_at - self.started_at).total_seconds() * 1000)

    @property
    def total_llm_calls(self) -> int:
        return sum(len(s.llm_calls) for s in self.steps)

    @property
    def total_cost_usd(self) -> float:
        return sum(
            call.cost_usd
            for step in self.steps
            for call in step.llm_calls
        )

    def get_provenance_chain(self) -> dict[str, Any]:
        """Return a serializable provenance chain."""
        return {
            "activity_id": self.activity_id,
            "status": self.status.value,
            "source": {
                "url": self.source_document.url,
                "content_hash": self.source_document.content_hash,
            },
            "extraction": {
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
                "total_llm_calls": self.total_llm_calls,
            },
            "output": {
                "entity_count": len(self.output_entities),
                "relationship_count": len(self.output_relationships),
                "rdf_output_path": self.rdf_output_path,
            },
            "steps": [
                {
                    "step_name": step.step_name,
                    "entities_extracted": step.entities_extracted,
                    "llm_calls": [
                        {
                            "call_id": call.call_id,
                            "model": call.model,
                            "tokens_in": call.tokens_in,
                            "tokens_out": call.tokens_out,
                            "cost_usd": call.cost_usd,
                            "duration_ms": call.duration_ms,
                        }
                        for call in step.llm_calls
                    ],
                }
                for step in self.steps
            ],
        }


class ProvenanceTracker:
    """Tracks provenance for multiple extraction activities."""

    def __init__(self) -> None:
        self._activities: dict[str, ExtractionActivity] = {}

    def start_activity(
        self,
        activity_id: str,
        url: str,
        content_hash: str,
        content_type: str | None = None,
    ) -> ExtractionActivity:
        doc = SourceDocument(
            url=url,
            content_hash=content_hash,
            content_type=content_type,
        )
        activity = ExtractionActivity(
            activity_id=activity_id,
            status=ExtractionActivityStatus.RUNNING,
            source_document=doc,
        )
        self._activities[activity_id] = activity
        return activity

    def get_activity(self, activity_id: str) -> ExtractionActivity | None:
        return self._activities.get(activity_id)

    def get_provenance_for_entity(self, entity_id: str) -> dict[str, Any] | None:
        for activity in self._activities.values():
            if entity_id in activity.output_entities:
                return {
                    "entity_id": entity_id,
                    "activity_id": activity.activity_id,
                    "source_url": activity.source_document.url,
                }
        return None

    def get_provenance_for_output(self, rdf_output_path: str) -> dict[str, Any] | None:
        for activity in self._activities.values():
            if activity.rdf_output_path == rdf_output_path:
                return {
                    "rdf_output_path": rdf_output_path,
                    "activity_id": activity.activity_id,
                    "source_url": activity.source_document.url,
                }
        return None


_provenance_tracker: ProvenanceTracker | None = None


def get_provenance_tracker() -> ProvenanceTracker:
    """Return the global provenance tracker singleton."""
    global _provenance_tracker
    if _provenance_tracker is None:
        _provenance_tracker = ProvenanceTracker()
    return _provenance_tracker


# Pricing per 1M tokens (input / output)
_MODEL_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
}
_DEFAULT_INPUT_PRICE = 5.00
_DEFAULT_OUTPUT_PRICE = 15.00


def create_llm_call_record(
    *,
    call_id: str,
    model: str,
    prompt_hash: str,
    prompt_version: str,
    temperature: float,
    tokens_in: int,
    tokens_out: int,
    duration_ms: int,
) -> LLMCall:
    """Create an LLMCall with automatic cost calculation."""
    input_price, output_price = _MODEL_PRICING.get(model, (_DEFAULT_INPUT_PRICE, _DEFAULT_OUTPUT_PRICE))
    cost_usd = (tokens_in / 1_000_000) * input_price + (tokens_out / 1_000_000) * output_price
    return LLMCall(
        call_id=call_id,
        model=model,
        prompt_hash=prompt_hash,
        prompt_version=prompt_version,
        temperature=temperature,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost_usd,
        duration_ms=duration_ms,
    )
