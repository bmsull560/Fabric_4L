# Changelog

All notable changes to Value Fabric are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

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
- Shared identity library (`value-fabric/shared/identity/`) promoted to single cross-layer auth package

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
