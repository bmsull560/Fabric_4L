from pydantic import BaseModel, Field
from typing import Any, Literal

class EntitySourceSpan(BaseModel):
    document_id: str = Field(..., description='Document identifier')
    start: int = Field(..., description='Start position in document')
    end: int = Field(..., description='End position in document')

class EntityProvenance(BaseModel):
    extraction_job_id: str = Field(..., description='Extraction job identifier')
    source_url: str | None = Field(None, description='Source URL if applicable')
    trace_id: str | None = Field(None, description='Trace identifier for observability')

class ExtractedEntity(BaseModel):
    entity_id: str
    type: str
    name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_span: EntitySourceSpan | None = None
    provenance: EntityProvenance | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)

class ExtractionResultSummary(BaseModel):
    job_id: str
    total_entities: int
    returned_entities: int
    page: int
    page_size: int
    total_pages: int
    mode: Literal['summary','full']

class ExtractionResultsResponse(BaseModel):
    summary: ExtractionResultSummary
    entities: list[ExtractedEntity] = Field(default_factory=list)
