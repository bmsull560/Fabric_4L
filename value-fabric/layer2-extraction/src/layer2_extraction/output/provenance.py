"""Provenance tracking for auditability.

Implements PROV-O ontology for tracking data lineage from source
documents through extraction to final RDF output.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ExtractionActivityStatus(str, Enum):
    """Status of an extraction activity."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SourceDocument:
    """Represents a source document in provenance chain.

    Attributes:
        url: Source URL
        content_hash: Hash of original content (for integrity)
        content_type: Document type (product_page, press_release, etc.)
        fetched_at: When document was retrieved
        size_bytes: Document size
        http_status: HTTP response code
    """

    url: str
    content_hash: str
    content_type: str | None = None
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    size_bytes: int = 0
    http_status: int = 200


@dataclass
class LLMCall:
    """Represents a single LLM API call.

    Attributes:
        call_id: Unique ID for this call
        model: Model name (gpt-4o, claude-3.5-sonnet, etc.)
        prompt_hash: Hash of prompt (for audit)
        prompt_version: Git commit hash of prompt template
        temperature: Temperature setting
        tokens_in: Input token count
        tokens_out: Output token count
        cost_usd: Estimated cost
        duration_ms: Call duration
        timestamp: When call was made
    """

    call_id: str
    model: str
    prompt_hash: str
    prompt_version: str
    temperature: float
    tokens_in: int
    tokens_out: int
    cost_usd: float
    duration_ms: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExtractionStep:
    """Represents a step in the extraction pipeline.

    Attributes:
        step_name: Name of the step (chunking, entity_extraction, etc.)
        started_at: Start timestamp
        completed_at: End timestamp
        entities_extracted: Count of entities found
        llm_calls: List of LLM calls made in this step
        errors: Any errors encountered
    """

    step_name: str
    started_at: datetime
    completed_at: datetime | None = None
    entities_extracted: int = 0
    llm_calls: list[LLMCall] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def duration_ms(self) -> int | None:
        """Calculate step duration in milliseconds."""
        if self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None


@dataclass
class ExtractionActivity:
    """Complete provenance record for an extraction job.

    This is the main provenance entity that tracks everything from
    source document to final output.

    Attributes:
        activity_id: Unique job ID
        status: Current status
        source_document: Original source
        steps: Pipeline steps executed
        output_entities: IDs of generated entities
        output_relationships: IDs of generated relationships
        rdf_output_path: Where RDF was saved
        started_at: Job start time
        completed_at: Job end time
        metadata: Additional metadata
    """

    activity_id: str
    status: ExtractionActivityStatus
    source_document: SourceDocument
    steps: list[ExtractionStep] = field(default_factory=list)
    output_entities: list[str] = field(default_factory=list)
    output_relationships: list[str] = field(default_factory=list)
    rdf_output_path: str | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_step(self, step: ExtractionStep) -> None:
        """Add a completed step to the activity."""
        self.steps.append(step)

    def complete(self, rdf_path: str | None = None) -> None:
        """Mark activity as completed."""
        self.status = ExtractionActivityStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if rdf_path:
            self.rdf_output_path = rdf_path

    def fail(self, error_message: str) -> None:
        """Mark activity as failed."""
        self.status = ExtractionActivityStatus.FAILED
        self.completed_at = datetime.utcnow()
        if self.steps:
            self.steps[-1].errors.append(error_message)

    @property
    def total_duration_ms(self) -> int | None:
        """Calculate total job duration."""
        if self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None

    @property
    def total_llm_calls(self) -> int:
        """Count total LLM calls."""
        return sum(len(step.llm_calls) for step in self.steps)

    @property
    def total_cost_usd(self) -> float:
        """Calculate total LLM cost."""
        return sum(call.cost_usd for step in self.steps for call in step.llm_calls)

    def get_provenance_chain(self) -> dict[str, Any]:
        """Get complete provenance chain for audit.

        Returns structured data suitable for API responses
        showing full lineage from source to output.
        """
        return {
            "activity_id": self.activity_id,
            "status": self.status.value,
            "source": {
                "url": self.source_document.url,
                "content_hash": self.source_document.content_hash,
                "content_type": self.source_document.content_type,
                "fetched_at": self.source_document.fetched_at.isoformat(),
            },
            "extraction": {
                "started_at": self.started_at.isoformat(),
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
                "duration_ms": self.total_duration_ms,
                "total_llm_calls": self.total_llm_calls,
                "total_cost_usd": round(self.total_cost_usd, 4),
            },
            "steps": [
                {
                    "step_name": step.step_name,
                    "started_at": step.started_at.isoformat(),
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                    "duration_ms": step.duration_ms,
                    "entities_extracted": step.entities_extracted,
                    "llm_calls": [
                        {
                            "call_id": call.call_id,
                            "model": call.model,
                            "prompt_version": call.prompt_version,
                            "tokens_in": call.tokens_in,
                            "tokens_out": call.tokens_out,
                            "cost_usd": round(call.cost_usd, 4),
                            "duration_ms": call.duration_ms,
                        }
                        for call in step.llm_calls
                    ],
                    "errors": step.errors,
                }
                for step in self.steps
            ],
            "output": {
                "entity_count": len(self.output_entities),
                "relationship_count": len(self.output_relationships),
                "rdf_output_path": self.rdf_output_path,
            },
        }


class ProvenanceTracker:
    """Track provenance for all extraction activities.

    Maintains a registry of extraction activities for audit queries.
    """

    def __init__(self):
        """Initialize provenance tracker."""
        self.activities: dict[str, ExtractionActivity] = {}

    def start_activity(
        self, activity_id: str, source_url: str, content_hash: str, content_type: str | None = None
    ) -> ExtractionActivity:
        """Start tracking a new extraction activity.

        Args:
            activity_id: Unique ID for this activity
            source_url: Source document URL
            content_hash: Hash of source content
            content_type: Document type

        Returns:
            New ExtractionActivity instance
        """
        source_doc = SourceDocument(
            url=source_url, content_hash=content_hash, content_type=content_type
        )

        activity = ExtractionActivity(
            activity_id=activity_id,
            status=ExtractionActivityStatus.RUNNING,
            source_document=source_doc,
        )

        self.activities[activity_id] = activity
        return activity

    def get_activity(self, activity_id: str) -> ExtractionActivity | None:
        """Get activity by ID."""
        return self.activities.get(activity_id)

    def get_provenance_for_entity(self, entity_id: str) -> dict[str, Any] | None:
        """Get provenance chain for a specific entity.

        Finds the activity that generated this entity.
        """
        for activity in self.activities.values():
            if entity_id in activity.output_entities:
                chain = activity.get_provenance_chain()
                chain["entity_id"] = entity_id
                return chain
        return None

    def get_provenance_for_output(self, output_path: str) -> dict[str, Any] | None:
        """Get provenance for RDF output file."""
        for activity in self.activities.values():
            if activity.rdf_output_path == output_path:
                return activity.get_provenance_chain()
        return None


# Global provenance tracker instance
_provenance_tracker: ProvenanceTracker | None = None


def get_provenance_tracker() -> ProvenanceTracker:
    """Get or create global provenance tracker."""
    global _provenance_tracker
    if _provenance_tracker is None:
        _provenance_tracker = ProvenanceTracker()
    return _provenance_tracker


def create_llm_call_record(
    call_id: str,
    model: str,
    prompt_hash: str,
    prompt_version: str,
    temperature: float,
    tokens_in: int,
    tokens_out: int,
    duration_ms: int,
) -> LLMCall:
    """Create an LLM call record with cost estimation.

    Args:
        call_id: Unique call ID
        model: Model name
        prompt_hash: Hash of prompt
        prompt_version: Git commit hash
        temperature: Temperature setting
        tokens_in: Input tokens
        tokens_out: Output tokens
        duration_ms: Call duration

    Returns:
        LLMCall record with cost estimate
    """
    # Cost estimates (as of 2024, per 1M tokens)
    costs_per_1m = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    }

    model_costs = costs_per_1m.get(model, {"input": 5.00, "output": 15.00})

    input_cost = (tokens_in / 1_000_000) * model_costs["input"]
    output_cost = (tokens_out / 1_000_000) * model_costs["output"]
    total_cost = input_cost + output_cost

    return LLMCall(
        call_id=call_id,
        model=model,
        prompt_hash=prompt_hash,
        prompt_version=prompt_version,
        temperature=temperature,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=total_cost,
        duration_ms=duration_ms,
    )
