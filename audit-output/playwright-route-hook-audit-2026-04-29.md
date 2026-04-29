# Playwright Route & Hook Audit Report
**Date:** 2026-04-29 **Base:** http://localhost:3001

## 1. Executive Summary
- Health score: 0%
- Verdict: Not ready — significant issues
- Console errors: 1158 | Network failures: 120
### Top 5 Risks
1. 48 routes crash
2. 1158 console errors
### Top 5 Fixes
1. Fix P0 hook null-checks on route params
2. Add ErrorBoundary to all lazy tabs
3. Handle API 401/403 with visible UI
4. Preserve account/tenant context on refresh
5. Fix responsive overflow & mobile nav

## 2. Route Inventory
| Route | From | Title | Heading | Status | CE | NF | Notes |
|-------|------|-------|---------|--------|----|----|-------|
| / | root | Value Fabric — Intelligence  | Create a value case | Partial | 3 | 2 | redirect:/→/home |
| /login | nav | Value Fabric — Intelligence  | Welcome back | Partial | 3 | 2 | redirect:/login→/home |
| /signup | nav | Value Fabric — Intelligence  | Create your account | Partial | 3 | 2 | redirect:/signup→/home |
| /home | sidebar | Value Fabric — Intelligence  | Create a value case | Partial | 3 | 2 |  |
| /command-center | sidebar | Value Fabric — Intelligence  | Command Center | Partial | 3 | 2 |  |
| /accounts | sidebar | Value Fabric — Intelligence  | Accounts | Fail | 25 | 2 |  |
| /accounts/acct-123 | deep-link | Value Fabric — Intelligence  | Accounts | Fail | 25 | 2 |  |
| /workflow/prospect | sidebar | Value Fabric — Intelligence  | Workflow | Partial | 1 | 2 |  |
| /workflow/intelligence | sidebar | Value Fabric — Intelligence  | Workflow | Partial | 1 | 1 |  |
| /workflow/ai-model | sidebar | Value Fabric — Intelligence  | Workflow | Partial | 1 | 1 |  |
| /workflow/driver-tree | sidebar | Value Fabric — Intelligence  | Workflow | Partial | 1 | 2 |  |
| /workflow/evidence | sidebar | Value Fabric — Intelligence  | Workflow | Partial | 1 | 1 |  |
| /workflow/calculator | sidebar | Value Fabric — Intelligence  | Workflow | Partial | 1 | 1 |  |
| /workflow/value-case | sidebar | Value Fabric — Intelligence  | Workflow | Partial | 1 | 1 |  |
| /intelligence/acct-123 | redirect | Value Fabric — Intelligence  | No heading | Fail | 23 | 2 | redirect:/intelligence/acct-123→/intelligence/acct-123/signa |
| /intelligence/acct-123/signals | tab | Value Fabric — Intelligence  | No heading | Fail | 23 | 1 |  |
| /intelligence/acct-123/drivers | tab | Value Fabric — Intelligence  | No heading | Fail | 28 | 2 |  |
| /intelligence/acct-123/evidence | tab | Value Fabric — Intelligence  | No heading | Fail | 23 | 3 |  |
| /intelligence/acct-123/stakeholders | tab | Value Fabric — Intelligence  | No heading | Fail | 23 | 2 |  |
| /intelligence/acct-123/enrichment | tab | Value Fabric — Intelligence  | No heading | Fail | 39 | 1 |  |
| /intelligence/acct-123/hypotheses | tab | Value Fabric — Intelligence  | No heading | Fail | 23 | 2 |  |
| /intelligence/acct-123/competitive | tab | Value Fabric — Intelligence  | No heading | Fail | 45 | 1 |  |
| /intelligence/acct-123/roi | tab | Value Fabric — Intelligence  | No heading | Fail | 23 | 2 |  |
| /intelligence/acct-123/evidence-library | tab | Value Fabric — Intelligence  | No heading | Fail | 23 | 1 |  |
| /intelligence/acct-123/ontology-match | tab | Value Fabric — Intelligence  | Ontology Match | Partial | 1 | 1 |  |
| /hypothesis/acct-123/hypothesis | tab | Value Fabric — Intelligence  | Something went wrong | Partial | 4 | 2 |  |
| /hypothesis/acct-123/discovery-questions | tab | Value Fabric — Intelligence  | Something went wrong | Partial | 4 | 2 |  |
| /hypothesis/acct-123/persona-fit | tab | Value Fabric — Intelligence  | Something went wrong | Partial | 4 | 2 |  |
| /hypothesis/acct-123/assumptions | tab | Value Fabric — Intelligence  | Something went wrong | Partial | 4 | 2 |  |
| /drivers/acct-123 | sidebar | Value Fabric — Intelligence  | No heading | Fail | 23 | 1 |  |
| /evidence/acct-123/evidence | tab | Value Fabric — Intelligence  | No heading | Fail | 23 | 1 |  |
| /evidence/acct-123/alternatives | tab | Value Fabric — Intelligence  | Alternatives | Partial | 1 | 1 |  |
| /evidence/acct-123/solution-cost | tab | Value Fabric — Intelligence  | Solution Cost | Partial | 1 | 1 |  |
| /calculator/acct-123/roi | tab | Value Fabric — Intelligence  | Something went wrong | Partial | 4 | 2 |  |
| /calculator/acct-123/value-model | tab | Value Fabric — Intelligence  | Something went wrong | Partial | 4 | 2 |  |
| /value-case/acct-123 | sidebar | Value Fabric — Intelligence  | No heading | Fail | 34 | 1 |  |
| /realization/acct-123 | sidebar | Value Fabric — Intelligence  | No heading | Fail | 60 | 1 |  |
| /studio/acct-123/action-plan | tab | Value Fabric — Intelligence  | No heading | Fail | 45 | 2 |  |
| /studio/acct-123/value-model | tab | Value Fabric — Intelligence  | No heading | Fail | 23 | 2 |  |
| /studio/acct-123/narrative | tab | Value Fabric — Intelligence  | No heading | Fail | 34 | 2 |  |
| /context/packs | sidebar | Value Fabric — Intelligence  | Value Packs | Fail | 33 | 1 |  |
| /context/models | sidebar | Value Fabric — Intelligence  | My Models | Fail | 17 | 2 |  |
| /context/formulas | sidebar | Value Fabric — Intelligence  | Formulas | Fail | 9 | 1 |  |
| /context/formulas/new | button | Value Fabric — Intelligence  | Formula Builder | Fail | 9 | 2 |  |
| /context/value-trees/explorer | sidebar | Value Fabric — Intelligence  | Tree Explorer | Fail | 9 | 1 |  |
| /context/agents | sidebar | Value Fabric — Intelligence  | Workflow Dashboard | Fail | 17 | 2 |  |
| /context/ontology | sidebar | Value Fabric — Intelligence  | Ontology Editor | Fail | 9 | 2 |  |
| /context/ontology/entities | sub-nav | Value Fabric — Intelligence  | Entity Browser | Fail | 9 | 2 |  |
| /context/ontology/entities/ent-123 | deep-link | Value Fabric — Intelligence  | No heading | Fail | 23 | 2 |  |
| /context/ontology/graph | sub-nav | Value Fabric — Intelligence  | Graph Explorer | Fail | 9 | 1 |  |
| /context/ingestion/jobs | sidebar | Value Fabric — Intelligence  | Ingestion Jobs | Fail | 9 | 2 |  |
| /context/extraction | sidebar | Value Fabric — Intelligence  | Extraction Engine | Partial | 1 | 1 |  |
| /context/integrations | sidebar | Value Fabric — Intelligence  | No heading | Fail | 12 | 1 |  |
| /context/sources | sidebar | Value Fabric — Intelligence  | Source Configuration | Fail | 22 | 1 |  |
| /deliverables/cases | sidebar | Value Fabric — Intelligence  | No heading | Fail | 12 | 2 |  |
| /deliverables/cases/case-123 | deep-link | Value Fabric — Intelligence  | No heading | Partial | 1 | 1 |  |
| /deliverables/calculators | sidebar | Value Fabric — Intelligence  | No heading | Partial | 1 | 1 |  |
| /deliverables/views/cfo | sidebar | Value Fabric — Intelligence  | No heading | Partial | 1 | 1 |  |
| /deliverables/views/executive | sidebar | Value Fabric — Intelligence  | No heading | Partial | 1 | 1 |  |
| /deliverables/views/technical | sidebar | Value Fabric — Intelligence  | No heading | Partial | 1 | 1 |  |
| /settings/content/formulas | sidebar | Value Fabric — Intelligence  | No heading | Fail | 23 | 1 |  |
| /settings/data/variables | sidebar | Value Fabric — Intelligence  | No heading | Fail | 34 | 5 |  |
| /settings/access/roles | sidebar | Value Fabric — Intelligence  | No heading | Fail | 33 | 2 |  |
| /settings/system/settings | sidebar | Value Fabric — Intelligence  | No heading | Fail | 12 | 2 |  |
| /settings/system/billing | sidebar | Value Fabric — Intelligence  | No heading | Fail | 23 | 1 |  |
| /governance/traces | sidebar | Value Fabric — Intelligence  | No heading | Fail | 12 | 1 |  |
| /governance/evidence | sidebar | Value Fabric — Intelligence  | Evidence | Fail | 9 | 1 |  |
| /governance/provenance | sidebar | Value Fabric — Intelligence  | No heading | Fail | 12 | 2 |  |
| /governance/compliance | sidebar | Value Fabric — Intelligence  | Compliance | Fail | 38 | 2 |  |
| /governance/benchmarks | sidebar | Value Fabric — Intelligence  | No heading | Fail | 12 | 1 |  |
| /governance/audit/log | sidebar | Value Fabric — Intelligence  | Audit Log | Fail | 14 | 1 |  |
| /governance/health | sidebar | Value Fabric — Intelligence  | No heading | Fail | 23 | 2 |  |
| /dev/integration | sidebar | Value Fabric — Intelligence  | Integration Dashboard | Fail | 25 | 1 |  |
| /nonexistent-route-xyz | edge-case | Value Fabric — Intelligence  | No heading | Partial | 1 | 2 |  |
| /intelligence | edge-case | Value Fabric — Intelligence  | No heading | Fail | 23 | 1 | redirect:/intelligence→/intelligence/acct-123/signals |
| /studio | edge-case | Value Fabric — Intelligence  | No heading | Fail | 45 | 2 | redirect:/studio→/studio/acct-123/action-plan |

## 3. Hook & State Audit
_No hook errors detected._

## 4. Navigation & Routing Audit
- Back/forward: OK
- Nested reload: OK
Redirects observed:
  - /
  - /login
  - /signup
  - /intelligence/acct-123
  - /intelligence
  - /studio

## 5. Data & API Audit
- /: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /login: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /signup: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /home: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /command-center: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /accounts: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /accounts/acct-123: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/accounts/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /workflow/prospect: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/workflow/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /workflow/intelligence: GET http://localhost:3001/workflow/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /workflow/ai-model: GET http://localhost:3001/workflow/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /workflow/driver-tree: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/workflow/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /workflow/evidence: GET http://localhost:3001/workflow/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /workflow/calculator: GET http://localhost:3001/workflow/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /workflow/value-case: GET http://localhost:3001/workflow/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/intelligence/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/signals: GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/drivers: GET http://localhost:3001/api/v1/agents/analysis/cases?account_id=acct-123 — net::ERR_ABORTED; GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/evidence: GET http://localhost:3001/api/v1/agents/accounts/acct-123 — net::ERR_ABORTED; GET http://localhost:3001/api/v1/agents/analysis/cases?account_id=acct-123 — net::ERR_ABORTED
- /intelligence/acct-123/stakeholders: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/enrichment: GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/hypotheses: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/competitive: GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/roi: GET http://localhost:3001/api/v1/graph/v1/competitive/competitors — net::ERR_ABORTED; GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/evidence-library: GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/ontology-match: GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /hypothesis/acct-123/hypothesis: GET http://localhost:3001/hypothesis/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED; GET http://localhost:3001/src/pages/hypothesis/HypothesisTab.tsx — net::ERR_ABORTED
- /hypothesis/acct-123/discovery-questions: GET http://localhost:3001/hypothesis/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED; GET http://localhost:3001/src/pages/hypothesis/DiscoveryQuestionsTab.tsx — net::ERR_ABORTED
- /hypothesis/acct-123/persona-fit: GET http://localhost:3001/hypothesis/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED; GET http://localhost:3001/src/pages/hypothesis/PersonaFitTab.tsx — net::ERR_ABORTED
- /hypothesis/acct-123/assumptions: GET http://localhost:3001/hypothesis/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED; GET http://localhost:3001/src/pages/hypothesis/AssumptionsTab.tsx — net::ERR_ABORTED
- /drivers/acct-123: GET http://localhost:3001/drivers/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /evidence/acct-123/evidence: GET http://localhost:3001/evidence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /evidence/acct-123/alternatives: GET http://localhost:3001/evidence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /evidence/acct-123/solution-cost: GET http://localhost:3001/evidence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /calculator/acct-123/roi: GET http://localhost:3001/calculator/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED; GET http://localhost:3001/src/pages/calculator/ROITab.tsx — net::ERR_ABORTED
- /calculator/acct-123/value-model: GET http://localhost:3001/calculator/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED; GET http://localhost:3001/src/pages/calculator/ValueModelTab.tsx — net::ERR_ABORTED
- /value-case/acct-123: GET http://localhost:3001/value-case/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /realization/acct-123: GET http://localhost:3001/realization/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /studio/acct-123/action-plan: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/studio/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /studio/acct-123/value-model: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/studio/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /studio/acct-123/narrative: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/studio/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/packs: GET http://localhost:3001/context/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/models: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/context/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/formulas: GET http://localhost:3001/context/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/formulas/new: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/context/formulas/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/value-trees/explorer: GET http://localhost:3001/context/value-trees/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/agents: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/context/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/ontology: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/context/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/ontology/entities: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/context/ontology/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/ontology/entities/ent-123: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/context/ontology/entities/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/ontology/graph: GET http://localhost:3001/context/ontology/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/ingestion/jobs: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/context/ingestion/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/extraction: GET http://localhost:3001/context/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/integrations: GET http://localhost:3001/context/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/sources: GET http://localhost:3001/context/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /deliverables/cases: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/deliverables/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /deliverables/cases/case-123: GET http://localhost:3001/deliverables/cases/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /deliverables/calculators: GET http://localhost:3001/deliverables/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /deliverables/views/cfo: GET http://localhost:3001/deliverables/views/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /deliverables/views/executive: GET http://localhost:3001/deliverables/views/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /deliverables/views/technical: GET http://localhost:3001/deliverables/views/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /settings/content/formulas: GET http://localhost:3001/settings/content/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /settings/data/variables: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/api/v1/graph/formulas? — net::ERR_ABORTED
- /settings/access/roles: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/settings/access/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /settings/system/settings: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/settings/system/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /settings/system/billing: GET http://localhost:3001/settings/system/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /governance/traces: GET http://localhost:3001/governance/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /governance/evidence: GET http://localhost:3001/governance/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /governance/provenance: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/governance/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /governance/compliance: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/governance/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /governance/benchmarks: GET http://localhost:3001/governance/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /governance/audit/log: GET http://localhost:3001/governance/audit/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /governance/health: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/governance/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /dev/integration: GET http://localhost:3001/dev/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /nonexistent-route-xyz: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence: GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /studio: GET http://localhost:3001/api/v1/agents/accounts/acct-123 — net::ERR_ABORTED; GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED

## 6. Accessibility & Responsive Audit
_Needs manual verification — automated checks limited in this run._

## 7. Prioritized Fix Backlog
### 1. Fix fail route /accounts
- Severity: P1 | Area: Routing/Rendering
- Problem: Failed to load resource: the server responded with a status of 404 (Not Found); Failed to load resource: the server resp 
- AC: No console errors, graceful empty/error states, screenshot match

### 2. Fix fail route /accounts/acct-123
- Severity: P1 | Area: Routing/Rendering
- Problem: Failed to load resource: the server responded with a status of 404 (Not Found); Failed to load resource: the server resp 
- AC: No console errors, graceful empty/error states, screenshot match

### 3. Fix fail route /intelligence/acct-123
- Severity: P1 | Area: Routing/Rendering
- Problem: Failed to load resource: the server responded with a status of 404 (Not Found); Failed to load resource: the server resp redirect:/intelligence/acct-123→/intelligence/acct-123/signals
- AC: No console errors, graceful empty/error states, screenshot match

### 4. Fix fail route /intelligence/acct-123/signals
- Severity: P1 | Area: Routing/Rendering
- Problem: Failed to load resource: the server responded with a status of 404 (Not Found); Failed to load resource: the server resp 
- AC: No console errors, graceful empty/error states, screenshot match

### 5. Fix fail route /intelligence/acct-123/drivers
- Severity: P1 | Area: Routing/Rendering
- Problem: Failed to load resource: the server responded with a status of 500 (Internal Server Error); [ApiClient] API request fail 
- AC: No console errors, graceful empty/error states, screenshot match

### 6. Fix fail route /intelligence/acct-123/evidence
- Severity: P1 | Area: Routing/Rendering
- Problem: Failed to load resource: the server responded with a status of 404 (Not Found); Failed to load resource: the server resp 
- AC: No console errors, graceful empty/error states, screenshot match

### 7. Fix fail route /intelligence/acct-123/stakeholders
- Severity: P1 | Area: Routing/Rendering
- Problem: Failed to load resource: the server responded with a status of 404 (Not Found); Failed to load resource: the server resp 
- AC: No console errors, graceful empty/error states, screenshot match

### 8. Fix fail route /intelligence/acct-123/enrichment
- Severity: P1 | Area: Routing/Rendering
- Problem: Failed to load resource: the server responded with a status of 500 (Internal Server Error); [ApiClient] API request fail 
- AC: No console errors, graceful empty/error states, screenshot match

## 8. Playwright Test Recommendations
1. Route smoke tests for every canonical path
2. Deep-link reload tests for /intelligence/:id/:tab and /studio/:id/:tab
3. Auth/tenant context propagation tests
4. Responsive viewport matrix (390/768/1280/1440)
5. Axe-core scan on all pages + keyboard-only journey
6. Error/empty/loading state tests with mocked API
