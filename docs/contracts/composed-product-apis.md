# Composed Product API Contracts

> Frontend modules that do not map cleanly to a single backend layer. Document the composition contract explicitly.

---

## 1. Account Intelligence Summary

| Field | Value |
|-------|-------|
| **Consumer Screen** | `/intelligence/accounts/{accountId}` |
| **Composed Endpoint** | Multiple hooks: `useIntelligenceBriefing`, `useAccountDetail`, `useAccountActivity`, `useProductSignalMatching` |
| **Backing Layers** | L4 (Intelligence, Accounts), L3 (Products, Graph signals), L1 (Ingestion history — optional) |
| **Composition Logic** | 1. Fetch account base record (`GET L4 /accounts/{id}`). 2. Fetch briefing (`GET L4 /intelligence/account/{id}/briefing`). 3. Fetch activity timeline (`GET L4 /accounts/{id}/activity`). 4. Fetch product-signal overlap (`GET L3 /products/signal-matching?account_id={id}`). 5. Merge into unified `AccountIntelligence` view model. |
| **Data Freshness** | Briefing: 5 min stale (detail). Activity: 5 min stale. Signals: 10 min stale (reference). |
| **Error Behavior (Partial Failure)** | If briefing fails, show account header + activity with empty intelligence panel. If activity fails, show briefing + static account card. If signals fail, hide signal-matching widget gracefully. |
| **Loading / Partial-Data** | Skeleton on account header. Independent skeletons on briefing panel, activity feed, and signals widget. Each section retries independently. |
| **Tenant / Auth** | `X-Tenant-ID` + Bearer JWT on all calls. Same tenant context propagated. |

---

## 2. Value Case / ROI Narrative

| Field | Value |
|-------|-------|
| **Consumer Screen** | `/value-cases/{caseId}` |
| **Composed Endpoint** | `useBusinessCase(caseId)` + `useBusinessCaseResult(caseId)` |
| **Backing Layers** | L4 (Workflow engine), L3 (Value trees, Formulas, Evidence, Competitive intel) |
| **Composition Logic** | 1. Retrieve workflow result (`GET L4 /workflows/{id}/result`). 2. Decompose `steps[]` by agent name: `ROICalculationAgent` → `parseBusinessCaseRoiOutput`. `NarrativeSynthesisAgent` → `parseBusinessCaseNarrativeOutput`. 3. If value tree context is needed, fetch `GET L3 /value-trees/{entity_id}`. 4. If evidence is needed, fetch `GET L3 /case-studies?prospect_id={id}`. 5. Render composed `BusinessCaseData`. |
| **Data Freshness** | Workflow result: polled every 5s while running; 5 min stale when completed. Value tree: 10 min stale. Evidence: 10 min stale. |
| **Error Behavior (Partial Failure)** | If ROI agent step missing, show narrative only with "ROI calculation pending" badge. If narrative missing, show ROI table with raw summary. If value tree unavailable, skip tree visualization. |
| **Loading / Partial-Data** | Skeleton header while workflow running. Step-by-step progress bar from workflow status. Once complete, fade-in sections as data arrives. |
| **Tenant / Auth** | `X-Tenant-ID` + Bearer JWT on all calls. Workflow result is tenant-scoped by backend. |

---

## 3. Hypothesis Workspace

| Field | Value |
|-------|-------|
| **Consumer Screen** | `/hypotheses` and `/hypotheses/{id}` |
| **Composed Endpoint** | `useHypotheses`, `useHypothesisDetail`, `useHypothesisStats` |
| **Backing Layers** | L4 (Value hypotheses, Account enrichment), L3 (Entities, Signals, Provenance) |
| **Composition Logic** | 1. Fetch hypothesis (`GET L4 /value-hypotheses/{id}`). 2. Fetch related entities (`GET L3 /entities?search_text={hypothesis.target}`). 3. Fetch provenance trail (`GET L3 /evidence/search?entity_id={id}`). 4. Fetch account enrichment status (`GET L4 /enrichment/status`). 5. Merge into workspace view with annotation UI. |
| **Data Freshness** | Hypothesis: 5 min stale. Entities: 10 min stale. Provenance: 10 min stale. Enrichment: realtime poll (2s). |
| **Error Behavior (Partial Failure)** | If entities fail, show hypothesis text with "related data unavailable". If provenance fails, hide evidence sidebar. If enrichment fails, show static hypothesis without live signals. |
| **Loading / Partial-Data** | Skeleton cards for each hypothesis. Inline spinner on entity matches. Empty-state illustration when no signals found. |
| **Tenant / Auth** | `X-Tenant-ID` + Bearer JWT on all calls. |

---

## 4. Governance Dashboard

| Field | Value |
|-------|-------|
| **Consumer Screen** | `/admin/governance` |
| **Composed Endpoint** | `useGovernanceTenants`, `useGovernanceUsers`, `useGovernanceApiKeys` |
| **Backing Layers** | L4 (Tenants, Users, API keys), L1-L5 (Audit logs — optional) |
| **Composition Logic** | 1. Fetch tenants (`GET L4 /tenants`). 2. Fetch users for selected tenant (`GET L4 /users`). 3. Fetch API keys (`GET L4 /api-keys`). 4. (Future) Fetch audit events from L4 `/v1/audit/logs` or L1 `/compliance/logs`. 5. Render dashboard with tenant selector. |
| **Data Freshness** | Tenants: 10 min stale (reference). Users: 5 min stale. API keys: 5 min stale. Audit: realtime poll (5s). |
| **Error Behavior (Partial Failure)** | If tenants fail, show error boundary with retry. If users fail, show tenant card with "users unavailable". If API keys fail, hide keys panel. |
| **Loading / Partial-Data** | Skeleton table for users and keys. Tenant selector loads first; other panels stream in. |
| **Tenant / Auth** | `X-Tenant-ID` + Bearer JWT. Admin scope required for user invite and API key deletion. |

---

## 5. Settings Configuration Center

| Field | Value |
|-------|-------|
| **Consumer Screen** | `/admin/settings` |
| **Composed Endpoint** | `usePlatformSettings`, `useIntegrations`, `useBillingEntitlements` |
| **Backing Layers** | L4 (Tenant settings, Integrations, Billing), L3 (Ontology schema — optional) |
| **Composition Logic** | 1. Fetch tenant settings (`GET L4 /tenant/settings`). 2. Fetch integrations (`GET L4 /integrations`). 3. Fetch billing entitlements (`GET L4 /billing/entitlements`). 4. (Future) Fetch ontology schema (`GET L3 /ontology/schema`). 5. Render settings form with feature-gated sections based on entitlements. |
| **Data Freshness** | Settings: 10 min stale. Integrations: 5 min stale. Billing: 5 min stale. |
| **Error Behavior (Partial Failure)** | If settings fail, show error with "retry" button. If integrations fail, show static settings without sync controls. If billing fails, assume all features enabled (fail-open for UX, backend still enforces). |
| **Loading / Partial-Data** | Settings form skeleton. Integrations load as toggles. Billing badges load last. |
| **Tenant / Auth** | `X-Tenant-ID` + Bearer JWT. Settings update requires admin or owner role. |

---

## Composition Pattern Registry

| Pattern | Used By | Implementation | Risk |
|---------|---------|----------------|------|
| **Hook aggregation** | Intelligence Summary, Governance | Multiple `useQuery` hooks in same component; React Query handles parallel fetching. | Low — independent cache and retry. |
| **Workflow result decomposition** | Value Case, Business Case | Parse `steps[]` array by `agent` name; extract `result.output`. | **High** — agent names are string constants; renaming an agent breaks frontend. |
| **Client-side matching** | Value Pack Suggestions | Local filter against cached `ValuePackFrameworkData`. | Medium — stale data, large payloads. |
| **SSE synthesis** | Agent Stream, C1 | Single POST → client emits synthetic event sequence. | Medium — event ordering and timeout handling. |
| **Sequential fetch** | Extraction → Ingestion | `useSubmitDomain` creates target then executes. | Low — mutation chain with rollback on error. |

---

## Recommendations

1. **Agent-name decomposition is fragile.** Introduce a `output_type` or `result_schema` field in workflow steps so frontend can route by schema rather than agent name.
2. **Value Case should be a first-class BFF endpoint.** Instead of decomposing workflow results in the frontend, create `GET /bff/value-cases/{id}` that returns a shaped `ValueCaseResponse`.
3. **Governance dashboard needs an audit composition endpoint.** Create `GET /bff/governance/dashboard?tenant_id={id}` that returns tenants, user count, key count, and recent audit events in one call.
4. **Settings should fetch via BFF.** `GET /bff/settings` can merge tenant settings, integration statuses, and feature flags into a single product-oriented shape.
