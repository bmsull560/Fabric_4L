# Value Fabric — Enterprise Agentic SaaS Platform

A production-grade, multi-agent system (MAS) that transforms unstructured enterprise data into
structured, actionable knowledge through an ontology-guided pipeline and autonomous AI agents.

## What it is

Value Fabric is an **enterprise agentic SaaS platform** built on a 6-layer semantic pipeline.
Agents reason over a knowledge graph to produce ROI analyses, business cases, and executive insights—
automatically, at scale, with full auditability.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND: REACT PRESENTATION                        │
│         (Vite · React Query · Zustand · shadcn/ui · Tailwind)             │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ REST/WebSocket
┌───────────────────────────────▼─────────────────────────────────────────────┐
│              LAYER 6: BENCHMARK SERVICE (Port 8006)                        │
│              (Peer Comparison · Statistical Validation · Datasets)         │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────────┐
│              LAYER 5: GROUND TRUTH (Port 8005)                              │
│    (TruthObject Validation · Maturity Ladder · Evidence-backed Claims)     │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────────┐
│              LAYER 4: AGENTIC WORKFLOW ENGINE (Port 8004)                    │
│      (LangGraph · ROI Calculator · Business Case Generator · Checkpoints)  │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ REST
┌───────────────────────────────▼─────────────────────────────────────────────┐
│          LAYER 3: KNOWLEDGE GRAPH & SEMANTIC LAYER (Port 8003)              │
│       (Neo4j · GraphRAG · Hybrid Retrieval · pgvector · Subgraph API)       │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ RDF/Turtle
┌───────────────────────────────▼─────────────────────────────────────────────┐
│         LAYER 2: ONTOLOGY-GUIDED EXTRACTION PIPELINE (Port 8002)           │
│    (Pydantic v2 · LLM Extraction · RDF/OWL · Provenance · Batch Ingest)    │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ Markdown chunks
┌───────────────────────────────▼─────────────────────────────────────────────┐
│           LAYER 1: INTELLIGENT DATA INGESTION SERVICE (Port 8001)         │
│     (Playwright · Celery/Redis · PostgreSQL · Multi-tenancy · Compliance) │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Frontend Governance

Frontend changes are governed by the root [`DESIGN.md`](DESIGN.md) contract. Human contributors and AI coding agents must read it before modifying `apps/web/`, reuse existing React/Vite/TypeScript/Tailwind/shadcn/TanStack Query patterns, and report validation results with any remaining risks.

## Package Manager Policy (Monorepo)

This repository uses **pnpm** as the canonical package manager.

```bash
# Enable corepack and activate the repo-pinned pnpm version
corepack enable
corepack use pnpm@10.18.1

# Install JavaScript/TypeScript dependencies
pnpm install
```

Using `npm install` or `yarn install` is not supported and will fail fast via the root `preinstall` guard.

Frontend workspace (`apps/web`) follows the same policy:

```bash
# Install from monorepo root (recommended)
pnpm install

# Or install only the frontend workspace
pnpm --dir apps/web install
```

## Quickstart

### Package manager policy (required)

This monorepo is **pnpm-only**. Use the root lockfile `pnpm-lock.yaml` as the canonical dependency snapshot.

```bash
# Enable Corepack and activate the pinned pnpm version
corepack enable
corepack prepare pnpm@10.18.1 --activate

# Install dependencies at repo root
pnpm install --frozen-lockfile
```

Running `npm install` or `npm ci` at repo root is not supported and will fail fast via `preinstall` checks.

```bash
# 1. Clone and enter repo
git clone https://github.com/bmsull560/Fabric_4L.git && cd Fabric_4L

# 2. Copy environment template
cp .env.example .env
# Fill in OPENAI_API_KEY and JWT_SECRET

# 3. Start all services
docker compose -f docker-compose.full.yml up -d

# 4. Run database migrations
make migrate

# 5. Verify everything works
make verify

# 6. Open the UI
open http://localhost:5173
```

## Repository map

| Path | Status | Purpose |
|------|--------|---------|
| `value_fabric/` | **Canonical** | Runtime Python package root for the six-layer platform |
| `value_fabric/layer1/` | **Canonical** | Layer 1 ingestion runtime modules |
| `value_fabric/layer2/` | **Canonical** | Layer 2 extraction runtime modules |
| `value_fabric/layer3/` | **Canonical** | Layer 3 knowledge/retrieval runtime modules |
| `value_fabric/layer4/` | **Canonical** | Layer 4 agent orchestration runtime modules |
| `value_fabric/layer5/` | **Canonical** | Layer 5 ground-truth runtime modules |
| `value_fabric/layer6/` | **Canonical** | Layer 6 benchmark runtime modules |
| `value_fabric/shared/` | **Canonical** | Shared runtime packages (identity, security, models, boundaries) |
| `services/` | **Maintained (service deployment layer)** | Deployable service apps, migrations, manifests, and service-specific tests |
| `services/layer1-ingestion/` ... `services/layer6-benchmarks/` | **Maintained** | Layer service entrypoints and infra wrappers |
| `services/api/` | **Maintained** | Cross-layer API service |
| `services/` | **Legacy reference** | Historical monorepo path naming retained for compatibility/docs backreferences |
| `apps/web/` | Canonical frontend | Current web UI package and build target |
| `contracts/` | **Canonical** | Versioned tool manifests, JSON Schemas, OpenAPI specs |
| `apps/web/` | **Canonical** | React + TypeScript UI |
| `k8s/` | **Canonical** | Kubernetes manifests |
| `monitoring/` | **Canonical** | Prometheus + Grafana dashboards |
| `packs/` | **Canonical** | Domain-specific data packs (life-sciences, manufacturing, software) |
| `docs/` | **Canonical** | Architecture docs and runbooks |
| `tests/` | **Canonical** | Cross-layer integration and agent evaluation tests |
| `.github/workflows/` | **Canonical** | CI pipelines |

### Source of truth paths

Runtime API modules (exact paths):

- `value_fabric/layer1/api/routes/`
- `value_fabric/layer2/api/routes/`
- `value_fabric/layer3/api/routes/`
- `value_fabric/layer5/api/`
- `value_fabric/layer6/api/routes/`

Domain/runtime packages (exact paths):

- `value_fabric/layer1/`
- `value_fabric/layer2/`
- `value_fabric/layer3/`
- `value_fabric/layer4/`
- `value_fabric/layer5/`
- `value_fabric/layer6/`
- `value_fabric/shared/`

## Core concepts

- **Contracts** — All tool schemas and API shapes live in `contracts/`. They are the source of truth.
- **Runtime** — Provider-agnostic orchestration in `services/layer4-agents/src/engine/`.
- **Agents** — Behavior defined as versioned artifacts in `layer4-agents/agents/` and `layer4-agents/skills/`.
- **Providers** — Vendor-specific adapters (OpenAI, Anthropic, Neo4j, pgvector) isolated from core logic.
- **Packs** — Domain vertical extensions that add ontology, formulas, and variables without touching core.
- **Drift Detection** — Automated checks for API contract drift, schema drift, and documentation staleness via CI/CD workflows and the Drift Assessor agent.

## Documentation

📚 **[Complete Documentation →](docs/README.md)**

🚀 **[Platform Launch Checklist →](docs/launch-checklists/platform-launch.md)** (Sprint 4 Release Hardening)

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
| [Drift Detection](docs/how-to-guides/drift-detection.md) | API contract, schema, and documentation drift detection |

### Architecture Decisions

| Document | Description |
|----------|-------------|
| [All ADRs](docs/explanations/adr/) | Architecture Decision Records |

### Meta

| Document | Description |
|----------|-------------|
| [`AGENTS.md`](AGENTS.md) | How to work with this repo as an AI agent |
| [`DESIGN.md`](DESIGN.md) | Production frontend governance contract for `apps/web/` |
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
