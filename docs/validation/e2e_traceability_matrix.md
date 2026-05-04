# Fabric_4L Frontend# E2E Validation Traceability Matrix

**Last Updated:** 2026-05-04 (Sprint 4 - Release Hardening)

## Phase 2 Deep Tests (Sprint 4)

Phase 2 of the E2E validation milestone added 7 new `-deep.spec.ts` files with 78 interaction-level tests across all P0 production-gate suites:

| Deep Test File | Test Count | Test IDs | Status |
|----------------|------------|----------|--------|
| j1-golden-path-deep.spec.ts | 15 | GP-DEEP-001–015 | 74.4% pass rate |
| j10-layer-ui-validation-deep.spec.ts | 12 | L1-DEEP–L6-DEEP | Partial |
| tenant-isolation-deep.spec.ts | 12 | SEC-DEEP-001–012 | Partial |
| j9-agent-grounding-deep.spec.ts | 10 | AG-DEEP-001–010 | Partial |
| j7-calculation-evidence-deep.spec.ts | 12 | CALC-DEEP-001–012 | Full suite passing (12/12) |
| j8-approval-review-deep.spec.ts | 10 | APPROVAL-DEEP-001–010 | Full suite passing (10/10) |
| export-workflows-deep.spec.ts | 7 | EXPORT-DEEP-001–008 | Full suite passing (7/7) |

**TDD Red Phase Results:** 58 passed, 18 failed, 2 flaky (74.4% pass rate)

**Full Suites Passing:**
- Calculation/Evidence (12/12)
- Approval Gates (10/10)
- Export (7/7)

**Failure Report:** [docs/validation/deep_validation_initial_failures.md](deep_validation_initial_failures.md)

**Supporting Infrastructure:**
- e2e/helpers/validation-program.ts — 10 new deep-test helpers
- e2e/fixtures/deep-test-data.ts — rich mock data factories
- package.json: test:e2e:validation:deep and test:e2e:validation:p0:deep commands
- Anti-skip guard extended with 7 deep files + 5 required evidence entries


**Scope.** This matrix converts the master workflow inventory into an executable frontend E2E validation program for Fabric_4L. The source-of-truth workflow contract is `/home/ubuntu/upload/Pasted_content_04.txt`, and the existing repository evidence comes from the Playwright title inventory, route inventory, router configuration, journey fixture, and current canonical journey suites audited during Phase 1–2.

**Classification rule.** Existing unit tests, API contract tests, route-render tests, and component tests are acknowledged as supporting evidence, but they are **not** treated as substitutes for full user workflow validation. A workflow is marked **Full E2E** only when a user-visible path is exercised through the UI with meaningful state transitions, tenant/account context, and pass/fail assertions for the workflow outcome.

| Workflow | Suite | Existing Coverage | Gap | Priority | New Test | Status |
|---|---|---|---|---|---|---|
| Account/prospect creation through setup | Golden Path E2E | Component and partial route coverage through `ProspectSetup.behavior.test.tsx`, `/workflow/prospect`, and account route smoke coverage. | No full E2E creation path proves account setup, duplicate detection, owner assignment, value-pack assignment, readiness, and audit history. | P0 production gate | `apps/web/e2e/journeys/j6-account-prospect-lifecycle.spec.ts` | Planned |
| Account edit/archive/merge lifecycle | Golden Path E2E | Account pages exist at `/accounts` and `/accounts/:id`; keyword hits show account tests but no lifecycle journey. | Edit, archive, duplicate detection, merge, and lifecycle audit are not validated as one user workflow. | P1 core workflow | `apps/web/e2e/journeys/j6-account-prospect-lifecycle.spec.ts` | Planned |
| Value pack assignment and tenant default override | Golden Path E2E | `/context/packs`, `/settings/data/value-packs`, and value-pack components exist; route/contract coverage is shallow. | No E2E asserts assignment during account setup, tenant-default override, or downstream model behavior. | P1 core workflow | `apps/web/e2e/journeys/j6-account-prospect-lifecycle.spec.ts` | Planned |
| Website/domain ingestion to value tree | Layer-by-Layer UI Validation | `apps/web/e2e/journeys/j1-ingestion-to-value-tree.spec.ts` validates command center ingestion, job visibility, value-tree explorer, and tenant localStorage in contract mode. | Document upload edge cases, duplicate handling, unsupported/large file behavior, retry, provenance metadata, and failed states remain uncovered. | P0 production gate | `apps/web/e2e/journeys/j10-layer-ui-validation.spec.ts` | Partial |
| Document ingestion edge cases | Layer-by-Layer UI Validation | Ingestion route exists at `/context/ingestion/jobs`; source configuration tests exist; no dedicated E2E for document states. | Single/multiple upload, duplicate document, unsupported file, large file, failed ingestion, progress, retry, and source provenance are missing. | P0 production gate | `apps/web/e2e/journeys/j10-layer-ui-validation.spec.ts` | Planned |
| Extraction signal review lifecycle | Layer-by-Layer UI Validation | `/context/extraction` route and extraction-engine suite exist; intelligence signal route exists at `/intelligence/:accountId/signals`; J2 partially visits signals. | User-visible signal approval/rejection/editing, duplicate merging, evidence-backed approval, low-confidence warnings, and rerun are not exercised. | P0 production gate | `apps/web/e2e/journeys/j10-layer-ui-validation.spec.ts` | Planned |
| Account intelligence and stakeholder review | Golden Path E2E | `j2-intelligence-workspace.spec.ts` partially validates account context, signals, drivers, evidence, stakeholders, and agent message rendering. | It does not prove full review decisions, stakeholder map quality, approval state, or lifecycle continuation into model/business case. | P1 core workflow | `apps/web/e2e/journeys/j8-approval-review-gates.spec.ts` | Partial |
| Knowledge graph exploration | Layer-by-Layer UI Validation | `/context/ontology/graph`, `/graph-explorer`, `/context/value-trees/explorer`, and `graph-explorer.spec.ts` exist; J1 checks value-tree node rendering. | Entity detail, relationship exploration, tenant-scoped search, graph refresh after extraction, provenance on nodes/edges, and empty graph handling are incomplete. | P1 core workflow | `apps/web/e2e/journeys/j10-layer-ui-validation.spec.ts` | Partial |
| Agent hypothesis generation | Agent Grounding and Governance | Agent routes and streams are covered partially by J2 and `agent-workflow-lifecycle.spec.ts`. | No E2E proves grounded factual claims, assumptions/inferences labeling, unsupported-claim refusal, no fabricated citations, or audit logging. | P0 production gate | `apps/web/e2e/journeys/j9-agent-grounding-governance.spec.ts` | Planned |
| Agent recommendation accept/reject/edit | Agent Grounding and Governance | Existing tests render agent output but do not assert recommendation lifecycle outcomes. | Accept, reject, edit, checkpoint/resume, structured error, and audit-event side effects are not validated. | P1 core workflow | `apps/web/e2e/journeys/j9-agent-grounding-governance.spec.ts` | Planned |
| Prompt-injection refusal through uploaded content | Security and Tenant Isolation; Agent Grounding and Governance | Keyword audit shows zero existing `grounding` and zero `refusal` hits in E2E/source inventory. | UI adversarial-file path is completely missing; agent must not obey instructions embedded in customer documents. | P0 production gate | `apps/web/e2e/journeys/j9-agent-grounding-governance.spec.ts` | Planned |
| Assumption and ground-truth lifecycle | Layer-by-Layer UI Validation | `/hypothesis/:accountId/assumptions`, `/governance/evidence`, and ground-truth API contract tests exist. | Source-of-truth selection, validation status, source lineage, and approved/rejected ground-truth lifecycle are not validated through UI. | P1 core workflow | `apps/web/e2e/journeys/j10-layer-ui-validation.spec.ts` | Planned |
| Benchmark policy and stale benchmark behavior | Layer-by-Layer UI Validation; Calculation and Evidence Integrity | `/governance/benchmarks`, benchmark API tests, and governance route smoke tests exist. | Benchmark application to formulas, confidence, stale warnings, approved customer override, and policy enforcement are not validated as a workflow. | P1 core workflow | `apps/web/e2e/journeys/j7-value-realization-and-calculation.spec.ts` | Planned |
| Value driver tree build and evidence mapping | Golden Path E2E; Calculation and Evidence Integrity | `/drivers/:accountId` and studio evidence/value-model routes exist; J2 partially visits drivers/evidence. | User-driven value tree build, evidence-to-driver mapping, unsupported evidence warning, and audit/version trail are incomplete. | P0 production gate | `apps/web/e2e/journeys/j7-value-realization-and-calculation.spec.ts` | Planned |
| Formula selection and scenario modeling | Calculation and Evidence Integrity | `formula-builder.spec.ts`, formula contract tests, calculator routes, and `/calculator/:accountId/roi` exist. | Required input validation, invalid numeric rejection, currency/time-period consistency, three-scenario reproducibility, reload stability, ROI/payback stability, and version history are not fully E2E. | P0 production gate | `apps/web/e2e/journeys/j7-value-realization-and-calculation.spec.ts` | Planned |
| Business case generation | Golden Path E2E | `j3-value-studio-deliverable.spec.ts`, `business-case.spec.ts`, and deliverable routes exist. | Existing tests are partial and do not prove approved business-case generation from validated hypotheses, formulas, evidence, and scenarios. | P0 production gate | `apps/web/e2e/journeys/j8-approval-review-gates.spec.ts` | Planned |
| Business case claim traceability | Agent Grounding and Governance; Calculation and Evidence Integrity | `decision-trace.spec.ts` and governance trace pages exist. | No E2E proves every business-case claim maps to evidence, benchmark, or explicit assumption after the golden path. | P0 production gate | `apps/web/e2e/journeys/j9-agent-grounding-governance.spec.ts` | Planned |
| Review and approval gates | Golden Path E2E; Security and Tenant Isolation | Admin/governance tests expose approval queue tabs and governance routes. | Hypothesis approval, formula review, model review, reviewer request changes, reject unsupported claims, user resubmission, approval history, export gating, and CRM push gating are not exercised end-to-end. | P0 production gate | `apps/web/e2e/journeys/j8-approval-review-gates.spec.ts` | Planned |
| Export and shared deliverable access | Golden Path E2E; Security and Tenant Isolation | Export appears in several route/surface tests; deliverable views exist at CFO/executive/technical routes. | Export after approval, export blocked before approval, unauthorized export blocking, shared executive-buyer view, and download/share state are not validated. | P0 production gate | `apps/web/e2e/export-workflows.spec.ts` | Planned |
| CRM and external integrations | Golden Path E2E; Operational Resilience | `/context/integrations`, `/settings/data/integrations`, and integration components exist. | CRM connect, import account/opportunity/contacts, push summary/ROI/business-case link, permission/field-mapping failures, retry failed sync, and sync log remain missing as workflows. | P1 core workflow | `apps/web/e2e/journeys/j6-account-prospect-lifecycle.spec.ts` and `apps/web/e2e/resilience/operational-resilience.spec.ts` | Planned |
| Collaboration, notifications, and tasks | Operational Resilience | Personal notifications route exists, notification UI exists in layout, but keyword audit found zero `collaboration` hits and sparse task coverage. | Teammate invite, reviewer assignment, comments, mentions, resolve comment, review/ingestion notifications, task create/assign/complete/overdue are missing. | P1 core workflow | `apps/web/e2e/collaboration/collaboration-notifications-tasks.spec.ts` | Planned |
| Value realization lifecycle | Golden Path E2E; Calculation and Evidence Integrity | `/realization/:accountId` route and `RealizationShell.tsx` exist; keyword hits are sparse. | Conversion from pre-sale case, target outcomes, baselines, metric owner, actuals, projected vs realized comparison, report, renewal narrative, expansion, and unrealized-value risk are not validated. | P1 core workflow | `apps/web/e2e/journeys/j7-value-realization-and-calculation.spec.ts` | Planned |
| Tenant isolation across account, documents, graph, evidence, agent, search, and export | Security and Tenant Isolation | `j5-tier-gated-security.spec.ts`, auth lifecycle, tier-gated navigation, settings-governance, and backend security tests provide partial coverage. | Cross-tenant direct URL, document URL, graph context, evidence search, agent leak refusal, forged tenant ID, missing tenant fail-closed, and export blocking need consolidated UI E2E coverage. | P0 production gate | `apps/web/e2e/security/tenant-isolation-validation.spec.ts` | Planned |
| Role and tier enforcement for write operations | Security and Tenant Isolation | Tier-navigation and admin settings access tests exist. | Read-only write blocking, non-admin settings denial, unauthorized export, and approval-gated writes are not consistently validated at workflow level. | P0 production gate | `apps/web/e2e/security/tenant-isolation-validation.spec.ts` | Planned |
| Operational empty/failure/retry states | Operational Resilience | Some generic page empty/skeleton/error state tests exist. | Empty account, no documents, failed ingestion retry, partial extraction warning, stale benchmark warning, agent service unavailable, graph service unavailable, CRM sync failure, export failure, long-running job progress, cancellation, and audit event for failed critical workflow are incomplete. | P1 core workflow | `apps/web/e2e/resilience/operational-resilience.spec.ts` | Planned |
| Resume partially completed workflow and unsaved-work protection | Operational Resilience | Workspace routes and persisted selected account exist. | Resume, checkpoint, unsaved changes warning, and partial completion continuity are not validated. | P1 core workflow | `apps/web/e2e/resilience/operational-resilience.spec.ts` | Planned |
| Persona journey: Sales Rep | Golden Path E2E | Individual surfaces exist; no persona-oriented journey suite. | Create account, import discovery notes, review signals, generate hypotheses, build first-pass case, and push CRM summary are not validated as a persona workflow. | P1 core workflow | `apps/web/e2e/personas/persona-journeys.spec.ts` | Planned |
| Persona journey: Value Engineer | Calculation and Evidence Integrity | Formula/calculator/evidence surfaces exist. | Evidence review, driver refinement, formula selection, assumption validation, scenario build, and CFO-ready case workflow are not validated. | P1 core workflow | `apps/web/e2e/personas/persona-journeys.spec.ts` | Planned |
| Persona journey: Sales Leader | Agent Grounding and Governance; Approval Gates | Governance and deliverable surfaces exist. | Strategic account review, weak evidence identification, pipeline value impact, and high-value approval are not validated. | P2 important workflow | `apps/web/e2e/personas/persona-journeys.spec.ts` | Planned |
| Persona journey: Customer Success Manager | Value Realization | Realization route exists. | Actual outcome tracking, renewal narrative, and expansion opportunity journey are missing. | P2 important workflow | `apps/web/e2e/personas/persona-journeys.spec.ts` | Planned |
| Persona journey: Admin | Security and Tenant Isolation | Admin settings route tests exist and are stronger than most persona coverage. | User/role/value-pack/integration configuration plus audit/security-event review is route/contract-heavy, not a unified admin workflow. | P1 core workflow | `apps/web/e2e/personas/persona-journeys.spec.ts` | Partial |
| Persona journey: Executive Buyer | Golden Path E2E | `/deliverables/views/executive` exists. | Shared approved case, executive summary, financial impact, assumptions, evidence, and download/share workflow are not validated. | P2 important workflow | `apps/web/e2e/personas/persona-journeys.spec.ts` | Planned |

## Six-Suite Validation Milestone Plan

| Suite | Purpose | P0/P1 Coverage Additions | Primary New Files |
|---|---|---|---|
| Golden Path E2E | Validate the complete business lifecycle from account/prospect setup to approved and shared business case. | Account/prospect lifecycle, value-pack assignment, ingestion, intelligence review, hypothesis approval, driver/evidence mapping, formula/scenario calculation, business-case review/approval, export, optional CRM push. | `j6-account-prospect-lifecycle.spec.ts`, `j8-approval-review-gates.spec.ts`, `export-workflows.spec.ts` |
| Layer-by-Layer UI Validation | Validate L1–L6 as user-facing workflows while preserving architectural layer boundaries. | L1 ingestion edge cases, L2 extraction review, L3 graph provenance/search, L4 agent UI failure, L5 ground-truth lifecycle, L6 benchmark warning/policy. | `j10-layer-ui-validation.spec.ts` |
| Security and Tenant Isolation | Validate UI/backend boundary behavior, fail-closed tenant context, role restrictions, and cross-tenant leak prevention. | Cross-tenant account/document/graph/evidence/export/agent blocking, forged/missing tenant context, read-only and non-admin enforcement. | `security/tenant-isolation-validation.spec.ts` |
| Agent Grounding and Governance | Validate grounded, auditable agent behavior under normal and adversarial inputs. | Evidence citations, assumptions/inferences labels, unsupported-claim refusal, fabricated-citation refusal, prompt-injection refusal, recommendation accept/reject/edit audit event. | `j9-agent-grounding-governance.spec.ts` |
| Calculation and Evidence Integrity | Validate reproducible economic modeling and claim-level evidence lineage. | Input validation, scenario reproducibility, customer override, ROI/payback stability, unapproved assumption blocking, claim traceability. | `j7-value-realization-and-calculation.spec.ts` |
| Operational Resilience | Validate failure, recovery, retry, empty, notification, and resume behavior. | Empty account, failed ingestion retry, partial extraction, stale benchmark, service failures, CRM/export retry, resume and unsaved-work protection, audit for failed critical workflow. | `resilience/operational-resilience.spec.ts`, `collaboration/collaboration-notifications-tasks.spec.ts` |

## Immediate Implementation Ordering

The next implementation phase should create the **P0 production-gate executable tests first**, then add P1 suites that expose the biggest readiness gaps. The recommended order is: `j6` account/prospect lifecycle, `j8` approval/review gates, `j9` agent grounding/refusal, `j7` calculation/evidence/value-realization, security tenant isolation, layer UI validation, collaboration/tasks, operational resilience, export workflows, and persona journeys.

No critical-path test should use `test.skip`, `test.fixme`, or silent conditional bypassing. If a workflow is not implemented, the test should fail with a useful user-visible assertion and be recorded in the failure report rather than weakened.

## Deep Validation Coverage (Phase 2 — Interaction-Level Tests)

**Date:** 2026-05-28 | **Status:** TDD Red Phase Complete

Deep validation adds 78 interaction-level tests in 7 new `-deep.spec.ts` files that exercise form submissions, state transitions, approval workflows, security boundaries, and agent behavior. These complement the existing 60+ route-surface tests.

| Deep Test File | Suite | Tests | Passed | Failed | Flaky | Traceability |
|---|---|---|---|---|---|---|
| `e2e/journeys/j1-golden-path-deep.spec.ts` | Golden Path E2E | 15 | 7 | 8 | 0 | GP-DEEP-001–015 |
| `e2e/journeys/j10-layer-ui-validation-deep.spec.ts` | Layer UI | 12 | 9 | 3 | 0 | L1-DEEP–L6-DEEP |
| `e2e/security/tenant-isolation-deep.spec.ts` | Security | 12 | 9 | 1 | 2 | SEC-DEEP-001–012 |
| `e2e/journeys/j9-agent-grounding-deep.spec.ts` | Agent Grounding | 10 | 7 | 3 | 0 | AG-DEEP-001–010 |
| `e2e/journeys/j7-calculation-evidence-deep.spec.ts` | Calculation | 12 | 12 | 0 | 0 | CALC-DEEP-001–012 |
| `e2e/journeys/j8-approval-review-deep.spec.ts` | Approval Gates | 10 | 10 | 0 | 0 | APPROVAL-DEEP-001–010 |
| `e2e/export/export-workflows-deep.spec.ts` | Export Gates | 7 | 7 | 0 | 0 | EXPORT-DEEP-001–008 |
| **Total** | | **78** | **58** | **18** | **2** | |

**Pass rate:** 74.4% first-attempt (76.9% including flaky). See `docs/validation/deep_validation_initial_failures.md` for classified failure report.

**Commands:**
- `pnpm run test:e2e:validation:deep` — all deep tests
- `pnpm run test:e2e:validation:p0:deep` — P0 deep tests only

**Supporting files:**
- `e2e/helpers/validation-program.ts` — deep-test utility helpers (form submission, workflow steps, disabled actions, API call tracking, audit events, sequential mocks, role switching)
- `e2e/fixtures/deep-test-data.ts` — rich mock data factories (accounts, business cases, signals, drivers, evidence, ROI scenarios, approvals, benchmarks, ground truth, agent responses)

## Backend-Integrated Validation Coverage (Phase 3 — Sprint 3)

**Date:** 2026-05-04 | **Status:** Infrastructure Complete, Tests Created

Backend-integrated tests use real backend data seeded by `scripts/db/seed-e2e-data.ts` instead of mock data. Tests require `PLAYWRIGHT_BACKEND_URL` to be set and fail closed if the backend is unavailable.

| Backend Test File | Suite | Tests | Traceability | Backend Data Source |
|---|---|---|---|---|
| `e2e/journeys/j1-golden-path-backend-integrated.spec.ts` | Golden Path E2E | 12 (3 skipped) | GP-BI-001–015 | `scripts/fixtures/meridian-automotive.ts` |

**Seeded Data:**
- Account: acct-meridian-001 (Meridian Automotive)
- Case: case-meridian-e2e-001
- Tenant: 00000000-0000-4000-e2e0-000000000001
- 5 signals, 3 drivers, 4 evidence items, 4 stakeholders

**Commands:**
- `pnpm run test:e2e:backend` — backend-integrated tests only
- Requires: `PLAYWRIGHT_BACKEND_URL=http://localhost:8004` (or other backend URL)
- Auto-seeds data via global-setup.ts before test execution
