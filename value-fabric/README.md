# Value Fabric - Enterprise AI Platform

A production-grade semantic foundation for enterprise AI workflows that transforms unstructured data into structured, actionable knowledge through an ontology-guided pipeline.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 4: AGENTIC WORKFLOW ENGINE                            │
│ (LangGraph + ROI Calculator + Business Case Generator)    │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│ LAYER 3: KNOWLEDGE GRAPH & SEMANTIC LAYER                 │
│ (Neo4j + GraphRAG + Hybrid Retrieval + Vector Store)      │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│ LAYER 2: ONTOLOGY-GUIDED EXTRACTION PIPELINE              │
│ (Pydantic Models + LLM Extraction + RDF/OWL Generation)     │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│ LAYER 1: INTELLIGENT DATA INGESTION SERVICE                 │
│ (Playwright + Redis Queue + PostgreSQL + Rate Limiting)   │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Unstructured Data (Web/SEC/API)
    ↓
Markdown + Metadata (Layer 1)
    ↓
RDF/OWL Triples + Provenance (Layer 2)
    ↓
Knowledge Graph (Layer 3)
    ↓
GraphRAG Retrieval (Layer 3)
    ↓
Agent Workflows (Layer 4)
    ↓
ROI Calculations / Business Cases
```

## Build Status

| Layer | Status | Location |
|-------|--------|----------|
| **Layer 2: Extraction** | ✅ Complete | `layer2-extraction/` |
| **Layer 3: Knowledge Graph** | ✅ Complete | `layer3-knowledge/` |
| Layer 4: Agents | 🔄 Pending | `layer4-agents/` |
| Layer 1: Ingestion | 🔄 Pending | `layer1-ingestion/` |

## Core Ontology

The Value Fabric is built around 4 entity types:

### Capability
Technical features that enable business outcomes.

```python
Capability(
    name="Real-Time Data Ingestion",
    technical_features=["Kafka streaming", "CDC"],
    api_endpoints=["/api/v1/ingest"],
    integrations=["Salesforce", "SAP"]
)
```

### UseCase
Business problems being solved.

```python
UseCase(
    name="Touchless Accounts Payable",
    industry_context=["Finance", "Manufacturing"],
    required_capabilities=["cap-123", "cap-456"],
    workflow_steps=["Capture", "Match", "Approve", "Pay"]
)
```

### Persona
Stakeholders in the buying process.

```python
Persona(
    role_type="economic_buyer",
    title="Chief Financial Officer",
    department="Finance",
    pain_points=["Manual processes", "Lack of visibility"]
)
```

### ValueDriver
Quantifiable business outcomes.

```python
ValueDriver(
    category="cost",
    name="Operational Cost Reduction",
    formula_string="({hours_saved} * {hourly_rate}) - {impl_cost}",
    unit="USD"
)
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| **API Framework** | FastAPI (Python 3.11+) |
| **Data Models** | Pydantic v2 |
| **LLM** | GPT-4o / Claude 3.5 Sonnet |
| **Embeddings** | text-embedding-3-large |
| **Chunking** | LangChain |
| **Graph DB** | Neo4j 5.x (planned) |
| **RDF** | rdflib (Turtle) |
| **Queue** | Redis + Celery |
| **Vector Store** | Pinecone (planned) |
| **Agents** | LangGraph (planned) |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API Key
- Python 3.11+ (for local development)

### Run Layer 2 (Extraction Pipeline)

```bash
# 1. Clone and navigate
cd value-fabric

# 2. Set environment variables
export OPENAI_API_KEY=sk-...
export LLM_MODEL=gpt-4o

# 3. Start services
docker-compose up --build

# 4. Verify health
curl http://localhost:8000/health
```

### Extract from Sample Document

```bash
curl -X POST http://localhost:8000/v1/extract \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "content_id": "sample-001",
  "source_url": "https://example.com/product",
  "markdown_content": "# Real-Time Analytics\n\nOur platform enables...",
  "extraction_config": {
    "confidence_threshold": 0.75
  }
}
EOF
```

## Project Structure

```
value-fabric/
├── docker-compose.yml           # Local orchestration
├── README.md                    # This file
│
├── layer2-extraction/            # ✅ COMPLETE
│   ├── src/
│   │   ├── models/              # Ontology (Pydantic)
│   │   ├── extraction/          # Pipeline stages
│   │   ├── output/              # RDF/Provenance
│   │   └── api/                 # FastAPI
│   ├── tests/                   # Test suite
│   ├── Dockerfile
│   └── pyproject.toml
│
├── layer3-knowledge/             # ✅ COMPLETE
│   ├── src/
│   │   ├── ingestion/           # Neo4j RDF loader
│   │   ├── schema/              # Constraints & indexes
│   │   ├── retrieval/           # GraphRAG + hybrid search
│   │   ├── analytics/           # Community detection
│   │   └── api/                 # FastAPI (port 8001)
│   ├── tests/
│   ├── Dockerfile
│   ├── docker-compose.yml       # Neo4j + API
│   └── pyproject.toml
│
├── layer4-agents/                # 🔄 PLACEHOLDER
│   # LangGraph workflows
│
├── layer1-ingestion/             # 🔄 PLACEHOLDER
│   # Playwright scraping
│
└── shared/                       # 🔄 PLACEHOLDER
    └── schemas/                  # Cross-layer types
```

## Global Rules

This project follows strict standards:

### Code Quality
- Python 3.11+ with `async/await`
- Strict type hints (mypy)
- Black formatting, Ruff linting
- 85% test coverage for Layer 2

### Data Governance
- Provenance: Every data point traces to source
- Confidence scores: 0.0-1.0 on all LLM outputs
- Schema validation: Zero tolerance for violations

### Security
- No hardcoded secrets (env vars only)
- PII detection with Presidio
- Rate limiting: 1000 req/min

### Observability
- Prometheus metrics
- Structured JSON logging
- OpenTelemetry traces

See full rules in project documentation.

## API Documentation

Layer 2 (Extraction) provides these endpoints:

| Endpoint | Description |
|----------|-------------|
| `POST /v1/extract` | Start extraction job |
| `GET /v1/extract/status/{id}` | Check job status |
| `POST /v1/extract/batch` | Batch extraction |
| `GET /v1/ontology/entities` | List entities |
| `GET /v1/audit/trace/{id}` | Full provenance |

OpenAPI spec available at `http://localhost:8000/docs`

## Roadmap

### Phase 1: Layer 2 ✅
- [x] Ontology models (Pydantic)
- [x] Semantic chunking
- [x] LLM extraction (OpenAI function calling)
- [x] Relationship extraction
- [x] Deduplication (embeddings)
- [x] RDF/OWL generation
- [x] Provenance tracking
- [x] FastAPI endpoints
- [x] Docker Compose setup

### Phase 2: Layer 3 ✅
- [x] Neo4j schema
- [x] RDF ingestion pipeline
- [x] GraphRAG retrieval
- [x] Vector index (Pinecone)
- [x] Community detection
- [x] Semantic layer

### Phase 3: Layer 4 🔄
- [ ] LangGraph workflow engine
- [ ] Whitespace analysis agent
- [ ] ROI calculator
- [ ] Business case generator
- [ ] Tool registry (24 skills)

### Phase 4: Layer 1 🔄
- [ ] Playwright scraping
- [ ] Redis job queue
- [ ] robots.txt compliance
- [ ] PII detection
- [ ] Rate limiting

## Contributing

### Setup

```bash
# 1. Install dependencies
cd layer2-extraction
pip install -e ".[dev]"

# 2. Run tests
pytest tests/ -v

# 3. Code quality
black src/ && ruff check src/
```

### Branch Naming
- `layer-2/feature/description`
- `fix/layer-2/bug-description`

### Commits
Use conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `refactor:` Code refactoring
- `test:` Tests

## License

Proprietary - Value Fabric Enterprise Platform

## Support

For questions or issues:
- Architecture: See `docs/adrs/`
- Runbook: See `docs/runbooks/`
- API: See OpenAPI spec at `/docs`
