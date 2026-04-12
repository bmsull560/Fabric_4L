# Value Fabric — Architecture

## Overview

Value Fabric is an AI-powered value selling platform built on a **4-layer pipeline architecture** that transforms raw, unstructured data into actionable business intelligence. Each layer is an independently deployable microservice with its own Docker Compose configuration, API surface, and test suite.

```
┌─────────────────────────────────────────────────────────────┐
│              LAYER 4: AGENTIC WORKFLOW ENGINE                │
│      (LangGraph · ROI Calculator · Business Case Generator) │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│          LAYER 3: KNOWLEDGE GRAPH & SEMANTIC LAYER          │
│       (Neo4j · GraphRAG · Hybrid Retrieval · pgvector)      │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│         LAYER 2: ONTOLOGY-GUIDED EXTRACTION PIPELINE        │
│    (Pydantic v2 · LLM Extraction · RDF/OWL · Provenance)    │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│           LAYER 1: INTELLIGENT DATA INGESTION SERVICE       │
│     (Playwright · Celery/Redis · PostgreSQL · Rate Limit)   │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 1 — Intelligent Data Ingestion Service

**Build order:** Phase 4 (built last, after Layer 3)  
**Status:** 🔄 Planned

### Purpose
Convert unstructured source materials (web pages, SEC filings, PDFs, APIs) into clean, normalized Markdown documents with full metadata.

### Components

| Component | Responsibility |
|-----------|---------------|
| **Scheduler Service** | Determines crawl targets and priorities |
| **Crawler Workers** | Headless Playwright browser instances executing extraction |
| **Post-Processor** | Cleans, deduplicates, and normalizes raw content to Markdown |
| **Source Registry** | Document metadata, freshness tracking, access URLs |

### Data Sources

| Priority | Sources |
|----------|---------|
| 1 | Corporate websites, SEC EDGAR filings (10-K/10-Q), earnings call transcripts |
| 2 | Competitor documentation, industry analyst reports, patent filings |
| 3 | LinkedIn company pages, news mentions (NewsAPI) |

### Compliance (Non-Negotiable)

- **robots.txt** parsing with 24-hour cache; never crawl Disallow paths
- **Rate limiting:** Global 1,000 req/min; per-domain 1 req/sec with 20% jitter
- **PII detection** with Microsoft Presidio — redact SSN, credit cards, phone, email; block pages with > 3 PII entities
- **Audit log:** URL, timestamp, IP, bytes downloaded, outcome (7-year retention)

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /crawl/website` | Start a site crawl; returns `{job_id, estimated_pages}` |
| `GET /crawl/status/{job_id}` | Poll crawl progress |
| `POST /crawl/sec-filings` | Fetch EDGAR filings by ticker |
| `GET /content/{content_id}` | Retrieve Markdown + metadata |
| `DELETE /content/{content_id}` | Soft delete with 30-day retention |

### Acceptance Criteria

- ≥ 1,000 pages/day throughput
- Zero robots.txt violations
- > 95% PII detection accuracy
- ≥ 4/5 Markdown readability score
- 99.5% API uptime

---

## Layer 2 — Ontology-Guided Extraction Pipeline

**Build order:** Phase 1 (built first)  
**Status:** ✅ Complete

### Purpose
Extract structured entities and relationships from ingested Markdown using LLMs, then serialize results as RDF/OWL with full provenance.

### Core Ontology (Pydantic v2 Models)

```
Capability → UseCase → Persona → ValueDriver
   ↓           ↓          ↓           ↓
[What we]  [How it's] [Who]     [Business]
[do]       [used]     [benefits] [outcome]
```

**Entity types:**

| Type | Description |
|------|-------------|
| `Capability` | Technical features or abilities (e.g., "Real-Time Data Ingestion") |
| `UseCase` | Business problem scenarios (e.g., "Touchless Accounts Payable") |
| `Persona` | Stakeholder roles: `economic_buyer`, `operational_user`, `stakeholder` |
| `ValueDriver` | Quantifiable outcomes: `revenue`, `cost`, `risk`, `capital` |

**Relationship types:** `enables`, `requires`, `benefits`, `drives`, `contributes_to`, `depends_on`, `alternative_to`

### Extraction Pipeline (6 Stages)

1. **Chunking & Preprocessing** — LangChain `RecursiveCharacterTextSplitter`; 2,000-token chunks, 200-token overlap
2. **Entity Extraction (LLM Call 1)** — GPT-4o or Claude 3.5 Sonnet; temperature 0.0; confidence threshold 0.8
3. **Relationship Extraction (LLM Call 2)** — Evidence-backed only; confidence threshold 0.75
4. **Semantic Alignment & Deduplication** — `text-embedding-3-large`; similarity threshold 0.85
5. **Validation & Normalization** — Pydantic schema validation; resolve all ID references
6. **RDF/OWL Serialization** — Turtle format; PROV-O provenance metadata; OWL axioms

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /v1/extract` | Start extraction job |
| `GET /v1/extract/status/{id}` | Check job status |
| `POST /v1/extract/batch` | Batch extraction |
| `POST /v1/extract-and-ingest` | Extract + push to Layer 3 in one call |
| `GET /v1/ontology/entities` | List entities |
| `GET /v1/audit/trace/{id}` | Full provenance trace |

### Acceptance Criteria

- > 95% Pydantic schema compliance
- Zero hallucinated entity types
- > 90% deduplication accuracy
- > 85% relationship precision (evidence-supported)
- 100 documents/hour per worker
- RDF validates with Apache Jena

---

## Layer 3 — Knowledge Graph & Semantic Layer

**Build order:** Phase 2 (after Layer 2)  
**Status:** ✅ Complete

### Purpose
Store, index, and query the structured knowledge graph; support GraphRAG and hybrid vector + graph retrieval.

### Data Model

**Nodes:** `:Capability`, `:UseCase`, `:Persona`, `:ValueDriver`, `:Formula`, `:Industry`

**Relationships:**

| Relationship | Direction |
|-------------|-----------|
| `ENABLES` | Capability → UseCase |
| `BENEFITS` | UseCase → Persona |
| `DRIVES` | UseCase → ValueDriver |
| `CONTRIBUTES_TO` | ValueDriver → ValueDriver (hierarchical) |
| `HAS_FORMULA` | ValueDriver → Formula |
| `APPLIES_TO` | Benchmark → Industry |

**Node properties:** `embedding` (1,536-dim), `confidence`, `source_url`, `extracted_at`

### GraphRAG Implementation

**Indexing Phase:**
- Entity embeddings stored in vector index
- Leiden community detection (Neo4j GDS)
- LLM-generated community summaries
- Hierarchical index built

**Retrieval Phase:**
- Vector search (cosine similarity) → entry nodes
- Graph traversal (BFS/DFS, max 3 hops) → connected subgraphs
- Reranking by relevance
- Citation support with source nodes

**Global Queries:** Use community summaries for broad questions (no vector search required)

### Semantic Layer

- Centralized metric definitions in YAML/JSON (ARR, NRR, CAC, LTV, Churn Rate)
- Row-level security filtered by JWT claims
- Column-level masking (hide formula parameters for non-admins)

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /v1/query/graph` | GraphRAG traversal with citations |
| `POST /v1/search/hybrid` | Vector + graph hybrid search |
| `POST /v1/ingest` | Ingest RDF from Layer 2 |
| `GET /v1/entities` | List entities |
| `POST /v1/query/value-tree` | Build full value chain from any node |
| `GET /health` / `GET /health/detailed` | Health checks |

### Performance Targets

| Query Type | Latency (p95) |
|-----------|--------------|
| Single-hop | < 50 ms |
| Multi-hop (3 levels) | < 200 ms |
| Vector + graph hybrid | < 500 ms |
| Concurrent connections | 1,000+ |
| Graph size | 10M nodes, 100M relationships |

### Acceptance Criteria

- > 90% multi-hop reasoning accuracy (vs. 60% vector-only baseline)
- Zero Cypher injection (pen tested)
- Semantic consistency: same metric = same value
- Full provenance trace < 500 ms

---

## Layer 4 — Agentic Workflow Engine

**Build order:** Phase 3 (after Layer 3)  
**Status:** 🔄 In Progress

### Purpose
Execute composable AI workflows for whitespace analysis, ROI calculation, business case generation, and provenance auditing.

### Agent Workflows

#### Workflow 1: Whitespace Analysis
`IngestProspect → ExtractInsights → MapToCapabilities → IdentifyWhitespace → GeneratePlan`  
**Output:** JSON account plan with whitespace opportunities, stakeholder map, entry strategy

#### Workflow 2: Dynamic ROI Calculator
Retrieves Value Tree from graph → safely evaluates formula strings (numexpr) → Monte Carlo sensitivity analysis  
**Output:** Deterministic ROI projection + risk assessment (best/worst/expected cases)

#### Workflow 3: Business Case Generator
Auto-generates Executive Summary, Current State, Proposed Solution, Financial Analysis, Risk Mitigation, Next Steps  
**Formats:** Markdown, DOCX, PDF, PPTX (10–15 slides)

#### Workflow 4: Provenance Audit Agent
Traverses PROV-O graph backward showing LLM calls → extractions → source documents with confidence scores at each step

### Skill Tiers

| Tier | Skills |
|------|--------|
| 1: Knowledge Navigation | `/graph_traverse`, `/semantic_search`, `/resolve_value_tree`, `/find_path` |
| 2: Reasoning | `/multi_hop_reason`, `/analyze_gaps` |
| 3: Calculation | `/evaluate_formula`, `/sensitivity_analysis` |
| 4: Content Generation | `/build_narrative`, `/generate_business_case`, `/write_executive_summary` |
| 5: Research | `/research_web`, `/analyze_competitor`, `/enrich_industry_context` |
| 6: Audit | `/trace_provenance`, `/escalate_to_human` |
| 7: Meta | `/value_fabric_help` |

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /agents/whitespace` | Start whitespace analysis workflow |
| `POST /agents/roi` | Execute ROI calculation |
| `POST /agents/business-case?format=pdf\|docx\|pptx` | Generate business case document |
| `GET /agents/status/{workflow_id}` | Poll workflow status |
| `POST /agents/{workflow_id}/approve` | Human-in-the-loop approval gate |

### Acceptance Criteria

- Whitespace analysis: < 5 minutes end-to-end
- ROI calculations deterministic (same inputs → same outputs)
- Business case documents rated ≥ 4/5 by sales team
- 99% workflow completion rate
- All actions logged with PROV-O metadata

---

## Data Flow

### Ingestion Flow

```
Source Document → Chunking → Embedding → Object Storage
                     ↓
               LLM Extraction → Entities + Relationships → RDF/OWL
                                                              ↓
                                                       Knowledge Graph (Neo4j)
```

### Query Flow

```
User Query → Agent Router → Skill Selection → Graph Query / Hybrid Search
                                                        ↓
                                              Confidence Check
                                                        ↓
                                     Response Synthesis / Human Escalation
```

### Generation Flow

```
Request → Value Tree Resolution → Formula Evaluation → Narrative → Document Assembly
              ↓                         ↓                  ↓
        Provenance Chain ← Evidence Quotes ← Source Documents
```

---

## Confidence & Provenance

### Confidence Scoring

Every entity, relationship, and generated output carries a confidence score (0.0–1.0) derived from:

- **Source quality** — authoritative vs. speculative
- **Extraction clarity** — explicit vs. inferred
- **Evidence strength** — direct quote vs. paraphrase
- **Model certainty** — logprob-based scoring

### Provenance Chain

```
Business Case → Narrative → Value Tree → Relationships → Extractions → Chunks → Documents
```

Each link records: timestamp, processing version, confidence, evidence quotes.

---

## Deployment Architecture

### Container Strategy

Each layer is an independently deployable container:

| Layer | Container | Port |
|-------|-----------|------|
| Layer 1 (Ingestion) | Document processing workers | 8000 |
| Layer 2 (Extraction) | LLM-based extraction (GPU-enabled) | 8000 |
| Layer 3 (Knowledge) | API server + Neo4j graph database | 8001 |
| Layer 4 (Agents) | LangGraph agent runtime | 8002 |

### Communication

- **Layer-to-layer:** REST/HTTP (async `httpx`)
- **Event streaming:** Redis / RabbitMQ for async Celery tasks
- **Storage:** PostgreSQL + Neo4j + MinIO (object storage)

### Scalability

- **Layers 1 & 2:** Horizontal scaling via Celery worker pools
- **Layer 3:** Read replicas for query load; Neo4j cluster for production
- **Layer 4:** Stateless agent runtime — scales with request volume

---

## Global Engineering Standards

| Standard | Requirement |
|----------|-------------|
| Language | Python 3.11+ with `async/await` |
| Type checking | Strict mypy |
| Formatting | Black |
| Linting | Ruff (zero warnings) |
| Test coverage | ≥ 85% (Layer 2) |
| Imports | Absolute only: stdlib → third-party → local |
| Commits | Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`) |
| Secrets | Environment variables only — no hardcoded secrets |
| Observability | Prometheus metrics, structured JSON logging, OpenTelemetry traces |
| API design | RESTful, `/v1/` prefix, standardized error format |
| Data provenance | URL + timestamp on all data |
| Confidence scores | 0.0–1.0 on all LLM outputs |

---

## Project Structure

```
Fabric_4L/
├── value-fabric/                # Core platform (Layers 1–4)
│   ├── layer1-ingestion/        # 🔄 Planned
│   ├── layer2-extraction/       # ✅ Complete
│   ├── layer3-knowledge/        # ✅ Complete
│   ├── layer4-agents/           # 🔄 In Progress
│   ├── layer5-ground-truth/     # Evaluation ground truth
│   ├── layer6-benchmarks/       # Benchmark service
│   └── shared/                  # Cross-layer Pydantic schemas
├── docs/                        # ADRs, runbooks, API specs
│   ├── architecture_overview.md
│   ├── pack_authoring_guide.md
│   └── product_brief.md
├── specs/                       # Detailed technical specifications
├── packs/                       # Domain-specific value packs
├── layer4-agents/               # Standalone agent skills & workflows
├── monitoring/                  # Prometheus / Grafana configuration
├── scripts/                     # Smoke tests, tooling scripts
├── artifacts/                   # Test reports and pipeline outputs
├── app.py                       # Streamlit sitemap utility
├── Architecture.md              # This file
└── Providers.md                 # External providers reference
```

---

*Document Version: 1.0*  
*Last Updated: April 2026*
