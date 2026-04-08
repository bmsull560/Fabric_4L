"""FastAPI application for Layer 2: Extraction Pipeline.

Provides REST API endpoints for:
- Extracting entities from content
- Batch extraction jobs
- Ontology queries
- Extraction status and results
"""

import os
import hashlib
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..models import (
    Capability, UseCase, Persona, ValueDriver, Feature,
    Relationship, ExtractionResult
)
from ..extraction.chunker import chunk_markdown
from ..extraction.llm_extractor import EntityExtractor, RelationshipExtractor
from ..extraction.deduplicator import deduplicate_entities
from ..output.rdf_generator import generate_rdf
from ..output.provenance import (
    get_provenance_tracker,
    ExtractionActivity,
    ExtractionStep,
    create_llm_call_record
)
from ..validation import EntailmentValidator, ValidationSeverity
from ..alignment import SemanticAligner

# Initialize FastAPI app
app = FastAPI(
    title="Value Fabric - Extraction Pipeline",
    description="Ontology-guided extraction of entities from unstructured text to RDF/OWL",
    version="1.0.0"
)

# CORS middleware
# Note: allow_origins=["*"] cannot be used with allow_credentials=True per browser security spec
# In production, specify exact origins or use environment variable
allow_origins = ["*"]
allow_credentials = False  # Must be False when using wildcard origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize extractors
entity_extractor = EntityExtractor(
    api_key=os.getenv("OPENAI_API_KEY"),
    model=os.getenv("LLM_MODEL", "gpt-4o")
)
relationship_extractor = RelationshipExtractor(
    api_key=os.getenv("OPENAI_API_KEY"),
    model=os.getenv("LLM_MODEL", "gpt-4o")
)


# Request/Response Models
class ExtractRequest(BaseModel):
    """Request body for extraction endpoint."""
    content_id: str = Field(..., description="ID of content to extract from (from Layer 1)")
    source_url: str = Field(..., description="URL of source document")
    markdown_content: str = Field(..., description="Markdown content to extract from")
    extraction_config: dict = Field(
        default_factory=lambda: {
            "entity_types": ["Capability", "UseCase", "Persona", "ValueDriver"],
            "confidence_threshold": 0.75,
            "chunk_size": 2000,
            "chunk_overlap": 200
        }
    )


class ExtractResponse(BaseModel):
    """Response from extraction endpoint."""
    extraction_job_id: str
    status: str
    message: str


class ExtractionStatusResponse(BaseModel):
    """Status of an extraction job."""
    job_id: str
    status: str
    entities_extracted: int
    relationships_extracted: int
    rdf_output_path: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]


class EntityListResponse(BaseModel):
    """List of entities in the ontology."""
    entity_type: str
    entities: List[dict]
    total: int


class RelationshipsResponse(BaseModel):
    """Relationships for an entity."""
    entity_id: str
    incoming: List[dict]
    outgoing: List[dict]


class ProvenanceResponse(BaseModel):
    """Provenance chain for an entity or output."""
    activity_id: str
    source: dict
    extraction: dict
    steps: List[dict]
    output: dict


# Background task for extraction
async def run_extraction(
    job_id: str,
    source_url: str,
    content: str,
    config: dict
):
    """Background extraction task.
    
    Executes the full 6-stage extraction pipeline:
    1. Chunk input
    2. Extract entities
    3. Extract relationships
    4. Deduplicate
    5. Validate
    6. Generate RDF
    """
    tracker = get_provenance_tracker()
    
    # Calculate content hash for provenance
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    
    # Start provenance tracking
    activity = tracker.start_activity(
        activity_id=job_id,
        source_url=source_url,
        content_hash=content_hash
    )
    
    try:
        # Stage 1: Chunking
        step1 = ExtractionStep(
            step_name="chunking",
            started_at=datetime.utcnow()
        )
        
        chunk_size = config.get("chunk_size", 2000)
        chunk_overlap = config.get("chunk_overlap", 200)
        
        chunks = chunk_markdown(
            content,
            source_url=source_url,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        step1.completed_at = datetime.utcnow()
        activity.add_step(step1)
        
        # Stage 2 & 3: Entity and Relationship Extraction
        step2 = ExtractionStep(
            step_name="entity_extraction",
            started_at=datetime.utcnow()
        )
        
        all_entities = {
            "capabilities": [],
            "use_cases": [],
            "personas": [],
            "value_drivers": [],
            "features": []
        }
        all_relationships = []
        
        confidence_threshold = config.get("confidence_threshold", 0.75)
        
        for i, chunk in enumerate(chunks):
            # Extract entities from chunk
            entities = await entity_extractor.extract_entities(
                text=chunk.content,
                source_url=source_url,
                extraction_job_id=job_id,
                confidence_threshold=confidence_threshold
            )
            
            # Collect entities
            for entity_type, entity_list in entities.items():
                all_entities[entity_type].extend(entity_list)
            
            # Extract relationships
            relationships = await relationship_extractor.extract_relationships(
                text=chunk.content,
                entities=entities,
                source_url=source_url,
                extraction_job_id=job_id,
                confidence_threshold=confidence_threshold - 0.05  # Slightly lower for relationships
            )
            all_relationships.extend(relationships)
        
        step2.completed_at = datetime.utcnow()
        step2.entities_extracted = sum(len(v) for v in all_entities.values())
        activity.add_step(step2)
        
        # Stage 3: Semantic Alignment
        step_align = ExtractionStep(
            step_name="semantic_alignment",
            started_at=datetime.utcnow()
        )
        
        aligner = SemanticAligner(
            similarity_threshold=0.85,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Align each entity type
        aligned_entities = {}
        for entity_type, entity_list in all_entities.items():
            if entity_list:
                aligned_list, _ = await aligner.align_entities(entity_list)
                aligned_entities[entity_type] = aligned_list
            else:
                aligned_entities[entity_type] = []
        
        all_entities = aligned_entities
        
        step_align.completed_at = datetime.utcnow()
        activity.add_step(step_align)
        
        # Stage 4: Deduplication
        step3 = ExtractionStep(
            step_name="deduplication",
            started_at=datetime.utcnow()
        )
        
        deduplicated = await deduplicate_entities(
            all_entities,
            api_key=os.getenv("OPENAI_API_KEY"),
            similarity_threshold=0.85,
            relationships=all_relationships,
            enable_coreference=True
        )
        
        step3.completed_at = datetime.utcnow()
        activity.add_step(step3)
        
        # Stage 5: Validation (EntailmentValidator with 6 validation rules)
        step4 = ExtractionStep(
            step_name="validation",
            started_at=datetime.utcnow()
        )
        
        # Create extraction result
        result = ExtractionResult(
            job_id=job_id,
            source_url=source_url,
            capabilities=deduplicated.get("capabilities", []),
            use_cases=deduplicated.get("use_cases", []),
            personas=deduplicated.get("personas", []),
            value_drivers=deduplicated.get("value_drivers", []),
            features=deduplicated.get("features", []),
            chunks_processed=len(chunks)
        )
        
        # Run entailment validation
        validator = EntailmentValidator()
        validation_results = validator.validate(result, all_relationships)
        
        # Check for validation errors
        errors = [r for r in validation_results if r.severity == ValidationSeverity.ERROR and not r.passed]
        warnings = [r for r in validation_results if r.severity == ValidationSeverity.WARNING and not r.passed]
        
        if errors:
            # Add errors to result
            result.errors.extend([f"[ERROR] {e.rule_id}: {e.message}" for e in errors])
        if warnings:
            # Log warnings but continue
            result.errors.extend([f"[WARNING] {w.rule_id}: {w.message}" for w in warnings])
        
        step4.completed_at = datetime.utcnow()
        step4.entities_extracted = len(validation_results)  # Track validation results count
        activity.add_step(step4)
        
        # Stage 6: RDF Generation
        step5 = ExtractionStep(
            step_name="rdf_generation",
            started_at=datetime.utcnow()
        )
        
        rdf_content = generate_rdf(result, all_relationships)
        
        # Save RDF to file (in production, this would go to S3/MinIO)
        output_dir = os.getenv("RDF_OUTPUT_DIR", "/tmp/rdf")
        os.makedirs(output_dir, exist_ok=True)
        rdf_path = f"{output_dir}/{job_id}.ttl"
        
        with open(rdf_path, "w") as f:
            f.write(rdf_content)
        
        step5.completed_at = datetime.utcnow()
        activity.add_step(step5)
        
        # Complete activity
        activity.output_entities = [e.id for e in result.get_all_entities()]
        activity.output_relationships = [r.id for r in all_relationships]
        activity.complete(rdf_path=rdf_path)
        
    except Exception as e:
        activity.fail(str(e))


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "layer2-extraction"}


@app.post("/v1/extract", response_model=ExtractResponse)
async def extract(
    request: ExtractRequest,
    background_tasks: BackgroundTasks
):
    """Start an extraction job.
    
    Extracts entities and relationships from provided Markdown content
    and generates RDF/OWL output.
    """
    job_id = str(uuid4())
    
    # Queue extraction as background task
    background_tasks.add_task(
        run_extraction,
        job_id=job_id,
        source_url=request.source_url,
        content=request.markdown_content,
        config=request.extraction_config
    )
    
    return ExtractResponse(
        extraction_job_id=job_id,
        status="queued",
        message="Extraction job started"
    )


@app.get("/v1/extract/status/{job_id}", response_model=ExtractionStatusResponse)
async def get_extraction_status(job_id: str):
    """Get status of an extraction job."""
    tracker = get_provenance_tracker()
    activity = tracker.get_activity(job_id)
    
    if not activity:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return ExtractionStatusResponse(
        job_id=activity.activity_id,
        status=activity.status.value,
        entities_extracted=len(activity.output_entities),
        relationships_extracted=len(activity.output_relationships),
        rdf_output_path=activity.rdf_output_path,
        started_at=activity.started_at,
        completed_at=activity.completed_at,
        duration_ms=activity.total_duration_ms
    )


@app.post("/v1/extract/batch")
async def extract_batch(
    requests: List[ExtractRequest],
    background_tasks: BackgroundTasks
):
    """Start a batch extraction job."""
    batch_id = str(uuid4())
    job_ids = []
    
    for req in requests:
        job_id = str(uuid4())
        job_ids.append(job_id)
        background_tasks.add_task(
            run_extraction,
            job_id=job_id,
            source_url=req.source_url,
            content=req.markdown_content,
            config=req.extraction_config
        )
    
    return {
        "batch_job_id": batch_id,
        "job_ids": job_ids,
        "status": "queued",
        "total_jobs": len(requests)
    }


@app.get("/v1/ontology/entities")
async def list_entities(
    entity_type: Optional[str] = Query(None, enum=["Capability", "UseCase", "Persona", "ValueDriver", "Feature"]),
    limit: int = Query(100, ge=1, le=1000)
):
    """List entities in the ontology.
    
    Note: In a full implementation, this would query a persistent store.
    For now, returns empty list (entities are in RDF files).
    """
    # This would query Neo4j or similar in production
    return EntityListResponse(
        entity_type=entity_type or "all",
        entities=[],
        total=0
    )


@app.get("/v1/ontology/relationships/{entity_id}")
async def get_relationships(entity_id: str):
    """Get relationships for an entity.
    
    Note: In a full implementation, this would query the graph database.
    """
    return RelationshipsResponse(
        entity_id=entity_id,
        incoming=[],
        outgoing=[]
    )


@app.get("/v1/audit/trace/{job_id}", response_model=ProvenanceResponse)
async def get_provenance(job_id: str):
    """Get full provenance trace for an extraction job."""
    tracker = get_provenance_tracker()
    activity = tracker.get_activity(job_id)
    
    if not activity:
        raise HTTPException(status_code=404, detail="Job not found")
    
    chain = activity.get_provenance_chain()
    
    return ProvenanceResponse(
        activity_id=chain["activity_id"],
        source=chain["source"],
        extraction=chain["extraction"],
        steps=chain["steps"],
        output=chain["output"]
    )


@app.get("/v1/audit/entity/{entity_id}")
async def get_entity_provenance(entity_id: str):
    """Get provenance for a specific entity."""
    tracker = get_provenance_tracker()
    chain = tracker.get_provenance_for_entity(entity_id)
    
    if not chain:
        raise HTTPException(status_code=404, detail="Entity provenance not found")
    
    return chain


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
