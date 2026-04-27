# 6. Implementation Roadmap

## 6.1 Phasing Philosophy

### 6.1.1 Prioritize by User Impact, Not Technical Dependency

The Fabric 4L integration recovery follows a single guiding principle: **a page rendering mock data is a broken page, regardless of how polished it looks.** The forensic audit reveals 154 routes with tiered navigation, role-based access control, and polished UI components, yet 81% of the 84 authenticated routes render hardcoded data, stale mocks, or no backend connection at all. Sixteen routes are green, fifty-one are red, and seventeen remain unevaluated. The instinct to perfect the architecture before touching the data layer would consume three sprints without changing a single user-facing metric. This roadmap reverses that priority. It targets the highest-user-impact pages first, replaces mock data with live endpoints in the same sprint the page is touched, and defers deep architectural refactoring until the facade rate drops below a threshold where structural work becomes the constraint on velocity.

The phasing strategy treats mock elimination as the primary driver of sprint commitment. Every page brought from red to green in Sprint 1-3 delivers immediate user value and provides a reference implementation for the hook patterns that later sprints scale. Accounts expansion, Workflows enablement, and HealthMonitor completion are not chosen because they are architecturally simple but because they represent core user journeys blocked entirely by the facade. A user who cannot view account details, trigger agent workflows, or monitor system health experiences the application as non-functional regardless of how refined the GraphExplorer or FormulaBuilder pages may be.

### 6.1.2 North Star Metric: Functional Route Percentage

The single metric that governs prioritization, sprint retrospectives, and quarterly planning is **Functional Route Percentage (FRP)**: the count of authenticated routes rendering live, backend-sourced data with proper error and loading states, divided by the total authenticated route count (84). The current FRP stands at **19.0%** — 16 green routes out of 84 authenticated. The roadmap sets explicit FRP checkpoints at the boundary of each phase:

| Phase | Sprints | FRP Start | FRP Target | Routes Added | Cumulative Green |
|-------|---------|-----------|------------|--------------|------------------|
| Phase 1: Kill the Mocks | 1-3 | 19% | 35% | +13 | 29 |
| Phase 2: Endpoint Adoption | 4-8 | 35% | 60% | +21 | 50 |
| Phase 3: Yellow to Green | 9-12 | 60% | 85% | +21 | 71 |
| Phase 4: Constitution Enforcement | Ongoing | 85% | 95%+ | +10+ | 80+ |

The FRP is measured weekly and published on the Integration Dashboard described in Section 6.3.2. A route counts as green only when it satisfies all three criteria: (1) the page component consumes a domain hook that calls a registered backend endpoint, (2) the hook returns typed data generated from or validated against the OpenAPI schema, and (3) the route implements error boundaries and skeleton loading states per the UI/UX Component Strategy (Document 5). Routes consuming generic passthrough hooks, routes with partial endpoint coverage, and routes that fall back to mock data during error conditions are classified as yellow and do not count toward FRP.

### 6.1.3 FRP Trajectory and Confidence Intervals

The current FRP of 19% (16/84) reflects the findings from Track A: Route Integrity Matrix. Track A found 16 green routes including `/accounts`, `/context/ontology/entities`, `/context/formulas`, `/governance/benchmarks`, and `/settings/system/settings`. The Sprint 1-3 target of 35% requires adding 13 functional routes, a pace of approximately 4.3 routes per sprint. The Sprint 4-8 target of 60% requires 21 additional routes across 5 sprints (4.2 per sprint), and the Sprint 9-12 target of 85% requires another 21 routes across 4 sprints (5.25 per sprint). The accelerating pace in Phase 3 is achievable because the Integration Dashboard, type generation pipeline, and standardized hook architecture built in Phases 1 and 2 reduce the marginal cost of each route conversion.

## 6.2 Phase 1: Kill the Mocks (Sprints 1-3)

### 6.2.1 Wire Six Orphan Pages to Real Endpoints

Phase 1 targets six pages that render mock data or have no backend connection despite the existence of ready backend endpoints. These pages are selected using two criteria: the backend endpoints required to power them already exist ( Track B found 236 orphan endpoints), and they sit on high-frequency user navigation paths. The six pages are:

**Accounts Expansion.** The `/accounts` route and its child `/accounts/:id` are already green, consuming the `useAccounts` hook. However, Track B identified 16 orphan Account endpoints that extend this surface significantly — filter options via `GET /v1/accounts/filters`, account search via `POST /v1/accounts/search`, account sync via `POST /v1/accounts/sync`, and sync status via `GET /v1/accounts/sync-status`. Sprint 1 expands the Accounts page to consume these 16 endpoints, adding account search, filtering, CRM sync triggers, and sync status indicators to the existing account list and detail views. The expanded Accounts page becomes the reference implementation for hook composition patterns that Phase 2 scales to other domains.

**AgentWorkflows Enablement.** The `/context/agents` route is classified as UNKNOWN — it has a `useWorkflows` hook registered but no confirmed backend endpoint binding. Track B found 9 orphan workflow endpoints including `POST /v1/workflows` (create), `GET /v1/workflows/active` (list active), `GET /v1/workflows/{workflow_id}` (status), `DELETE /v1/workflows/{workflow_id}` (cancel), `POST /v1/workflows/{workflow_id}/pause`, and `POST /v1/workflows/{workflow_id}/resume`. Sprint 2 wires these 9 endpoints to the AgentWorkflows page, converting it from unknown to green and unblocking agent checkpoint and resume functionality that the platform markets as a core capability.

**HealthMonitor Completion.** The `/governance/health` route is already green via `useSystemHealth`, but Track B found 12 orphan Health endpoints that the current implementation does not consume. These include system health metrics, service status checks, and diagnostic endpoints from the `state-inspector` and `health` domains. Sprint 2 deepens the HealthMonitor integration to consume all 12 endpoints, adding service-level health breakdowns, diagnostic logs, and state inspector panels that transform the page from a simple status indicator into a comprehensive monitoring dashboard.

**OntologyEditor Completion.** The `/context/ontology` route is UNKNOWN — it registers a `useOntology` hook but lacks confirmed backend binding. Track B found 14 orphan Ontology endpoints including `GET /v1/ontology/entities` (list), `GET /v1/ontology/relationships/{entity_id}` (relationships), `GET /v1/ontology/schema/types` (type list), `PUT /v1/ontology/schema/types/{type_id}` (update), and `DELETE /v1/ontology/schema/types/{type_id}` (delete). Sprint 3 wires all 14 endpoints to the OntologyEditor, enabling full CRUD operations on ontology types, entities, and relationships.

**EntityDetail Wiring.** The `/context/ontology/entities/:entityId` route is RED with an UNKNOWN hook and no backend endpoint. Sprint 3 wires it to `GET /v1/ontology/entities` and the relationship endpoints, enabling entity detail views with relationship traversal.

**IngestionJobs Confirmation.** The `/context/ingestion/jobs` route is UNKNOWN with a `useIngestion` hook. Sprint 3 confirms the backend binding and converts it to green.

### 6.2.2 Delete or Deprioritize Sunset Candidates

Two red routes are flagged for architectural review during Phase 1 rather than wiring: `/command-center` (CommandCenter) and `/deliverables/calculators` (InteractiveBusinessCase). Neither page has a registered backend endpoint, and product management has not confirmed their inclusion in the Q2-Q3 roadmap. Sprint 1 includes a sunset evaluation task for both pages. If product confirms deprecation, the routes are removed from the application shell and their component code archived. If product confirms retention, they are added to the Phase 2 backlog with newly specified backend endpoints. The default decision is **delete**: a page with no backend contract and no product commitment should not ship in the facade.

### 6.2.3 Replace RED Hooks with Real Implementations

Track A identified two RED hooks that must be replaced in Phase 1. `useSources` powers the `/context/sources` page (SourceConfiguration) with mock data — it must be reimplemented to consume the Layer 1 ingestion endpoints. `useOpportunities` is referenced in the hook registry but has no corresponding route — it is either connected to an orphaned page or is dead code. Sprint 1 reimplements `useSources` against `DELETE l1` and the full Layer 1 ingestion endpoint set. Sprint 3 either wires `useOpportunities` to the Value Studio rebuild scope or removes it from the registry.

### 6.2.4 Phase 1 Deliverable

Phase 1 delivers 29 green routes from 16, raising FRP from 19% to 35%. The specific route additions by sprint are:

| Sprint | Routes Targeted | Endpoint Domains | Hook Work | Expected FRP |
|--------|----------------|------------------|-----------|--------------|
| Sprint 1 | `/accounts` (expand), `/accounts/:id` (expand), `/context/sources`, Sunset eval: `/command-center`, `/deliverables/calculators` | Accounts (16), Ingestion (26), sunset review | Replace `useSources`, expand `useAccounts` | 24% (+5) |
| Sprint 2 | `/context/agents`, `/governance/health` (deepen), `/context/ingestion/jobs` | Workflows (9), Health (12), State Inspector (12) | Confirm `useWorkflows`, deepen `useSystemHealth` | 30% (+5) |
| Sprint 3 | `/context/ontology`, `/context/ontology/entities/:entityId`, `/home` | Ontology (14), Entity detail | Wire `useOntology`, wire `useEntityDetail` | 35% (+4) |

The +13 route count in Phase 1 includes the expansion of `/accounts` and `/governance/health` (counted as new functional surfaces due to their scope increase), the conversion of five UNKNOWN/RED routes to green, and the removal of two sunset candidates from the authenticated denominator. The expanded Accounts page with search, filter, and sync represents a functionally distinct surface from the basic list view that was previously green. Similarly, the deepened HealthMonitor with 12 endpoints is treated as a new functional route because it exposes capabilities that were not previously available.

## 6.3 Phase 2: Endpoint Adoption (Sprints 4-8)

### 6.3.1 Onboard 50+ DIL Endpoints Using Standardized Hook Architecture

Phase 2 scales the patterns established in Phase 1 across the remaining high-value endpoint domains. The 236 orphan endpoints identified by Track B are grouped by domain, and the top-priority domains are onboarded across five sprints. The standardized three-tier hook architecture (Document 3) is the delivery mechanism: protocol hooks wrap the API client with tenant context propagation and error mapping, domain hooks implement caching and optimistic update policies per the Hook Architecture Contract, and page hooks compose domain hooks for specific route data requirements.

**Sprint 4** targets the Formula and Business Case domains. The UNKNOWN routes `/context/formulas/:formulaId` and `/context/formulas/new` are wired to the Formula detail endpoints (`GET /v1/formulas/{formula_id}`, `POST /v1/formulas/evaluate`, `POST /v1/formulas/scenario`). The UNKNOWN routes `/deliverables/cases` and `/deliverables/cases/:caseId` are wired to their backend counterparts. These conversions leverage the existing green `/context/formulas` route as a reference — the formula list already works, and the detail pages extend the same domain hook with additional query parameters.

**Sprint 5** targets the Deliverables views and ValuePacks expansion. The three UNKNOWN CFO/executive/technical view routes (`/deliverables/views/cfo`, `/deliverables/views/executive`, `/deliverables/views/technical`) are wired to the business case rendering endpoints. The ValuePacks domain (9 orphan endpoints including `POST /v1/valuepacks`, `GET /v1/valuepacks/compare`, `GET /v1/valuepacks/ontology-map`) is connected to expand the existing green `/context/packs` route from a simple list to a full management interface with compare and ontology mapping capabilities.

**Sprint 6** targets the Governance audit pages. The UNKNOWN routes `/governance/audit/changes`, `/governance/audit/log`, `/governance/compliance`, and `/governance/evidence` are wired to the Ground Truth and audit endpoints (13 orphan endpoints in the `ground-truth` domain). The DecisionTrace component, which currently consumes `useProvenance` for a subset of governance routes, is expanded to cover the full audit trail surface.

**Sprint 7** targets the remaining Governance routes and the Graph/Value Tree domains. The UNKNOWN routes `/governance/integrity`, `/governance/provenance`, and `/governance/traces` are wired to their backend endpoints. The 3 Graph orphan endpoints (`GET /entities/{entity_id}/subgraph`, `GET /graph`, `GET /v1/graph/subgraph`) and 2 Value Tree endpoints (`GET /v1/value-trees/{entity_id}`, `GET /v1/value-trees/{entity_id}/paths`) are connected to extend the existing green GraphExplorer and enable the ValueTreeExplorer.

**Sprint 8** targets the Settings access routes and Model Registry. The three RED Settings access routes (`/settings/access/keys`, `/settings/access/roles`, `/settings/access/teams`) are wired to the Users, API Keys, and permission endpoints (5+ orphan endpoints in the Users domain, 3 in API Keys). The Model Registry domain (7 orphan endpoints) is connected to deepen the existing `/context/models` green route with full model versioning capabilities.

### 6.3.2 Build Integration Dashboard

Parallel to the endpoint onboarding, Sprints 4-6 build the **Integration Dashboard**: a developer-only page at `/context/integrations` that visualizes the integration health of the entire application. The dashboard displays four panels: (1) an **Endpoint Coverage** panel showing the percentage of the 244 backend endpoints that have at least one consuming frontend hook, with drill-down by layer and domain; (2) a **Hook Health** panel showing the 44 hooks color-coded by their data source classification (green, yellow, red) with click-through to hook source; (3) a **Mock Detection** panel listing all components containing hardcoded data, with file paths and line numbers extracted by the `detect_mock_data` script; and (4) a **Route Integrity Matrix** panel reproducing the Track A color classification with live updates as routes are converted.

The Integration Dashboard is built using the same hook architecture it monitors — it consumes a `useIntegrationMetrics` hook that aggregates data from the route registry, hook analysis, and endpoint coverage APIs. It ships as a dev-only route gated by environment variable, visible in development and staging but not in production. The dashboard serves two purposes: it makes the integration problem visible to the entire engineering organization, and it provides the data feed for the weekly FRP tracking described in Section 6.6.

### 6.3.3 Complete Type Generation Pipeline

Sprints 6-8 complete the Type Generation Pipeline specified in Document 4. The pipeline auto-generates TypeScript types from the backend OpenAPI schemas at build time, version-locks frontend types to backend API versions, and fails CI when backend schema changes without corresponding frontend type regeneration. By Sprint 8, all critical domains (Accounts, Ontology, Workflows, Health, Formulas, ValuePacks, Governance, Settings) have automated type generation configured. The remaining domains (Tools, Analysis, CRM Webhooks, OIDC SSO) are scheduled for Phase 3.

### 6.3.4 Phase 2 Deliverable

Phase 2 delivers 50 green routes from 29, raising FRP from 35% to 60%. The 21 additional routes come from converting 17 UNKNOWN routes to green, expanding 3 existing green routes with new endpoint coverage (ValuePacks, GraphExplorer, Models), and wiring 1 previously RED Settings route block. The Integration Dashboard ships as a working dev tool, and the Type Generation Pipeline covers all critical domains.

## 6.4 Phase 3: Yellow to Green (Sprints 9-12)

### 6.4.1 Refactor Pages Using Generic or Incomplete Hooks

Phase 3 addresses the architectural debt that Phases 1 and 2 deliberately deferred. Seventeen routes remain classified as UNKNOWN at the start of Phase 3 — these are primarily the Intelligence Workspace tab routes and Value Studio sub-routes that require deep architectural rebuilds rather than simple endpoint wiring. Track A classified these as UNKNOWN because no meaningful hook analysis was possible: the components render hardcoded tab content with no data fetching infrastructure in place.

**Sprint 9** targets the Intelligence Workspace signal and driver surfaces. The routes `/intelligence/:accountId/signals`, `/intelligence/signals`, `/intelligence/:accountId/drivers`, and `/intelligence/drivers` are rebuilt with dedicated domain hooks (`useSignals`, `useDrivers`) that consume the 3 orphan Signals endpoints and the analysis endpoints from Layer 3. These routes were previously redirects or hardcoded tabs — Sprint 9 replaces them with functional data surfaces that render live signal and driver data filtered by account context.

**Sprint 10** targets the Intelligence Workspace evidence and stakeholder surfaces. The routes `/intelligence/:accountId/evidence`, `/intelligence/evidence`, `/intelligence/:accountId/stakeholders`, and `/intelligence/stakeholders` are rebuilt with `useEvidence` and `useStakeholders` hooks consuming the Ground Truth and evidence endpoints. The deep refactor of the Intelligence Workspace is completed in this sprint: the generic `AccountContextSync` redirect pattern is replaced with dedicated page components for each tab, each with its own domain hook, error boundary, and skeleton state.

### 6.4.2 Deep Refactor of Intelligence Workspace and Value Studio

The Intelligence Workspace and Value Studio represent the two largest architectural rebuilds in the roadmap. Track A found that the Intelligence Workspace routes (`/intelligence/:accountId/*` and `/intelligence/*`) all resolve to `WorkspaceContextRedirect` or `AccountContextSync` components — redirect shells with no data surfaces. The Value Studio routes (`/model/value-studio` and its seven sub-routes: `/discovery`, `/explorer`, `/mapping`, `/modeling`, `/narrative`, `/tracking`, `/validation`) are similarly hollow, all resolving to `WorkspaceContextRedirect` with hardcoded tab labels.

**Sprint 11** executes the Value Studio architectural rebuild. The eight Value Studio routes are replaced with dedicated page components: `ValueStudioDiscovery`, `ValueStudioExplorer`, `ValueStudioMapping`, `ValueStudioModeling`, `ValueStudioNarrative`, `ValueStudioTracking`, and `ValueStudioValidation`. Each component consumes a dedicated domain hook (`useValueStudioDiscovery`, `useValueStudioModeling`, etc.) that wires to the ValuePacks, Value Tree, and Formula endpoints from Layers 3 and 4. The `useOpportunities` hook, if it survives the Sprint 3 evaluation, is either integrated here or removed. The rebuild follows the three-tier hook architecture established in Phase 2, with each domain hook implementing proper caching, optimistic updates, and error handling per the Hook Architecture Contract.

### 6.4.3 Implement UI/UX Component Strategy

Sprint 12 completes the UI/UX Component Strategy (Document 5) across all 71 green routes. Every async component receives a corresponding skeleton state. The error state taxonomy — network error, permission error, empty state, partial degradation — is implemented with distinct UI patterns for each classification. Optimistic update patterns are applied to mutation-heavy routes (Accounts, Workflows, Formulas, ValuePacks) where user feedback latency must be minimized.

The Settings content routes (`/settings/content/approvals`, `/settings/content/formulas`, `/settings/content/versions`) are wired to the FormulaGovernance backend endpoints. The `/home` route (ValueNarrativeHome) is rebuilt from a static landing page to a personalized dashboard consuming the account context, recent signals, and active workflows. Any remaining UNKNOWN routes from the Track A matrix are classified and converted.

### 6.4.4 Phase 3 Deliverable

Phase 3 delivers 71 green routes from 50, raising FRP from 60% to 85%. The 21 additional routes come from the Intelligence Workspace tab rebuild (8 routes), the Value Studio architectural rebuild (8 routes), the Settings content wiring (3 routes), the `/home` rebuild (1 route), and the completion of any remaining UNKNOWN classifications (1 route). All 71 green routes implement the full UI/UX Component Strategy with skeleton states and error boundaries.

## 6.5 Phase 4: Constitution Enforcement (Ongoing)

### 6.5.1 CI Gates: Automated Enforcement of Integration Contracts

Phase 4 begins when FRP reaches 85% and shifts the engineering culture from project-based recovery to continuous enforcement. Three CI gates are implemented to prevent regression and ensure sustainable development velocity:

**`detect_mock_data` Gate.** This gate fails the build when hardcoded arrays, mock objects, or static data fixtures are detected in page components. The detection script scans all files in `src/pages/` and `src/components/` for patterns indicative of mock data: arrays of objects with obviously fake field values (`mockData`, `testData`, `dummy*`), static imports of `.mock.ts` files, and objects with hardcoded IDs matching known mock prefixes. The gate runs on every pull request and blocks merge if any page component added or modified in the PR contains mock data. Exception: mock data is permitted in `*.test.ts` files and in `src/mocks/` directories that are explicitly excluded from production builds.

**`endpoint_coverage` Gate.** This gate fails the build when a backend endpoint has had an OpenAPI spec change but no corresponding frontend hook update within two sprint cycles (four weeks). The gate maintains a registry mapping each of the 244 backend endpoints to its consuming frontend hook(s). When the backend schema changes, the endpoint is flagged with a timestamp; if four weeks pass without the corresponding hook being updated, the gate fails. This prevents the drift condition that created the 236 orphan endpoints: backend teams shipping endpoints without frontend contracts.

**`type_sync_check` Gate.** This gate fails the build when the TypeScript types generated from the OpenAPI spec drift from the types imported by the frontend hooks. It runs the type generation pipeline in CI and compares the output against the committed type definitions. Any mismatch — field additions, type changes, or missing interfaces — fails the build and notifies the team in Slack.

### 6.5.2 Contract Council: RFC Process for New Endpoints

The Contract Council is a lightweight governance process that ensures new backend endpoints cannot ship without corresponding frontend hook specifications. The process has three rules:

**Rule 1: No endpoint without a hook spec.** Before a backend endpoint merges to main, a frontend engineer must approve the corresponding hook specification — the hook name, query key pattern, request/response types, error mapping, and cache policy. The hook spec is submitted as part of the backend PR and reviewed by a frontend engineer from the Contract Council rotation.

**Rule 2: No mock data beyond the introducing sprint.** A page component may use mock data during its initial development sprint, but the mock data must be removed before the sprint demo. If mock data remains at sprint end, the feature branch is not eligible for merge. This rule prevents the accumulation of "temporary" mocks that become permanent fixtures.

**Rule 3: Contract.md is the source of truth.** The six canonical contracts (2.1-2.6) and the three missing contracts (API Boundary, Type Synchronization, Hook Architecture) are maintained in `contracts/` at the repository root. Implementation drift from the contracts is treated as a bug, not a style difference. Contract amendments require an RFC approved by both a frontend architect and a backend engineer.

### 6.5.3 Facade Budget Enforcement

The facade budget is a quarterly quota for non-green routes. Starting from the 15% non-green rate at the beginning of Phase 4 (100% minus 85% FRP), the budget requires a 10 percentage point reduction per quarter: Q1 targets <5% non-green, Q2 and onward target <5%. The budget is enforced through the weekly FRP review: if the non-green percentage does not decrease by at least 2.5 percentage points per month, the sprint plan is reprioritized to address the highest-impact remaining red or yellow routes.

The facade budget applies only to authenticated routes. Redirect routes (70 of 154) are excluded from FRP calculations because they do not render data surfaces. The budget is published on the Integration Dashboard and reviewed monthly by engineering leadership and product management.

### 6.5.4 Phase 4 Deliverable

Phase 4 stabilizes FRP at 95% or above, with the remaining 5% consisting of deliberately maintained redirect routes and experimental features under active development. The three CI gates run on every build, the Contract Council reviews all new endpoint proposals, and the facade budget prevents regression. Sustainable development velocity is restored because the integration infrastructure — hook architecture, type generation, error handling, loading states — is now a shared platform that new features inherit rather than rebuild.

## 6.6 Success Metrics and Tracking

### 6.6.1 Weekly Dashboard

The Integration Dashboard at `/context/integrations` is the single source of truth for all integration metrics. It updates daily via a CI cron job and displays four primary metrics:

| Metric | Current | Sprint 3 | Sprint 8 | Sprint 12 | Ongoing Target |
|--------|---------|----------|----------|-----------|----------------|
| Functional Route Percentage (FRP) | 19% (16/84) | 35% (29/84) | 60% (50/84) | 85% (71/84) | 95%+ (80/84) |
| Orphan Endpoint Count | 236 | 210 | 150 | 80 | <50 |
| Mock Data Instances | 51+ | 30 | 15 | 5 | 0 |
| Contract Compliance % | ~60% | 65% | 80% | 90% | 100% |

**FRP** is calculated as green authenticated routes divided by total authenticated routes (84). The denominator decreases only when sunset candidates are removed — two routes in Phase 1 if `/command-center` and `/deliverables/calculators` are deprecated.

**Orphan Endpoint Count** tracks the number of backend endpoints with no consuming frontend hook. The target trajectory reduces orphans by ~26 in Phase 1, ~60 in Phase 2, ~70 in Phase 3, and reaches <50 by the end of the first ongoing quarter. An endpoint ceases to be orphan when any frontend hook calls it, even if the route is not yet green — this metric rewards endpoint adoption independently of route completion.

**Mock Data Instances** counts the number of page components containing hardcoded data, as detected by the `detect_mock_data` script. The 51+ current count corresponds to the 51 RED routes. The trajectory eliminates mock data aggressively in Phase 1 (where the highest-user-impact pages are fixed), then continues at a slower pace as remaining red routes are addressed in Phases 2 and 3.

**Contract Compliance %** measures adherence to the 9 contracts (6 canonical + 3 missing) weighted by criticality. The API Boundary, Type Synchronization, and Hook Architecture contracts each contribute 15% to the score; the 6 canonical contracts contribute the remaining 55%. Contract 2.2 (DB Session) and 2.3 (Middleware) are already ratified at 80% and 90% respectively, providing a baseline of ~35%. The trajectory ratifies Contract 2.1 (Tenant Context) by Sprint 3, Contracts 2.4 (Tool Boundary) and 2.5 (Agent Output) by Sprint 8, and Contract 2.6 (UI State) plus the 3 missing contracts by Sprint 12.

### 6.6.2 Monthly Review

The monthly review is a one-hour meeting attended by the engineering lead, product manager, and frontend architect. The agenda has three items: (1) **Facade Budget Status** — review the current non-green percentage against the quarterly target, identify the highest-impact routes to convert in the coming month, and reprioritize if the monthly decrease falls below 2.5 percentage points; (2) **Sprint Commitment vs. Delivery** — compare the FRP target from the previous month's plan against the actual FRP achieved, analyze variance, and adjust the next month's route targets accordingly; (3) **Technical Debt Items** — review integration-related debt items (hook patterns needing cleanup, type definitions with known drift, components with suboptimal error handling) and allocate debt-reduction capacity in the upcoming sprint plan.

### 6.6.3 Quarterly Goal

The quarterly goal is a 10 percentage point reduction in the non-green route rate until the facade rate falls below 5%. The quarter starting at 85% FRP (15% non-green) targets 95% FRP (5% non-green). Subsequent quarters maintain the 95%+ target. The quarterly goal is published in the engineering OKRs and tracked on the Integration Dashboard.

## Appendix A: 12-Sprint Route Target Timeline

| Sprint | Phase | Routes Targeted | Endpoint Domains | Primary Hook Work | FRP After |
|--------|-------|----------------|------------------|-------------------|-----------|
| Sprint 1 | Kill the Mocks | `/accounts` (expand), `/context/sources`, sunset eval: `/command-center`, `/deliverables/calculators` | Accounts (16), Ingestion (26) | Replace `useSources`, expand `useAccounts` | 24% |
| Sprint 2 | Kill the Mocks | `/context/agents`, `/governance/health` (deepen), `/context/ingestion/jobs` | Workflows (9), Health (12), State Inspector (12) | Confirm `useWorkflows`, deepen `useSystemHealth` | 30% |
| Sprint 3 | Kill the Mocks | `/context/ontology`, `/context/ontology/entities/:entityId`, `/home` | Ontology (14), Entity detail | Wire `useOntology`, `useEntityDetail` | 35% |
| Sprint 4 | Endpoint Adoption | `/context/formulas/:formulaId`, `/context/formulas/new`, `/deliverables/cases`, `/deliverables/cases/:caseId` | Formulas (5), Business Cases | `useFormulaDetail`, `useBusinessCases` | 40% |
| Sprint 5 | Endpoint Adoption | `/deliverables/views/cfo`, `/deliverables/views/executive`, `/deliverables/views/technical`, expand `/context/packs` | ValuePacks (9), Business Case views | `useValuePackManagement`, `useBusinessCaseViews` | 45% |
| Sprint 6 | Endpoint Adoption | `/governance/audit/changes`, `/governance/audit/log`, `/governance/compliance`, `/governance/evidence`, Integration Dashboard MVP | Ground Truth (13), Audit | Expand `useProvenance`, `useIntegrationMetrics` | 50% |
| Sprint 7 | Endpoint Adoption | `/governance/integrity`, `/governance/provenance`, `/governance/traces`, expand GraphExplorer | Graph (3), Value Trees (2), Ground Truth | `useGraphDetail`, `useValueTrees` | 55% |
| Sprint 8 | Endpoint Adoption | `/settings/access/keys`, `/settings/access/roles`, `/settings/access/teams`, expand `/context/models` | Users (5), API Keys (3), Model Registry (7) | `usePermissions`, `useModelRegistry` | 60% |
| Sprint 9 | Yellow to Green | `/intelligence/:accountId/signals`, `/intelligence/signals`, `/intelligence/:accountId/drivers`, `/intelligence/drivers` | Signals (3), Analysis (5) | `useSignals`, `useDrivers` | 66% |
| Sprint 10 | Yellow to Green | `/intelligence/:accountId/evidence`, `/intelligence/evidence`, `/intelligence/:accountId/stakeholders`, `/intelligence/stakeholders` | Ground Truth (13), Evidence | `useEvidence`, `useStakeholders` | 72% |
| Sprint 11 | Yellow to Green | `/model/value-studio`, `/model/value-studio/discovery`, `/explorer`, `/mapping`, `/modeling`, `/narrative`, `/tracking`, `/validation` | ValuePacks (9), Value Trees (2) | Full Value Studio hook set | 80% |
| Sprint 12 | Yellow to Green | `/settings/content/approvals`, `/settings/content/formulas`, `/settings/content/versions`, `/home` (rebuild), final cleanup | FormulaGovernance (5), Home | `useFormulaGovernance`, `useHomeDashboard` | 85% |

This timeline maps each of the 84 authenticated routes to a specific sprint, with explicit endpoint domain targets and hook deliverables. The Integration Dashboard, Type Generation Pipeline, and CI gates are infrastructure workstreams that run parallel to the route conversion timeline and are not counted as route deliverables. The two sunset candidates (`/command-center`, `/deliverables/calculators`) are excluded from the FRP denominator if deprecated in Sprint 1, reducing the authenticated route count from 84 to 82 and adjusting the 85% target to 70 green routes instead of 71.
