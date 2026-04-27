# Plan: Generate 6-File Design Brief for Fabric 4L Integration Recovery

## Context
Based on Tri-Track Audit findings (executive-summary.md + track-a/b/c data), produce the 6 interconnected design brief documents specified in design-brief-plans.md.

## Source Data
- `executive-summary.md` — Audit findings, metrics, recommendations
- `track-a-hook-analysis.json` — 47 hooks with data source classification
- `track-a-route-extraction.json` — 154 routes with component mappings
- `track-a-route-matrix.csv/.md` — Route integrity matrix (GREEN/RED/UNKNOWN)
- `track-b-openapi-analysis.json` — 244 endpoints, 236 orphans
- `track-b-orphan-registry.md` — Domain-entity orphan analysis
- `track-c-contract-gaps.md` — 6 canonical contracts + 3 missing contracts

## Stage 1: Outline Design (Orchestrator)
Design detailed outlines for all 6 documents based on the source data and the structure defined in design-brief-plans.md. Load `report-writing` skill for outline conventions.

## Stage 2: Parallel Document Writing (6 Sub-agents)
Load `report-writing` skill. Deploy 6 parallel writer agents, one per document:

- **Writer_D1**: Document 1 — Integration Contract Specification
- **Writer_D2**: Document 2 — Page Reality Index  
- **Writer_D3**: Document 3 — Hook Architecture Blueprint
- **Writer_D4**: Document 4 — Type Synchronization Protocol
- **Writer_D5**: Document 5 — UI/UX Component Strategy
- **Writer_D6**: Document 6 — Implementation Roadmap

Each writer receives: (1) report-writing skill guidance, (2) relevant source data, (3) document-specific outline.

## Stage 3: Quality Review (3 Parallel Reviewers)
Deploy 3 reviewer agents across all 6 documents for:
- Technical accuracy (data consistency with source files)
- Cross-document coherence (consistent terminology, no contradictions)
- Structural completeness (all outline sections covered)

## Stage 4: Assembly & Final Output
Compile all 6 documents with consistent headers, table of contents, and cross-references. Output as final .md files.

## Output Files
- `/mnt/agents/output/01-integration-contract-specification.md`
- `/mnt/agents/output/02-page-reality-index.md`
- `/mnt/agents/output/03-hook-architecture-blueprint.md`
- `/mnt/agents/output/04-type-synchronization-protocol.md`
- `/mnt/agents/output/05-ui-ux-component-strategy.md`
- `/mnt/agents/output/06-implementation-roadmap.md`
