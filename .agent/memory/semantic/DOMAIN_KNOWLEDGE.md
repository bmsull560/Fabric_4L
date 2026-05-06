# Domain Knowledge

> Stable facts about the domains you work in. Not procedures (those go in
> skills), not preferences (those go in `personal/PREFERENCES.md`), not
> time-bound events (those go in `episodic/`). Pure reference material.

## Example sections
- API contracts you reuse
- Vendor quirks ("service X rate-limits at 60 rpm, not the documented 100")
- Domain-specific terminology

## Seeds
_(empty — populate as you go)_

## Value Fabric Platform

### Layer Structure
- **Layer 1 (Ingestion)**: Port 8001 - Data ingestion, crawling, document parsing using Playwright, Celery/Redis, PostgreSQL
- **Layer 2 (Extraction)**: Port 8002 - Ontology-guided extraction using Pydantic v2, LLM extraction, RDF/OWL, provenance tracking
- **Layer 3 (Knowledge)**: Port 8003 - Knowledge graph and semantic layer using Neo4j, GraphRAG, hybrid retrieval, pgvector
- **Layer 4 (Agents)**: Port 8004 - Agentic workflow engine using LangGraph, ROI calculator, business case generator, checkpoints
- **Layer 5 (Ground Truth)**: Port 8005 - Ground truth management, TruthObject validation, maturity ladder, evidence-backed claims
- **Layer 6 (Benchmarks)**: Port 8006 - Benchmark service for peer comparison, statistical validation, datasets

### Canonical Paths
- Runtime Python package: `value_fabric/` (layer1/ through layer6/ subdirectories)
- Service deployment: `services/` (layer1-ingestion/ through layer6-benchmarks/)
- Frontend: `apps/web/` (React + TypeScript, not the legacy `frontend/` directory)
- Contracts: `contracts/` (source of truth for tool schemas and API shapes)
- Domain packs: `packs/` (life-sciences, manufacturing, software verticals)

### Technology Stack
- **Frontend**: React, Vite, React Query, Zustand, shadcn/ui, Tailwind
- **Backend**: Python, FastAPI, Pydantic v2
- **Databases**: PostgreSQL (with RLS for tenant isolation), Neo4j (knowledge graph), pgvector (vector search)
- **Message Queue**: Celery with Redis
- **Orchestration**: LangGraph for agent workflows
- **Package Manager**: pnpm (monorepo)
- **Testing**: E2E with Playwright, pytest for Python

### Key Architectural Principles
- Strict tenant isolation via PostgreSQL RLS
- Provider-agnostic orchestration (OpenAI, Anthropic, Neo4j, pgvector adapters isolated)
- Contracts as single source of truth in `contracts/` directory
- Clear separation between runtime packages (`value_fabric/`) and service deployment (`services/`)
- Domain verticals extend via packs without touching core code
