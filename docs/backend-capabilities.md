# Backend Capabilities Inventory

**Generated:** May 2, 2026  
**Scope:** All 6 Layers (L1-L6)  

---

## Layer 1: Ingestion Service

### Scope
Web data ingestion with Playwright crawling, Redis job queues, and compliance management.

### API Surface
- **Base:** `/api/v1/ingestion`
- **Endpoints:** 30+ routes

| Category | Endpoints | Status |
|----------|-----------|--------|
| Targets | GET/POST/PATCH/DELETE `/targets` | ✅ Active |
| Jobs | GET/POST `/jobs/{id}` (cancel, retry, results) | ✅ Active |
| Content | GET `/content` (raw, extracted) | ✅ Active |
| Compliance | GET/POST `/compliance` (logs, summary) | ✅ Active |
| Crawl Decisions | GET `/crawl-decisions` (HTTPX Fast Path) | ✅ Active |

### Connections
- **Output:** L2 Extraction via internal HTTPS
- **State:** PostgreSQL (jobs), Redis (queue), MinIO (documents)

### Limits
- Async job model (no synchronous responses)
- Requires Playwright/browser infrastructure
- No direct frontend integration; jobs polled via L3/L4

---

## Layer 2: Extraction Service

### Scope
LLM-powered entity extraction, ontology-guided processing, RDF/OWL generation.

### API Surface
- **Base:** `/api/v1/extraction`
- **Routes:** 5 modules (ontology, extraction, tier_policy)

| Category | Endpoints | Status |
|----------|-----------|--------|
| Ontology | GET/POST/PUT `/ontology/types`, `/ontology/schemas` | ✅ Active |
| Extraction | POST `/extract`, `/extract/async` | ✅ Active |
| Jobs | GET `/jobs/{id}` (progress, results) | ✅ Active |

### Connections
- **Input:** L1 raw content
- **Output:** L3 Knowledge Graph (RDF/OWL entities)
- **External:** OpenAI/Anthropic for LLM extraction

### Limits
- GPU worker dependency for LLM extraction
- Extraction job tracking (async only)
- No real-time streaming

---

## Layer 3: Knowledge Graph & Semantic Layer

### Scope
Neo4j graph storage, vector search (Pinecone), GraphRAG, entity analytics, DIL services.

### API Surface
- **Base:** `/v1/*`
- **Routers:** 15 modules, 96+ endpoints

| Router | Endpoints | Purpose |
|--------|-----------|---------|
| `value_packs.py` | 16 | Value pack management, deployment |
| `products.py` | 12 | Product portfolio (DIL Phase 1) |
| `competitive_intel.py` | 11 | Competitors, battlecards, win/loss (DIL Phase 2) |
| `formula_governance.py` | 10 | Formula approval workflows |
| `evidence.py` | 9 | Case study library (DIL Phase 1) |
| `formulas.py` | 8 | Formula CRUD, evaluation |
| `variables.py` | 8 | Variable registry |
| `roi_calculator.py` | 7 | ROI calc, templates, benchmarks (DIL Phase 2) |
| `entities.py` | 4 | Entity browser, subgraphs |
| `value_trees.py` | 2 | Value tree traversal |
| `benchmarks.py` | 4 | Benchmark data |
| `models.py` | 5 | Value model management |

### Connections
- **Database:** Neo4j (graph), PostgreSQL (metadata), Pinecone (vectors)
- **Input:** L2 extraction results
- **Output:** L4 Agents query this layer

### Limits
- Neo4j cluster dependency
- Tenant-scoped queries required
- Vector search requires Pinecone

---

## Layer 4: Agentic Workflow Engine

### Scope
LangGraph orchestration, multi-agent workflows, tool registry, real-time streaming, billing.

### API Surface
- **Base:** `/v1/*`
- **Routers:** 20 modules, 98+ endpoints

| Router | Endpoints | Purpose |
|--------|-----------|---------|
| `billing.py` | 25 | Stripe integration, usage, invoices |
| `workflows.py` | 11 | Workflow execution, state |
| `analysis.py` | 10 | Analysis workflows |
| `accounts.py` | 9 | Account CRUD, CRM sync |
| `value_hypotheses.py` | 7 | Value hypothesis generation (DIL Phase 2) |
| `integrations.py` | 6 | CRM integrations |
| `tools.py` | 6 | Tool registry |
| `narratives.py` | 5 | Narrative generation (DIL Phase 3) |
| `enrichment.py` | 4 | Account enrichment (DIL Phase 1) |
| `signals.py` | 4 | Signal detection |
| `agent_stream.py` | 1 | SSE streaming |
| `checkpoints.py` | 12 | Workflow checkpoints |
| `crm_webhooks.py` | 3 | CRM webhooks |
| `intelligence.py` | 3 | Intelligence orchestrator (DIL Phase 3) |

### Connections
- **Input:** L3 Knowledge Graph queries
- **Validation:** L5 Ground Truth
- **Benchmarks:** L6 Benchmarks
- **State:** PostgreSQL + Redis + Checkpoint Saver

### Limits
- PostgreSQL + Redis required
- Complex state management
- LangGraph dependency

---

## Layer 5: Ground Truth

### Scope
Fact validation, evidence grading, truth object lifecycle, provenance tracking.

### API Surface
- **Base:** Internal service (limited external exposure)
- **Router:** `layer5_ground_truth/src/layer5_ground_truth/api/router.py`

| Category | Endpoints | Status |
|----------|-----------|--------|
| Validation | POST `/validate` | ✅ Active |
| Truth Objects | CRUD `/truths/{id}` | ✅ Active |
| Audit Trail | GET `/truths/{id}/audit` | ✅ Active |
| Governance | GET `/stats`, `/maturity` | ✅ Active |
| Model Registry | 12 endpoints | ✅ Active |

### Connections
- **Called by:** L4 Agents during workflow execution
- **Storage:** PostgreSQL with audit triggers

### Limits
- Primarily internal service
- No direct frontend hooks

---

## Layer 6: Benchmarks

### Scope
Comparative intelligence, market benchmarks, industry analytics.

### API Surface
- **Base:** `/health`, `/v1/benchmarks`
- **Endpoints:** 5

| Endpoint | Purpose |
|----------|---------|
| GET `/benchmarks` | List benchmarks |
| GET `/benchmarks/{industry}` | Industry-specific |
| POST `/benchmarks/compare` | Comparative analysis |

### Connections
- **Called by:** L4 for ROI calculations
- **Source:** External market data + internal aggregation

### Limits
- Minimal frontend exposure
- Read-only service

---

## Summary Table

| Layer | Services | Endpoints | Frontend Hooks | Integration Status |
|-------|----------|-----------|----------------|-------------------|
| L1 | Ingestion | 30+ | 0 | Internal only |
| L2 | Extraction | 20+ | 0 | Internal only |
| L3 | Knowledge + DIL | 96+ | 38+ | ✅ Integrated |
| L4 | Agents + Billing | 98+ | 25+ | ✅ Integrated |
| L5 | Ground Truth | 10+ | 0 | Internal only |
| L6 | Benchmarks | 5+ | 0 | L4 proxy only |
