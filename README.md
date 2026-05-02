# Value Fabric — Enterprise Agentic SaaS Platform

A production-grade, multi-agent system (MAS) that transforms unstructured enterprise data into
structured, actionable knowledge through an ontology-guided pipeline and autonomous AI agents.

## What it is

Value Fabric is an **enterprise agentic SaaS platform** built on a 4-layer semantic pipeline.
Agents reason over a knowledge graph to produce ROI analyses, business cases, and executive insights—
automatically, at scale, with full auditability.

```
┌──────────────────────────────────────────────────────┐
│  LAYER 4 · AGENTIC WORKFLOW ENGINE                   │
│  LangGraph · Business Analyst Agent · ROI Engine     │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│  LAYER 3 · KNOWLEDGE GRAPH & SEMANTIC LAYER          │
│  Neo4j · GraphRAG · Hybrid Retrieval · pgvector      │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│  LAYER 2 · ONTOLOGY-GUIDED EXTRACTION PIPELINE       │
│  Pydantic · LLM Extraction · RDF/OWL Generation      │
└────────────────────┬─────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────┐
│  LAYER 1 · INTELLIGENT DATA INGESTION                │
│  Playwright · Redis Queue · PostgreSQL · Rate Limit  │
└──────────────────────────────────────────────────────┘
```

## Quickstart

```bash
# 1. Clone and enter repo
git clone https://github.com/bmsull560/Fabric_4L.git && cd Fabric_4L

# 2. Copy environment template
cp value-fabric/.env.example value-fabric/.env
# Fill in OPENAI_API_KEY and JWT_SECRET

# 3. Start all services
cd value-fabric && docker compose up -d

# 4. Run database migrations
make migrate

# 5. Verify everything works
make verify

# 6. Open the UI
open http://localhost:5173
```

## Repository map

| Path | Purpose |
|------|---------|
| `value-fabric/` | Core monorepo — all backend services |
| `value-fabric/layer1-ingestion/` | Data ingestion service (FastAPI + Playwright) |
| `value-fabric/layer2-extraction/` | Ontology-guided extraction (LLM + RDF) |
| `value-fabric/layer3-knowledge/` | Knowledge graph API (Neo4j + pgvector) |
| `value-fabric/layer4-agents/` | Agentic workflow engine (LangGraph) |
| `value-fabric/layer5-ground-truth/` | Ground truth & evaluation store |
| `value-fabric/layer6-benchmarks/` | Benchmark harness |
| `value-fabric/shared/` | Cross-layer identity, auth, and audit libraries |
| `layer4-agents/` | Agent behavior artifacts (prompts, skills, workflows) |
| `contracts/` | Versioned tool manifests, JSON Schemas, OpenAPI specs |
| `apps/web/` | React + TypeScript UI (canonical frontend) |
| `frontend/` | ⚠️ OBSOLETE — migrated to `apps/web/` |
| `k8s/` | Kubernetes manifests |
| `monitoring/` | Prometheus + Grafana dashboards |
| `packs/` | Domain-specific data packs (life-sciences, manufacturing, software) |
| `docs/` | Architecture docs and runbooks |
| `tests/` | Cross-layer integration and agent evaluation tests |
| `.github/workflows/` | CI pipelines |

## Core concepts

- **Contracts** — All tool schemas and API shapes live in `contracts/`. They are the source of truth.
- **Runtime** — Provider-agnostic orchestration in `value-fabric/layer4-agents/src/engine/`.
- **Agents** — Behavior defined as versioned artifacts in `layer4-agents/agents/` and `layer4-agents/skills/`.
- **Providers** — Vendor-specific adapters (OpenAI, Anthropic, Neo4j, pgvector) isolated from core logic.
- **Packs** — Domain vertical extensions that add ontology, formulas, and variables without touching core.

## Documentation

📚 **[Complete Documentation →](docs/README.md)**

Our documentation follows the [Diátaxis Framework](https://diataxis.fr/) with tutorials, how-to guides, reference, and explanations.

### Getting Started

| Document | Description |
|----------|-------------|
| [Quickstart (15 min)](docs/getting-started/quickstart.md) | Get a local instance running fast |
| [Environment Setup](docs/getting-started/environment.md) | Configure secrets, env vars, and services |

### Core Concepts

| Document | Description |
|----------|-------------|
| [System Architecture](docs/core-concepts/architecture.md) | C4 model diagrams and layer interactions |
| [Security Model](docs/core-concepts/security-model.md) | Authentication, RBAC, and tenant isolation |
| [Ontology System](docs/core-concepts/ontology-system.md) | Entity taxonomy and extraction pipeline |

### API Reference

| Document | Description |
|----------|-------------|
| [API Overview](docs/reference/api-overview.md) | Authentication patterns and common formats |
| [Layer 1: Ingestion](docs/reference/layer1-ingestion-api.md) | Web scraping and job management |
| [Layer 2: Extraction](docs/reference/layer2-extraction-api.md) | LLM-based entity extraction |
| [Layer 3: Knowledge Graph](docs/reference/layer3-knowledge-api.md) | Neo4j + pgvector hybrid search |
| [Layer 4: Agents](docs/reference/layer4-agents-api.md) | Workflow orchestration with LangGraph |
| [Layer 5: Ground Truth](docs/reference/layer5-ground-truth-api.md) | Evaluation and benchmarking |

### Troubleshooting & Operations

| Document | Description |
|----------|-------------|
| [Troubleshooting Guide](docs/troubleshooting/index.md) | Decision trees and common issues |
| [Runbooks](docs/troubleshooting/runbooks/) | 38 operational procedures |

### Architecture Decisions

| Document | Description |
|----------|-------------|
| [All ADRs](docs/explanations/adr/) | Architecture Decision Records |

### Meta

| Document | Description |
|----------|-------------|
| [`AGENTS.md`](AGENTS.md) | How to work with this repo as an AI agent |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Developer contribution guide |
| [`SECURITY.md`](SECURITY.md) | Vulnerability reporting |
| [`ROADMAP.md`](ROADMAP.md) | Completion status and roadmap |

## SDK Installation

```bash
pip install valuefabric-sdk
```

Or install from source:

```bash
cd sdk/python
pip install -e ".[dev]"
```

See [`sdk/python/README.md`](sdk/python/README.md) for SDK usage and CLI examples.

## Security

Never commit real secrets. Use `.env` files (gitignored) locally, and short-lived OIDC credentials in CI.
See [`SECURITY.md`](SECURITY.md) for the full policy and how to report vulnerabilities.

## License

See [`LICENSE`](LICENSE) for terms.
