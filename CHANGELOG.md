# Changelog

All notable changes to Value Fabric are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [1.0.0] — 2026-05-12

### Deployment Target
- Environment: production
- Namespace: fabric-4l-prod
- Registry: ghcr.io/value-fabric

### Infrastructure
- Kubernetes manifests validated via `kubectl kustomize`
- Production overlay: 3,175 lines of rendered manifests
- HPA, PDB, NetworkPolicies, and monitoring configured
- ExternalSecrets configured for secret management

### Services
| Service | Replicas | Layer |
|---------|----------|-------|
| layer1-ingestion | 3 | L1 |
| layer2-extraction | 3 | L2 |
| layer3-knowledge | 3 | L3 |
| layer4-agents | 3 | L4 |
| layer5-ground-truth | 2 | L5 |
| layer6-benchmarks | 2 | L6 |
| frontend (web) | 2 | UI |

### Fixes
- Fixed K8s overlay patches: corrected container name (`frontend` → `web`)
- Fixed K8s overlay patches: corrected ConfigMap name (`global-config` → `value-fabric-config`)
- Fixed K8s overlay patches: added missing namespace metadata
- Aligned all version sources to 1.0.0

## [Unreleased]

### Added
- `AGENTS.md` — contributor guide for AI agents and developers (P0 MAS best practice)
- `contracts/tool-manifests/` — versioned JSON Schema tool manifests for all agent skills
- `contracts/jsonschema/` — shared data model schemas (entities, events)
- `tests/evals/` — golden-trace agent evaluation framework with fixtures
- Root `README.md` with repo map and quickstart
- `CONTRIBUTING.md` — developer setup, coding standards, PR conventions
- `SECURITY.md` — supported versions and vulnerability reporting
- `CHANGELOG.md` — SemVer-based release history
- `Makefile` — developer ergonomics (`verify`, `test`, `lint`, `build`, `migrate`, `evals`)
- `.github/dependabot.yml` — automated dependency updates (pip, npm, GitHub Actions)

---

### Changed
- Canonical launch readiness source set to `docs/readiness/current.md`; roadmap launch criteria references now point to canonical readiness.

## [0.9.0] — 2026-04-12

### Added
- Layer 5 Ground Truth store (100% complete, production-ready)
- Layer 4 Agent Engine with LangGraph orchestration, pause/resume controls
- Frontend: Command Center, Graph Explorer, admin screens
- Governance middleware: JWT auth, RBAC, API key management
- Audit log (append-only, DB trigger-enforced) — `audit_events` table
- Alembic migrations for governance tables (tenants, users, api_keys) and audit_events
- Monitoring stack: Prometheus, Grafana dashboards, alerting rules
- Kubernetes manifests for all layers + external secrets (Vault integration)
- Domain packs: life-sciences, manufacturing, software

### Changed
- Shared identity library (`packages/shared/src/value_fabric/shared/identity/`) promoted to single cross-layer auth package

### Fixed
- Pagination contract consistency across all layer APIs
- Graph traversal depth limit handling in Layer 3

---

## [0.8.0] — 2026-03-15

### Added
- Layer 3 Knowledge Graph API (Neo4j + pgvector + GraphRAG hybrid retrieval)
- Layer 2 Ontology-guided extraction pipeline (LLM + RDF/OWL generation)
- Layer 1 Intelligent ingestion service (Playwright + Redis + PostgreSQL)
- Agent behavior artifacts: `layer4-agents/agents/`, `layer4-agents/skills/`, `layer4-agents/workflows/`
- Business Analyst Agent and Knowledge Navigator Agent definitions
- 12 atomic skill definitions (evaluate_formula, semantic_search, graph_traverse, etc.)
- CI pipeline: lint, type-check, 80%+ coverage gate per layer
- Docker Compose for local full-stack development
