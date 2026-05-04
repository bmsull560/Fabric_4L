# Fabric_4L Architecture

## Layered Architecture (L1-L6)

### L1 Ingestion
- Accepts external inputs: websites, CRM records, PDFs, call notes, public filings, case studies, product docs, spreadsheets, uploaded files, APIs.
- Normalizes raw inputs into source documents and ingestion events.

### L2 Extraction
- Extracts signals, entities, pain points, metrics, claims, stakeholders, use cases, and evidence snippets.
- Produces structured extraction results with provenance.

### L3 Knowledge
- Maintains the knowledge graph.
- Graph abstraction for accounts, personas, signals, drivers, levers, formulas, evidence, business cases, and relationships.
- In MVP: mock graph store; production target is Neo4j.

### L4 Agents
- Orchestrates multi-agent workflows.
- LangGraph-style workflows with checkpointing, resume, tool execution, and review gates.
- In MVP: mockable orchestration with MockLLMProvider.

### L5 Ground Truth
- Stores validated truth objects.
- Tracks human-verified claims, formulas, evidence, assumptions, benchmark approvals, and review decisions.

### L6 Benchmarks
- Stores benchmark datasets, policies, industry averages, confidence levels, and formula calibration metadata.

## Frontend Architecture

- React 19 + TypeScript + Vite
- Tailwind CSS + shadcn/ui primitives
- TanStack Query for server state
- Zustand for client state
- React Router for navigation
- Recharts for charts
- React Flow for graph visualization

## Backend Service Architecture

- FastAPI with modular routers
- Pydantic v2 models for request/response validation
- In-memory mock database with tenant isolation patterns
- Services layer for business logic (ROI, governance, agents)
- Seed data loader from existing `packs/` directory

## Data Stores

| Store | Purpose | MVP | Production |
|-------|---------|-----|------------|
| MockDatabase | Relational data | In-memory | PostgreSQL |
| Graph | Knowledge relationships | Mock | Neo4j |
| Cache/Queue | Async jobs | Mock | Redis + Celery |
| Vector | Semantic search | N/A | pgvector / Qdrant |
| Object Storage | Documents | N/A | S3-compatible |

## Agent Orchestration

- `AgentOrchestrator` class manages agent runs
- `MockLLMProvider` implements provider abstraction:
  - `generateStructured()`
  - `summarize()`
  - `extract()`
  - `classify()`
  - `reason()`
- Supports checkpointing, resume, cancel, and review gates

## Evidence Provenance

Every AI-generated object carries:
- `source`
- `confidence`
- `status`
- `evidenceIds`
- `createdBy`: agent | user | system
- `reviewState`

## Governance Model

- Review decisions on AI-generated claims
- Evidence approval workflows
- Formula validation gates
- Ground truth tracking
- Production readiness gates

## Tenant Isolation Model

- Every account-scoped object includes `tenantId`
- Tenant context middleware extracts `X-Tenant-ID` header
- API handlers require tenant context
- Mock database filters all queries by tenant
- Tests verify cross-tenant access is blocked

## Production Deployment Path

1. Docker Compose for local development
2. Kubernetes-ready manifests in `infra/k8s/`
3. GitHub Actions CI/CD pipelines
4. OPA policy gates in `.fabric/`
