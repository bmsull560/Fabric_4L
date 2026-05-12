"""Provenance tracking for Layer 2 extraction."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from value_fabric.layer2.models.extraction_cost import ExtractionCost


class ExtractionStatus(str, Enum):
    """Status of an extraction step or activity."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SourceDocument(BaseModel):
    """Reference to a source document."""

    model_config = ConfigDict(extra="forbid")

    url: str
    hash: str = ""
    file_type: str = "markdown"
    content_length: int = 0
    retrieved_at: datetime | None = None

    def __init__(self, **data: Any):
        if "retrieved_at" not in data:
            data["retrieved_at"] = datetime.utcnow()
        super().__init__(**data)


class LLMCall(BaseModel):
    """Record of a single LLM API call."""

    model_config = ConfigDict(extra="forbid")

    model: str = "gpt-4o"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    cost: ExtractionCost | None = None


class ExtractionStep(BaseModel):
    """A single step in an extraction activity."""

    model_config = ConfigDict(extra="forbid")

    step_name: str
    status: ExtractionStatus = ExtractionStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    llm_calls: list[LLMCall] = Field(default_factory=list)
    error_message: str | None = None

    def __init__(self, **data: Any):
        if "started_at" not in data:
            data["started_at"] = datetime.utcnow()
        super().__init__(**data)

    @property
    def duration(self) -> float:
        """Duration in seconds."""
        if self.started_at is None:
            return 0.0
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()

    def add_llm_call(self, call: LLMCall) -> None:
        self.llm_calls.append(call)

    def complete(self) -> None:
        self.status = ExtractionStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def fail(self, message: str) -> None:
        self.status = ExtractionStatus.FAILED
        self.error_message = message
        self.completed_at = datetime.utcnow()


class ExtractionActivity(BaseModel):
    """Top-level provenance record for an extraction job."""

    model_config = ConfigDict(extra="forbid")

    activity_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_documents: list[SourceDocument] = Field(default_factory=list)
    steps: list[ExtractionStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    status: ExtractionStatus = ExtractionStatus.PENDING
    error_message: str | None = None

    def add_step(self, step: ExtractionStep) -> None:
        self.steps.append(step)

    def add_source_document(self, doc: SourceDocument) -> None:
        self.source_documents.append(doc)

    def complete(self) -> None:
        self.status = ExtractionStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def fail(self, message: str) -> None:
        self.status = ExtractionStatus.FAILED
        self.error_message = message
        self.completed_at = datetime.utcnow()

    @property
    def total_duration(self) -> float:
        """Total duration in seconds across all steps."""
        return sum(s.duration for s in self.steps)

    @property
    def total_llm_calls(self) -> int:
        return sum(len(s.llm_calls) for s in self.steps)

    @property
    def total_cost(self) -> float:
        total = 0.0
        for step in self.steps:
            for call in step.llm_calls:
                if call.cost:
                    total += call.cost.cost_usd
        return total

    def get_provenance_chain(self) -> list[dict[str, Any]]:
        """Return a serializable provenance chain."""
        chain: list[dict[str, Any]] = []
        for step in self.steps:
            chain.append(
                {
                    "step_name": step.step_name,
                    "status": step.status.value,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                    "duration": step.duration,
                    "llm_calls": len(step.llm_calls),
                    "error_message": step.error_message,
                }
            )
        return chain
