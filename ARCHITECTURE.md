# Architecture

Value Fabric uses a six-layer microservices architecture with strict tenant isolation via PostgreSQL RLS.

For full details, see:

- [System Overview](docs/architecture/system-overview.md)
- [Architecture Concepts](docs/core-concepts/architecture.md)
- [ADR-001: Six-Layer Architecture](docs/explanations/adr/ADR-001-six-layer-architecture.md)
- [Component Interaction Map](docs/architecture/component-interaction-map.md)

## Layers

| Layer | Service | Purpose |
| --- | --- | --- |
| 1 | layer1-ingestion | Data ingestion, crawling, document parsing |
| 2 | layer2-extraction | Ontology extraction, NLP processing |
| 3 | layer3-knowledge | Knowledge graph, evidence search |
| 4 | layer4-agents | AI agents, workflow orchestration |
| 5 | layer5-ground-truth | Ground truth management, model registry |
| 6 | layer6-benchmarks | Benchmarking, performance evaluation |
