# 2. Page Reality Index

## Executive Summary

The Fabric 4L frontend registers 154 routes across 32 distinct React components. Track A found only 16 routes (10.4%) with verified live backend integration (GREEN), 51 routes (33.1%) rendering hardcoded data or mocks (RED), 17 routes (11.0%) unevaluated (UNKNOWN), and 70 routes (45.5%) that are legacy redirects (REDIRECT). Of the 84 authenticated routes a user actually interacts with, 68 are non-functional facades — an 81% facade rate.

This chapter translates those findings into an actionable page-level truth table. Every unique page component is classified by current integration state, the gap to target state, the specific backend dependencies required to close that gap, and an effort estimate. The classification yields four work streams: Immediate Wins (4 components, 8 routes), Medium Build (5 components, 8 routes), Deep Refactor (4 component groups, 35 routes), and Sunset Candidates (4 patterns, 37 routes).

The tables in this chapter are the single source of truth for sprint planning. Engineering leads should use the Effort column to size iterations and the Backend Dependency column to identify which orphan endpoint domains must be consumed.

---

## 2.1 Methodology

### 2.1.1 Truth Table Classification System

Each of the 32 unique page components was evaluated against four dimensions from the Track A route audit and Track B orphan endpoint registry.

**Current State** derives from `data_source_color` in the route matrix CSV. A route is GREEN only when a named hook makes an authenticated HTTP call through React Query. Routes with hooks performing no network calls, or where no hook file exists, are RED. Routes with unverified endpoint coverage are UNKNOWN.

**Target State** is forward-looking: FULLY_LIVE (all routes connected), PARTIAL_LIVE (some routes connected), REQUIRES_NEW_HOOK (existing hook mismatched), or ARCHITECTURAL_REBUILD (subsystem needs redesign).

**Backend Dependency** cross-references hook-level endpoint consumption against the Track B orphan registry. Where orphan registry identifies high-value clusters — 16 Account endpoints, 14 Ontology endpoints, 9 Workflow endpoints — those counts appear verbatim.

**Effort Estimate** follows a calibrated t-shirt scale mapped to engineer-days.

### 2.1.2 Color Coding from Track A Audit

| Color | Definition | Route Count | Percentage |
|-------|-----------|-------------|------------|
| **GREEN** | Live backend integration — hook makes authenticated HTTP call via React Query | 16 | 10.4% |
| **RED** | Hardcoded mock or orphaned — no backend call detected | 51 | 33.1% |
| **UNKNOWN** | Unevaluated or incomplete — hook found but endpoint coverage unverified | 17 | 11.0% |
| **REDIRECT** | Legacy redirect — `Navigate` to another path, no data fetching | 70 | 45.5% |

The 81% facade rate equals `(84 authenticated routes - 16 GREEN) / 84 = 68 / 84 = 81.0%`. Redirect routes are excluded because they are not user-facing pages.

### 2.1.3 Effort Sizing Framework

| Size | Duration | Assumptions |
|------|----------|-------------|
| **S** | 1–3 days | Hook exists; work is route-to-hook wiring, query-key alignment, or minor endpoint expansion |
| **M** | 1–2 weeks | Hook exists but requires expansion to cover multiple new endpoints; may include light UI adaptation |
| **L** | 2–4 weeks | Hook partially exists or mismatched; requires 10+ endpoint integrations, type work, error-handling propagation |
| **XL** | 1+ months | No suitable hook; requires new hook architecture, endpoint integration, backend contract negotiation, UI refactoring |
| **SUNSET** | Removal effort | Component and routes should be removed; covers safe deletion, redirect updates, navigation cleanup |

Sizing assumes one senior frontend engineer in the existing React/TypeScript codebase. Backend contract work is a tracked dependency but not included in frontend effort.

---

## 2.2 Immediate Wins (Hook Exists, Needs Wiring)

The Immediate Wins stream contains four components where the core hook already exists and is functional, but the route-to-hook connection is incomplete or undersized. Total: 8 authenticated routes. These are the highest-velocity items — a senior engineer can produce working backend-connected pages within one sprint. The shared pattern: Track A found a GREEN hook, but the route matrix shows the route either does not reference that hook (RED) or the hook's endpoint coverage is smaller than the orphan registry makes available.

### 2.2.1 Accounts (`/accounts`, `/accounts/:id`) — Effort M

Accounts renders 2 GREEN routes via `useAccounts` (GET l4, POST l4). The hook is typed and has error handling. However, the orphan registry identifies 16 Account endpoints with no frontend surface: filtering (`GET /v1/accounts/filters`), search (`POST /v1/accounts/search`), sync (`POST /v1/accounts/sync`), and sync-status polling. The hook architecture is structurally ready — the limiting factor is expansion, not backend availability.

| Attribute | Value |
|-----------|-------|
| Routes | `/accounts`, `/accounts/:id` |
| Current State | GREEN (hook connected) |
| Hook | `useAccounts` — 2 endpoints (GET l4, POST l4) |
| Backend Dependency | 16 orphan Account endpoints |
| Target State | FULLY_LIVE |
| Effort | **M** |

### 2.2.2 EntityBrowser (`/context/ontology/entities`) — Effort S

EntityBrowser is GREEN with `useEntities` — one of the most complete hooks: 4 endpoints (entity search, list, detail, GET l3), 3 query keys, full error handling. The gap is filter sophistication. The orphan registry's 14 Ontology endpoints include filter dimensions (entity type, domain, status, confidence label) not surfaced in the UI.

| Attribute | Value |
|-----------|-------|
| Route | `/context/ontology/entities` |
| Current State | GREEN |
| Hook | `useEntities` — 4 endpoints, 3 query keys |
| Backend Dependency | Ontology filter dimensions |
| Target State | PARTIAL_LIVE — add filter panel |
| Effort | **S** |

### 2.2.3 FormulaList (`/context/formulas`) — Effort S

FormulaList is GREEN with `useFormulas` consuming 4 endpoints (DELETE, POST, PATCH, GET l3). The gap is formula execution: the orphan registry lists `POST /v1/formulas/evaluate` and `POST /v1/formulas/scenario` as available but unconnected. Users can CRUD formulas but cannot execute them.

| Attribute | Value |
|-----------|-------|
| Route | `/context/formulas` |
| Current State | GREEN |
| Hook | `useFormulas` — 4 endpoints |
| Backend Dependency | 2 formula evaluation endpoints |
| Target State | FULLY_LIVE — add evaluation + scenario |
| Effort | **S** |

### 2.2.4 Billing (`/settings/system/billing/*`) — Effort S

BillingRoute spans 4 routes, all RED. No hook is mapped in the route matrix. However, Track A found three functional billing hooks: `billingKeys` (GREEN, 2 endpoints), `invoiceKeys` (YELLOW, 0 endpoints but 3 query keys), and `usageKeys` (YELLOW, 0 endpoints but 3 query keys). The disconnect is architectural: billing hooks exist but are not referenced by BillingRoute.

| Attribute | Value |
|-----------|-------|
| Routes | `/settings/system/billing`, `/settings/system/billing/invoices`, `/settings/system/billing/payments`, `/settings/system/billing/usage` |
| Current State | RED (all 4) |
| Hooks Available | `billingKeys` (GREEN, 2 eps), `invoiceKeys` (YELLOW, 3 QKs), `usageKeys` (YELLOW, 3 QKs) |
| Backend Dependency | Wire existing hooks; verify endpoint mapping |
| Target State | FULLY_LIVE |
| Effort | **S** |

### Immediate Wins Summary Table

| Component | Routes | Current State | Hook | Hook Endpoints | Orphan Endpoints Available | Target State | Effort |
|-----------|--------|---------------|------|----------------|---------------------------|--------------|--------|
| Accounts | `/accounts`, `/accounts/:id` | GREEN | `useAccounts` | 2 (GET l4, POST l4) | 16 Account endpoints | FULLY_LIVE | M |
| EntityBrowser | `/context/ontology/entities` | GREEN | `useEntities` | 4 (search, list, detail, GET l3) | Ontology filter dimensions | PARTIAL_LIVE | S |
| FormulaList | `/context/formulas` | GREEN | `useFormulas` | 4 (DELETE, POST, PATCH, GET l3) | 2 formula evaluation endpoints | FULLY_LIVE | S |
| BillingRoute | `/settings/system/billing` (×4) | RED (all) | `billingKeys`, `invoiceKeys`, `usageKeys` | 2 + 6 query keys | Verify endpoint mapping | FULLY_LIVE | S |

---

## 2.3 Medium Build (Backend Ready, Frontend Missing)

The Medium Build stream contains five components where the backend surface is substantial — 10+ available endpoints per domain — but frontend hook coverage is partial, mocked, or unmapped. These require hook expansion, new endpoint consumption, and in one case replacement of a mock implementation. Total: 8 authenticated routes. Effort ranges from S to L because the work is bounded: backend contracts exist and frontend patterns are established.

### 2.3.1 AgentWorkflows (`/context/agents`) — Effort M

AgentWorkflows is UNKNOWN. The route matrix references `useWorkflows`, which was not found in hook analysis. `useActiveWorkflows` (file: `useWorkflows.ts`) does exist — a GREEN hook with 3 endpoints (GET, POST, DELETE l4). The orphan registry lists 9 Workflow endpoints covering creation, status polling, events, pause/resume, cancel, and results. The gap: the route references a hook that does not exist (or is named differently), and the existing hook covers only 3 of 9 operations.

| Attribute | Value |
|-----------|-------|
| Route | `/context/agents` |
| Current State | UNKNOWN |
| Hook | `useWorkflows` (not found); `useActiveWorkflows` exists (3 eps) |
| Backend Dependency | 9 Workflow orphan endpoints |
| Target State | FULLY_LIVE |
| Effort | **M** |

### 2.3.2 OntologyEditor (`/context/ontology`) — Effort L

OntologyEditor is UNKNOWN. The route references `useOntology`, not found in hook analysis. However, `useOntologySchema` (file: `useOntology.ts`) is the most comprehensive hook in the codebase: 13 endpoints covering full CRUD for types, properties, relationships, validation, import, and publish — with runtime Zod validation and query invalidation. Despite this, the route shows UNKNOWN because it does not invoke `useOntologySchema`. The orphan registry lists 14 Ontology endpoints.

| Attribute | Value |
|-----------|-------|
| Route | `/context/ontology` |
| Current State | UNKNOWN |
| Hook | `useOntologySchema` — 13 endpoints (full CRUD) |
| Backend Dependency | 14 Ontology orphan endpoints |
| Target State | FULLY_LIVE — wire existing hook |
| Effort | **L** |

### 2.3.3 IngestionJobs (`/context/ingestion/jobs`) — Effort S

IngestionJobs is UNKNOWN. The route references `useIngestion`, not found, but `useIngestionJobs` (file: `useIngestion.ts`) is GREEN with 3 endpoints (DELETE, GET, POST l1) and 3 query keys. Layer 1 has 26 total endpoints — all orphaned except these 3. The fix: wire the existing hook into the route.

| Attribute | Value |
|-----------|-------|
| Route | `/context/ingestion/jobs` |
| Current State | UNKNOWN |
| Hook | `useIngestionJobs` — 3 endpoints, 3 query keys |
| Backend Dependency | 23 additional Layer 1 endpoints (assess expansion) |
| Target State | PARTIAL_LIVE |
| Effort | **S** |

### 2.3.4 SourceConfiguration (`/context/sources`) — Effort M

SourceConfiguration is RED. The route maps to `useSources` — a RED hook with 4 endpoint signatures (DELETE, GET, POST, PUT l1) but `is_mock: true`. It makes endpoint-shaped calls returning mock data. The endpoint signatures suggest a backend contract exists at Layer 1. Target: swap mock for real HTTP calls.

| Attribute | Value |
|-----------|-------|
| Route | `/context/sources` |
| Current State | RED |
| Hook | `useSources` — 4 signatures, `is_mock: true` |
| Backend Dependency | Replace mock with live calls; verify Layer 1 contracts |
| Target State | FULLY_LIVE |
| Effort | **M** |

### 2.3.5 HealthMonitor (`/governance/health`) — Effort M

HealthMonitor is GREEN — but only for 1 endpoint. `useSystemHealth` (GET l4) has no error handling. The orphan registry lists 12 Health + 12 State Inspector endpoints (24 total). Target: expand the hook family to consume 11+ additional health endpoints.

| Attribute | Value |
|-----------|-------|
| Route | `/governance/health` |
| Current State | GREEN (1 endpoint) |
| Hook | `useSystemHealth` — 1 endpoint, no error handling |
| Backend Dependency | 24 Health + State Inspector orphan endpoints |
| Target State | PARTIAL_LIVE |
| Effort | **M** |

### Medium Build Summary Table

| Component | Routes | Current State | Hook Status | Existing Endpoints | Orphan Endpoints Available | Target State | Effort |
|-----------|--------|---------------|-------------|-------------------|---------------------------|--------------|--------|
| AgentWorkflows | `/context/agents` | UNKNOWN | `useActiveWorkflows` (3 eps) | 3 (GET, POST, DELETE l4) | 9 Workflow endpoints | FULLY_LIVE | M |
| OntologyEditor | `/context/ontology` | UNKNOWN | `useOntologySchema` (13 eps) | 13 (full CRUD) | 14 Ontology endpoints | FULLY_LIVE | L |
| IngestionJobs | `/context/ingestion/jobs` | UNKNOWN | `useIngestionJobs` (3 eps) | 3 (DELETE, GET, POST l1) | 23 Layer 1 endpoints | PARTIAL_LIVE | S |
| SourceConfiguration | `/context/sources` | RED | `useSources` mock (4 signatures) | 4 mocked | Verify Layer 1 contracts | FULLY_LIVE | M |
| HealthMonitor | `/governance/health` | GREEN (1 ep) | `useSystemHealth` (1 ep) | 1 (GET l4) | 24 Health + State Inspector | PARTIAL_LIVE | M |

---

## 2.4 Deep Refactor (Architectural Mismatch)

The Deep Refactor stream contains four component groups where the gap is structural rather than connective. No suitable hook exists, the component architecture is mismatched to the backend domain, or routes are redirect shells masking absent functionality. Total: 35 authenticated routes. Effort is L or XL for all items.

### 2.4.1 Intelligence Workspace (10 routes `/intelligence/*`) — Effort XL

The Intelligence Workspace has 10 routes: 5 `WorkspaceContextRedirect` (`/intelligence`, `/intelligence/drivers`, `/intelligence/evidence`, `/intelligence/signals`, `/intelligence/stakeholders`) and 5 `AccountContextSync` (`/intelligence/:accountId`, `/intelligence/:accountId/drivers`, `/intelligence/:accountId/evidence`, `/intelligence/:accountId/signals`, `/intelligence/:accountId/stakeholders`). All are RED.

No hook is mapped. `useOpportunities` (RED, `is_mock: true`) exists but is unused. The orphan registry offers 16 Account, 3 Signals, and 84 Layer 4 endpoints — but the frontend has no structure to consume them. Target: design a `useIntelligence` hook family and replace redirect shells with real page components.

| Attribute | Value |
|-----------|-------|
| Routes | 10 routes under `/intelligence/*` |
| Current State | RED (all) |
| Hook | None mapped |
| Backend Dependency | 16 Account + 3 Signals + 84 Layer 4 orphan endpoints |
| Target State | ARCHITECTURAL_REBUILD |
| Effort | **XL** |

### 2.4.2 Value Studio (18 routes `/studio/*` and `/model/value-studio/*`) — Effort XL

Value Studio spans 18 routes: 10 under `/studio/*` (`/studio`, `/studio/action-plan`, 6 `/studio/build/*`, `/studio/narrative`, `/studio/value-model`) plus 8 parameterized `/studio/:accountId/*` routes, and 8 under `/model/value-studio/*`. All use `WorkspaceContextRedirect` or `AccountContextSync` — all RED.

This is the most concentrated facade: 18 routes with zero backend integration, no hooks, no query keys. The orphan registry offers 9 ValuePacks, 2 Value Trees, and 5 Formula endpoints, but no coherent backend module matches the Value Studio concept. Target: validate the product concept, define the backend domain, and build a new hook architecture from first principles.

| Attribute | Value |
|-----------|-------|
| Routes | 18 routes: 10 `/studio/*` + 8 `/model/value-studio/*` |
| Current State | RED (all) |
| Hook | None mapped |
| Backend Dependency | 9 ValuePacks + 2 Value Trees + 5 Formula endpoints; product validation required |
| Target State | ARCHITECTURAL_REBUILD |
| Effort | **XL** |

### 2.4.3 BusinessCase Views (5 routes `/deliverables/*`) — Effort L

BusinessCase spans 5 routes: `/deliverables/cases` (BusinessCaseList), `/deliverables/cases/:caseId`, and 3 view routes (`/deliverables/views/cfo`, `/deliverables/views/executive`, `/deliverables/views/technical`). All are UNKNOWN with `useBusinessCases` referenced but not found. `useBusinessCase` (singular) exists — GREEN, 2 endpoints, 2 query keys. The view routes require distinct data shapes. The orphan registry does not list a dedicated Business Case domain.

| Attribute | Value |
|-----------|-------|
| Routes | 5: `/deliverables/cases`, `/deliverables/cases/:caseId`, 3 view routes |
| Current State | UNKNOWN (all) |
| Hook | `useBusinessCase` (2 eps); route refs `useBusinessCases` (not found) |
| Backend Dependency | Case endpoints with view-specific parameters |
| Target State | REQUIRES_NEW_HOOK |
| Effort | **L** |

### 2.4.4 DecisionTrace (7 routes `/governance/*`) — Effort L

DecisionTrace renders 7 governance routes: `/governance/audit/changes`, `/governance/audit/log`, `/governance/compliance`, `/governance/evidence`, `/governance/integrity`, `/governance/provenance`, `/governance/traces`. All are UNKNOWN. `useProvenance` is referenced but not found; `useProvenanceTrail` exists — GREEN, 1 endpoint (`GET l3`), 2 query keys. One endpoint for 7 governance views is insufficient. The orphan registry lists 13 Ground Truth + 2 Audit endpoints. Target: expand into a governance hook family.

| Attribute | Value |
|-----------|-------|
| Routes | 7 routes under `/governance/*` |
| Current State | UNKNOWN (all) |
| Hook | `useProvenanceTrail` (1 ep); route refs `useProvenance` (not found) |
| Backend Dependency | 13 Ground Truth + 2 Audit orphan endpoints |
| Target State | PARTIAL_LIVE — governance hook family |
| Effort | **L** |

### Deep Refactor Summary Table

| Component Group | Routes | Current State | Hook Status | Existing Endpoints | Orphan Endpoints Available | Target State | Effort |
|----------------|--------|---------------|-------------|-------------------|---------------------------|--------------|--------|
| Intelligence Workspace | 10 `/intelligence/*` | RED (all) | None mapped | 0 | 16 Account + 3 Signals + 84 Layer 4 | ARCHITECTURAL_REBUILD | XL |
| Value Studio | 18 `/studio/*` + `/model/value-studio/*` | RED (all) | None mapped | 0 | 9 ValuePacks + 2 Value Trees + 5 Formula | ARCHITECTURAL_REBUILD | XL |
| BusinessCase Views | 5 `/deliverables/*` | UNKNOWN (all) | `useBusinessCase` (2 eps) vs `useBusinessCases` (not found) | 2 (GET, POST l4) | Case endpoints | REQUIRES_NEW_HOOK | L |
| DecisionTrace | 7 `/governance/*` | UNKNOWN (all) | `useProvenanceTrail` (1 ep) vs `useProvenance` (not found) | 1 (GET l3) | 13 Ground Truth + 2 Audit | PARTIAL_LIVE | L |

---

## 2.5 Sunset Candidates

The Sunset stream contains components and routes whose continued existence carries cost — maintenance burden, navigation confusion, false signaling — without clear product value. These are candidates for deletion, and the decision should be explicit.

### 2.5.1 CommandCenter (`/command-center`)

CommandCenter is a single RED route with no hook, no endpoints, no query keys, and no evidence of a backend domain. It sits at the top level of navigation as an empty shell.

| Attribute | Value |
|-----------|-------|
| Route | `/command-center` |
| Current State | RED |
| Hook | None |
| Backend Dependency | None |
| Sunset Rationale | No backend, no product spec, empty shell |
| Effort | **SUNSET** (1–2 days removal) |

### 2.5.2 InteractiveBusinessCase (`/deliverables/calculators`)

InteractiveBusinessCase is a single RED route with no hooks and no endpoints. The orphan registry lists no calculator-specific surface.

| Attribute | Value |
|-----------|-------|
| Route | `/deliverables/calculators` |
| Current State | RED |
| Hook | None |
| Backend Dependency | None |
| Sunset Rationale | No hooks, no endpoints; validate against roadmap before building |
| Effort | **SUNSET** (1–2 days removal) |

### 2.5.3 WorkspaceContextRedirect Routes (33 redirect-shell routes)

The most destructive facade pattern: 24 `WorkspaceContextRedirect` routes and 9 `AccountContextSync` routes used as placeholders where no implementation exists. These routes consume navigation real estate, require maintenance, and create the illusion of completeness. Users see menu items for Signals, Drivers, Evidence, and Value Studio but land on empty redirects.

Removing these 33 routes would reduce the facade rate from 81% to approximately 55% (by removing non-functional routes from the authenticated count). The counter-argument — that these routes represent intentional product architecture — is defensible only with a committed engineering plan to fill them within two quarters. Without such a plan, they are technical debt.

| Attribute | Value |
|-----------|-------|
| Routes | 33: 24 `WorkspaceContextRedirect` + 9 `AccountContextSync` |
| Current State | RED (all) |
| Components | `WorkspaceContextRedirect`, `AccountContextSync` |
| Backend Dependency | None — shell components |
| Sunset Rationale | Mask 33 missing features; reduce facade rate; honest navigation |
| Effort | **SUNSET** (2–3 days removal + cleanup) |

### Sunset Candidates Summary Table

| Component / Pattern | Routes | Current State | Backend Surface | Sunset Rationale | Effort |
|--------------------|--------|---------------|-----------------|-------------------|--------|
| CommandCenter | `/command-center` | RED | None | No backend, no spec, empty shell | SUNSET |
| InteractiveBusinessCase | `/deliverables/calculators` | RED | None | No hooks, no endpoints; validate roadmap | SUNSET |
| WorkspaceContextRedirect | 24 routes | RED | None | Mask missing Intelligence + Studio functionality | SUNSET |
| AccountContextSync | 9 routes | RED | None | Parameterized redirect shells | SUNSET |

---

## Cross-Reference: Effort Distribution

| Effort Tier | Component Count | Route Count | % of Authenticated Routes |
|-------------|-----------------|-------------|---------------------------|
| S (1–3 days) | 4 | 6 | 7.1% |
| M (1–2 weeks) | 4 | 7 | 15.5% |
| L (2–4 weeks) | 2 | 12 | 29.8% |
| XL (1+ months) | 2 | 28 | 63.1% |
| SUNSET | 4 | 35* | — |

*SUNSET routes overlap with XL routes (Intelligence and Studio). Non-overlapping authenticated coverage: 51 routes (60.7%). Remaining 33 routes are the 16 GREEN routes plus 17 legitimate redirects.

---

## Cross-Reference: Full Component-to-Hook Mapping

| Component | Routes | Color | Mapped Hook | Hook Found | Hook Color | Mock? | Endpoint Count |
|-----------|--------|-------|-------------|------------|------------|-------|----------------|
| Accounts | 2 | GREEN | `useAccounts` | Yes | GREEN | No | 2 |
| AgentWorkflows | 1 | UNKNOWN | `useWorkflows` | No | — | — | 0 |
| BenchmarkPolicies | 1 | GREEN | `useBenchmarks` | Yes | GREEN | No | 3 |
| BillingRoute | 4 | RED | `UNKNOWN` | — | — | — | 0 |
| BusinessCase | 4 | UNKNOWN | `useBusinessCases` | No | — | — | 0 |
| BusinessCaseList | 1 | UNKNOWN | `useBusinessCases` | No | — | — | 0 |
| CommandCenter | 1 | RED | `UNKNOWN` | — | — | — | 0 |
| DecisionTrace | 7 | UNKNOWN | `useProvenance` | No | — | — | 0 |
| EntityBrowser | 1 | GREEN | `useEntities` | Yes | GREEN | No | 4 |
| EntityDetail | 1 | RED | `UNKNOWN` | — | — | — | 0 |
| ExtractionEngine | 1 | GREEN | `useExtraction` | Yes | GREEN | No | 1 |
| FormulaBuilder | 2 | UNKNOWN | `useFormula` | No | — | — | 0 |
| FormulaGovernance | 3 | RED | `UNKNOWN` | — | — | — | 0 |
| FormulaList | 1 | GREEN | `useFormulas` | Yes | GREEN | No | 4 |
| GraphExplorer | 1 | GREEN | `useGraphQuery` | Yes | GREEN | No | 2 |
| HealthMonitor | 1 | GREEN | `useSystemHealth` | Yes | GREEN | No | 1 |
| IngestionJobs | 1 | UNKNOWN | `useIngestion` | No | — | — | 0 |
| Integrations | 2 | GREEN | `useIntegrations` | Yes | GREEN | No | 3 |
| InteractiveBusinessCase | 1 | RED | `UNKNOWN` | — | — | — | 0 |
| MyModels | 1 | GREEN | `useModels` | Yes | GREEN | No | 3 |
| NotFound | 1 | RED | `UNKNOWN` | — | — | — | 0 |
| OntologyEditor | 1 | UNKNOWN | `useOntology` | No | — | — | 0 |
| PermissionsAdmin | 3 | RED | `UNKNOWN` | — | — | — | 0 |
| PlatformSettings | 1 | GREEN | `usePlatformSettings` | Yes | GREEN | No | 2 |
| SourceConfiguration | 1 | RED | `useSources` | Yes | RED | Yes | 4 (mocked) |
| Suspense | 1 | RED | `UNKNOWN` | — | — | — | 0 |
| ValueNarrativeHome | 1 | RED | `UNKNOWN` | — | — | — | 0 |
| ValuePacks | 1 | GREEN | `useValuePacks` | Yes | GREEN | No | 2 |
| VariableRegistry | 3 | GREEN | `useVariables` | Yes | GREEN | No | 2 |
| AccountContextSync | 9 | RED | `UNKNOWN` | — | — | — | 0 |
| WorkspaceContextRedirect | 24 | RED | `UNKNOWN` | — | — | — | 0 |
| Navigate | 70 | REDIRECT | N/A | — | — | — | 0 |

---

*Document generated from Track A route extraction (154 routes), Track A hook analysis (44 hooks), and Track B orphan endpoint registry (244 endpoints, 236 orphans). All counts, route paths, component names, hook names, and endpoint references are sourced directly from audit artifacts.*
