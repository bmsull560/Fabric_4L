# Normalization Decision Document

> Architectural decision: Should the frontend call layer APIs directly through aliases, or should there be a BFF / API Gateway product contract?

---

## Decision

**Adopt a Product API / BFF layer between the frontend and backend layer services.**

```
Frontend  →  Product API / BFF  →  Layer Services (L1–L6)
```

**Not:**
```
Frontend  →  Layer 1
Frontend  →  Layer 2
Frontend  →  Layer 3
...
```

The existing direct-layer pattern is retained as a **transitional architecture** during BFF build-out, but all new product surfaces must be designed against the BFF contract, not against individual layer APIs.

---

## Status

| Aspect | State |
|--------|-------|
| Decision | **Proposed** — awaiting architecture review ratification |
| BFF implementation | Not started — this document is the charter |
| Transition plan | Phase 0 (documentation + contract tests) → Phase 1 (gateway normalization) → Phase 2 (BFF composition endpoints) → Phase 3 (frontend migration) |

---

## Justification

### 1. Frontend is a composed product surface, not a layer-debug UI

The frontend modules (Intelligence, Value Cases, Hypotheses, Governance) aggregate data from 2–4 backend layers. Today this composition lives implicitly in React hooks. A BFF makes these product contracts explicit, testable, and versioned.

### 2. Cross-layer workflows require composition

- **Value Case** = workflow result (L4) + value tree (L3) + evidence (L3) + formulas (L3).
- **Intelligence Summary** = account (L4) + briefing (L4) + graph signals (L3) + ingestion history (L1).
- **Governance Dashboard** = tenants (L4) + users (L4) + API keys (L4) + audit logs (L4/L1).

Composing these in the frontend creates tight coupling, duplicate data fetching, and inconsistent error handling.

### 3. Stability: frontend should not break when backend paths refactor internally

Current state: frontend imports `LAYER_PREFIXES` and constructs paths like `/api/v1/agents/v1/intelligence/...`. If L4 renames `/v1/intelligence` to `/v1/briefings`, the frontend breaks. A BFF isolates the frontend from layer-internal routing changes.

### 4. Auth/tenant normalization belongs at gateway

- `X-Tenant-ID` is injected by frontend `client.ts` today, but backend layers handle it inconsistently (some use JWT claims fallback, some default to `"default"`).
- API keys vs JWT vs OIDC flows have different middleware paths per layer.
- A gateway/BFF can enforce a single auth model and propagate a normalized tenant context to layers.

### 5. Response envelope consistency is easier at a single translation layer

Today:
- L1 returns `JobListResponse` with nested pagination.
- L2 returns `ExtractionStatusResponse` with flat fields.
- L3 returns `GraphQueryResponse` with optional `context_graph`.
- L4 returns workflow results in 4 different pagination/array shapes.
- L5 returns `TruthObjectListResponse` with its own pagination.
- Errors are `{"detail"}`, `{"message","code"}`, or plain text.

A gateway/BFF can wrap all responses in a consistent envelope and normalize errors.

---

## What the BFF Owns

| Responsibility | Owner | Notes |
|----------------|-------|-------|
| **Route aliases** | BFF / Gateway | `/api/intelligence/*` → calls L4 + L3. `/api/value-cases/*` → calls L4 + L3. |
| **Response normalization** | BFF / Gateway | Enforce `{ data, meta, links? }` envelope. Normalize pagination to `{ items, total, limit, offset, has_more }`. |
| **Composed product endpoints** | BFF | `GET /api/product/intelligence/accounts/{id}/summary`, `GET /api/product/value-cases/{id}`, etc. |
| **Error envelope standardization** | Gateway | All errors → `{ message, code, trace_id, status }`. |
| **Auth / tenant propagation** | Gateway | Resolve tenant from JWT, API key, or header; inject into layer calls. |
| **Caching / TTL** | BFF | Cache reference data (ontology, value packs) with short TTLs. |
| **Rate limiting (per product)** | Gateway | Product-level rate limits, not just per-layer. |

## What the BFF Does NOT Own

| Responsibility | Owner | Notes |
|----------------|-------|-------|
| **Business logic** | Backend layers | BFF delegates to L1–L6. No orchestration logic beyond simple parallel fetching. |
| **Graph traversal algorithms** | L3 | BFF calls L3; does not implement graph queries. |
| **LLM extraction logic** | L2 | BFF calls L2; does not run extraction. |
| **Workflow execution** | L4 | BFF calls L4; does not run LangGraph. |
| **Truth validation rules** | L5 | BFF calls L5; does not validate truths. |

---

## Proposed BFF Endpoint Surface (Phase 1)

| Product Endpoint | Method | Backing Layers | Composition |
|------------------|--------|----------------|-------------|
| `/api/product/accounts` | GET | L4 | Accounts list + sync status. |
| `/api/product/accounts/{id}/intelligence` | GET | L4, L3 | Account + briefing + deal readiness + signals. |
| `/api/product/value-cases` | GET/POST | L4 | Workflow list filtered by type; creation. |
| `/api/product/value-cases/{id}` | GET | L4, L3 | Workflow result decomposed into ROI + narrative + evidence. |
| `/api/product/value-cases/{id}/export` | POST | L4 | Document export initiation. |
| `/api/product/hypotheses` | GET/POST | L4, L3 | Hypotheses + related entities + provenance. |
| `/api/product/governance/dashboard` | GET | L4 | Tenants + users + API keys + audit summary. |
| `/api/product/settings` | GET/PATCH | L4, L3 | Tenant settings + integrations + feature flags. |
| `/api/product/ingestion/status` | GET | L1 | Recent jobs + stats + source health. |
| `/api/product/extraction/status` | GET | L2 | Active extraction jobs + progress. |
| `/api/product/graph/search` | POST | L3 | Unified graph query + entity search. |
| `/api/product/truths/dashboard` | GET | L5 | Freshness summary + stale count + maturity ladder. |

---

## Migration Strategy

### Phase 0: Contract Lock (current)
- ✅ Complete contract map, route audit, and normalization strategy.
- ✅ Establish contract test stubs (this package).
- ✅ Add drift detection script to CI.

### Phase 1: Gateway Normalization (no BFF yet)
- Add gateway rewrite rules for all `/api/product/*` → existing layer paths.
- Normalize error responses at gateway.
- Standardize pagination envelope at gateway for L1, L4, L5.
- **Frontend impact:** None. Gateway improves backend responses transparently.

### Phase 2: BFF Composition Endpoints
- Build BFF service (can be a lightweight router in L4 or a new service).
- Implement composed endpoints for Intelligence, Value Cases, Governance, Settings.
- Add caching and circuit breakers.
- **Frontend impact:** New hooks can opt into BFF endpoints; old hooks remain functional.

### Phase 3: Frontend Migration
- Migrate hooks one domain at a time: Workflows → Value Cases → Intelligence → Governance.
- Remove `LAYER_PREFIXES` from frontend; all calls go to `/api/product/*`.
- Deprecate direct layer client paths.
- **Timeline:** 2–3 sprints per domain.

### Phase 4: Layer API Internalization
- Once frontend no longer calls layers directly, layer paths can be refactored internally without frontend coordination.
- Gateway can enforce internal-only access to layer APIs.

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| BFF becomes a bottleneck / SPOF | High | Deploy BFF as stateless replicas with health checks. Use circuit breakers for layer calls. |
| BFF adds latency | Medium | Cache reference data. Use HTTP/2 or connection pooling to layers. |
| BFF logic creeps into business logic | High | Enforce "BFF owns composition only" rule in code review. |
| Frontend migration takes too long | Medium | Phase 1 gateway improvements deliver value immediately; BFF migration is incremental. |
| Backend teams resist path changes | Low | Phase 4 allows layer refactoring only after frontend migration is complete. No immediate changes required. |

---

## Decision Record

| Field | Value |
|-------|-------|
| **Decision ID** | ADR-2026-001 |
| **Title** | Adopt Product API / BFF Layer Between Frontend and Backend Services |
| **Context** | Frontend directly calls 6 backend layers with inconsistent paths, shapes, and auth handling. Product workflows require cross-layer composition that currently lives in React hooks. |
| **Decision** | Build a BFF / Product API layer. Frontend calls `/api/product/*`; BFF delegates to L1–L6. |
| **Consequences** | + Frontend stability. + Explicit product contracts. + Centralized auth/tenant. + Easier mobile/API consumer support. − Additional service to operate. − Migration cost. |
| **Author** | Contract Alignment Package |
| **Date** | 2026-04-30 |
