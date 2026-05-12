# Fabric_4L Contract Inventory

**Author:** Manus AI + Platform Contracts WG
**Sprint:** Sprint 0, stabilization and contract inventory
**Status (updated 2026-05-12):** L1–L6 and cross-layer ownership, validation status, and integration points are now explicitly assigned at endpoint-family granularity.

## Purpose

This inventory is the canonical working register for frontend-backend contract alignment. It records API contract artifacts, generated TypeScript DTO surfaces, frontend consumers, runtime validation coverage, mapper coverage, risk level, ownership, integration test anchors, and migration status.

## Allowed Migration Status Values

| Status | Meaning |
|---|---|
| `unknown` | The endpoint, consumer, or contract surface has not yet been inspected. |
| `inventoried` | The surface has been identified and recorded, but generated DTO, validation, or adapter coverage may still be incomplete. |
| `generated` | A generated TypeScript DTO/client artifact exists for the OpenAPI surface. |
| `validated` | Runtime validation exists for the response payload before feature logic consumes it. |
| `adapted` | DTO-to-domain mapping exists and React-facing code receives domain or view models only. |
| `migrated` | The endpoint or feature follows the full contract pattern: OpenAPI, generated DTO, Zod validation, mapper, tests, and UI boundary compliance. |
| `deprecated` | The endpoint or frontend consumer is still present but has an approved retirement path. |
| `removed` | The endpoint or frontend consumer has been retired. |

## Risk-Level Definitions

| Risk | Definition | Examples |
|---|---|---|
| P0 | A mismatch can create tenant, governance, financial, workflow, evidence, policy, or launch-readiness risk. | L3 graph topology, L4 agent/workflow events, L5 truth/evidence, L6 benchmark policy decisions, formulas, ROI, value-case outputs, tenant/account identity. |
| P1 | A mismatch can break important product workflows or user trust but does not directly govern high-risk decisions. | Account setup, integrations metadata, source configuration, pack framework display, usage and invoice status. |
| P2 | A mismatch is primarily display-only, administrative, or migration-cleanup debt. | Low-risk labels, static metadata, non-authoritative presentation fields. |

## Contract Inventory (endpoint-family granularity)

| Layer | Service | Endpoint Family | HTTP Methods | Operation IDs | OpenAPI Artifact | Generated TS Client | Frontend Integration Points | Runtime Validator Status | Mapper Status | Contract Tests | Risk | Owner | Migration Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L1 | Ingestion | `/api/*` ingestion workflow and source lifecycle | GET/POST/PUT/PATCH/DELETE | `layer1-*` family in spec | `contracts/openapi/layer1-ingestion.json` | `apps/web/src/api/generated/l1/index.ts` | Service-to-service + planned web ingestion admin surfaces | OpenAPI schema-backed responses in service routes; frontend adapter coverage pending | API boundary mappers pending per endpoint | `tests/contract/test_layer1_compatibility_deprecation_contract.py`; `services/layer1-ingestion/tests/test_observability_contract_integration.py` | P1 | Layer 1 Ingestion Team + Platform Contracts WG | `generated` | Integration point: ingestion jobs, source metadata, compliance-aware job state propagation. |
| L2 | Extraction | `/v1/*` extraction and ontology APIs | GET/POST/PUT/PATCH/DELETE | `layer2-*` family in spec | `contracts/openapi/layer2-extraction.json` | `apps/web/src/api/generated/l2/index.ts` | Service-to-service extraction orchestration; no direct React consumers in generated client tree | Route-level schema enforcement present; cross-layer response validation partially covered | Domain mapping mostly backend-side; frontend mapper not yet required for direct consume | `tests/contract/test_l2_l3_contract.py`; `services/layer2-extraction/tests/test_api_rate_limit_contract.py` | P1 | Layer 2 Extraction Team + Ontology Platform Team | `generated` | Integration point: ontology-guided extraction payloads consumed by L3 ingest APIs. |
| L3 | Knowledge / Graph | `/v1/*`, `/graph/*`, `/entities/*` knowledge graph surfaces | GET/POST/PUT/PATCH/DELETE | `layer3-*`, `graph-*`, `entity-*` families | `contracts/openapi/layer3-knowledge.json` | `apps/web/src/api/generated/l3/index.ts` | `apps/web/src/api/packs.ts`; `apps/web/src/api/valuePackFramework.ts` | Partial runtime validation in `apps/web/src/api/validation.ts`; backend contract tests present | Partial adapter patterns in API modules; full endpoint-family mappers still in progress | `tests/contract/test_layer3_contract.py`; `tests/contract/test_l3_graph_contract.py`; `tests/contract/test_graph_api_contract.py`; `tests/contract/test_entity_contract.py`; `tests/contract/test_l3_value_trees_contract.py`; `tests/contract/test_l3_formulas_contract.py`; `tests/contract/test_l3_route_alias_parity.py`; `tests/contract/test_l3_graph_deprecation_contract.py`; `tests/contract/test_l3_provenance_audit_contract.py` | P0 | Layer 3 Knowledge Team + Graph UI Team | `inventoried` | Integration point: graph queries, formulas, value trees, and provenance are consumed by value-pack UI features. |
| L4 | Agents / Workflow | `/v1/*`, `/auth/*`, root workflow/tool endpoints | GET/POST/PUT/PATCH/DELETE | `layer4-*`, `workflow-*`, `tool-*` families | `contracts/openapi/layer4-agents.json` | `apps/web/src/api/generated/l4/index.ts` | Agent/workflow UIs and streaming clients in app workspace | Partial event parsing and contract assertions exist; additional runtime response guards pending | Endpoint-family mapper coverage is mixed; workflow output mapping prioritized | `tests/contract/test_layer4_contract.py`; `tests/contract/test_l4_workflows_contract.py`; `tests/contract/test_l4_frontend_contract.py`; `services/layer4-agents/tests/test_workflow_canonical_contract.py`; `services/layer4-agents/tests/test_frontend_endpoint_contracts.py`; `services/layer4-agents/tests/test_tools_routes_contract.py`; `services/layer4-agents/tests/test_tool_result_contract.py`; `services/layer4-agents/tests/test_agent_tool_result_contracts.py`; `services/layer4-agents/tests/test_governance_workflow_contracts.py`; `services/layer4-agents/tests/test_startup_contract.py` | P0 | Layer 4 Agents Team + Agent Experience Team | `inventoried` | Integration point: workflow execution, checkpoint/resume, and tool-result streams into right-rail agent UX. |
| L5 | Ground Truth | `/api/*` truth object, evidence, governance endpoints | GET/POST/PUT/PATCH/DELETE | `layer5-*`, `ground-truth-*` families | `contracts/openapi/layer5-ground-truth.json` | `apps/web/src/api/generated/l5/index.ts` | `apps/web/src/hooks/useGroundTruthGovernance.ts` (API-boundary hook) | Backend contract tests present; frontend hook-level schema guards need explicit mapper gate | Hook-level mapper classification in progress (API hook vs UI hook boundary) | `tests/contract/test_layer5_contract.py`; `tests/contract/test_journey_contracts.py`; `tests/contract/test_layer_integration.py` | P0 | Layer 5 Ground Truth Team + Governance UI Team | `inventoried` | Integration point: evidence-backed truth validation and governance decisions surfaced in workflow and audit UX. |
| L6 | Benchmarks / Policy | `/v1/*` benchmarks, datasets, industry lists | GET/POST | `layer6-*`, `benchmark-*` families | `contracts/openapi/layer6-benchmarks.json` | `apps/web/src/api/generated/l6/index.ts` | Benchmark and policy comparison UI surfaces (generated client available; direct imports pending expansion) | Contract validation present in backend API schemas; frontend validation coverage pending first-class modules | Mapper coverage pending dedicated benchmark API modules | `tests/contract/test_layer_integration.py`; `tests/contract/test_journey_contracts.py` | P0 | Layer 6 Benchmarks Team + Benchmark UI Team | `generated` | Integration point: benchmark comparisons and policy metadata consumed by strategy and peer-analysis views. |
| Cross-layer | Signals | `/v1/signals/*` intelligence signals APIs | GET/POST | `signals-*` family | `contracts/openapi/signals.json` | `apps/web/src/api/generated/signals/index.ts` | Cross-workspace intelligence features and future L3/L4 insight panes | OpenAPI-defined contract exists; runtime validators per consumer are pending | Mapper coverage pending as signals consumers scale | `tests/contract/test_layer_integration.py`; `tests/contract/test_journey_contracts.py`; `tests/contract/test_system_route_contract.py` | P1 | Intelligence Platform Team + Frontend Platform Team | `generated` | Integration point: signal feeds enrich graph context and workflow prioritization experiences. |

## Cross-check evidence

- OpenAPI artifacts checked: `contracts/openapi/layer1-ingestion.json`, `contracts/openapi/layer2-extraction.json`, `contracts/openapi/layer3-knowledge.json`, `contracts/openapi/layer4-agents.json`, `contracts/openapi/layer5-ground-truth.json`, `contracts/openapi/layer6-benchmarks.json`, `contracts/openapi/signals.json`.
- Generated frontend client surfaces checked: `apps/web/src/api/generated/l1/index.ts`, `apps/web/src/api/generated/l2/index.ts`, `apps/web/src/api/generated/l3/index.ts`, `apps/web/src/api/generated/l4/index.ts`, `apps/web/src/api/generated/l5/index.ts`, `apps/web/src/api/generated/l6/index.ts`, `apps/web/src/api/generated/signals/index.ts`.
- Direct generated-consumer references currently present: `apps/web/src/api/packs.ts`, `apps/web/src/api/valuePackFramework.ts`, `apps/web/src/hooks/useGroundTruthGovernance.ts`.

## Sprint 0 Inventory Acceptance Status

| Acceptance Item | Status | Evidence |
|---|---|---|
| Inventory template is committed. | COMPLETE | This document defines the canonical inventory columns and statuses. |
| Risk-level definitions are included. | COMPLETE | P0, P1, and P2 classifications are defined above. |
| Endpoint-family ownership is assigned for L1–L6 and cross-layer surfaces. | COMPLETE | All inventory rows now include concrete owners and integration points. |
| Generated DTO imports are cataloged. | COMPLETE | Generated index surfaces and direct consuming modules are listed above. |
| Contract test anchors are linked for each family. | COMPLETE | Every inventory row includes `tests/contract` and/or layer-specific suites. |
| Remaining placeholder markers in this inventory are eliminated. | COMPLETE | Placeholder markers were removed from L1–L6 and cross-layer inventory rows. |
