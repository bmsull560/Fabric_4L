# Layer 3: Knowledge Graph & Semantic Layer

Layer 3 of the Value Fabric platform consumes RDF/OWL triples from Layer 2 and provides a queryable knowledge graph with GraphRAG retrieval capabilities.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 3: KNOWLEDGE GRAPH                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │ RDF Ingestion   │  │ GraphRAG        │  │ Analytics     │  │
│  │ - Neo4j Loader  │  │ - Multi-hop       │  │ - Communities │  │
│  │ - Schema Init   │  │ - Vector Search   │  │ - Centrality  │  │
│  │ - Sync Manager  │  │ - Hybrid Search   │  │ - Similarity  │  │
│  └────────┬────────┘  └────────┬────────┘  └───────┬───────┘  │
│           │                    │                    │          │
│           └────────────────────┼────────────────────┘          │
│                                │                               │
│                     ┌──────────▼──────────┐                    │
│                     │   Neo4j 5.x         │                    │
│                     │   + GDS Library     │                    │
│                     └─────────────────────┘                    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Pinecone API key (optional, for vector search)

### Run with Docker

```bash
# 1. Set environment variables
export PINECONE_API_KEY=your_key_here  # Optional

# 2. Start services
docker-compose up -d

# 3. Wait for Neo4j to initialize (first run takes ~30s)
sleep 30

# 4. Verify health
curl http://localhost:8001/health
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/v1/ingest` | POST | Ingest RDF data from Layer 2 |
| `/v1/query` | POST | GraphRAG natural language query |
| `/v1/search` | POST | Hybrid entity search |
| `/v1/entity/{id}/context` | GET | Get entity neighborhood |
| `/v1/entity/traverse` | POST | Traverse 4-layer value tree |
| `/v1/analytics/communities` | POST | Detect communities |
| `/v1/analytics/centrality` | POST | Calculate centrality |
| `/v1/analytics/similar` | POST | Find similar entities |
| `/v1/analytics/compare` | POST | Compare two entities |
| `/v1/schema/status` | GET | Schema verification |

### Example Usage

#### Ingest RDF Data

```bash
curl -X POST http://localhost:8001/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "rdf_data": "@prefix vf: <https://valuefabric.io/ontology/> . vf:cap-1 a vf:Capability ; vf:name \"Real-Time Data Ingestion\" .",
    "source_id": "doc-001",
    "extraction_job_id": "job-123"
  }'
```

#### GraphRAG Query

```bash
curl -X POST http://localhost:8001/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How can data processing capabilities benefit finance teams?",
    "entity_type": "Capability",
    "max_hops": 3,
    "max_results": 10
  }'
```

#### Hybrid Search

```bash
curl -X POST http://localhost:8001/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "real-time analytics",
    "search_type": "hybrid",
    "top_k": 10
  }'
```

#### Detect Communities

```bash
curl -X POST http://localhost:8001/v1/analytics/communities \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm": "louvain",
    "entity_types": ["Persona", "UseCase"],
    "min_community_size": 3
  }'
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `password` | Neo4j password |
| `PINECONE_API_KEY` | - | Pinecone API key (optional) |
| `API_PORT` | `8001` | API server port |

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Code quality
black src/ && ruff check src/
```

## Project Structure

```
layer3-knowledge/
├── src/
│   ├── __init__.py
│   ├── config.py              # Settings management
│   ├── ingestion/             # RDF → Neo4j pipeline
│   ├── schema/                # Neo4j constraints & indexes
│   ├── retrieval/             # GraphRAG, hybrid search
│   ├── analytics/             # Community detection, centrality
│   └── api/                   # FastAPI application
├── tests/                     # Test suite
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Integration

- **Input**: RDF/Turtle from Layer 2 extraction pipeline
- **Output**: GraphRAG results to Layer 4 agent workflows
