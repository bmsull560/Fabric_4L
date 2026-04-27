# Fabric 4L: Frontend-Backend Integration Recovery — System Design Brief (6 Documents)

## Document 1: Integration Contract Specification (~4500 words, 4 tables, 2 code blocks)

### 1.1 Purpose and Scope
#### 1.1.1 Define the API boundary contract as the foundational agreement between frontend and backend data exchange
#### 1.1.2 Scope covers all 244 DIL endpoints with only 8 currently connected — the 96.7% orphan gap must be addressed
#### 1.1.3 Reference the 6 canonical contracts (CONTRACT.md 2.1-2.6) and 3 missing contracts identified in Track C audit

### 1.2 Endpoint-to-Hook Mapping Registry
#### 1.2.1 Registry structure: all 50+ priority DIL endpoints assigned to frontend hooks with clear ownership
#### 1.2.2 Priority 1 mappings: 16 Account/CRM endpoints → useAccounts + new useAccountDetail, useAccountSearch, useAccountSync hooks
#### 1.2.3 Priority 1 mappings: 9 Workflow endpoints → useWorkflows expansion with useWorkflowStatus, useWorkflowEvents, useWorkflowControl
#### 1.2.4 Priority 1 mappings: 12 Health endpoints → useSystemHealth expansion with useHealthHistory, useHealthAlerts
#### 1.2.5 Priority 2 mappings: 14 Ontology endpoints → useOntologySchema already partially connected, needs completion
#### 1.2.6 Priority 2 mappings: 8 Checkpoint endpoints → new useCheckpoints hook for agent resume
#### 1.2.7 Priority 3 mappings: remaining 180+ endpoints by domain (ValuePacks 9, Models 7, Integrations 6, etc.)

### 1.3 Type Generation Pipeline
#### 1.3.1 Backend Zod schema → OpenAPI spec → frontend TypeScript auto-generation at build time
#### 1.3.2 CI gate: build fails when backend schema changes without corresponding frontend type regeneration
#### 1.3.3 Version-locking strategy: frontend types pinned to backend API version tags

### 1.4 Error Boundary Behavior
#### 1.4.1 HTTP status code → UIErrorType mapping: 401 (re-auth), 403 (permission error), 404 (not found), 422 (validation), 500+ (system error)
#### 1.4.2 Error boundary hierarchy: page-level > section-level > component-level
#### 1.4.3 Retry policy per endpoint category: idempotent (3 retries), mutation (1 retry), stream (no retry)

### 1.5 Loading State Hierarchy
#### 1.5.1 Skeleton > spinner > cache > empty state priority order
#### 1.5.2 Every async component must declare its loading strategy in the contract
#### 1.5.3 Loading state aggregation for composed hooks (page hooks calling multiple domain hooks)

### 1.6 Contract Governance
#### 1.6.1 RFC process: new backend endpoints cannot ship without frontend hook specification
#### 1.6.2 CI enforcement gates: detect_mock_data, endpoint_coverage, type_sync_check
#### 1.6.3 The "Facade Budget": max 40% non-green routes, reduce 10% per quarter to <5%

## Document 2: Page Reality Index (~4000 words, 3 large tables)

### 2.1 Methodology
#### 2.1.1 Truth table classification system: Current State, Target State, Backend Dependency, Effort Estimate
#### 2.1.2 Color coding preserved from Track A audit: GREEN (live), RED (mock), UNKNOWN (unevaluated), REDIRECT (legacy)
#### 2.1.3 Effort sizing: S (1-3 days), M (1-2 weeks), L (2-4 weeks), XL (1+ months), SUNSET (delete)

### 2.2 Immediate Wins (Hook Exists, Needs Wiring)
#### 2.2.1 Accounts (/accounts, /accounts/:id): useAccounts exists, needs expansion to 16 connected endpoints — Effort M
#### 2.2.2 EntityBrowser (/context/ontology/entities): useEntities connected, needs filter enhancement — Effort S
#### 2.2.3 FormulaList (/context/formulas): useFormulas connected, needs formula evaluation endpoint — Effort S
#### 2.2.4 Billing (/settings/system/billing/*): billingKeys exist but route is RED — needs route-to-hook wiring — Effort S

### 2.3 Medium Build (Backend Ready, Frontend Missing)
#### 2.3.1 AgentWorkflows (/context/agents): useWorkflows exists but endpoint N/A — connect 9 workflow endpoints — Effort M
#### 2.3.2 OntologyEditor (/context/ontology): useOntologySchema partially connected — complete 14 endpoints — Effort L
#### 2.3.3 IngestionJobs (/context/ingestion/jobs): useIngestion exists but route UNKNOWN — verify connection — Effort S
#### 2.3.4 SourceConfiguration (/context/sources): useSources is RED/mock — replace with real useSources — Effort M
#### 2.3.5 HealthMonitor (/governance/health): useSystemHealth connected, needs 11 more health endpoints — Effort M

### 2.4 Deep Refactor (Architectural Mismatch)
#### 2.4.1 Intelligence Workspace (10 routes /intelligence/*): all RED, needs dedicated hook architecture — Effort XL
#### 2.4.2 Value Studio (7 routes /studio/*, 7 routes /model/value-studio/*): all RED/redirect, needs full rebuild — Effort XL
#### 2.4.3 BusinessCase views (/deliverables/views/*): useBusinessCases exists but routes UNKNOWN — needs view-specific hooks — Effort L
#### 2.4.4 DecisionTrace (7 routes /governance/*): useProvenance exists but 6 routes UNKNOWN — expand coverage — Effort L

### 2.5 Sunset Candidates
#### 2.5.1 CommandCenter (/command-center): single route, no backend surface, unclear product purpose — candidate for removal
#### 2.5.2 InteractiveBusinessCase (/deliverables/calculators): no hooks, no endpoints — evaluate against product roadmap
#### 2.5.3 WorkspaceContextRedirect routes: 30+ redirect routes that mask missing functionality — decision required

## Document 3: Hook Architecture Blueprint (~4000 words, 3 tables, 3 code blocks)

### 3.1 The Three-Tier Hook System
#### 3.1.1 Tier 1 — Protocol Hooks: Zod-validated API client wrappers (lowest level), direct HTTP abstraction
#### 3.1.2 Tier 2 — Domain Hooks: useFabricQuery, useFabricMutation with standard error handling, caching, optimistic updates
#### 3.1.3 Tier 3 — Page Hooks: composed domain hooks for specific page data requirements with loading/error state aggregation
#### 3.1.4 Strict rule: No page component calls fetch directly; no page component uses mock data after T+30 days

### 3.2 Tier 1: Protocol Hooks
#### 3.2.1 apiClient.ts as the single HTTP gateway: interceptors, tenant header injection, request/response logging
#### 3.2.2 Zod runtime validation: every response validated against schema before reaching domain hooks
#### 3.2.3 Protocol hook examples: useApiGet, useApiPost, useApiDelete with typed generics

### 3.3 Tier 2: Domain Hooks
#### 3.3.1 useFabricQuery: wraps useQuery with standardized staleTime, retryPolicy, errorMapping
#### 3.3.2 useFabricMutation: wraps useMutation with optimistic update patterns, invalidation rules
#### 3.3.3 Query key namespace convention: QK.{domain}.{action}({params}) for cache consistency
#### 3.3.4 Current domain hooks analysis: 26 green hooks are the model, 18 need creation or refactoring

### 3.4 Tier 3: Page Hooks
#### 3.4.1 Composition pattern: page hooks aggregate multiple domain hooks into page-specific data shapes
#### 3.4.2 Loading state aggregation: derived isLoading from all constituent domain hooks
#### 3.4.3 Error state aggregation: prioritized error display (first error > most recent error)

### 3.5 Migration Strategy for Existing Hooks
#### 3.5.1 Current hook inventory: 44 hooks analyzed — 26 green, 5 yellow, 2 red, 11 unknown
#### 3.5.2 Refactor order: red first (useSources, useOpportunities), then yellow (useInvoices, useUsageKeys, etc.), then unknown
#### 3.5.3 Backward compatibility: existing hook APIs preserved during refactor, internal implementation changes

## Document 4: Type Synchronization Protocol (~3000 words, 2 tables, 2 code blocks)

### 4.1 Current Type Drift Problem
#### 4.1.1 244 backend endpoints with Zod schemas, frontend types manually defined with detected drift
#### 4.1.2 Multiple any types detected in hooks: useC1Stream, useComposition, useAuth, usePolling
#### 4.1.3 No automated detection: schema changes on backend silently break frontend assumptions

### 4.2 Auto-Generation Pipeline
#### 4.2.1 Build-time generation: openapi-typescript or similar tool to generate types from OpenAPI spec
#### 4.2.2 Output location: src/generated/api-types.ts — never manually edited
#### 4.2.3 CI integration: type generation runs as pre-build step, failures block deployment

### 4.3 Version Locking Strategy
#### 4.3.1 Backend API version tags (git tags or package versions) pinned in frontend package.json
#### 4.3.2 Breaking change detection: CI compares generated types against committed version, fails on mismatch
#### 4.3.3 Gradual migration path: start with critical domains (Accounts, Ontology, Workflows), expand to full coverage

### 4.4 Manual Type Boundaries
#### 4.4.1 When to keep manual types: UI-specific shapes, form state, view models that don't map 1:1 to API
#### 4.4.2 Hybrid approach: generated types for API layer, manual types for presentation layer
#### 4.4.3 Type guard functions for runtime validation at protocol hook layer

### 4.5 Implementation Steps
#### 4.5.1 Phase 1: Set up generation tool and CI pipeline for OpenAPI → TypeScript
#### 4.5.2 Phase 2: Replace manual API types in green hooks first (reference implementation)
#### 4.5.3 Phase 3: Full migration — all hooks use generated types, manual types only for UI layer

## Document 5: UI/UX Component Strategy (~3500 words, 3 tables)

### 5.1 Skeleton System
#### 5.1.1 Every async component must have a corresponding skeleton state matching the final layout shape
#### 5.1.2 Skeleton hierarchy: page skeleton > section skeleton > card skeleton > inline skeleton
#### 5.1.3 Implementation: Skeleton components co-located with their async counterparts, naming convention {Component}Skeleton
#### 5.1.4 Priority mapping: 16 green routes get skeletons first (immediate wins), then 51 red routes

### 5.2 Error State Taxonomy
#### 5.2.1 Network error: retry button, automatic retry with backoff, offline detection
#### 5.2.2 Permission error (403): upgrade prompt, contact admin message, feature gating UI
#### 5.2.3 Not found error (404): helpful navigation suggestions, create-new CTA where applicable
#### 5.2.4 Validation error (422): inline field errors, form-level summary, scroll-to-first-error
#### 5.2.5 System error (500+): incident reference, support contact, graceful degradation
#### 5.2.6 Empty state: contextual illustration, next-step guidance, create-first CTA

### 5.3 Optimistic Update Patterns
#### 5.3.1 Where optimistic updates apply: user-initiated mutations (create, update, delete) with predictable outcomes
#### 5.3.2 Rollback strategy: on mutation failure, revert UI state and show error toast
#### 5.3.3 Conflict resolution: when optimistic state diverges from server response on refetch
#### 5.3.4 Current gaps: useSources, useOpportunities use mock data — no optimistic update possible without real mutations

### 5.4 Async State Machine
#### 5.4.1 Unified async state: idle > loading > success | error > refreshing
#### 5.4.2 State transitions: every async component must handle all 5 states explicitly
#### 5.4.3 Refresh pattern: pull-to-refresh, background refetch, and manual refresh button

### 5.5 Component Library Requirements
#### 5.5.1 AsyncWrapper component: handles loading, error, empty states for any child component
#### 5.5.2 ErrorBoundary component: catches unhandled errors, displays fallback UI, logs to monitoring
#### 5.5.3 DataTable skeleton: column-aligned shimmer matching table headers
#### 5.5.4 Form skeleton: field-aligned shimmer matching form layout

## Document 6: Implementation Roadmap (~3500 words, 2 tables, 1 Gantt-like timeline)

### 6.1 Phasing Philosophy
#### 6.1.1 Prioritize by user impact, not technical dependency: kill mocks before perfecting architecture
#### 6.1.2 North star metric: Functional Route Percentage (% of 84 authenticated routes rendering live data)
#### 6.1.3 Current FRP: 16/84 = 19%; Sprint 1-3 target: 35%; Sprint 4-8 target: 60%; Sprint 9-12 target: 85%

### 6.2 Phase 1: Kill the Mocks (Sprint 1-3)
#### 6.2.1 Wire 6 orphan pages to real endpoints: Accounts expansion, Workflows, HealthMonitor, Ontology completion
#### 6.2.2 Delete or deprioritize sunset candidates: CommandCenter, InteractiveBusinessCase evaluation
#### 6.2.3 Replace useSources and useOpportunities (RED hooks) with real implementations
#### 6.2.4 Deliverable: FRP increases from 19% to 35% (+13 functional routes)

### 6.3 Phase 2: Endpoint Adoption (Sprint 4-8)
#### 6.3.1 Onboard 50+ DIL endpoints using the new hook architecture (Documents 1-3 contracts)
#### 6.3.2 Build Integration Dashboard: dev-only page showing endpoint coverage %, hook health, mock detection
#### 6.3.3 Complete Type Generation Pipeline (Document 4) for all critical domains
#### 6.3.4 Deliverable: FRP increases from 35% to 60% (+21 functional routes)

### 6.4 Phase 3: Yellow to Green (Sprint 9-12)
#### 6.4.1 Refactor yellow pages: replace generic workspace hooks with dedicated domain hooks
#### 6.4.2 Deep refactor of Intelligence Workspace and Value Studio (architectural rebuild)
#### 6.4.3 Implement remaining UI/UX Component Strategy (Document 5): skeletons, error states for all routes
#### 6.4.4 Deliverable: FRP increases from 60% to 85% (+21 functional routes)

### 6.5 Phase 4: Constitution Enforcement (Ongoing)
#### 6.5.1 CI gates: detect_mock_data fails build, endpoint_coverage fails after 2 sprints orphan, type_sync_check fails on drift
#### 6.5.2 Contract Council: RFC process for new endpoints, no mock data beyond introducing sprint
#### 6.5.3 Facade Budget enforcement: quarterly review, reduce non-green % by 10 points per quarter to <5%
#### 6.5.4 Deliverable: FRP stabilizes at 95%+, sustainable development velocity restored

### 6.6 Success Metrics and Tracking
#### 6.6.1 Weekly dashboard: FRP, orphan endpoint count, mock data instances, contract compliance %
#### 6.6.2 Monthly review: facade budget status, sprint commitment vs delivery, technical debt items
#### 6.6.3 Quarterly goal: 10% reduction in non-green routes until <5% facade rate achieved

# References
## fabric4l.agent.outline.md
- **Type**: Master outline for all 6 design brief documents
- **Path**: /mnt/agents/output/fabric4l.agent.outline.md

## Source Data Files
- **executive-summary.md**: /mnt/agents/upload/executive-summary.md
- **track-a-hook-analysis.json**: /mnt/agents/upload/track-a-hook-analysis.json
- **track-a-route-extraction.json**: /mnt/agents/upload/track-a-route-extraction.json
- **track-a-route-matrix.csv**: /mnt/agents/upload/track-a-route-matrix.csv
- **track-a-route-matrix.md**: /mnt/agents/upload/track-a-route-matrix.md
- **track-b-openapi-analysis.json**: /mnt/agents/upload/track-b-openapi-analysis.json
- **track-b-orphan-registry.md**: /mnt/agents/upload/track-b-orphan-registry.md
- **track-c-contract-gaps.md**: /mnt/agents/upload/track-c-contract-gaps.md
- **design-brief-plans.md**: /mnt/agents/upload/design-brief-plans.md
