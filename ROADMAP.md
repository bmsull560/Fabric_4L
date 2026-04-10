# Value Fabric Platform - Completion Roadmap

**Repository:** https://github.com/bmsull560/Fabric_4L  
**Audit Date:** 2026-04-09  
**Total Files:** 338  
**Frontend Files:** 96  
**Python Files:** 100+

---

## Executive Summary

The Value Fabric platform has substantial implementation across all 4 original layers:

| Layer | Completion | Status | Key Gaps |
|-------|-----------|--------|----------|
| **L1: Ingestion** | ~75% | Advanced | Celery/Redis wiring, monitoring |
| **L2: Extraction** | ~85% | Advanced | `/extract-and-ingest` endpoint, L3 pipeline |
| **L3: Knowledge Graph** | ~75% | Advanced | Vector indexes, GraphRAG tuning |
| **L4: Agents** | ~70% | Advanced | LangGraph wiring, resume endpoints |
| **L5: Ground Truth** | ~100% | Production Ready | ✅ Complete |
| **Frontend** | ~65% | Advanced | TanStack Query, API integration |
| **DevOps/Infra** | ~40% | Intermediate | Docker Compose ready, needs CI/CD |

---

## Layer-by-Layer Analysis

### **LAYER 1: Intelligent Data Ingestion Service** (75% Complete)

**What's Built:**
- ✅ FastAPI application with full REST API (`/api/v1/ingestion`)
- ✅ SQLAlchemy models with migrations (Alembic)
- ✅ Playwright crawler implementation
- ✅ PII scanner (compliance)
- ✅ robots.txt checker
- ✅ SEC EDGAR adapter
- ✅ XBRL parser
- ✅ Priority queue scheduler
- ✅ Content extractor/post-processor
- ✅ Unit tests

**What's Missing:**
- ⚠️ Celery task queue integration (stubs exist, not wired to L2)
- ⚠️ Redis integration for distributed processing
- ❌ Proxy rotation implementation
- ⚠️ Rate limiting enforcement (partial)
- ✅ S3/MinIO integration configured in docker-compose
- ❌ Production monitoring/alerting
- ❌ Kubernetes deployment manifests

**Key Files:**
```
value-fabric/layer1-ingestion/src/api/main.py          # FastAPI routes
value-fabric/layer1-ingestion/src/shared/models.py     # Database models
value-fabric/layer1-ingestion/src/crawler/playwright_crawler.py
value-fabric/layer1-ingestion/src/compliance/pii_scanner.py
```

---

### **LAYER 2: Ontology-Guided Extraction Pipeline** (65% Complete)

**What's Built:**
- ✅ Pydantic ontology models (Capability, UseCase, Persona, ValueDriver)
- ✅ Relationship definitions
- ✅ Text chunker implementation
- ✅ Semantic aligner (deduplication)
- ✅ Coreference resolver
- ✅ RDF/OWL generator
- ✅ Provenance tracker
- ✅ Entailment validator stub

**What's Missing:**
- ✅ LLM integration (OpenAI/Anthropic client) - COMPLETE
- ✅ Prompt templates for extraction - COMPLETE
- ✅ Function calling schema implementation - COMPLETE
- ✅ Vector embedding generation - COMPLETE
- ❌ APQC/BIAN/FIBO reference model integration
- ✅ Full validation pipeline orchestration - COMPLETE
- ✅ Confidence scoring mechanism - COMPLETE

**Key Files:**
```
value-fabric/layer2-extraction/src/models/ontology.py
value-fabric/layer2-extraction/src/extraction/llm_extractor.py    # Stub
value-fabric/layer2-extraction/src/output/rdf_generator.py
value-fabric/layer2-extraction/src/alignment/semantic_aligner.py
```

---

### **LAYER 3: Knowledge Graph + Semantic Layer** (70% Complete)

**What's Built:**
- ✅ Extensive FastAPI application structure
- ✅ GraphRAG retrieval implementation
- ✅ Hybrid search (vector + graph)
- ✅ Vector store abstraction
- ✅ Community detection (Leiden)
- ✅ Similarity analytics
- ✅ Centrality metrics
- ✅ Agent implementations (whitespace, ROI, narrative, provenance)
- ✅ API middleware, rate limiting, auth stubs
- ✅ Redis cache abstraction
- ✅ Prometheus metrics stubs
- ✅ Comprehensive test suite

**What's Missing:**
- ✅ Neo4j connection (driver implemented, docker-compose wired)
- ⚠️ Neo4j vector indexes (schema defined, needs verification)
- ❌ Pinecone/Weaviate integration
- ✅ GraphRAG query endpoint exists (needs E2E verification)
- ❌ Semantic layer metric definitions
- ⚠️ Row-level security implementation (partial)
- ❌ Production performance tuning

**Key Files:**
```
value-fabric/layer3-knowledge/src/api/main.py
value-fabric/layer3-knowledge/src/retrieval/graph_rag.py
value-fabric/layer3-knowledge/src/retrieval/hybrid_search.py
value-fabric/layer3-knowledge/src/agents/whitespace_analysis.py
value-fabric/layer3-knowledge/src/schema/initializer.py
```

---

### **LAYER 4: Agentic Workflow Engine** (60% Complete)

**What's Built:**
- ✅ Tool registry structure
- ✅ Knowledge tools, calculation tools, generation tools
- ✅ Workflow base classes
- ✅ Business case, ROI calculator, whitespace workflows
- ✅ Agent state models (Pydantic)
- ✅ Message bus abstraction
- ✅ Tenant context middleware
- ✅ Provenance store
- ✅ Layer 1/2/3 client integrations

**What's Missing:**
- ✅ LangGraph state machine (base classes implemented)
- ⚠️ Workflow executor engine (partial, needs OrchestrationController wiring)
- ⚠️ State manager persistence (AsyncPostgresSaver configured)
- ❌ Human-in-the-loop integration (`/resume` endpoint)
- ✅ Workflow scheduler (TaskScheduler implemented)
- ✅ Tool execution orchestration (ToolRegistry wired)
- ❌ Agent decision logic (which workflow to run)

**Key Files:**
```
value-fabric/layer4-agents/src/tools/registry.py
value-fabric/layer4-agents/src/workflows/business_case.py
value-fabric/layer4-agents/src/workflows/roi_calculator.py
value-fabric/layer4-agents/src/workflows/whitespace.py
value-fabric/layer4-agents/src/models/agent_state.py
value-fabric/layer4-agents/src/engine/executor.py    # Stub
```

---

### **LAYER 5: Ground Truth Layer** (95% Complete) ⭐ PRODUCTION READY

**What's Built:**
- ✅ TruthObject SQLAlchemy model with all fields
- ✅ TruthSource, ValidationEvent, MaturityHistory models
- ✅ Validation state machine (extracted → supported → corroborated → approved)
- ✅ Maturity ladder (0-5 levels) with progression tracking
- ✅ FastAPI with full REST API (/api/v1/truths)
- ✅ Layer 3 Knowledge Graph integration client
- ✅ Auto-advancement logic
- ✅ Dispute resolution workflow
- ✅ Comprehensive test suite

**What's Missing:**
- ⚠️ Production hardening (rate limiting exists, needs monitoring dashboards)
- ❌ Human approval workflow UI integration (frontend)
- ✅ Background scheduler integration (FreshnessMonitor complete)

**This is a critical new layer** that separates inferred from verified facts.

---

### **Frontend** (65% Complete)

**What's Built:**
- ✅ React + TypeScript application
- ✅ shadcn/ui component library (complete)
- ✅ Routing with wouter
- ✅ Page structure for all major features:
  - Command Center
  - Extraction Engine
  - Ontology Browser
  - Value Tree Explorer
  - Formula Builder
  - Graph Explorer
  - Agent Workflows
  - Business Case
  - Decision Trace
- ✅ AppShell layout
- ✅ Theme context
- ✅ Error boundaries

**What's Missing:**
- ❌ API client integration (TanStack Query)
- ❌ State management (Zustand/Redux)
- ❌ Backend API connection (real HTTP client)
- ❌ Real data fetching (currently mock data)
- ⚠️ Loading/error states (ErrorBoundaries exist, need API error handling)
- ❌ Form handling (React Hook Form)
- ⚠️ Authentication UI (middleware exists, UI not connected)

**Key Files:**
```
frontend/client/src/App.tsx
frontend/client/src/components/AppShell.tsx
frontend/client/src/pages/CommandCenter.tsx
frontend/client/src/components/ui/    # shadcn components
```

---

### **DevOps & Infrastructure** (20% Complete)

**What's Built:**
- ✅ Basic Docker awareness (some services)
- ✅ Alembic migrations

**What's Missing:**
- ✅ Docker Compose for local development (root docker-compose.yml complete)
- ❌ Kubernetes manifests
- ❌ Terraform/CloudFormation
- ❌ CI/CD pipeline (GitHub Actions)
- ✅ Environment configuration (.env.example exists)
- ⚠️ Secrets management (env var based, needs Vault/integration)
- ⚠️ Monitoring stack (stubs exist, needs Grafana)
- ⚠️ Logging aggregation (structured logging, needs aggregation)

---

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEPENDENCY FLOW                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  L1: Ingestion ─────────────────┐                               │
│  (75% complete)                 │                               │
│  Missing: Celery, Redis, S3     │                               │
│                                 ▼                               │
│  L2: Extraction ────────────────┤                               │
│  (65% complete)                 │                               │
│  Missing: LLM client, prompts   │                               │
│  BLOCKED BY: L1 (needs content) │                               │
│                                 ▼                               │
│  L3: Knowledge Graph ───────────┤                               │
│  (70% complete)                 │                               │
│  Missing: Neo4j connection      │                               │
│  BLOCKED BY: L2 (needs RDF)     │                               │
│                                 ▼                               │
│  L5: Ground Truth ──────────────┤  ◄── 95% COMPLETE             │
│  (95% complete)                 │                               │
│  Missing: Background scheduler    │                               │
│  ← L3 (writes to KG)            │                               │
│                                 ▼                               │
│  L4: Agents ────────────────────┤                               │
│  (60% complete)                 │                               │
│  Missing: LangGraph wiring      │                               │
│  BLOCKED BY: L3 (needs graph)   │                               │
│                                 ▼                               │
│  Frontend ──────────────────────┘                               │
│  (65% complete)                                                 │
│  Missing: API integration                                       │
│  BLOCKED BY: L4 (needs endpoints)                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5 Prioritized Next Tasks

### **Task 1: Implement Freshness Monitoring (L5)** ⭐ CRITICAL ✅ COMPLETE
**Priority:** P0 | **Effort:** 1 day | **Status:** COMPLETED 2026-04-09

**Why First:**
- Ground Truth layer is 100% complete — freshness monitoring was the final gap
- Required for production: automatically marks expired truths as stale

**Delivered:**
- `value-fabric/layer5-ground-truth/src/services/freshness_monitor.py` (112 lines)
- `POST /truths/check-stale` endpoint
- `GET /truths/stale` query endpoint
- `GET /truths/freshness-summary` analytics endpoint
- Configurable TTL per claim_type in config
- 52-match comprehensive test suite
- **Status: COMPLETED** ✅

---

### **Task 2: Wire LLM Integration (L2)** ⭐ CRITICAL ✅ COMPLETE
**Priority:** P0 | **Effort:** 2-3 days | **Status:** COMPLETED 2026-04-09

**Why Second:**
- Layer 2 required LLM client for extraction pipeline
- Now unblocks Neo4j ingestion and knowledge graph population

**Delivered:**
- `layer2-extraction/src/shared/llm_client.py` - Unified async client with OpenAI/Anthropic
- `layer2-extraction/src/extraction/llm_extractor.py` - Entity & Relationship extractors
- 6 prompt templates for entity extraction
- Function calling with strict JSON schema output
- Confidence scoring from logprobs
- Cost tracking (`CostRecord`, `PRICING` dictionary)
- Exponential backoff retry logic
- **Status: COMPLETED** ✅

**Files Modified:**
- `src/shared/llm_client.py` - Unified client with optional OpenAI/Anthropic
- `src/extraction/llm_extractor.py` - Entity & Relationship extractors
- `src/models/__init__.py` - Fixed exports (RoleType, ValueCategory, ExtractionResult)
- `src/validation/entailment_validator.py` - Fixed absolute imports
- `src/alignment/semantic_aligner.py` - Fixed absolute imports
- `src/extraction/deduplicator.py` - Fixed absolute imports
- `src/coreference/coreference_resolver.py` - Fixed absolute imports

---

### **Task 3: Connect Neo4j (L3)** 🔄 IN PROGRESS
**Priority:** P0 | **Effort:** 2-3 days | **Status:** ~70% Complete

**Current State:**
- ✅ `layer3-knowledge/src/db/driver.py` - Async Neo4j driver with retry logic (159 lines)
- ✅ `docker-compose.yml` - Neo4j 5-community service configured
- ✅ `layer2-extraction/src/integration/layer3_client.py` - L2→L3 HTTP client (415 lines)
- ✅ `layer3-knowledge/src/ingestion/neo4j_loader.py` - RDF to Neo4j loader (383 lines)
- ✅ `layer3-knowledge/src/schema/initializer.py` - Schema constraints/indexes (252 lines)

**Remaining:**
- [ ] Verify vector index creation with real embeddings
- [ ] Wire `POST /v1/ingest` through to Neo4j loader
- [ ] End-to-end test: L2 extract → L3 ingest → Neo4j query
- [ ] GraphRAG query execution with real multi-hop traversal
- [ ] Hybrid search with vector + graph ranking

---

### **Task 4: LangGraph Workflow Engine (L4)** 🔄 IN PROGRESS
**Priority:** P1 | **Effort:** 4-5 days | **Status:** ~60% Complete

**Current State:**
- ✅ `layer4-agents/src/workflows/base.py` - BaseWorkflow with LangGraph StateGraph (404 lines)
- ✅ `layer4-agents/src/engine/executor.py` - OrchestrationController with task scheduler (586 lines)
- ✅ `layer4-agents/src/tools/registry.py` - ToolRegistry with 24+ skills (342 lines)

**Remaining:**
- [ ] AsyncPostgresSaver configuration for checkpointing
- [ ] OrchestrationController → LangGraph facade refactoring
- [ ] `interrupt_before` / `interrupt_after` for human-in-the-loop
- [ ] `POST /v1/workflows/{id}/resume` endpoint
- [ ] Workflow resumption after interruption
- [ ] Tool execution error recovery

---

### **Task 5: Frontend API Integration** 🔴 NOT STARTED
**Priority:** P1 | **Effort:** 3-4 days | **Status:** 0% Complete | **Blocked by:** Task 6

**Why Next:**
- Frontend has complete UI (10 screens) but all mock data
- 12 critical gaps identified in UI/backend analysis
- Cannot integrate until backend APIs return real data

**Required:**
- [ ] TanStack Query setup with caching
- [ ] Zustand state management stores
- [ ] API client with error handling
- [ ] Real data fetching: Command Center (ingestion jobs)
- [ ] Real data fetching: Ontology Browser (entities)
- [ ] Real data fetching: Graph Explorer (nodes/edges)
- [ ] Real data fetching: Agent Workflows (workflow status)
- [ ] Form submissions with React Hook Form

---

## New Approved Tasks (Added 2026-04-10)

### **Task 6: L2→L3 Pipeline Endpoint (L2)** ⭐ CRITICAL
**Priority:** P0 | **Effort:** 1 day | **Status:** 0% Complete | **Unblocks:** End-to-end extraction

**Gap:** L2 has `Layer3KnowledgeClient` but no `/extract-and-ingest` endpoint to trigger it.

**Acceptance Criteria:**
- [ ] `POST /v1/extract-and-ingest` endpoint in `layer2-extraction/src/api/main.py`
- [ ] Background task calls `Layer3KnowledgeClient.ingest_extraction_result()`
- [ ] Returns job ID that tracks both extraction and ingestion status
- [ ] Configurable: skip ingestion if L3 unavailable (queue for retry)

**Implementation:**
- Modify: `layer2-extraction/src/api/main.py` (add endpoint, lines ~410-420)
- Uses existing: `layer2-extraction/src/integration/layer3_client.py`

---

### **Task 7: Neo4j Vector Indexes + E2E Verification (L3)** ⭐ CRITICAL
**Priority:** P0 | **Effort:** 2 days | **Status:** ~50% Complete | **Unblocks:** GraphRAG, Hybrid Search

**Gap:** Neo4j driver exists but vector indexes and end-to-end pipeline need verification.

**Acceptance Criteria:**
- [ ] Vector index creation for entity embeddings (Neo4j 5.x native vector index)
- [ ] Auto-generate embeddings on entity ingestion
- [ ] `POST /v1/ingest` creates nodes with embeddings in Neo4j
- [ ] `POST /v1/query/graph` returns multi-hop results from real Neo4j data
- [ ] `POST /v1/search/hybrid` combines vector + graph scores
- [ ] E2E test passes: Extract → Ingest → Query

**Implementation:**
- Modify: `layer3-knowledge/src/schema/initializer.py` (add vector index setup)
- Modify: `layer3-knowledge/src/ingestion/neo4j_loader.py` (embedding generation)
- Create: `layer3-knowledge/tests/test_e2e_pipeline.py` (NEW)

---

### **Task 8: LangGraph Checkpointing + Resume (L4)** ⭐ CRITICAL
**Priority:** P0 | **Effort:** 3 days | **Status:** ~40% Complete | **Unblocks:** Human-in-the-loop, fault tolerance

**Gap:** BaseWorkflow has LangGraph but no checkpointing or resume capability.

**Acceptance Criteria:**
- [ ] `AsyncPostgresSaver` configured in `docker-compose.yml`
- [ ] `POST /v1/workflows/{id}/resume` endpoint works
- [ ] Workflows pause at `interrupt_before` nodes
- [ ] Resume with user input continues workflow
- [ ] State survives container restart

**Implementation:**
- Modify: `layer4-agents/src/workflows/base.py` (add checkpointer to compile())
- Modify: `layer4-agents/src/engine/executor.py` (facade pattern, thread_id=workflow_id)
- Modify: `layer4-agents/src/api/routes/workflows.py` (add /resume endpoint)
- Update: `docker-compose.yml` (add Postgres service for LangGraph)

---

### **Task 9: Frontend Core API Integration** ⭐ CRITICAL
**Priority:** P0 | **Effort:** 3 days | **Status:** 0% Complete | **Blocked by:** Task 6, 7 | **Unblocks:** User testing

**Gap:** 10-screen UI exists but all mock data. Cannot connect until backend APIs work.

**Acceptance Criteria:**
- [ ] TanStack Query client with caching and error handling
- [ ] Zustand stores: `ontologyStore`, `workflowStore`, `analysisStore`
- [ ] Command Center shows real ingestion jobs from `GET /v1/ingestion/jobs`
- [ ] Ontology Browser queries real entities from `GET /v1/entities`
- [ ] Agent Workflows lists real workflows from `GET /v1/workflows`
- [ ] Graph Explorer shows real nodes/edges from `POST /v1/graph/query`

**Implementation:**
- Create: `frontend/client/src/lib/queryClient.ts`
- Create: `frontend/client/src/stores/ontologyStore.ts`, `workflowStore.ts`
- Create: `frontend/client/src/hooks/useEntities.ts`, `useWorkflows.ts`
- Modify: `frontend/client/src/pages/CommandCenter.tsx`, `OntologyBrowser.tsx`, `AgentWorkflows.tsx`

---

### **Task 10: Extraction Streaming + Job Status (L2/Frontend)**
**Priority:** P1 | **Effort:** 2 days | **Status:** 0% Complete | **Unblocks:** Live monitoring

**Gap:** Extraction Engine UI shows static 68% progress; needs real-time updates.

**Acceptance Criteria:**
- [ ] SSE endpoint `GET /v1/jobs/{id}/events` streams step progress
- [ ] Frontend WebSocket/SSE connection displays live terminal output
- [ ] Pipeline steps update: chunking → NER → semantic → assembly
- [ ] Entity chips populate as discovered
- [ ] Job completion/failure events propagate immediately

**Implementation:**
- Modify: `layer2-extraction/src/api/main.py` (add SSE streaming)
- Create: `frontend/client/src/hooks/useJobStream.ts` (WebSocket/SSE hook)
- Modify: `frontend/client/src/pages/ExtractionEngine.tsx` (live terminal)

---

### **Task 11: Formula Builder + Value Tree APIs (L3/Frontend)**
**Priority:** P1 | **Effort:** 2 days | **Status:** 0% Complete | **Unblocks:** ROI calculations

**Gap:** Formula Builder UI non-functional; needs evaluation backend.

**Acceptance Criteria:**
- [ ] `POST /v1/formulas/evaluate` executes formulas with variables
- [ ] `GET /v1/formulas/variables` lists available variables
- [ ] `GET /v1/value-trees/{id}` returns resolved value tree
- [ ] Formula Builder evaluates and shows results
- [ ] Value Tree Explorer displays actual tree data

**Implementation:**
- Create: `layer3-knowledge/src/api/routes/formulas.py`
- Create: `layer3-knowledge/src/api/routes/value_trees.py`
- Modify: `frontend/client/src/pages/FormulaBuilder.tsx`
- Modify: `frontend/client/src/pages/ValueTreeExplorer.tsx`

---

### **Task 12: Document Export + Provenance APIs (L3/L4/Frontend)**
**Priority:** P1 | **Effort:** 2 days | **Status:** 0% Complete | **Unblocks:** Business case sharing

**Gap:** Business Case UI has Export button (no-op); Decision Trace shows mock audit logs.

**Acceptance Criteria:**
- [ ] `POST /v1/documents/export` generates PDF from business case
- [ ] `GET /v1/provenance/{entity_id}` returns full audit trail
- [ ] `GET /v1/audit/logs` lists system audit events
- [ ] Export button functional in Business Case page
- [ ] Decision Trace shows real provenance data

**Implementation:**
- Create: `layer4-agents/src/tools/document_export.py` (PDF generation)
- Modify: `layer3-knowledge/src/api/main.py` (add provenance endpoints)
- Create: `frontend/client/src/hooks/useProvenance.ts`
- Modify: `frontend/client/src/pages/DecisionTrace.tsx`, `BusinessCase.tsx`

---

### **Task 13: Monitoring + Health Dashboards**
**Priority:** P2 | **Effort:** 2 days | **Status:** ~20% Complete | **Unblocks:** Production confidence

**Gap:** Prometheus stubs exist; Grafana dashboards missing.

**Acceptance Criteria:**
- [ ] Prometheus metrics endpoint `/metrics` on all layers (real counters, not zeros)
- [ ] Grafana dashboard JSON for Value Fabric
- [ ] Structured JSON logging with correlation IDs
- [ ] Health checks show dependency status (not just "healthy")
- [ ] Alerting rules: high error rate, slow queries, disk space

**Implementation:**
- Modify: All `src/api/main.py` (replace mocked metrics with real counters)
- Create: `monitoring/grafana/dashboards/value-fabric.json`
- Create: `monitoring/alerting/rules.yml`
- Update: `layer3-knowledge/src/api/main.py:599-611` (active_connections, total_requests)

---

### **Task 14: CI/CD Pipeline (GitHub Actions)**
**Priority:** P2 | **Effort:** 2 days | **Status:** 0% Complete | **Unblocks:** Automated deployment

**Gap:** No automated testing or deployment pipeline.

**Acceptance Criteria:**
- [ ] PR checks: lint, test, build for all layers
- [ ] Main branch: test, build, push to container registry
- [ ] Integration tests with `docker-compose up`
- [ ] Image tagging: sha, branch, latest
- [ ] Secrets management for staging/production

**Implementation:**
- Create: `.github/workflows/pr-checks.yml`
- Create: `.github/workflows/build-deploy.yml`
- Create: `.github/workflows/integration-tests.yml`

---

## Updated Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPROVED TASK FLOW (2026-04-10)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Task 6: L2→L3 Endpoint ────────┐                                 │
│  (P0 - Backend)                │                                 │
│                                ▼                                 │
│  Task 7: Neo4j Vector ─────────┼──────┐                          │
│  (P0 - Backend)                │       │                         │
│                                ▼       ▼                         │
│  Task 8: LangGraph Resume ──────┘       │                         │
│  (P0 - Agents)                         │                         │
│                                ▼       ▼                         │
│  Task 9: Frontend Core ────────┴───────┘                         │
│  (P0 - Frontend)                                               │
│                                │                                 │
│            ┌───────────────────┼───────────────────┐             │
│            ▼                   ▼                   ▼             │
│      Task 10:            Task 11:            Task 12:          │
│      Streaming            Formulas            Export/            │
│      (P1)                 (P1)                Provenance       │
│                                                                │
│            ┌───────────────────┴───────────────────┐             │
│            ▼                                       ▼             │
│      Task 13: Monitoring                    Task 14: CI/CD       │
│      (P2)                                   (P2)                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Alternative: Parallel Track Approach

If you have resources to work in parallel:

**Track A (Backend Core):**
- Task 1: Freshness Monitoring (L5)
- Task 2: LLM Integration (L2)
- Task 3: Neo4j Connection (L3)

**Track B (Agent Orchestration):**
- Task 4: LangGraph Workflows (L4)

**Track C (Frontend):**
- Task 5: API Integration (Frontend)
- Polish UI components
- Add missing pages

**Track D (DevOps):**
- Docker Compose setup
- Kubernetes manifests
- CI/CD pipeline

---

## Quick Wins (1-2 days each)

1. **Docker Compose for Local Dev**
   - PostgreSQL, Redis, Neo4j, MinIO
   - All services running together

2. **Environment Configuration**
   - `.env` files for all layers
   - Configuration validation

3. **API Documentation**
   - OpenAPI specs for all endpoints
   - Postman collection

4. **Health Check Endpoints**
   - `/health` for each service
   - Dependency status

---

## Definition of "Production Ready"

| Criterion | Current | Target | Responsible Task |
|-----------|---------|--------|------------------|
| End-to-end workflow | ❌ | ✅ | Task 6 + 7 |
| All APIs responding | ⚠️ (partial) | ✅ | Task 6 + 8 |
| Frontend showing real data | ❌ | ✅ | Task 9 |
| Tests passing | ⚠️ (~60%) | >80% | Task 7 (E2E) |
| Docker deployment | ✅ | ✅ | Task 9 (compose ready) |
| Monitoring | ⚠️ (stubs) | ✅ | Task 13 |
| Documentation | ⚠️ (specs only) | Complete | Ongoing |

---

## Recommended Kimi Prompts

### Prompt 1: Freshness Monitoring Service (L5)
```
Implement the Freshness Monitoring service for Layer 5 Ground Truth at:
https://github.com/bmsull560/Fabric_4L

Create: value-fabric/layer5-ground-truth/src/services/freshness_monitor.py
Add endpoint: value-fabric/layer5-ground-truth/src/api/router.py

Requirements:
- Periodic job that queries for truths where expires_at < now() AND is_stale = false
- Sets is_stale=True and creates a ValidationEvent for the transition
- Configurable TTL per claim_type (in config.py)
- API endpoint: POST /truths/check-stale (admin only, triggers check)
- Query endpoint: GET /truths/stale (list all stale truths for org)
- Follow existing patterns from state_machine.py and truth_service.py

Include:
- Unit tests for the monitor service
- Integration with existing TruthStatus and ValidationEvent models
- Background task scheduling (APScheduler or similar)
```

### Prompt 2: LLM Integration
```
Implement LLM integration for Layer 2 Extraction Pipeline at:
https://github.com/bmsull560/Fabric_4L

Modify:
- layer2-extraction/src/extraction/llm_extractor.py
- Create: layer2-extraction/src/shared/llm_client.py
- Create: layer2-extraction/src/extraction/prompts/

Requirements:
- Async OpenAI client with retry logic
- Prompt templates for entity extraction (Capability, UseCase, Persona, ValueDriver)
- Prompt templates for relationship extraction
- Function calling with strict JSON schema output
- Confidence scoring from logprobs
- Cost tracking per API call

Follow patterns from layer2-extraction/src/models/ontology.py
```

### Prompt 3: Neo4j Connection
```
Connect Neo4j to Layer 3 Knowledge Graph at:
https://github.com/bmsull560/Fabric_4L

Modify:
- layer3-knowledge/src/schema/initializer.py
- layer3-knowledge/src/ingestion/neo4j_loader.py
- layer3-knowledge/src/retrieval/graph_rag.py

Requirements:
- Neo4j async driver with connection pooling
- Cypher schema for: Capability, UseCase, Persona, ValueDriver nodes
- Relationship types: ENABLES, BENEFITS, DRIVES, CONTRIBUTES_TO
- Vector index for embeddings
- GraphRAG query execution with hybrid search
- RDF to Neo4j ingestion from Layer 2
```

---

## Phase 2: Architecture Extensions (Post-Production)

**Source:** `architecture-scoping-value-packs-formulas-benchmarks-27dd8a.md`

**Scope:** New functional domains and UX model for enterprise scalability. **Start after Tasks 6-14 complete.**

### **New Layer 6: Benchmark Service** ⭐ NEW LAYER
**Priority:** P1 | **Effort:** 2-3 weeks | **Depends on:** Task 7 (Neo4j), Task 12 (Provenance)

**Concept:** Standalone service for comparative intelligence (peer benchmarking, statistical validation). Distinct from Ground Truth—benchmarks are curated datasets, not validated claims.

**Key Capabilities:**
- Benchmark dataset management by industry/segment
- Peer comparison APIs (`POST /v1/benchmarks/compare`)
- Range validation (`POST /v1/benchmarks/validate`)
- Integration with Formula evaluation for sanity checks

**Acceptance Criteria:**
- [ ] Layer 6 service skeleton (port 8006) with FastAPI
- [ ] Manufacturing benchmark dataset (reference implementation)
- [ ] Comparison API with statistical profiles (p10, p50, p90)
- [ ] Integration with Layer 4 formula evaluation
- [ ] Docker Compose includes benchmark service

**Implementation:**
- Create: `value-fabric/layer6-benchmarks/` (new directory)
- Create: `value-fabric/layer6-benchmarks/src/api/main.py`
- Create: `value-fabric/layer6-benchmarks/src/models/benchmark_dataset.py`
- Modify: `docker-compose.yml` (add benchmark service)
- Create: `specs/benchmark_service_spec.md`

---

### **Task 15: Value Pack Domain (L4 Agents + L3 KG)**
**Priority:** P1 | **Effort:** 1-2 weeks | **Depends on:** Task 8 (LangGraph), Task 9 (Frontend)

**Concept:** Reusable, industry-specific packages combining ontology slice, value drivers, formulas, benchmarks, and workflow templates.

**Acceptance Criteria:**
- [ ] `:ValuePack` node schema in Neo4j with relationships to `:Industry`, `:ValueDriver`, `:Formula`, `:Benchmark`
- [ ] `/packs` skill family in Layer 4:
  - `pack_list` - List available packs
  - `pack_load` - Load pack into workspace
  - `pack_execute` - Run pack workflow
  - `pack_customize` - Fork pack for account
- [ ] API endpoints: `GET /v1/packs`, `POST /v1/packs/{id}/execute`
- [ ] Frontend Value Models page (Tier 1 UX)

**Implementation:**
- Create: `value-fabric/layer4-agents/src/skills/pack_skills.py`
- Create: `specs/value_pack_schema.py`
- Modify: `layer3-knowledge/src/schema/initializer.py` (add ValuePack nodes)
- Modify: `frontend/client/src/pages/ValueModels.tsx` (NEW - simplified pack UI)

---

### **Task 16: Formula Governance (L4 Agents)**
**Priority:** P1 | **Effort:** 1-2 weeks | **Depends on:** Task 11 (Formula APIs), Task 15 (Value Packs)

**Concept:** Versioned, governed financial logic with activation lifecycle and approval workflows.

**Acceptance Criteria:**
- [ ] `FormulaGovernance` model with version, status (DRAFT|ACTIVE|DEPRECATED), approval flow
- [ ] Formula versioning with semver (`GET /v1/formulas/{id}/versions`)
- [ ] Activation/deprecation workflows (`POST /v1/formulas/{id}/activate`)
- [ ] Approval state machine with admin-only transitions
- [ ] Dependency tracking (`GET /v1/formulas/{id}/dependencies`)

**Implementation:**
- Create: `value-fabric/layer4-agents/src/models/formula_governance.py`
- Modify: `value-fabric/layer4-agents/src/services/formula_engine.py`
- Modify: `value-fabric/layer4-agents/src/api/routes/analysis.py` (add governance routes)
- Create: `specs/formula_governance_spec.md`

---

### **Task 17: Variable Registry (L3 KG + L5 Ground Truth)**
**Priority:** P1 | **Effort:** 1-2 weeks | **Depends on:** Task 15 (Value Packs), Task 16 (Formula Governance)

**Concept:** Centralized variable definitions with source binding, validation rules, and provenance. Schemas in KG, validated values as TruthObjects in L5.

**Acceptance Criteria:**
- [ ] `:Variable` node schema in Neo4j with relationships to `:Industry`, `:DataSource`, `:Formula`
- [ ] Variable definition API (`GET/POST /v1/variables`)
- [ ] Source binding framework (CRM field, benchmark lookup, user input)
- [ ] Integration with L5 Ground Truth for `claim_type=VARIABLE_VALUE`
- [ ] Variable search by context (`GET /v1/variables/search`)

**Implementation:**
- Create: `value-fabric/layer4-agents/src/models/variable_registry.py`
- Modify: `layer3-knowledge/src/schema/initializer.py` (add Variable nodes)
- Modify: `layer5-ground-truth/src/models/truth_object.py` (add VARIABLE_VALUE claim_type)
- Create: `layer3-knowledge/src/api/routes/variables.py` (NEW)

---

### **Task 18: Three-Tier UX Model (Frontend)**
**Priority:** P2 | **Effort:** 2-3 weeks | **Depends on:** Task 9 (Frontend Core)

**Concept:** Progressive disclosure UI - Standard users see simplified flows, Advanced users see internals, Admins see governance controls.

**Tier Structure:**
- **Tier 1 (Standard):** Command Center, Accounts, Value Models, Business Cases, Workflows, Evidence
- **Tier 2 (Advanced):** Value Tree Explorer, Formula Studio, Graph Explorer, Ontology Browser
- **Tier 3 (Admin):** Formula Governance, Benchmark Policies, Variable Registry, Data Sources, Pack Management

**Acceptance Criteria:**
- [ ] Navigation reorganization by tier
- [ ] "Advanced Mode" toggle for Tier 2 surfaces
- [ ] Admin Control Plane (`/admin/*`) for Tier 3
- [ ] Progressive disclosure patterns (hide complexity from Tier 1)
- [ ] Route protection by user tier

**Implementation:**
- Create: `frontend/client/src/components/navigation/TieredNav.tsx`
- Create: `frontend/client/src/pages/admin/FormulaGovernance.tsx`
- Create: `frontend/client/src/pages/admin/BenchmarkPolicies.tsx`
- Create: `frontend/client/src/pages/admin/VariableRegistry.tsx`
- Modify: `frontend/client/src/App.tsx` (tier-based routing)
- Create: `specs/three_tier_ux_model.md`

---

### **Task 19: Manufacturing Value Pack (Reference Implementation)**
**Priority:** P2 | **Effort:** 1 week | **Depends on:** Task 15 (Value Pack Domain), Task 17 (Variable Registry)

**Concept:** Complete reference Value Pack for Manufacturing industry - the "golden example" for pack authoring.

**Acceptance Criteria:**
- [ ] Manufacturing ontology slice (capabilities, value drivers, use cases)
- [ ] 5-7 manufacturing formulas with governance metadata
- [ ] Variable definitions for manufacturing KPIs (OEE, throughput, downtime)
- [ ] Benchmark references (manufacturing operational metrics)
- [ ] Workflow template for manufacturing business case
- [ ] Pack testing framework
- [ ] Pack authoring documentation

**Implementation:**
- Create: `packs/manufacturing/` (pack content directory)
- Create: `packs/manufacturing/ontology.json`
- Create: `packs/manufacturing/formulas.json`
- Create: `packs/manufacturing/variables.json`
- Create: `packs/manufacturing/workflow_template.json`
- Create: `docs/pack_authoring_guide.md`

---

## Phase 2 Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 2: ARCHITECTURE EXTENSIONS                     │
│              (Start after Tasks 6-14 Complete)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Task 15: Value Packs ────────┐                                 │
│  (P1 - L4/L3)                │                                 │
│                              ▼                                 │
│  Task 16: Formula ────────────┼──────┐                          │
│  Governance (P1)            │       │                         │
│                              ▼       ▼                         │
│  Task 17: Variable ───────────┘       │                         │
│  Registry (P1)                        │                         │
│                              ▼       ▼                         │
│  Task 19: Manufacturing ─────┴───────┘                         │
│  Pack (P2)                                                      │
│                              │                                 │
│  Task 6-14 Complete ────────►│                                 │
│  (Production Ready)          ▼                                 │
│                    Task 18: Three-Tier UX                     │
│                    (P2 - Frontend)                               │
│                              │                                 │
│            ┌─────────────────┴─────────────────┐               │
│            ▼                                   ▼               │
│      Task X: Layer 6                     (Parallel Track)      │
│      Benchmark Service                 Task Y: Life Sciences   │
│      (P1 - New Layer)                    Pack (Future)           │
│                                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary

**Estimated Time to Production:**
- **Current State:** ~72% overall, 0% production-ready (no E2E workflow)
- **After Task 6-9 (P0):** ~85% overall, 80% production-ready (E2E working)
- **After All Tasks (6-14):** ~90% overall, 95% production-ready
- **Sequential:** 2-3 weeks
- **Parallel (3 tracks):** 1-1.5 weeks

**Estimated Time to Full Architecture (Phase 1 + Phase 2):**
- **Phase 1 (Production):** 2-3 weeks (Tasks 6-14)
- **Phase 2 (Extensions):** 6-8 weeks (Tasks 15-19 + Layer 6 Benchmark Service)
- **Total Sequential:** 8-11 weeks
- **Total Parallel (4 tracks):** 5-6 weeks

**Biggest Risks (Phase 1):**
1. **Task 7 (Neo4j Vector Indexes):** Neo4j 5.x vector index syntax may differ from expectations
2. **Task 8 (LangGraph Resume):** Checkpointing with Postgres may require schema migrations
3. **Task 9 (Frontend):** Large surface area (10 screens) could reveal more backend gaps

**Biggest Risks (Phase 2):**
1. **Layer 6 Benchmark Service:** New layer means new deployment, monitoring, operational overhead
2. **Three-Tier UX:** Navigation reorganization may confuse existing users during transition
3. **Value Pack Complexity:** Manufacturing pack scope could expand (Life Sciences planned next)

**Biggest Opportunities:**
1. **Strong foundation:** Docker Compose, LLM client, Neo4j driver all exist
2. **Incremental progress:** Each P0 task unlocks visible functionality
3. **UI ready:** Frontend needs only API wiring (no component work)
4. **Ground Truth complete:** L5 is production-ready reference implementation
5. **Enterprise-ready:** Phase 2 adds governance, benchmarking, tiered UX for enterprise sales

**Next Action:**
🚀 **Start Task 6 (L2→L3 Endpoint)** — Add `/extract-and-ingest` to bridge extraction → knowledge graph. This is the final pipe to complete the data flow.

**Critical Path (Phase 1):**
```
Task 6 (1d) → Task 7 (2d) → Task 8 (3d) → Task 9 (3d) = 9 days to user-visible E2E
```

**Complete Roadmap Scope:**
- **Tasks 1-5:** ✅ Completed (Freshness, LLM, partial Neo4j, partial LangGraph, Frontend planned)
- **Tasks 6-14:** 🔄 Phase 1 - Production Readiness (9 tasks, 4 P0, 3 P1, 2 P2)
- **Tasks 15-19:** 📋 Phase 2 - Architecture Extensions (5 tasks, 4 P1, 1 P2 + New Layer 6)
- **Total Tasks:** 19 tasks + 1 new layer
- **Estimated Effort:** 8-11 weeks (full implementation)
