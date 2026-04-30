# Playwright Route & Hook Audit Report
**Date:** 2026-04-30 **Base:** http://localhost:3001

## 1. Executive Summary
- Health score: 0%
- Verdict: Not ready — significant issues
- Console errors: 4059 | Network failures: 205
### Top 5 Risks
1. 54 routes crash
2. 5 routes blocked
3. 4059 console errors
### Top 5 Fixes
1. Fix P0 hook null-checks on route params
2. Add ErrorBoundary to all lazy tabs
3. Handle API 401/403 with visible UI
4. Preserve account/tenant context on refresh
5. Fix responsive overflow & mobile nav

## 2. Route Inventory
| Route | From | Title | Heading | Status | CE | NF | Notes |
|-------|------|-------|---------|--------|----|----|-------|
| / | root | Value Fabric — Intelligence  | Create a value case | Fail | 90 | 3 | empty:"No data found"; redirect:/→/home |
| /login | nav | Value Fabric — Intelligence  | Create a value case | Fail | 89 | 2 | empty:"No data found"; redirect:/login→/home |
| /signup | nav | Value Fabric — Intelligence  | Create a value case | Fail | 89 | 2 | empty:"No data found"; redirect:/signup→/home |
| /home | sidebar | Value Fabric — Intelligence  | Create a value case | Fail | 89 | 2 | empty:"No data found" |
| /command-center | sidebar | Value Fabric — Intelligence  | Command Center | Fail | 89 | 2 | empty:"No data found" |
| /accounts | sidebar | Value Fabric — Intelligence  | Accounts | Fail | 97 | 2 | errUI:"Failed to load accounts" |
| /accounts/acct-123 | deep-link | Value Fabric — Intelligence  | Accounts | Fail | 97 | 1 | errUI:"Failed to load accounts" |
| /workflow/prospect | sidebar | Value Fabric — Intelligence  | Workflow | Partial | 1 | 1 |  |
| /workflow/intelligence | sidebar | Value Fabric — Intelligence  | Workflow | Partial | 1 | 1 |  |
| /workflow/ai-model | sidebar | Value Fabric — Intelligence  | Workflow | Partial | 1 | 1 |  |
| /workflow/driver-tree | sidebar | Value Fabric — Intelligence  | Workflow | Partial | 1 | 1 |  |
| /workflow/evidence | sidebar | Value Fabric — Intelligence  | Workflow | Partial | 1 | 1 |  |
| /workflow/calculator | sidebar | Value Fabric — Intelligence  | Workflow | Partial | 1 | 1 |  |
| /workflow/value-case | sidebar | Value Fabric — Intelligence  | Workflow | Partial | 1 | 1 |  |
| /intelligence/acct-123 | redirect | Value Fabric — Intelligence  | No heading | Fail | 57 | 1 | errUI:"Failed to load signal data."; redirect:/intelligence/ |
| /intelligence/acct-123/signals | tab | Value Fabric — Intelligence  | No heading | Fail | 57 | 1 | errUI:"Failed to load signal data." |
| /intelligence/acct-123/drivers | tab | Value Fabric — Intelligence  | No heading | Fail | 57 | 1 |  |
| /intelligence/acct-123/evidence | tab | Value Fabric — Intelligence  | No heading | Fail | 57 | 1 |  |
| /intelligence/acct-123/stakeholders | tab | Value Fabric — Intelligence  | No heading | Fail | 57 | 1 |  |
| /intelligence/acct-123/enrichment | tab | Value Fabric — Intelligence  | No heading | Fail | 97 | 1 |  |
| /intelligence/acct-123/hypotheses | tab | Value Fabric — Intelligence  | No heading | Fail | 65 | 1 | errUI:"Failed to load hypotheses." |
| /intelligence/acct-123/competitive | tab | Value Fabric — Intelligence  | No heading | Fail | 129 | 1 |  |
| /intelligence/acct-123/roi | tab | Value Fabric — Intelligence  | No heading | Fail | 65 | 1 |  |
| /intelligence/acct-123/evidence-library | tab | Value Fabric — Intelligence  | No heading | Fail | 65 | 1 |  |
| /intelligence/acct-123/ontology-match | tab | Value Fabric — Intelligence  | Ontology Match | Partial | 1 | 1 |  |
| /hypothesis/acct-123/hypothesis | tab | Value Fabric — Intelligence  | Something went wrong | Partial | 4 | 2 | errUI:"Something went wrong" |
| /hypothesis/acct-123/discovery-questions | tab | Value Fabric — Intelligence  | Something went wrong | Partial | 4 | 2 | errUI:"Something went wrong" |
| /hypothesis/acct-123/persona-fit | tab | Value Fabric — Intelligence  | Something went wrong | Partial | 4 | 2 | errUI:"Something went wrong" |
| /hypothesis/acct-123/assumptions | tab | Value Fabric — Intelligence  | Something went wrong | Partial | 4 | 2 | errUI:"Something went wrong" |
| /drivers/acct-123 | sidebar | Value Fabric — Intelligence  | No heading | Fail | 57 | 1 |  |
| /evidence/acct-123/evidence | tab | Value Fabric — Intelligence  | No heading | Fail | 57 | 1 |  |
| /evidence/acct-123/alternatives | tab | Value Fabric — Intelligence  | No heading | Partial | 105 | 102 |  |
| /evidence/acct-123/solution-cost | tab |  | No heading | Blocked | 0 | 2 | nav timeout:page.goto: net::ERR_CONNECTION_REFUSED at http:/ |
| /calculator/acct-123/roi | tab |  | No heading | Blocked | 0 | 2 | nav timeout:page.goto: net::ERR_CONNECTION_REFUSED at http:/ |
| /calculator/acct-123/value-model | tab |  | No heading | Blocked | 0 | 2 | nav timeout:page.goto: net::ERR_CONNECTION_REFUSED at http:/ |
| /value-case/acct-123 | sidebar |  | No heading | Blocked | 0 | 2 | nav timeout:page.goto: net::ERR_CONNECTION_REFUSED at http:/ |
| /realization/acct-123 | sidebar |  | No heading | Blocked | 0 | 2 | nav timeout:page.goto: net::ERR_EMPTY_RESPONSE at http://loc |
| /studio/acct-123/action-plan | tab | Value Fabric — Intelligence  | No heading | Fail | 121 | 1 |  |
| /studio/acct-123/value-model | tab | Value Fabric — Intelligence  | No heading | Fail | 57 | 1 |  |
| /studio/acct-123/narrative | tab | Value Fabric — Intelligence  | No heading | Fail | 124 | 7 | nav timeout:page.goto: Timeout 15000ms exceeded.
Call log:
 |
| /context/packs | sidebar | Value Fabric — Intelligence  | Value Packs | Fail | 132 | 2 | errUI:"Failed to load value packs" |
| /context/models | sidebar | Value Fabric — Intelligence  | My Models | Fail | 65 | 1 | errUI:"Failed to load models" |
| /context/formulas | sidebar | Value Fabric — Intelligence  | Formulas | Fail | 33 | 1 | errUI:"Failed to load formulas" |
| /context/formulas/new | button | Value Fabric — Intelligence  | Formula Builder | Fail | 33 | 1 | errUI:"Failed to load variables" |
| /context/value-trees/explorer | sidebar | Value Fabric — Intelligence  | Tree Explorer | Fail | 25 | 1 |  |
| /context/agents | sidebar | Value Fabric — Intelligence  | Workflow Dashboard | Fail | 145 | 1 | errUI:"Request failed with status code 500" |
| /context/ontology | sidebar | Value Fabric — Intelligence  | Ontology Editor | Fail | 25 | 1 | errUI:"Failed to load ontology" |
| /context/ontology/entities | sub-nav | Value Fabric — Intelligence  | Entity Browser | Fail | 25 | 1 | errUI:"Request failed with status code 500"; empty:"No data  |
| /context/ontology/entities/ent-123 | deep-link | Value Fabric — Intelligence  | Entity Not Found | Fail | 49 | 1 | errUI:"Request failed with status code 500" |
| /context/ontology/graph | sub-nav | Value Fabric — Intelligence  | Graph Explorer | Fail | 25 | 1 | errUI:"Error loading graph" |
| /context/ingestion/jobs | sidebar | Value Fabric — Intelligence  | Ingestion Jobs | Fail | 121 | 1 | errUI:"Failed" |
| /context/extraction | sidebar | Value Fabric — Intelligence  | Extraction Engine | Partial | 1 | 1 | spinner>1.5s |
| /context/integrations | sidebar | Value Fabric — Intelligence  | Integrations | Fail | 33 | 1 | errUI:"Failed to load integrations" |
| /context/sources | sidebar | Value Fabric — Intelligence  | Source Configuration | Fail | 65 | 1 | errUI:"Failed to load sources" |
| /deliverables/cases | sidebar | Value Fabric — Intelligence  | No heading | Fail | 25 | 1 | errUI:"Failed to load business cases" |
| /deliverables/cases/case-123 | deep-link | Value Fabric — Intelligence  | No heading | Partial | 1 | 1 |  |
| /deliverables/calculators | sidebar | Value Fabric — Intelligence  | No heading | Partial | 1 | 1 |  |
| /deliverables/views/cfo | sidebar | Value Fabric — Intelligence  | No heading | Partial | 1 | 1 |  |
| /deliverables/views/executive | sidebar | Value Fabric — Intelligence  | No heading | Partial | 1 | 1 |  |
| /deliverables/views/technical | sidebar | Value Fabric — Intelligence  | No heading | Partial | 1 | 1 |  |
| /settings/content/formulas | sidebar | Value Fabric — Intelligence  | No heading | Fail | 65 | 1 | errUI:"Failed to load formula governance" |
| /settings/data/variables | sidebar | Value Fabric — Intelligence  | No heading | Fail | 97 | 1 | errUI:"Failed to load variable registry" |
| /settings/access/roles | sidebar | Value Fabric — Intelligence  | No heading | Fail | 65 | 1 | errUI:"Failed to load permissions data" |
| /settings/system/settings | sidebar | Value Fabric — Intelligence  | No heading | Fail | 33 | 1 | errUI:"Failed to load platform settings" |
| /settings/system/billing | sidebar | Value Fabric — Intelligence  | No heading | Fail | 49 | 1 | errUI:"Failed to load billing information: Request failed wi |
| /governance/traces | sidebar | Value Fabric — Intelligence  | Decision Traces | Fail | 25 | 1 |  |
| /governance/evidence | sidebar | Value Fabric — Intelligence  | Evidence | Fail | 33 | 1 | errUI:"Request failed with status code 500" |
| /governance/provenance | sidebar | Value Fabric — Intelligence  | Provenance Trail | Fail | 25 | 1 |  |
| /governance/compliance | sidebar | Value Fabric — Intelligence  | Compliance | Fail | 129 | 1 |  |
| /governance/benchmarks | sidebar | Value Fabric — Intelligence  | No heading | Fail | 33 | 1 | errUI:"Failed to load benchmark policies" |
| /governance/audit/log | sidebar | Value Fabric — Intelligence  | Audit Log | Fail | 33 | 1 |  |
| /governance/health | sidebar | Value Fabric — Intelligence  | No heading | Fail | 140 | 1 | errUI:"Failed to load health data" |
| /dev/integration | sidebar | Value Fabric — Intelligence  | Integration Dashboard | Fail | 164 | 2 |  |
| /nonexistent-route-xyz | edge-case | Value Fabric — Intelligence  | No heading | Partial | 1 | 2 |  |
| /intelligence | edge-case | Value Fabric — Intelligence  | No heading | Fail | 57 | 1 | errUI:"Failed to load signal data."; redirect:/intelligence→ |
| /studio | edge-case | Value Fabric — Intelligence  | No heading | Fail | 121 | 1 | redirect:/studio→/studio/acct-123/action-plan |
| /hypothesis | edge-case | Value Fabric — Intelligence  | Accounts | Fail | 97 | 1 | errUI:"Failed to load accounts"; redirect:/hypothesis→/accou |
| /evidence | edge-case | Value Fabric — Intelligence  | Accounts | Fail | 97 | 1 | errUI:"Failed to load accounts"; redirect:/evidence→/account |
| /calculator | edge-case | Value Fabric — Intelligence  | Accounts | Fail | 97 | 1 | errUI:"Failed to load accounts"; redirect:/calculator→/accou |

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
  - /evidence/acct-123/solution-cost
  - /calculator/acct-123/roi
  - /calculator/acct-123/value-model
  - /value-case/acct-123
  - /realization/acct-123
  - /intelligence
  - /studio
  - /hypothesis
  - /evidence
  - /calculator

## 5. Data & API Audit
- /: GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED; GET https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap — net::ERR_ABORTED
- /login: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /signup: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /home: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /command-center: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /accounts: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /accounts/acct-123: GET http://localhost:3001/accounts/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /workflow/prospect: GET http://localhost:3001/workflow/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /workflow/intelligence: GET http://localhost:3001/workflow/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /workflow/ai-model: GET http://localhost:3001/workflow/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /workflow/driver-tree: GET http://localhost:3001/workflow/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /workflow/evidence: GET http://localhost:3001/workflow/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /workflow/calculator: GET http://localhost:3001/workflow/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /workflow/value-case: GET http://localhost:3001/workflow/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123: GET http://localhost:3001/intelligence/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/signals: GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/drivers: GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/evidence: GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/stakeholders: GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/enrichment: GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/hypotheses: GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/competitive: GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/roi: GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/evidence-library: GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence/acct-123/ontology-match: GET http://localhost:3001/intelligence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /hypothesis/acct-123/hypothesis: GET http://localhost:3001/hypothesis/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED; GET http://localhost:3001/src/pages/hypothesis/HypothesisTab.tsx — net::ERR_ABORTED
- /hypothesis/acct-123/discovery-questions: GET http://localhost:3001/hypothesis/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED; GET http://localhost:3001/src/pages/hypothesis/DiscoveryQuestionsTab.tsx — net::ERR_ABORTED
- /hypothesis/acct-123/persona-fit: GET http://localhost:3001/hypothesis/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED; GET http://localhost:3001/src/pages/hypothesis/PersonaFitTab.tsx — net::ERR_ABORTED
- /hypothesis/acct-123/assumptions: GET http://localhost:3001/hypothesis/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED; GET http://localhost:3001/src/pages/hypothesis/AssumptionsTab.tsx — net::ERR_ABORTED
- /drivers/acct-123: GET http://localhost:3001/drivers/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /evidence/acct-123/evidence: GET http://localhost:3001/evidence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /evidence/acct-123/alternatives: GET http://localhost:3001/evidence/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED; GET http://localhost:3001/src/components/ui/alert.tsx — net::ERR_EMPTY_RESPONSE
- /evidence/acct-123/solution-cost: GET http://localhost:3001/evidence/acct-123/solution-cost — net::ERR_CONNECTION_REFUSED; GET http://localhost:3001/evidence/acct-123/solution-cost — net::ERR_CONNECTION_REFUSED
- /calculator/acct-123/roi: GET http://localhost:3001/calculator/acct-123/roi — net::ERR_CONNECTION_REFUSED; GET http://localhost:3001/calculator/acct-123/roi — net::ERR_CONNECTION_REFUSED
- /calculator/acct-123/value-model: GET http://localhost:3001/calculator/acct-123/value-model — net::ERR_CONNECTION_REFUSED; GET http://localhost:3001/calculator/acct-123/value-model — net::ERR_CONNECTION_REFUSED
- /value-case/acct-123: GET http://localhost:3001/value-case/acct-123 — net::ERR_CONNECTION_REFUSED; GET http://localhost:3001/value-case/acct-123 — net::ERR_CONNECTION_REFUSED
- /realization/acct-123: GET http://localhost:3001/realization/acct-123 — net::ERR_EMPTY_RESPONSE; GET http://localhost:3001/realization/acct-123 — net::ERR_EMPTY_RESPONSE
- /studio/acct-123/action-plan: GET http://localhost:3001/studio/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /studio/acct-123/value-model: GET http://localhost:3001/studio/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /studio/acct-123/narrative: GET http://localhost:3001/studio/acct-123/narrative — net::ERR_ABORTED; GET http://localhost:3001/studio/acct-123/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/packs: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/context/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/models: GET http://localhost:3001/context/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/formulas: GET http://localhost:3001/context/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/formulas/new: GET http://localhost:3001/context/formulas/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/value-trees/explorer: GET http://localhost:3001/context/value-trees/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/agents: GET http://localhost:3001/context/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/ontology: GET http://localhost:3001/context/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/ontology/entities: GET http://localhost:3001/context/ontology/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/ontology/entities/ent-123: GET http://localhost:3001/context/ontology/entities/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/ontology/graph: GET http://localhost:3001/context/ontology/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/ingestion/jobs: GET http://localhost:3001/context/ingestion/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/extraction: GET http://localhost:3001/context/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/integrations: GET http://localhost:3001/context/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /context/sources: GET http://localhost:3001/context/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /deliverables/cases: GET http://localhost:3001/deliverables/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /deliverables/cases/case-123: GET http://localhost:3001/deliverables/cases/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /deliverables/calculators: GET http://localhost:3001/deliverables/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /deliverables/views/cfo: GET http://localhost:3001/deliverables/views/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /deliverables/views/executive: GET http://localhost:3001/deliverables/views/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /deliverables/views/technical: GET http://localhost:3001/deliverables/views/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /settings/content/formulas: GET http://localhost:3001/settings/content/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /settings/data/variables: GET http://localhost:3001/settings/data/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /settings/access/roles: GET http://localhost:3001/settings/access/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /settings/system/settings: GET http://localhost:3001/settings/system/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /settings/system/billing: GET http://localhost:3001/settings/system/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /governance/traces: GET http://localhost:3001/governance/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /governance/evidence: GET http://localhost:3001/governance/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /governance/provenance: GET http://localhost:3001/governance/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /governance/compliance: GET http://localhost:3001/governance/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /governance/benchmarks: GET http://localhost:3001/governance/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /governance/audit/log: GET http://localhost:3001/governance/audit/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /governance/health: GET http://localhost:3001/governance/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /dev/integration: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/dev/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /nonexistent-route-xyz: POST http://localhost:3001/__manus__/logs — net::ERR_ABORTED; GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /intelligence: GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /studio: GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /hypothesis: GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /evidence: GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED
- /calculator: GET http://localhost:3001/%VITE_ANALYTICS_ENDPOINT%/umami — net::ERR_ABORTED

## 6. Accessibility & Responsive Audit
_No responsive overflow._
- Keyboard focus on /login: OK

## 7. Prioritized Fix Backlog
### 1. Fix fail route /
- Severity: P1 | Area: Routing/Rendering
- Problem: Failed to load resource: the server responded with a status of 404 (Not Found); Failed to load resource: the server resp empty:"No data found"; redirect:/→/home
- AC: No console errors, graceful empty/error states, screenshot match

### 2. Fix fail route /login
- Severity: P1 | Area: Routing/Rendering
- Problem: Failed to load resource: the server responded with a status of 404 (Not Found); Failed to load resource: the server resp empty:"No data found"; redirect:/login→/home
- AC: No console errors, graceful empty/error states, screenshot match

### 3. Fix fail route /signup
- Severity: P1 | Area: Routing/Rendering
- Problem: Failed to load resource: the server responded with a status of 404 (Not Found); Failed to load resource: the server resp empty:"No data found"; redirect:/signup→/home
- AC: No console errors, graceful empty/error states, screenshot match

### 4. Fix fail route /home
- Severity: P1 | Area: Routing/Rendering
- Problem: Failed to load resource: the server responded with a status of 404 (Not Found); Failed to load resource: the server resp empty:"No data found"
- AC: No console errors, graceful empty/error states, screenshot match

### 5. Fix fail route /command-center
- Severity: P1 | Area: Routing/Rendering
- Problem: Failed to load resource: the server responded with a status of 404 (Not Found); Failed to load resource: the server resp empty:"No data found"
- AC: No console errors, graceful empty/error states, screenshot match

### 6. Fix fail route /accounts
- Severity: P1 | Area: Routing/Rendering
- Problem: Failed to load resource: the server responded with a status of 404 (Not Found); Failed to load resource: the server resp errUI:"Failed to load accounts"
- AC: No console errors, graceful empty/error states, screenshot match

### 7. Fix fail route /accounts/acct-123
- Severity: P1 | Area: Routing/Rendering
- Problem: Failed to load resource: the server responded with a status of 404 (Not Found); Failed to load resource: the server resp errUI:"Failed to load accounts"
- AC: No console errors, graceful empty/error states, screenshot match

### 8. Fix fail route /intelligence/acct-123
- Severity: P1 | Area: Routing/Rendering
- Problem: Failed to load resource: the server responded with a status of 404 (Not Found); Failed to load resource: the server resp errUI:"Failed to load signal data."; redirect:/intelligence/acct-123→/intelligence/acct-123/signals
- AC: No console errors, graceful empty/error states, screenshot match

## 8. Playwright Test Recommendations
1. Route smoke tests for every canonical path
2. Deep-link reload tests for /intelligence/:id/:tab and /studio/:id/:tab
3. Auth/tenant context propagation tests
4. Responsive viewport matrix (390/768/1280/1440)
5. Axe-core scan on all pages + keyboard-only journey
6. Error/empty/loading state tests with mocked API
