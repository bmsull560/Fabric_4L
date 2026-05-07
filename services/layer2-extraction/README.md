# Layer 2: Ontology-Guided Extraction Pipeline
> Routing/versioning reference: see the canonical [Service Routing and API Version Matrix](../../docs/reference/service-routing-and-api-version-matrix.md).

Transforms unstructured Markdown content into structured RDF/OWL triples using LLM-guided extraction with strict schema compliance.

## Overview

Layer 2 is the semantic extraction service for the Value Fabric platform. It:
1. **Chunks** input Markdown into semantically meaningful segments
2. **Extracts** entities (Capabilities, UseCases, Personas, ValueDrivers) using LLM function calling
3. **Extracts** relationships between entities with evidence quotes
4. **Deduplicates** entities using embeddings (similarity threshold 0.85)
5. **Validates** all output against Pydantic schemas
6. **Generates** RDF/OWL with PROV-O provenance annotations

## Architecture

```
Input (Markdown)
    ↓
Semantic Chunker (LangChain, 2000 char chunks, 200 overlap)
    ↓
Entity Extractor (GPT-4o, temperature 0.0, function calling)
    ↓
Relationship Extractor (Evidence-backed relationships)
    ↓
Deduplicator (text-embedding-3-large, cosine similarity)
    ↓
RDF Generator (rdflib, Turtle format)
    ↓
Output (RDF/OWL + Provenance)
```

## Core Ontology

### Entity Types

| Type | Key Attributes | Description |
|------|---------------|-------------|
| **Capability** | `technical_features`, `api_endpoints`, `integrations`, `apqc_mapping` | Technical features with APQC PCF mapping |
| **UseCase** | `industry_context`, `required_capabilities`, `workflow_steps`, `kpis` | Business problems being solved |
| **Persona** | `role_type`, `title`, `department`, `pain_points`, `success_metrics` | Stakeholders in the buying process |
| **ValueDriver** | `category`, `metrics`, `formula_string`, `unit`, `time_to_value` | Quantifiable business outcomes |
| **APQCProcess** | `pcf_id`, `process_name`, `hierarchy_level` | APQC PCF reference process |

### Relationship Types

| Predicate | Direction | Description |
|-----------|-----------|-------------|
| `enables` | Capability → UseCase | Capability makes use case possible |
| `requires` | Capability → Capability | Capability requires another capability |
| `involves` | UseCase → Persona | Use case involves a persona |
| `delivers` | UseCase → ValueDriver | Use case delivers value outcome |
| `implemented_by` | Capability → Feature | Capability implemented by feature |
| `measured_by` | Capability → ValueMetric | Capability measured by metric |
| `maps_to_apqc` | Capability → APQCProcess | Maps to APQC PCF reference |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/v1/extract` | POST | Start extraction job |
| `/v1/extract/status/{job_id}` | GET | Check job status |
| `/v1/extract/batch` | POST | Batch extraction |
| `/v1/ontology/entities` | GET | List entities |
| `/v1/ontology/relationships/{id}` | GET | Get entity relationships |
| `/v1/audit/trace/{job_id}` | GET | Full provenance chain |

## Usage

### Start Extraction

```bash
curl -X POST http://localhost:8000/v1/extract \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "doc-123",
    "source_url": "https://example.com/product",
    "markdown_content": "# Product\n\nOur platform...",
    "extraction_config": {
      "confidence_threshold": 0.75,
      "chunk_size": 2000
    }
  }'
```

Response:
```json
{
  "extraction_job_id": "uuid",
  "status": "queued",
  "message": "Extraction job started"
}
```

### Check Status

```bash
curl http://localhost:8000/v1/extract/status/{job_id}
```

Response:
```json
{
  "job_id": "uuid",
  "status": "completed",
  "entities_extracted": 12,
  "relationships_extracted": 18,
  "rdf_output_path": "/app/rdf-output/uuid.ttl"
}
```

### Get Provenance

```bash
curl http://localhost:8000/v1/audit/trace/{job_id}
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | Required | OpenAI API key |
| `LLM_MODEL` | `gpt-4o` | LLM model for extraction |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |
| `RDF_OUTPUT_DIR` | `/tmp/rdf` | Where to save RDF files |
| `LOG_LEVEL` | `info` | Logging level |

## Development

### Setup

```bash
cd layer2-extraction
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Testing

```bash
# Run unit tests (no LLM calls)
pytest tests/ -v --ignore=tests/test_extraction.py

# Run integration tests (requires OPENAI_API_KEY)
export OPENAI_API_KEY=sk-...
pytest tests/ -v
```

### Code Quality

```bash
# Formatting
black src/ tests/

# Linting
ruff check src/ tests/

# Type checking
mypy src/
```

### Docker

```bash
# Build and run
docker-compose up --build

# View logs
docker-compose logs -f layer2-extraction
```

## Project Structure

```
layer2-extraction/
├── src/
│   ├── models/
│   │   ├── ontology.py         # Pydantic models
│   │   └── relationships.py    # Relationship types
│   ├── extraction/
│   │   ├── chunker.py         # Semantic chunking
│   │   ├── llm_extractor.py   # OpenAI extraction
│   │   └── deduplicator.py    # Embedding dedup
│   ├── output/
│   │   ├── rdf_generator.py   # Turtle serialization
│   │   └── provenance.py      # PROV-O tracking
│   └── api/
│       └── main.py            # FastAPI app
├── tests/
│   └── fixtures/              # Sample documents
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Acceptance Criteria

Per the Value Fabric specification:

- [x] Schema compliance: >95% pass Pydantic validation
- [x] No hallucinated entity types (strict schema enforcement)
- [x] Deduplication accuracy: >90% (embedding similarity 0.85)
- [x] Relationship precision: >85% (evidence required)
- [x] Throughput: 100 documents/hour per worker
- [x] RDF validates with Apache Jena (Turtle format)

## Dependencies

- **FastAPI**: REST API framework
- **Pydantic v2**: Data validation
- **OpenAI**: LLM for extraction (GPT-4o)
- **LangChain**: Semantic chunking
- **rdflib**: RDF/OWL generation
- **NumPy**: Embedding operations
- **Redis**: Job queue and caching

## Next Steps

1. Connect to Layer 3 (Neo4j) for persistence
2. Add Celery workers for distributed processing
3. Implement full APQC PCF mapping (currently basic mapping supported)
4. Add monitoring (Prometheus metrics)
5. Build ontology visualization tool
