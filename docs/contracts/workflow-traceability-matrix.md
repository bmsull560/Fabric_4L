# Workflow Traceability Matrix

> Map every user-facing workflow step to backend objects, status fields, and event sources.

---

## Workflow 1: Configure Ingestion → Run Ingestion → Monitor Job

| UI Step | Backend Layer | Backend Object | Status Field | Event Source | Required ID | Frontend Query Key |
|---------|---------------|----------------|--------------|--------------|-------------|--------------------|
| User opens "Sources" page | L1 | `Target` (source config) | — | Polling | — | `QK.sources.list(filters)` |
| User creates new source | L1 | `Target` | `status: draft` | Mutation response | `target_id` | `QK.sources.detail(id)` |
| User validates source | L1 | `Target` | `connection_test: passed/failed` | POST response | `target_id` | `QK.sources.detail(id)` |
| User clicks "Run" | L1 | `IngestionJob` | `status: pending` | POST response | `job_id` (returned from execute) | `QK.ingestion.detail(id)` |
| Job queued | L1 | `IngestionJob` | `status: pending` | Polling (5s) | `job_id` | `QK.ingestion.detail(id)` |
| Crawling in progress | L1 | `IngestionJob` | `status: running`, `progress.current_stage: crawling` | Polling (5s) | `job_id` | `QK.ingestion.detail(id)` |
| Extraction in progress | L1 | `IngestionJob` | `status: running`, `progress.current_stage: extracting` | Polling (5s) | `job_id` | `QK.ingestion.detail(id)` |
| Job completed | L1 | `IngestionJob` | `status: completed` | Polling (5s) | `job_id` | `QK.ingestion.detail(id)` |
| View compliance logs | L1 | `ComplianceLog` | `severity: info/warn/error` | Polling (30s) | `job_id` | `QK.ingestion.logs(id)` |

---

## Workflow 2: Trigger Extraction → Monitor Extraction → Retrieve Results

| UI Step | Backend Layer | Backend Object | Status Field | Event Source | Required ID | Frontend Query Key |
|---------|---------------|----------------|--------------|--------------|-------------|--------------------|
| User submits extraction | L2 | `ExtractionJob` | `status: PENDING` | POST response | `job_id` | `QK.extraction.job(id)` |
| Browser acquiring | L2 | `ExtractionJob` | `status: BROWSER_ACQUIRING` | Polling (2s) | `job_id` | `QK.extraction.job(id)` |
| Navigating / crawling | L2 | `ExtractionJob` | `status: NAVIGATING` | Polling (2s) | `job_id` | `QK.extraction.job(id)` |
| NER extraction | L2 | `ExtractionJob` | `status: EXTRACTING` | Polling (2s) | `job_id` | `QK.extraction.job(id)` |
| Semantic mapping | L2 | `ExtractionJob` | `status: TRANSFORMING` | Polling (2s) | `job_id` | `QK.extraction.job(id)` |
| Fabric assembly / storing | L2 | `ExtractionJob` | `status: STORING` | Polling (2s) | `job_id` | `QK.extraction.job(id)` |
| Completed | L2 | `ExtractionJob` | `status: COMPLETED` | Polling (2s) | `job_id` | `QK.extraction.job(id)` |
| View extracted entities | L2 | `ExtractionJob` | `extracted_entities: [...]` | Polling (2s) | `job_id` | `QK.extraction.job(id)` |
| Retrieve raw results | L2 | — | — | — | `job_id` | `QK.extraction.results(id)` |

**🔴 Gap:** `QK.extraction.results(id)` has no verified backend endpoint. The frontend currently reads `extracted_entities` from the job status response. A dedicated results endpoint may be needed for large payloads.

---

## Workflow 3: Persist to Graph → Query Entities / Subgraph

| UI Step | Backend Layer | Backend Object | Status Field | Event Source | Required ID | Frontend Query Key |
|---------|---------------|----------------|--------------|--------------|-------------|--------------------|
| Ingested content ingested to graph | L3 | `Entity` | `confidence_score` | Background (async) | `source_id` | `QK.graph.query(params)` |
| User searches entities | L3 | `Entity` | — | Query | — | `QK.entities.search(query)` |
| User views entity detail | L3 | `Entity` | `entity_type`, `properties` | Query | `entity_id` | `QK.entities.detail(id)` |
| User explores neighborhood | L3 | `Entity` + relationships | — | Query | `entity_id` | `QK.graph.context(entityId, hops)` |
| User traverses value paths | L3 | `Entity` + paths | `value_score` | Query | `entity_id` | `QK.graph.traversal(params)` |
| User visualizes subgraph | L3 | `Subgraph` | — | Query | `center_entity_id` | `QK.graph.subgraph(...)` |

---

## Workflow 4: Build Value Tree → Attach Formulas / Models / Variables

| UI Step | Backend Layer | Backend Object | Status Field | Event Source | Required ID | Frontend Query Key |
|---------|---------------|----------------|--------------|--------------|-------------|--------------------|
| User selects root entity | L3 | `Entity` | `entity_type` (must be Capability/UseCase) | Query | `entity_id` | `QK.entities.detail(id)` |
| System resolves value tree | L3 | `ValueTree` | `direction`, `max_depth` | Query | `entity_id` | `QK.valueTrees.tree(...)` |
| User attaches formula | L3 | `Formula` | `status: draft` | Mutation | `formula_id` | `QK.formulas.detail(id)` |
| User evaluates formula | L3 | `FormulaEvaluationResult` | `result`, `confidence` | POST response | `formula_id` | — |
| User attaches value model | L3 | `ValueModel` | `status: active` | Mutation | `model_id` | `QK.models.detail(id)` |
| User applies value pack | L3 | `ValuePack` | `status: applied` | POST response | `pack_id` | `QK.valuePacks.detail(id)` |
| User views value tree stats | L3 | `ValueTreeStats` | `total_nodes`, `max_depth` | Query | `entity_id` | `QK.valueTrees.tree(...)` |

---

## Workflow 5: Run Agent Workflow → Monitor via SSE → Complete / Fail

| UI Step | Backend Layer | Backend Object | Status Field | Event Source | Required ID | Frontend Query Key |
|---------|---------------|----------------|--------------|--------------|-------------|--------------------|
| User creates workflow | L4 | `WorkflowInstance` | `status: pending` | POST response | `workflow_instance_id` | `QK.workflows.detail(id)` |
| Workflow queued | L4 | `WorkflowInstance` | `status: pending` | SSE / Polling | `workflow_instance_id` | `QK.workflows.detail(id)` |
| Workflow running | L4 | `WorkflowInstance` | `status: running`, `progress_percentage` | SSE (primary) + Polling (fallback) | `workflow_instance_id` | `QK.workflows.detail(id)` |
| Step started | L4 | `WorkflowStep` | `event_type: node_started` | SSE | `workflow_instance_id` | SSE stream |
| Step completed | L4 | `WorkflowStep` | `event_type: node_completed` | SSE | `workflow_instance_id` | SSE stream |
| Workflow completed | L4 | `WorkflowInstance` | `status: completed`, `has_output: true` | SSE / Polling | `workflow_instance_id` | `QK.workflows.detail(id)` |
| User views result | L4 | `WorkflowResult` | `output` | Query | `workflow_instance_id` | `QK.workflows.detail(id)` + `GET /workflows/{id}/result` |
| Workflow failed | L4 | `WorkflowInstance` | `status: failed`, `error_count` | SSE / Polling | `workflow_instance_id` | `QK.workflows.detail(id)` |
| Workflow paused | L4 | `WorkflowInstance` | `status: paused` | Mutation response | `workflow_instance_id` | `QK.workflows.detail(id)` |
| Workflow resumed | L4 | `WorkflowInstance` | `status: running` | Mutation response | `workflow_instance_id` | `QK.workflows.detail(id)` |

**SSE Event Shape (L4):**
```
event: workflow_event
data: {"event_id": "...", "event_type": "node_started|node_completed|workflow_completed|error", "timestamp": "...", "message": "...", "payload": {...}}
```

---

## Workflow 6: Validate Output Against Ground Truth → View Benchmarks

| UI Step | Backend Layer | Backend Object | Status Field | Event Source | Required ID | Frontend Query Key |
|---------|---------------|----------------|--------------|--------------|-------------|--------------------|
| User views truth records | L5 | `TruthObject` | `status: validated|pending|stale` | Polling (30s) | — | `QK.groundTruth.list(filters)` |
| User validates a truth | L5 | `TruthObject` | `status: validated` | POST response | `truth_id` | `QK.groundTruth.list(filters)` |
| User views validation audit | L5 | `ValidationEvent` | `event_type`, `confidence` | Query | `truth_id` | `QK.groundTruth.audit(truthId)` |
| User views freshness summary | L5 | `FreshnessSummary` | `stale_count`, `fresh_count` | Query | — | `QK.groundTruth.freshnessSummary()` |
| User runs benchmark comparison | L6 | `BenchmarkComparison` | `score`, `percentile` | POST response | — | `QK.benchmarks.list(filters)` |
| User views maturity ladder | L5 | `MaturityLadder` | `levels: [...]` | Query | — | `QK.groundTruth.maturityLadder()` |

---

## Workflow 7: Export Document / Business Case

| UI Step | Backend Layer | Backend Object | Status Field | Event Source | Required ID | Frontend Query Key |
|---------|---------------|----------------|--------------|--------------|-------------|--------------------|
| User opens business case | L4 | `WorkflowInstance` | `status: completed` | Query | `workflow_id` | `QK.businessCases.detail(id)` |
| User clicks "Export PDF" | L4 | `DocumentExport` | `status: generating` | POST response | `workflow_id` | `QK.documents.export(id)` |
| System generates document | L4 | `DocumentExport` | `status: ready` | Polling (2s) | `export_job_id` | `QK.documents.export(id)` |
| User downloads file | L4 | Blob | `Content-Type: application/pdf` | Direct download | `export_job_id` | — |
| User exports to CRM | L4 | `IntegrationSync` | `status: synced|failed` | POST response | `workflow_id` | `QK.integrations.detail(provider)` |

---

## Event Source Summary

| Source | Used By | Latency | Reliability | Fallback |
|--------|---------|---------|-------------|----------|
| **React Query polling** | Ingestion, Extraction, Workflows (fallback), Ground Truth | 2s–30s | High | — |
| **SSE (Server-Sent Events)** | Workflows (primary), Agent Stream, C1 | <1s | Medium (connection may drop) | Polling every 5s |
| **WebSocket** | Signals (prospect stream) | <100ms | Medium | SSE or polling |
| **Mutation response** | Create source, Run ingestion, Create workflow, Validate truth | Immediate | High | — |
| **Background async** | Graph ingestion, Extraction → Graph persist | Minutes | High | Manual retry via UI |

---

## ID Propagation Chain

```
Source Config (target_id)
    ↓ POST /targets/{target_id}/execute
Ingestion Job (job_id)
    ↓ Background pipeline
Extraction Job (job_id) — may be same or different ID
    ↓ Background pipeline
Graph Entity (entity_id)
    ↓ User action
Value Tree (root_entity_id)
    ↓ User action
Workflow (workflow_instance_id)
    ↓ Agent execution
Business Case / Document Export (export_job_id)
    ↓ User action
Ground Truth (truth_id)
```

**Critical observation:** There is no unified `correlation_id` propagated across all UI steps. Each layer has its own ID space. The frontend must track multiple IDs to present a coherent user journey.

**Recommendation:** Introduce a `trace_id` or `session_id` that flows from ingestion → extraction → graph → workflow, surfaced in UI as "Job lineage" or "Audit trail".
