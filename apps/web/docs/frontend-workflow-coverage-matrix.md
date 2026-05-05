# Frontend Workflow Coverage Matrix

**Owner:** Frontend Platform  
**Last updated:** May 5, 2026  
**Purpose:** This matrix is the source of truth for deciding whether user-facing frontend workflows are functioning as expected. It complements Playwright, Vitest, contract tests, accessibility scans, and bundle checks by making the expected workflow proof explicit.

## Release Gate Policy

A workflow is considered release-significant when it appears in the **P0** or **P1** tables below. Release-significant workflow tests must fail closed: they must not use `test.skip`, `test.fixme`, backend skip valves, or placeholder assertions. A green workflow result means the tested user can reach the intended business state, the route persists the expected context across navigation or reload, invalid actions are blocked before mutation, and API failures expose recoverable UI states.

| Gate | Required evidence |
|---|---|
| Type safety | `pnpm run check` passes. |
| Contract safety | `pnpm run test:contracts` passes and schema drift checks validate canonical OpenAPI fixtures. |
| P0 workflow safety | `pnpm run test:e2e:validation:p0` and `pnpm run test:e2e:guard` pass in CI-capable environments. |
| Broad workflow safety | `pnpm run test:e2e:validation` passes before release candidate sign-off. |
| Accessibility and resilience | P0 flows include keyboard, error, and role-state assertions through focused E2E or component tests. |
| Build and bundle confidence | `pnpm run build` and `pnpm run test:bundle-budget` pass. |

## P0 Workflows

| ID | Workflow | Primary routes | Required test evidence | Persona coverage | Resilience proof | Accessibility proof | Owner |
|---|---|---|---|---|---|---|---|
| P0-ACCOUNT-LIFECYCLE | Account-to-approved-business-case lifecycle | `/accounts`, `/workflow/prospect`, `/workflow/value-case`, `/value-case/:accountId`, `/deliverables/cases/:caseId` | `e2e/journeys/j6-account-prospect-lifecycle.spec.ts`; `e2e/journeys/j11-golden-path-business-lifecycle.spec.ts`; `e2e/journeys/j1-golden-path-backend-integrated.spec.ts` | Admin, seller, reviewer | Reload preserves account/workflow context; duplicate or invalid account submissions are blocked. | Primary forms, account picker, review dialog, and export CTA are keyboard-reachable. | Frontend Platform |
| P0-CALC-EVIDENCE | Value realization, calculation, and evidence | `/calculator/:accountId`, `/calculator/:accountId/roi`, `/workflow/calculator`, `/workflow/evidence`, `/realization/:accountId` | `e2e/journeys/j7-value-realization-and-calculation.spec.ts`; `e2e/journeys/j7-calculation-evidence-deep.spec.ts` | Seller, reviewer | Failed recalculation and missing evidence states are visible and recoverable. | Numeric inputs, validation messages, and evidence upload controls are announced. | Value Workflow |
| P0-APPROVAL-EXPORT | Approval-gated deliverables and export | `/governance`, `/governance/traces`, `/deliverables`, `/deliverables/cases/:caseId` | `e2e/journeys/j8-approval-review-gates.spec.ts`; `e2e/journeys/j8-approval-review-deep.spec.ts`; `e2e/export-workflows.spec.ts`; `e2e/export/export-workflows-deep.spec.ts` | Seller, reviewer, admin | Export remains blocked until approval; rejected items can be remediated. | Review decision controls and blocked-export messages are keyboard and screen-reader visible. | Governance |
| P0-AGENT-GOVERNANCE | Agent grounding, prompt-injection handling, and tenant-safe evidence | `/workflow/intelligence`, `/context/agents`, `/governance/evidence`, `/governance/traces` | `e2e/journeys/j9-agent-grounding-governance.spec.ts`; `e2e/journeys/j9-agent-grounding-deep.spec.ts`; `e2e/security/tenant-isolation-validation.spec.ts`; `e2e/security/tenant-isolation-deep.spec.ts` | Seller, admin, restricted user | Prompt injection is rejected; cross-tenant data is not shown; trace failure states explain remediation. | Agent response, citation, and trace regions expose useful labels and status. | AI Experience |
| P0-LAYER-VALIDATION | Layered product navigation and UI state validation | `/context/*`, `/workflow/*`, `/studio/:accountId/*`, `/command-center` | `e2e/journeys/j10-layer-ui-validation.spec.ts`; `e2e/journeys/j10-layer-ui-validation-deep.spec.ts`; `e2e/navigation.spec.ts` | Admin, seller, restricted user | Loading, empty, error, unauthorized, and success states are asserted for each layer. | Navigation, sidebar, tabs, and fallback routes are keyboard-reachable. | Frontend Platform |

## P1 Workflows

| ID | Workflow | Primary routes | Required test evidence | Risk to monitor |
|---|---|---|---|---|
| P1-INTELLIGENCE | Intelligence workspace enrichment, stakeholders, signals, and ontology match | `/intelligence/:accountId`, `/intelligence/:accountId/enrichment`, `/intelligence/:accountId/stakeholders`, `/intelligence/:accountId/signals`, `/intelligence/:accountId/ontology-match` | `e2e/journeys/j2-intelligence-workspace.spec.ts`; `e2e/contracts/account-scoped-workspaces.spec.ts` | Data freshness, account context drift, stale enrichment status. |
| P1-STUDIO | Studio workspace parity with modern workflows | `/studio/:accountId`, `/studio/:accountId/action-plan`, `/studio/:accountId/value-model`, `/studio/:accountId/narrative`, `/studio/:accountId/roi`, `/studio/:accountId/evidence` | `e2e/journeys/j3-value-studio-deliverable.spec.ts`; `e2e/value-tree-explorer.spec.ts` | Legacy route drift and inconsistent account scoping. |
| P1-CONTEXT | Context sources, extraction, ontology, formulas, models, and value packs | `/context/sources`, `/context/extraction`, `/context/ontology`, `/context/formulas`, `/context/models`, `/context/packs` | `e2e/journeys/j1-ingestion-to-value-tree.spec.ts`; `src/pages/ExtractionEngine.test.tsx`; `src/pages/ValuePacks.test.tsx`; `src/pages/formulaBuilderLogic.test.ts` | CRUD drift, importer failures, stale schema fixtures. |
| P1-SETTINGS | Tenant, team, billing, data, and governance settings | `/settings/*`, `/settings/team/*`, `/settings/billing/*`, `/settings/governance/*`, `/settings/data/*` | `e2e/admin.spec.ts`; `e2e/admin-system.spec.ts`; `e2e/contracts/settings-governance.spec.ts` | Role leakage, sensitive action exposure, audit gaps. |
| P1-PERSONAL | User profile, sessions, security, preferences, and notifications | `/personal/*` | `e2e/collaboration/collaboration-notifications-tasks.spec.ts`; `src/components/layout/GlobalLayout.test.tsx` | Low direct route coverage and session-state drift. |
| P1-INTEGRATIONS | CRM and external integration lifecycle | `/settings/data/integrations`, `/context/integrations`, `/dev/integration` | `e2e/integrations/crm-external-integrations.spec.ts`; `e2e/journeys/j17-crm-integration.spec.ts` | Mock/real API divergence and secret-handling UX. |

## P2 Watchlist

| Route or workflow | Required action |
|---|---|
| `/formula-builder` | Ensure the standalone route has explicit component or E2E coverage beyond broad navigation. |
| `/graph-explorer` | Ensure the standalone graph route has assertions for empty, success, and error states. |
| `/signup` and `/login/callback` | Keep auth lifecycle tests aligned with the deployed identity provider behavior. |
| `/dev/integration` | Keep development-only route gated and excluded from production-sensitive navigation. |

## Sprint Acceptance Checklist

| Sprint | Acceptance criteria |
|---|---|
| Sprint 1 | TypeScript, contract tests, full Vitest, build, and critical E2E guard pass locally. |
| Sprint 2 | Every P0 workflow has an owning test file, route list, persona expectation, resilience proof, and accessibility proof in this matrix. |
| Sprint 3 | Every P1 workflow has a route-family test owner and a documented risk to monitor. |
| Sprint 4 | P0 workflows include persona, accessibility, responsive navigation, and API failure-state coverage expectations. |
| Sprint 5 | Release confidence is automated through `verify:frontend`, workflow-matrix validation, bundle-budget validation, and fail-closed E2E guard checks. |
