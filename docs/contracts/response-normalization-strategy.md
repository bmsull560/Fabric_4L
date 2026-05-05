# Response Normalization Strategy

> Document the chosen normalization approach for every endpoint family. Do not change runtime code.

---

## Decision Framework

| Option | Name | Description | Owner |
|--------|------|-------------|-------|
| **A** | Backend Standard Envelope | Backend returns `{ data: T, meta: {...} }` for all responses. | Backend |
| **B** | Frontend API Adapters | Frontend hook/client normalizes resource-root payloads before state consumption. | Frontend |
| **C** | BFF/Gateway Normalization | Proxy/gateway layer rewrites responses into product-oriented shapes. | Gateway / BFF |

**Current state:** The system uses a **hybrid of B and C**, with heavy B (frontend adapters) and implicit C (Vite dev proxy rewrites paths but not bodies). There is no consistent backend envelope (Option A is not adopted).

---

## Normalization by Endpoint Family

### 1. Ingestion (L1)

| Aspect | Current State |
|--------|---------------|
| **Chosen option** | **B** — Frontend adapters |
| **Current actual shape** | Backend returns resource-root objects: `JobListResponse` (paginated with `items`, `total`, etc.), `ApiJobDetailDto`, `DataSource`. |
| **Expected shape** | Frontend `parseIngestionJobs`, `parseIngestionAggregation` coerce fields and flatten nested structures. |
| **Adapter needed?** | Yes — runtime parsers in `frontend/client/src/types/api.ts` |
| **Owner** | Frontend |

**Details:**
- `parseIngestionJobs` maps `progress_percent_complete` → `progress`, coerces dates.
- `parseIngestionAggregation` normalizes `by_status` Record and filters non-numeric values.
- `ApiJobDetailDto` is used directly; no envelope wrapper.

---

### 2. Extraction (L2)

| Aspect | Current State |
|--------|---------------|
| **Chosen option** | **B** — Frontend adapters |
| **Current actual shape** | `ExtractionStatusResponse` (backend-defined Pydantic model). |
| **Expected shape** | `ExtractionJob` — frontend transforms backend status strings (`BROWSER_ACQUIRING`, `STORING`) into step arrays with percentages. |
| **Adapter needed?** | Yes — `useExtractionJob` hook performs heavy transformation. |
| **Owner** | Frontend |

**Details:**
- Frontend builds a 4-step wizard UI from a flat `status` field.
- `progress_logs` are mapped to `LogLine` with color coding.
- `extracted_entities` are mapped to `EntityChip` with color mapping.
- **Gap resolved:** The legacy `/jobs/{id}` alias was removed. Frontend must call `GET /extract/status/{id}`. Adapter logic for response transformation is still required.

---

### 3. Graph Query (L3)

| Aspect | Current State |
|--------|---------------|
| **Chosen option** | **B** — Frontend Zod validation |
| **Current actual shape** | `GraphQueryResponse` — flat object with `entities`, `relationships`, `context_graph`. |
| **Expected shape** | Same as backend shape; validated at runtime with `GraphQueryResponseSchema`. |
| **Adapter needed?** | Minimal — validation only. |
| **Owner** | Frontend |

**Details:**
- `safeParseResponse` is used to validate trust boundaries.
- On validation failure, frontend throws and shows error state.
- `context_graph` is optional; frontend handles missing field gracefully.

---

### 4. Entities (L3)

| Aspect | Current State |
|--------|---------------|
| **Chosen option** | **B** — Frontend adapters |
| **Current actual shape** | `EntityListResponse` (backend paginated). |
| **Expected shape** | `Entity[]` with normalized `entity_type` and `confidence_score`. |
| **Adapter needed?** | Yes — `parseEntityResults` normalizes field name variants (`id` vs `entity_id`, `name` vs `title`, `confidence` vs `confidence_score`). |
| **Owner** | Frontend |

**Details:**
- `parseEntityResults` is a defensive parser that accepts multiple backend field names for the same semantic concept.
- This suggests backend has inconsistent field naming across endpoints or historical schema evolution.

---

### 5. Formulas (L3)

| Aspect | Current State |
|--------|---------------|
| **Chosen option** | **B** — Frontend Zod + adapters |
| **Current actual shape** | `Formula`, `FormulaEvaluationResult`, `ApprovalRequest` (backend Pydantic). |
| **Expected shape** | Same shape, strictly validated via Zod (`FormulaSchema`, `FormulaEvaluationResultSchema`). |
| **Adapter needed?** | Yes — validation and error formatting. |
| **Owner** | Frontend |

**Details:**
- `FormulaSchema` enforces `version` regex (`^\d+\.\d+\.\d+$`), `status` enum, datetime formats.
- Governance endpoints (`/formulas/approvals/pending`) return a different shape; no dedicated Zod schema exists for approval list.

---

### 6. Value Trees (L3)

| Aspect | Current State |
|--------|---------------|
| **Chosen option** | **B** — Frontend Zod validation |
| **Current actual shape** | `ValueTreeResponse` (backend OpenAPI-generated). |
| **Expected shape** | Same shape; validated with `ValueTreeResponseSchema`. |
| **Adapter needed?** | Minimal — validation only. |
| **Owner** | Frontend |

---

### 7. Value Packs (L3)

| Aspect | Current State |
|--------|---------------|
| **Chosen option** | **B** — Frontend adapters |
| **Current actual shape** | `ValuePack[]` from `/v1/packs`; `ValuePackFrameworkData` from `/v1/valuepacks/{id}`. |
| **Expected shape** | Unified `ValuePack` type in frontend; `useSuggestValuePacks` performs client-side matching against cached framework data. |
| **Adapter needed?** | Yes — client-side composition and matching logic. |
| **Owner** | Frontend |

**Details:**
- `useSuggestValuePacks` does not call a dedicated backend endpoint; it matches locally.
- **Future:** If suggestion logic becomes complex, move to BFF (Option C) or backend API.

---

### 8. Workflows (L4)

| Aspect | Current State |
|--------|---------------|
| **Chosen option** | **B** — Heavy frontend normalization |
| **Current actual shape** | Multiple shapes: `WorkflowStatusResponse`, `WorkflowResultResponse`, `PaginatedWorkflows` (new), raw array (legacy). |
| **Expected shape** | `Workflow` — frontend normalizes `workflow_id` vs `workflow_instance_id` vs `id`, `progress` vs `progress_percentage`, date fields. |
| **Adapter needed?** | Yes — `normalizeWorkflow`, `normalizeWorkflowList`, `extractWorkflowList`, `parsePaginatedResponse`. |
| **Owner** | Frontend |

**Details:**
- `useWorkflows.ts` handles 4 response formats: paginated object, raw array, `{ workflows: [] }`, and individual status objects.
- This is the most complex normalization surface in the frontend.
- **Risk:** Every backend pagination change requires frontend adapter updates.

---

### 9. Business Cases (L4)

| Aspect | Current State |
|--------|---------------|
| **Chosen option** | **B** — Frontend decomposition |
| **Current actual shape** | `WorkflowResultResponse` with `steps: [{ agent, result: { output } }]`. |
| **Expected shape** | `BusinessCaseData` — frontend decomposes workflow result by agent name (`ROICalculationAgent`, `NarrativeSynthesisAgent`). |
| **Adapter needed?** | Yes — `useBusinessCases.ts` extracts `roiResult` and `narrativeResult` from step array. |
| **Owner** | Frontend |

**Details:**
- `parseBusinessCaseRoiOutput` and `parseBusinessCaseNarrativeOutput` are runtime parsers.
- Business case data is **implicitly composed** inside a workflow result; no dedicated business-case API exists.

---

### 10. Intelligence / Narratives / Accounts (L4)

| Aspect | Current State |
|--------|---------------|
| **Chosen option** | **B** — Frontend type casting |
| **Current actual shape** | Backend returns resource-root objects (`AccountBriefing`, `Narrative`, `Account`). |
| **Expected shape** | Same shapes; frontend casts `response.data as Type`. |
| **Adapter needed?** | No — shapes align well. |
| **Owner** | Frontend |

---

### 11. Ground Truth (L5)

| Aspect | Current State |
|--------|---------------|
| **Chosen option** | **B** — Frontend normalization |
| **Current actual shape** | `TruthObjectListResponse` (OpenAPI-generated), `ValidationEventResponse[]`, `FreshnessSummaryResponse`. |
| **Expected shape** | Same shapes; `useGroundTruthGovernance.ts` normalizes pagination with `normalizeTruthItems` and constructs `StaleTruthsResponse`. |
| **Adapter needed?** | Yes — pagination normalization. |
| **Owner** | Frontend |

---

### 12. Agent Stream / C1 (L4)

| Aspect | Current State |
|--------|---------------|
| **Chosen option** | **B** — Client-side event synthesis |
| **Current actual shape** | SSE stream of raw events or JSON chunks. |
| **Expected shape** | AG-UI event sequence (`RUN_STARTED` → `STEP_STARTED` → `TEXT_MESSAGE` → `RUN_FINISHED`). |
| **Adapter needed?** | Yes — `AgentEventClient.ts` synthesizes full AG-UI lifecycle from a single POST response. |
| **Owner** | Frontend |

**Details:**
- `sendAgentMessage` wraps `POST /agent-stream/chat` and emits synthetic events.
- C1 stream (`POST /c1/stream`) is consumed as raw fetch with custom chunk parsing.

---

### 13. Error Responses (All Layers)

| Aspect | Current State |
|--------|---------------|
| **Chosen option** | **B** — Frontend error parser |
| **Current actual shape** | Inconsistent across layers: FastAPI `{"detail": "..."}`, custom `{"message", "code", "trace_id"}`, or plain text. |
| **Expected shape** | `ErrorResponse = { message?: string, code?: string, trace_id?: string }` |
| **Adapter needed?** | Yes — `client.ts` uses `ErrorResponseSchema` with Zod `safeParse`. Falls back to `error.message`. |
| **Owner** | Frontend (today); should move to **Gateway (C)**. |

---

## Strategic Recommendation

| Endpoint Family | Current Option | Target Option | Rationale |
|-----------------|----------------|---------------|-----------|
| Ingestion | B | C (Gateway) | Stable shape; gateway can add envelope if needed. |
| Extraction | B | C (Gateway) | Heavy frontend transformation should move closer to backend. |
| Graph / Entities | B | B | Validation at trust boundary is correct; keep frontend Zod. |
| Formulas | B | B | High-risk domain; frontend validation adds safety. |
| Workflows | B | C (BFF) | Multi-shape normalization is brittle; BFF should canonicalize pagination. |
| Business Cases | B | C (BFF) | Composed decomposition belongs in BFF. |
| Intelligence / Accounts | B | B | Simple casting; no normalization needed. |
| Ground Truth | B | C (Gateway) | Pagination normalization belongs at gateway. |
| Agent Stream | B | B | Real-time streaming requires client-side adapters. |
| Errors (all) | B | C (Gateway) | Gateway must enforce consistent error envelope. |

**Summary:** The frontend currently owns too much normalization. The highest-leverage migration is:
1. **Gateway (Option C)** owns error envelopes and pagination wrappers.
2. **BFF (Option C)** owns business-case decomposition and workflow result shaping.
3. **Frontend (Option B)** keeps runtime validation (Zod) for high-risk domains (Graph, Formulas).

See `normalization-decision.md` for the architectural decision record.
