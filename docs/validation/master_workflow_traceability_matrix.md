# Fabric_4L Master Workflow Traceability Matrix and Validation Execution Plan

Create a master validation control plane that maps 30 workflow categories (300+ workflows) to existing test coverage, defines validation gates, execution cadence, gap prioritization, and recommends the next implementation batch focused on P0 stabilization.

## Matrix Maintenance Contract

- This document is the canonical release-level workflow inventory for Fabric_4L.
- The frontend-focused subset remains in `apps/web/docs/frontend-workflow-coverage-matrix.md`.
- Backend object, status, and event lineage remains in `docs/contracts/workflow-traceability-matrix.md`.
- The matrix must fail closed in CI via `python3 scripts/ci/assert_master_workflow_traceability.py` or `make check-workflow-matrix`.
- Release-significant gate commands listed here must resolve to current repository commands rather than stale ad hoc invocations.

## Executive Master Traceability Matrix

| ID | Workflow Category | Risk | Priority | Current Coverage | Test Type | Gate | Status | Gap | Next Action |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Authentication, Tenant, and Workspace Access | Critical | P0 | Deep frontend E2E + route smoke | Deep frontend E2E, Route smoke | P0 production gate | Partial (2 flaky) | MFA enable, session expiry, deep link handling, role enforcement | Fix SEC-DEEP-007/008 flaky tests, add missing auth edge cases |
| 2 | Account and Prospect Setup | High | P0 | Component + partial route | Component, Route smoke | P0 production gate | Planned | Full E2E creation path, duplicate detection, merge, audit history | Implement j6-account-prospect-lifecycle.spec.ts E2E |
| 3 | Data Ingestion Workflows — Layer 1 | High | P0 | Deep frontend E2E + route smoke | Deep frontend E2E, Route smoke | P0 production gate | Partial (3 failures) | Document edge cases, retry, provenance metadata, failed states | Fix GP-DEEP-003, L1-DEEP-002 failures, add missing edge cases |
| 4 | Extraction and Signal Detection — Layer 2 | High | P0 | Deep frontend E2E + route smoke | Deep frontend E2E, Route smoke | P0 production gate | Partial (2 failures) | Signal approval/rejection, duplicate merging, evidence backing, rerun | Fix GP-DEEP-006, L2-DEEP-002 failures, add signal lifecycle |
| 5 | Knowledge Graph and Context Engine — Layer 3 | Medium | P1 | Route smoke + partial deep | Route smoke, Deep frontend E2E | P1 core lifecycle | Partial | Entity detail, relationship exploration, provenance, graph refresh | Enhance j10-layer-ui-validation-deep.spec.ts L3 tests |
| 6 | Value Pack Selection and Governance | Medium | P1 | Route smoke | Route smoke | P1 core lifecycle | Planned | Pack assignment, tenant default override, pack-driven classification, versioning | Add pack governance E2E to j6 or dedicated suite |
| 7 | Prospect Intelligence Workflow | High | P0 | Deep frontend E2E + partial route | Deep frontend E2E, Route smoke | P0 production gate | Partial | Signal review, agent explanation, evidence links, hypothesis promotion | Enhance j2-intelligence-workspace.spec.ts with deep interactions |
| 8 | Stakeholder Mapping | Medium | P1 | Partial route | Route smoke | P1 core lifecycle | Planned | Manual stakeholder CRUD, linking to pains/initiatives, messaging | Add stakeholder lifecycle to j2 or dedicated suite |
| 9 | Hypothesis Generation Workflow — Layer 4 | Critical | P0 | Deep frontend E2E + partial route | Deep frontend E2E, Route smoke | P0 production gate | Partial (3 failures) | Grounded claims, assumption labeling, refusal, evidence backing | Fix AG-DEEP-001/002/009 failures, enhance grounding tests |
| 10 | Value Driver Tree Workflow | High | P0 | Partial route | Route smoke | P0 production gate | Planned | Driver CRUD, lever mapping, evidence linkage, priority changes | Implement j7-value-realization-and-calculation.spec.ts driver tests |
| 11 | Evidence Matching Workflow | High | P0 | Deep frontend E2E (passing) | Deep frontend E2E | P0 production gate | Passing | None - CALC-DEEP-001–012 all pass | Maintain passing suite, add evidence CRUD edge cases |
| 12 | Benchmark and Ground Truth Workflow — Layers 5 and 6 | High | P0 | Deep frontend E2E + route smoke | Deep frontend E2E, Route smoke | P0 production gate | Partial (1 failure) | Benchmark application, stale warnings, ground-truth lifecycle, policy | Fix L6-DEEP-001 failure, add benchmark governance E2E |
| 13 | Formula Selection and Calculation Workflow | Critical | P0 | Deep frontend E2E (passing) | Deep frontend E2E | P0 production gate | Passing | None - CALC-DEEP-001–012 all pass | Maintain passing suite, add formula selection edge cases |
| 14 | Value Calculator Workflow | Critical | P0 | Deep frontend E2E (passing) | Deep frontend E2E | P0 production gate | Passing | None - CALC-DEEP-001–012 all pass | Maintain passing suite, add scenario CRUD edge cases |
| 15 | Business Case Generation Workflow | Critical | P0 | Deep frontend E2E + partial route | Deep frontend E2E, Route smoke | P0 production gate | Partial (2 failures) | Template selection, audience targeting, claim traceability, export | Fix GP-DEEP-013/015 failures, enhance business case E2E |
| 16 | Narrative and Proposal Workflow | Medium | P1 | Partial route | Route smoke | P1 core lifecycle | Planned | Narrative generation, tone adjustment, claim grounding, versioning | Add narrative workflow to j8 or dedicated suite |
| 17 | Agentic Chat and Right-Rail Workflow | Critical | P0 | Deep frontend E2E + partial route | Deep frontend E2E, Route smoke | P0 production gate | Partial (3 failures) | Agent citations, fact/inference distinction, refusal, recommendation lifecycle | Fix AG-DEEP-001/002/009 failures, enhance agent E2E |
| 18 | Review, Approval, and Governance Workflow | Critical | P0 | Deep frontend E2E (passing) | Deep frontend E2E | P0 production gate | Passing | None - APPROVAL-DEEP-001–010 all pass | Maintain passing suite, add policy configuration E2E |
| 19 | Versioning, Audit, and Traceability | Critical | P0 | Partial route | Route smoke | P0 production gate | Planned | Version history, comparison, source lineage, audit trail export | Add audit/traceability E2E to governance suite |
| 20 | Collaboration Workflow | Medium | P2 | Partial route | Route smoke | P2 important workflow | Planned | Team invite, comments, mentions, notifications, tasks | Implement collaboration-notifications-tasks.spec.ts |
| 21 | CRM and External System Workflow | Medium | P1 | Partial route | Route smoke | P1 core lifecycle | Planned | CRM connect, import, push, sync log, retry, field mapping | Implement crm-external-integrations.spec.ts |
| 22 | Value Realization Workflow | Medium | P1 | Partial route | Route smoke | P1 core lifecycle | Planned | Pre-sale to post-sale conversion, outcomes tracking, variance analysis | Enhance j7-value-realization-and-calculation.spec.ts |
| 23 | Search and Retrieval Workflow | Medium | P1 | Partial route | Route smoke | P1 core lifecycle | Planned | Cross-tenant search, role-based filtering, result context landing | Add search workflow to j10 or dedicated suite |
| 24 | Notifications and Task Workflow | Low | P2 | Partial route | Route smoke | P2 important workflow | Planned | Notification types, task lifecycle, filtering, overdue handling | Implement collaboration-notifications-tasks.spec.ts |
| 25 | Admin Configuration Workflow | Medium | P1 | Route smoke | Route smoke | P1 core lifecycle | Partial | User/role management, tenant settings, value packs, integrations, policies | Enhance admin.spec.ts with configuration workflows |
| 26 | Security and Compliance User Workflows | Critical | P0 | Deep frontend E2E + route smoke | Deep frontend E2E, Route smoke | P0 production gate | Partial (1 failure + 2 flaky) | Unauthorized access, PII handling, prompt injection, cross-tenant leak | Fix SEC-DEEP-002 failure, fix SEC-DEEP-007/008 flaky, add security E2E |
| 27 | Error, Empty State, and Recovery Workflows | High | P1 | Partial route | Route smoke | P1 core lifecycle | Planned | Empty states, service failures, retry, resume, unsaved work protection | Implement operational-resilience.spec.ts |
| 28 | Full End-to-End Golden Path | Critical | P0 | Deep frontend E2E + backend-gated | Deep frontend E2E, Backend-gated E2E | P0 production gate | Partial (8 failures) | Complete golden path from account to CRM push with real services | Fix GP-DEEP-001/003/004/005/006/013/015 failures, run j11 against L1-L6 |
| 29 | Full End-to-End Adversarial Path | Critical | P0 | None | None | P0 production gate | Missing | Adversarial input handling, prompt injection, cross-tenant leak prevention | Implement adversarial path test suite (security) |
| 30 | Persona-Based Validation Journeys | Medium | P1 | Partial route | Route smoke | P1 core lifecycle | Planned | Sales Rep, Value Engineer, Sales Leader, CSM, Admin, Executive Buyer | Implement persona-journeys.spec.ts |

## P0/P1 Detailed Matrix

### Authentication, Tenant, and Workspace Access (P0, Critical)

| ID | Workflow | Risk | Priority | Current Coverage | Test Type | Test File(s) | Gate | Status | Gap | Next Action |
|---|---|---|---|---|---|---|---|---|---|---|
| 1.1 | User signs up or is provisioned | High | P0 | Route smoke | Route smoke | auth-lifecycle.spec.ts | P0 | Passing | Provisioning flow not validated | Add provisioning E2E |
| 1.2 | User logs in with email/password or SSO | High | P0 | Deep frontend E2E | Deep frontend E2E | j0-auth-session.spec.ts | P0 | Passing | None | Maintain |
| 1.3 | User logs out successfully | Medium | P1 | Route smoke | Route smoke | auth-lifecycle.spec.ts | P1 | Passing | None | Maintain |
| 1.4 | User resets password | Medium | P1 | None | None | None | P1 | Missing | Password reset flow not validated | Add password reset E2E |
| 1.5 | User enables or verifies MFA | High | P0 | None | None | None | P0 | Missing | MFA enable/verify not validated | Add MFA E2E |
| 1.6 | User switches between workspaces or tenants | High | P0 | Route smoke | Route smoke | auth-lifecycle.spec.ts | P0 | Passing | Tenant switch validation shallow | Enhance tenant switch E2E |
| 1.7 | User attempts unauthorized tenant access | Critical | P0 | Deep frontend E2E | Deep frontend E2E | tenant-isolation-deep.spec.ts | P0 | Partial (SEC-DEEP-002 failure) | Foreign account driver route error state | Fix SEC-DEEP-002 |
| 1.8 | User with read-only role attempts write action | Critical | P0 | Deep frontend E2E | Deep frontend E2E | tenant-isolation-deep.spec.ts | P0 | Flaky (SEC-DEEP-007/008) | Timing race in role switch | Fix SEC-DEEP-007/008 flaky |
| 1.9 | User with admin role manages workspace settings | Medium | P1 | Route smoke | Route smoke | admin.spec.ts | P1 | Passing | Settings workflow not end-to-end | Enhance admin workflow E2E |
| 1.10 | User session expires and re-authentication required | High | P0 | None | None | None | P0 | Missing | Session expiry handling not validated | Add session expiry E2E |
| 1.11 | User opens deep link while unauthenticated and redirects | Medium | P1 | Route smoke | Route smoke | auth-lifecycle.spec.ts | P1 | Passing | Deep link edge cases not covered | Add deep link edge cases |
| 1.12 | User opens deep link without permission and receives safe error | High | P0 | Route smoke | Route smoke | auth-lifecycle.spec.ts | P0 | Passing | Error message validation shallow | Enhance error validation |

### Account and Prospect Setup (P0, High)

| ID | Workflow | Risk | Priority | Current Coverage | Test Type | Test File(s) | Gate | Status | Gap | Next Action |
|---|---|---|---|---|---|---|---|---|---|---|
| 2.1 | User creates a new prospect account | High | P0 | Component | Component, Route smoke | ProspectSetup.behavior.test.tsx, /workflow/prospect | P0 | Planned | Full E2E creation path missing | Implement j6-account-prospect-lifecycle.spec.ts |
| 2.2 | User imports an account from CRM | Medium | P1 | None | None | None | P1 | Missing | CRM import flow not validated | Add CRM import E2E |
| 2.3 | User manually enters account details | High | P0 | Component | Component, Route smoke | ProspectSetup.behavior.test.tsx, /workflow/prospect | P0 | Planned | Full manual entry E2E missing | Implement j6-account-prospect-lifecycle.spec.ts |
| 2.4 | User enriches an account using company website/domain | High | P0 | Deep frontend E2E | Deep frontend E2E | j1-golden-path-deep.spec.ts | P0 | Partial (GP-DEEP-003 failure) | Domain ingestion from command center | Fix GP-DEEP-003 |
| 2.5 | User assigns an industry or value pack to the account | High | P0 | Route smoke | Route smoke | /context/packs, /settings/data/value-packs | P0 | Planned | Value pack assignment E2E missing | Add pack assignment to j6 |
| 2.6 | User overrides tenant default value pack for specific account | Medium | P1 | None | None | None | P1 | Missing | Override workflow not validated | Add override E2E to j6 |
| 2.7 | User edits account metadata | Medium | P1 | Route smoke | Route smoke | /accounts, /accounts/:id | P1 | Planned | Edit workflow E2E missing | Add edit E2E to j6 |
| 2.8 | User deletes or archives an account | Medium | P1 | Route smoke | Route smoke | /accounts, /accounts/:id | P1 | Planned | Delete/archive E2E missing | Add lifecycle E2E to j6 |
| 2.9 | User views account summary | Low | P2 | Route smoke | Route smoke | /accounts, /accounts/:id | P2 | Passing | None | Maintain |
| 2.10 | User sees account-level readiness/completeness score | Medium | P1 | Route smoke | Route smoke | /accounts/:id | P1 | Planned | Readiness score validation missing | Add readiness E2E to j6 |
| 2.11 | User handles duplicate account detection | High | P0 | None | None | None | P0 | Missing | Duplicate detection workflow not validated | Add duplicate detection E2E |
| 2.12 | User merges duplicate accounts | High | P0 | None | None | None | P0 | Missing | Merge workflow not validated | Add merge E2E to j6 |
| 2.13 | User views audit history for account changes | Medium | P1 | None | None | None | P1 | Missing | Audit history E2E missing | Add audit E2E to j6 |

### Data Ingestion Workflows — Layer 1 (P0, High)

| ID | Workflow | Risk | Priority | Current Coverage | Test Type | Test File(s) | Gate | Status | Gap | Next Action |
|---|---|---|---|---|---|---|---|---|---|---|
| 3.1 | User uploads a document | High | P0 | Deep frontend E2E | Deep frontend E2E | j1-golden-path-deep.spec.ts | P0 | Partial | Single upload validated, edge cases missing | Add edge cases to j10 |
| 3.2 | User uploads multiple documents | High | P0 | None | None | None | P0 | Missing | Multiple upload workflow not validated | Add to j10-layer-ui-validation-deep.spec.ts |
| 3.3 | User uploads unsupported file types | Medium | P1 | None | None | None | P1 | Missing | Unsupported file handling not validated | Add to j10-layer-ui-validation-deep.spec.ts |
| 3.4 | User uploads very large files | Medium | P1 | None | None | None | P1 | Missing | Large file handling not validated | Add to j10-layer-ui-validation-deep.spec.ts |
| 3.5 | User uploads duplicate files | Medium | P1 | None | None | None | P1 | Missing | Duplicate detection not validated | Add to j10-layer-ui-validation-deep.spec.ts |
| 3.6 | User imports content from a website | High | P0 | Deep frontend E2E | Deep frontend E2E | j1-golden-path-deep.spec.ts | P0 | Partial (GP-DEEP-003 failure) | Domain ingestion command center | Fix GP-DEEP-003 |
| 3.7 | User imports CRM records | Medium | P1 | None | None | None | P1 | Missing | CRM import workflow not validated | Add to j10 or CRM suite |
| 3.8 | User imports call transcripts | Medium | P1 | None | None | None | P1 | Missing | Transcript import not validated | Add to j10-layer-ui-validation-deep.spec.ts |
| 3.9 | User imports sales notes | Medium | P1 | None | None | None | P1 | Missing | Notes import not validated | Add to j10-layer-ui-validation-deep.spec.ts |
| 3.10 | User imports customer emails or meeting summaries | Medium | P1 | None | None | None | P1 | Missing | Email/summary import not validated | Add to j10-layer-ui-validation-deep.spec.ts |
| 3.11 | User connects an external data source | Medium | P1 | Route smoke | Route smoke | /context/integrations | P1 | Planned | Connection workflow E2E missing | Add to integrations suite |
| 3.12 | User disconnects an external data source | Medium | P1 | Route smoke | Route smoke | /context/integrations | P1 | Planned | Disconnection workflow E2E missing | Add to integrations suite |
| 3.13 | User views ingestion status | High | P0 | Deep frontend E2E | Deep frontend E2E | j1-golden-path-deep.spec.ts | P0 | Partial (GP-DEEP-004 failure) | Job progress monitoring | Fix GP-DEEP-004 |
| 3.14 | User retries a failed ingestion | High | P0 | Deep frontend E2E | Deep frontend E2E | j10-layer-ui-validation-deep.spec.ts | P0 | Partial (L1-DEEP-002 failure) | Retry button not exposed | Fix L1-DEEP-002 |
| 3.15 | User cancels an in-progress ingestion | Medium | P1 | None | None | None | P1 | Missing | Cancellation workflow not validated | Add to j10-layer-ui-validation-deep.spec.ts |
| 3.16 | User sees partial ingestion warnings | Medium | P1 | None | None | None | P1 | Missing | Partial ingestion handling not validated | Add to j10-layer-ui-validation-deep.spec.ts |
| 3.17 | User sees provenance for every ingested item | High | P0 | Route smoke | Route smoke | /context/ingestion/jobs | P0 | Planned | Provenance validation E2E missing | Add to j10-layer-ui-validation-deep.spec.ts |
| 3.18 | User verifies source metadata, timestamps, and ownership | Medium | P1 | None | None | None | P1 | Missing | Metadata validation not validated | Add to j10-layer-ui-validation-deep.spec.ts |
| 3.19 | User confirms tenant isolation on ingested content | Critical | P0 | Deep frontend E2E | Deep frontend E2E | tenant-isolation-deep.spec.ts | P0 | Passing | None | Maintain |

### Extraction and Signal Detection — Layer 2 (P0, High)

| ID | Workflow | Risk | Priority | Current Coverage | Test Type | Test File(s) | Gate | Status | Gap | Next Action |
|---|---|---|---|---|---|---|---|---|---|---|
| 4.1 | User runs extraction on uploaded content | High | P0 | Route smoke | Route smoke | /context/extraction | P0 | Passing | None | Maintain |
| 4.2 | User runs extraction on website content | High | P0 | Route smoke | Route smoke | /context/extraction | P0 | Passing | None | Maintain |
| 4.3 | User runs extraction on CRM opportunity data | Medium | P1 | None | None | None | P1 | Missing | CRM extraction not validated | Add to j10 or CRM suite |
| 4.4 | User extracts pains, initiatives, metrics, stakeholders, risks, and desired outcomes | High | P0 | Route smoke | Route smoke | /context/extraction | P0 | Passing | None | Maintain |
| 4.5 | User reviews AI-extracted signals | High | P0 | Deep frontend E2E | Deep frontend E2E | j1-golden-path-deep.spec.ts | P0 | Partial (GP-DEEP-005 failure) | Signal review with source/confidence | Fix GP-DEEP-005 |
| 4.6 | User approves a signal | High | P0 | Deep frontend E2E | Deep frontend E2E | j1-golden-path-deep.spec.ts | P0 | Partial (GP-DEEP-006 failure) | Approve/reject action buttons | Fix GP-DEEP-006 |
| 4.7 | User rejects a signal | High | P0 | Deep frontend E2E | Deep frontend E2E | j1-golden-path-deep.spec.ts | P0 | Partial (GP-DEEP-006 failure) | Approve/reject action buttons | Fix GP-DEEP-006 |
| 4.8 | User edits a signal | Medium | P1 | None | None | None | P1 | Missing | Signal edit workflow not validated | Add to j10-layer-ui-validation-deep.spec.ts |
| 4.9 | User merges duplicate signals | Medium | P1 | None | None | None | P1 | Missing | Signal merge workflow not validated | Add to j10-layer-ui-validation-deep.spec.ts |
| 4.10 | User marks a signal as low-confidence | High | P0 | Deep frontend E2E | Deep frontend E2E | j10-layer-ui-validation-deep.spec.ts | P0 | Partial (L2-DEEP-002 failure) | Low-confidence warning badge | Fix L2-DEEP-002 |
| 4.11 | User filters signals by source, confidence, stakeholder, value category, or value pack | Medium | P1 | Route smoke | Route smoke | /intelligence/:accountId/signals | P1 | Passing | None | Maintain |
| 4.12 | User views supporting evidence for a signal | High | P0 | Route smoke | Route smoke | /intelligence/:accountId/signals | P0 | Passing | None | Maintain |
| 4.13 | User opens source citation from a signal | High | P0 | Route smoke | Route smoke | /intelligence/:accountId/signals | P0 | Passing | None | Maintain |
| 4.14 | User validates signal-to-evidence grounding | High | P0 | Route smoke | Route smoke | /intelligence/:accountId/signals | P0 | Passing | None | Maintain |
| 4.15 | User reruns extraction after adding new documents | Medium | P1 | None | None | None | P1 | Missing | Rerun workflow not validated | Add to j10-layer-ui-validation-deep.spec.ts |
| 4.16 | User compares extraction results before and after new evidence | Medium | P1 | None | None | None | P1 | Missing | Comparison workflow not validated | Add to j10-layer-ui-validation-deep.spec.ts |
| 4.17 | User handles conflicting evidence | Medium | P1 | None | None | None | P1 | Missing | Conflict resolution not validated | Add to j10-layer-ui-validation-deep.spec.ts |
| 4.18 | User handles unsupported or noisy documents | Medium | P1 | None | None | None | P1 | Missing | Noisy document handling not validated | Add to j10-layer-ui-validation-deep.spec.ts |
| 4.19 | User confirms PII detection and redaction behavior, where applicable | High | P0 | None | None | None | P0 | Missing | PII handling not validated | Add PII E2E to security suite |

### Hypothesis Generation Workflow — Layer 4 (P0, Critical)

| ID | Workflow | Risk | Priority | Current Coverage | Test Type | Test File(s) | Gate | Status | Gap | Next Action |
|---|---|---|---|---|---|---|---|---|---|---|
| 9.1 | User generates AI value hypotheses | Critical | P0 | Route smoke | Route smoke | agent-workflow-lifecycle.spec.ts | P0 | Passing | None | Maintain |
| 9.2 | User reviews multiple hypotheses | Critical | P0 | Route smoke | Route smoke | agent-workflow-lifecycle.spec.ts | P0 | Passing | None | Maintain |
| 9.3 | User approves a hypothesis | Critical | P0 | Route smoke | Route smoke | agent-workflow-lifecycle.spec.ts | P0 | Passing | None | Maintain |
| 9.4 | User modifies a hypothesis | High | P0 | None | None | None | P0 | Missing | Hypothesis edit workflow not validated | Add to j9-agent-grounding-deep.spec.ts |
| 9.5 | User skips a hypothesis | Medium | P1 | Route smoke | Route smoke | agent-workflow-lifecycle.spec.ts | P1 | Passing | None | Maintain |
| 9.6 | User asks the agent to justify a hypothesis | Critical | P0 | Deep frontend E2E | Deep frontend E2E | j9-agent-grounding-deep.spec.ts | P0 | Partial (AG-DEEP-001 failure) | Agent response with evidence citations | Fix AG-DEEP-001 |
| 9.7 | User asks the agent to identify assumptions | Critical | P0 | Deep frontend E2E | Deep frontend E2E | j9-agent-grounding-deep.spec.ts | P0 | Partial (AG-DEEP-002 failure) | Assumption vs fact labeling | Fix AG-DEEP-002 |
| 9.8 | User asks the agent to identify missing evidence | High | P0 | None | None | None | P0 | Missing | Missing evidence workflow not validated | Add to j9-agent-grounding-deep.spec.ts |
| 9.9 | User maps hypothesis to stakeholder | Medium | P1 | Route smoke | Route smoke | agent-workflow-lifecycle.spec.ts | P1 | Passing | None | Maintain |
| 9.10 | User maps hypothesis to value category | Medium | P1 | Route smoke | Route smoke | agent-workflow-lifecycle.spec.ts | P1 | Passing | None | Maintain |
| 9.11 | User converts approved hypothesis into value driver | High | P0 | Route smoke | Route smoke | agent-workflow-lifecycle.spec.ts | P0 | Passing | None | Maintain |
| 9.12 | User rejects hallucinated or unsupported hypothesis | Critical | P0 | Deep frontend E2E | Deep frontend E2E | j9-agent-grounding-deep.spec.ts | P0 | Partial (AG-DEEP-009 failure) | Business case claim types | Fix AG-DEEP-009 |
| 9.13 | User verifies every hypothesis has source grounding or clear assumption label | Critical | P0 | Deep frontend E2E | Deep frontend E2E | j9-agent-grounding-deep.spec.ts | P0 | Partial (AG-DEEP-002 failure) | Assumption labeling | Fix AG-DEEP-002 |

### Business Case Generation Workflow (P0, Critical)

| ID | Workflow | Risk | Priority | Current Coverage | Test Type | Test File(s) | Gate | Status | Gap | Next Action |
|---|---|---|---|---|---|---|---|---|---|---|
| 15.1 | User generates a business case | Critical | P0 | Deep frontend E2E | Deep frontend E2E | j1-golden-path-deep.spec.ts | P0 | Partial (GP-DEEP-013 failure) | Business case "approved" status | Fix GP-DEEP-013 |
| 15.2 | User selects business case template | High | P0 | Route smoke | Route smoke | business-case.spec.ts | P0 | Passing | None | Maintain |
| 15.3 | User selects audience (CFO, CIO, CRO, COO, technical buyer, executive sponsor) | High | P0 | Route smoke | Route smoke | business-case.spec.ts | P0 | Passing | None | Maintain |
| 15.4 | User includes or excludes selected drivers | High | P0 | Route smoke | Route smoke | business-case.spec.ts | P0 | Passing | None | Maintain |
| 15.5 | User includes selected evidence | High | P0 | Route smoke | Route smoke | business-case.spec.ts | P0 | Passing | None | Maintain |
| 15.6 | User includes selected benchmarks | High | P0 | Route smoke | Route smoke | business-case.spec.ts | P0 | Passing | None | Maintain |
| 15.7 | User includes scenario comparison | High | P0 | Route smoke | Route smoke | business-case.spec.ts | P0 | Passing | None | Maintain |
| 15.8 | User generates executive summary | High | P0 | Route smoke | Route smoke | business-case.spec.ts | P0 | Passing | None | Maintain |
| 15.9 | User generates financial model narrative | High | P0 | Route smoke | Route smoke | business-case.spec.ts | P0 | Passing | None | Maintain |
| 15.10 | User generates stakeholder-specific narrative | Medium | P1 | Route smoke | Route smoke | business-case.spec.ts | P1 | Passing | None | Maintain |
| 15.11 | User edits generated business case | High | P0 | Route smoke | Route smoke | business-case.spec.ts | P0 | Passing | None | Maintain |
| 15.12 | User asks agent to tighten argument | High | P0 | None | None | None | P0 | Missing | Agent argument tightening not validated | Add to j9-agent-grounding-deep.spec.ts |
| 15.13 | User asks agent to identify weak claims | Critical | P0 | Deep frontend E2E | Deep frontend E2E | j9-agent-grounding-deep.spec.ts | P0 | Partial (AG-DEEP-009 failure) | Business case claim types | Fix AG-DEEP-009 |
| 15.14 | User asks agent to add citations | High | P0 | Deep frontend E2E | Deep frontend E2E | j9-agent-grounding-deep.spec.ts | P0 | Partial (AG-DEEP-001 failure) | Agent response with evidence citations | Fix AG-DEEP-001 |
| 15.15 | User validates every claim maps to evidence, benchmark, or assumption | Critical | P0 | Deep frontend E2E | Deep frontend E2E | j1-golden-path-deep.spec.ts | P0 | Partial (GP-DEEP-015 failure) | Claim traceability labels | Fix GP-DEEP-015 |
| 15.16 | User exports business case to PDF, DOCX, or slides | Critical | P0 | Deep frontend E2E (passing) | Deep frontend E2E | export-workflows-deep.spec.ts | P0 | Passing | None | Maintain |
| 15.17 | User regenerates business case after model changes | High | P0 | None | None | None | P0 | Missing | Regeneration workflow not validated | Add to j8-approval-review-deep.spec.ts |
| 15.18 | User compares old and new versions | Medium | P1 | None | None | None | P1 | Missing | Version comparison not validated | Add to j8-approval-review-deep.spec.ts |

### Security and Compliance User Workflows (P0, Critical)

| ID | Workflow | Risk | Priority | Current Coverage | Test Type | Test File(s) | Gate | Status | Gap | Next Action |
|---|---|---|---|---|---|---|---|---|---|---|
| 26.1 | User attempts unauthorized tenant access | Critical | P0 | Deep frontend E2E | Deep frontend E2E | tenant-isolation-deep.spec.ts | P0 | Partial (SEC-DEEP-002 failure) | Foreign account drivers URL fails closed | Fix SEC-DEEP-002 |
| 26.2 | User attempts unauthorized account access | Critical | P0 | Deep frontend E2E | Deep frontend E2E | tenant-isolation-deep.spec.ts | P0 | Passing | None | Maintain |
| 26.3 | User attempts unauthorized document access | Critical | P0 | Deep frontend E2E | Deep frontend E2E | tenant-isolation-deep.spec.ts | P0 | Passing | None | Maintain |
| 26.4 | User attempts unauthorized export | Critical | P0 | Deep frontend E2E | Deep frontend E2E | export-workflows-deep.spec.ts | P0 | Passing | None | Maintain |
| 26.5 | User attempts prompt injection through uploaded document | Critical | P0 | None | None | None | P0 | Missing | Prompt injection refusal not validated | Add adversarial path E2E |
| 26.6 | User uploads content containing PII | High | P0 | None | None | None | P0 | Missing | PII detection/redaction not validated | Add PII E2E to security suite |
| 26.7 | User requests agent to reveal restricted data | Critical | P0 | None | None | None | P0 | Missing | Agent refusal not validated | Add to j9-agent-grounding-deep.spec.ts |
| 26.8 | User requests agent to ignore governance policy | Critical | P0 | None | None | None | P0 | Missing | Policy refusal not validated | Add to j9-agent-grounding-deep.spec.ts |
| 26.9 | User attempts cross-tenant search leakage | Critical | P0 | Deep frontend E2E | Deep frontend E2E | tenant-isolation-deep.spec.ts | P0 | Passing | None | Maintain |
| 26.10 | User validates role-based export restrictions | Critical | P0 | Deep frontend E2E | Deep frontend E2E | export-workflows-deep.spec.ts | P0 | Passing | None | Maintain |
| 26.11 | Admin exports audit log | Medium | P1 | None | None | None | P1 | Missing | Audit export workflow not validated | Add audit export E2E |
| 26.12 | Admin configures retention policy | Medium | P1 | Route smoke | Route smoke | admin.spec.ts | P1 | Planned | Retention policy E2E missing | Add to admin suite |
| 26.13 | Admin deletes account data according to policy | High | P0 | None | None | None | P0 | Missing | Data deletion workflow not validated | Add data deletion E2E |
| 26.14 | Admin validates deletion or archival behavior | High | P0 | None | None | None | P0 | Missing | Deletion validation not validated | Add data deletion E2E |

### Full End-to-End Golden Path (P0, Critical)

| ID | Workflow | Risk | Priority | Current Coverage | Test Type | Test File(s) | Gate | Status | Gap | Next Action |
|---|---|---|---|---|---|---|---|---|---|---|
| 28.1 | User creates new account | High | P0 | Deep frontend E2E | Deep frontend E2E | j1-golden-path-deep.spec.ts | P0 | Partial (GP-DEEP-001 failure) | User creates account via prospect form | Fix GP-DEEP-001 |
| 28.2 | User assigns value pack | High | P0 | Route smoke | Route smoke | /context/packs | P0 | Planned | Value pack assignment E2E missing | Add to j1 or j6 |
| 28.3 | User ingests company website | High | P0 | Deep frontend E2E | Deep frontend E2E | j1-golden-path-deep.spec.ts | P0 | Partial (GP-DEEP-003 failure) | Domain ingestion from command center | Fix GP-DEEP-003 |
| 28.4 | User uploads discovery notes | High | P0 | Deep frontend E2E | Deep frontend E2E | j1-golden-path-deep.spec.ts | P0 | Passing | None | Maintain |
| 28.5 | System extracts signals | High | P0 | Deep frontend E2E | Deep frontend E2E | j1-golden-path-deep.spec.ts | P0 | Passing | None | Maintain |
| 28.6 | User approves signals | High | P0 | Deep frontend E2E | Deep frontend E2E | j1-golden-path-deep.spec.ts | P0 | Partial (GP-DEEP-006 failure) | Approve/reject extracted signals | Fix GP-DEEP-006 |
| 28.7 | System builds account graph | High | P0 | Route smoke | Route smoke | /context/ontology/graph | P0 | Passing | None | Maintain |
| 28.8 | User reviews stakeholder map | Medium | P1 | Route smoke | Route smoke | /intelligence/:accountId/signals | P1 | Passing | None | Maintain |
| 28.9 | System generates value hypotheses | Critical | P0 | Deep frontend E2E | Deep frontend E2E | j9-agent-grounding-deep.spec.ts | P0 | Partial (AG-DEEP-001/002/009 failures) | Agent grounding failures | Fix AG-DEEP-001/002/009 |
| 28.10 | User approves hypotheses | Critical | P0 | Route smoke | Route smoke | agent-workflow-lifecycle.spec.ts | P0 | Passing | None | Maintain |
| 28.11 | System generates value driver tree | High | P0 | Route smoke | Route smoke | /drivers/:accountId | P0 | Passing | None | Maintain |
| 28.12 | User maps evidence to drivers | High | P0 | Deep frontend E2E (passing) | Deep frontend E2E | j7-calculation-evidence-deep.spec.ts | P0 | Passing | None | Maintain |
| 28.13 | User selects formulas | Critical | P0 | Deep frontend E2E (passing) | Deep frontend E2E | j7-calculation-evidence-deep.spec.ts | P0 | Passing | None | Maintain |
| 28.14 | User fills assumptions | Critical | P0 | Deep frontend E2E (passing) | Deep frontend E2E | j7-calculation-evidence-deep.spec.ts | P0 | Passing | None | Maintain |
| 28.15 | User creates Conservative, Expected, and Optimistic scenarios | Critical | P0 | Deep frontend E2E (passing) | Deep frontend E2E | j7-calculation-evidence-deep.spec.ts | P0 | Passing | None | Maintain |
| 28.16 | System calculates ROI and payback | Critical | P0 | Deep frontend E2E (passing) | Deep frontend E2E | j7-calculation-evidence-deep.spec.ts | P0 | Passing | None | Maintain |
| 28.17 | User generates business case | Critical | P0 | Deep frontend E2E | Deep frontend E2E | j1-golden-path-deep.spec.ts | P0 | Partial (GP-DEEP-013/015 failures) | Business case status and traceability | Fix GP-DEEP-013/015 |
| 28.18 | Reviewer approves business case | Critical | P0 | Deep frontend E2E (passing) | Deep frontend E2E | j8-approval-review-deep.spec.ts | P0 | Passing | None | Maintain |
| 28.19 | User exports business case | Critical | P0 | Deep frontend E2E (passing) | Deep frontend E2E | export-workflows-deep.spec.ts | P0 | Passing | None | Maintain |
| 28.20 | User pushes summary to CRM | Medium | P1 | Route smoke | Route smoke | /context/integrations | P1 | Planned | CRM push E2E missing | Add to j11 or CRM suite |
| 28.21 | User converts case into post-sale value realization plan | Medium | P1 | Route smoke | Route smoke | /realization/:accountId | P1 | Planned | Realization conversion E2E missing | Add to j7 |

## Appendix: P2/P3 Workflow Backlog

### Collaboration, Notifications, and Tasks (P2, Medium/Low)
- Team invite, reviewer assignment, comments, mentions, resolve comment
- Review/ingestion notifications, task create/assign/complete/overdue
- **Owner:** QA Lead + Frontend Lead
- **Proposed file:** `apps/web/e2e/collaboration/collaboration-notifications-tasks.spec.ts`

### Narrative and Proposal Workflow (P2, Medium)
- Narrative generation, tone adjustment, claim grounding, versioning
- **Owner:** Frontend Lead + Agent/AI Lead
- **Proposed file:** `apps/web/e2e/journeys/j12-narrative-proposal.spec.ts`

### Search and Retrieval Workflow (P1, Medium)
- Cross-tenant search, role-based filtering, result context landing
- **Owner:** Backend Lead + Data/Graph Lead
- **Proposed file:** `apps/web/e2e/journeys/j13-search-retrieval.spec.ts`

### Value Realization Workflow (P1, Medium)
- Pre-sale to post-sale conversion, outcomes tracking, variance analysis
- **Owner:** Backend Lead + Frontend Lead
- **Proposed file:** Enhance `apps/web/e2e/journeys/j7-value-realization-and-calculation.spec.ts`

### Persona-Based Validation Journeys (P1/P2, Medium)
- Sales Rep, Value Engineer, Sales Leader, CSM, Admin, Executive Buyer
- **Owner:** QA Lead + Product Lead
- **Proposed file:** `apps/web/e2e/personas/persona-journeys.spec.ts`

## Validation Gate Map

| Gate | Purpose | Required Suites | Command | Pass Criteria | Blocks Release? |
|---|---|---|---|---|---|
| Developer PR smoke | Fast feedback on route-level changes | Route smoke, Component tests | `pnpm run test:e2e:contracts` | All route smoke tests pass | No |
| Frontend validation baseline | Validate 60 core workflow surfaces | 10 validation journey suites | `pnpm run test:e2e:validation` | 60/60 tests pass | No |
| P0 deep frontend validation | Validate 78 interaction-level P0 workflows | 7 deep test files | `pnpm run test:e2e:validation:p0:deep` | 78/78 tests pass, 0 flaky | Yes |
| Anti-skip guard | Prevent silent test weakening | All E2E files | `pnpm run test:e2e:guard` | No skipped critical tests | Yes |
| Backend-gated Playwright validation | Validate golden path against local L1-L6 | j11-golden-path-business-lifecycle.spec.ts | `pnpm run test:e2e:journeys --file=j11-golden-path-business-lifecycle.spec.ts` | All j11 tests pass with seeded L1-L6 data | Yes |
| Backend-integrated service validation | Validate 8 backend-integrated workflows | 9 backend-integrated test files | `make test-backend-integrated-validation` | All backend-integrated tests pass | Yes |
| Release smoke | Validate staging/release candidate health | Release environment smoke | `make test-backend-integrated-release-smoke` | All smoke checks pass | Yes |
| Full production-readiness validation | Complete validation program | All frontend + backend-integrated suites | Full validation suite | All P0 gates pass, backend-integrated green | Yes |

## Execution Cadence

| Cadence | Runs | Why | Owner | Expected Duration | Failure Policy |
|---|---|---|---|---|---|
| On every PR | Developer PR smoke, Frontend validation baseline | Fast feedback on route/component changes | Frontend Lead | 5-10 min | Block merge if route smoke fails |
| On frontend-affecting PRs | P0 deep frontend validation, Anti-skip guard | Catch interaction-level regressions | QA Lead | 15-20 min | Block merge if P0 deep fails or flaky |
| On backend/service PRs | Backend-gated Playwright validation | Validate service contract changes | Backend Lead | 10-15 min | Block merge if j11 fails |
| Nightly | Full frontend validation + backend-integrated | Catch cross-layer integration issues | QA Lead + Backend Lead | 30-45 min | Create ticket, alert team |
| Before release candidate | Release smoke + Full production-readiness validation | Validate staging environment readiness | Platform/DevOps Lead | 45-60 min | Block release if any gate fails |
| Before production launch | Full production-readiness validation + manual review | Final production gate | Security Lead + Platform/DevOps Lead | 60-90 min | Block launch if any gate fails |

## Gap Prioritization

| Gap | Workflow Area | Risk | Priority | Recommended Fix | Suggested Test File | Owner |
|---|---|---|---|---|---|---|
| SEC-DEEP-007/008 flaky | Tenant isolation role switching | High | P0 | Stabilize switchToReadOnlyUser with waitForURL or navigation state check | tenant-isolation-deep.spec.ts | Security Lead + Frontend Lead |
| GP-DEEP-001 failure | Account creation via prospect form | High | P0 | Add prospect form fill() target or implement UI affordance | j1-golden-path-deep.spec.ts | Frontend Lead |
| GP-DEEP-003 failure | Domain ingestion from command center | High | P0 | Add domain input or submit action to command center UI | j1-golden-path-deep.spec.ts | Frontend Lead |
| GP-DEEP-004 failure | Ingestion job progress monitoring | Medium | P0 | Align job list rendering to expected "completed" / "100%" text pattern | j1-golden-path-deep.spec.ts | Frontend Lead + Backend Lead |
| GP-DEEP-005 failure | Signal review with source/confidence | Medium | P0 | Align mock signal data to surface confidence % in visible text | j1-golden-path-deep.spec.ts | Frontend Lead |
| GP-DEEP-006 failure | Approve/reject extracted signals | High | P0 | Add approve/reject action buttons to signal review page | j1-golden-path-deep.spec.ts | Frontend Lead |
| GP-DEEP-013 failure | Business case "approved" status | Medium | P0 | Ensure business case detail renders "approved" as visible text | j1-golden-path-deep.spec.ts | Frontend Lead |
| GP-DEEP-015 failure | Claim traceability labels | High | P0 | Add evidence/benchmark/assumption claim type labels to business case detail | j1-golden-path-deep.spec.ts | Frontend Lead |
| L1-DEEP-002 failure | Retry button on failed ingestion | Medium | P0 | Expose and wire retry button in ingestion jobs list | j10-layer-ui-validation-deep.spec.ts | Frontend Lead |
| L2-DEEP-002 failure | Low-confidence signal warning | Medium | P0 | Add "low confidence" or "44%" or "unverified" text indicator to signals page | j10-layer-ui-validation-deep.spec.ts | Frontend Lead |
| L6-DEEP-001 failure | Stale benchmark warning badge | Medium | P0 | Surface stale-warning or confidence badge on benchmark governance page | j10-layer-ui-validation-deep.spec.ts | Frontend Lead |
| AG-DEEP-001 failure | Agent response with evidence citations | High | P0 | Add chat input on signals page to trigger agent response with citations | j9-agent-grounding-deep.spec.ts | Frontend Lead + Agent/AI Lead |
| AG-DEEP-002 failure | Assumption vs fact labeling | High | P0 | Add distinct assumption/fact labels to action plan page | j9-agent-grounding-deep.spec.ts | Frontend Lead + Agent/AI Lead |
| AG-DEEP-009 failure | Business case claim types | High | P0 | Add evidence/benchmark/assumption claim type labels to business case detail (same as GP-DEEP-015) | j9-agent-grounding-deep.spec.ts | Frontend Lead |
| SEC-DEEP-002 failure | Foreign account drivers URL fails closed | High | P0 | Ensure foreign-account drivers route renders explicit error or empty state | tenant-isolation-deep.spec.ts | Security Lead + Frontend Lead |
| Backend-gated j11 not run | Golden path against local L1-L6 | Critical | P0 | Run j11 against seeded L1-L6 data after frontend P0 stable | j11-golden-path-business-lifecycle.spec.ts | Backend Lead + Platform/DevOps Lead |
| Backend-integrated 61-test red-state | Backend-integrated service validation | Critical | P0 | Address backend-integrated failures after j11 stable | tests/backend_integrated/*.py | Backend Lead + Platform/DevOps Lead |

## Recommended Next Implementation Batch

### Phase 1: Stabilize P0 Deep Frontend Tests (Immediate)

**Objective:** Close 18 failing + 2 flaky tests to achieve 78/78 passing P0 deep frontend validation.

**Priority Order:**

1. **Fix flaky tests first** (SEC-DEEP-007/008)
   - Stabilize `switchToReadOnlyUser` with explicit waitForURL or navigation state check
   - **Owner:** Security Lead + Frontend Lead
   - **File:** `apps/web/e2e/security/tenant-isolation-deep.spec.ts`

2. **Fix Category A: Missing UI Affordance** (7 failures)
   - GP-DEEP-001: Add prospect form fill() target
   - GP-DEEP-003: Add domain input/submit to command center
   - GP-DEEP-006: Add approve/reject buttons to signal review
   - L1-DEEP-002: Expose retry button in ingestion jobs
   - L6-DEEP-001: Surface stale benchmark warning badge
   - AG-DEEP-001: Add chat input on signals page
   - AG-DEEP-002: Add assumption/fact labels to action plan
   - **Owner:** Frontend Lead (with Agent/AI Lead for AG-DEEP-001/002)

3. **Fix Category B: Data Contract Mismatch** (6 failures)
   - GP-DEEP-004: Align job list rendering to "completed" / "100%" pattern
   - GP-DEEP-005: Align mock signal data to surface confidence %
   - L2-DEEP-002: Add low-confidence warning indicator
   - GP-DEEP-013: Ensure "approved" status renders as visible text
   - GP-DEEP-015: Add claim type labels to business case detail
   - AG-DEEP-009: Add claim type labels (same as GP-DEEP-015)
   - **Owner:** Frontend Lead + Backend Lead

4. **Fix Category C: Security Edge Case** (1 failure)
   - SEC-DEEP-002: Ensure foreign-account drivers route renders error state
   - **Owner:** Security Lead + Frontend Lead

**Success Criteria:**
- `pnpm run test:e2e:validation:p0:deep` passes with 78/78 tests
- 0 flaky tests
- Anti-skip guard passes

**Estimated Duration:** 3-5 days

### Phase 2: Confirm Frontend Baseline (After Phase 1)

**Objective:** Verify original 60 validation tests still pass after P0 deep fixes.

**Actions:**
- Run `pnpm run test:e2e:validation`
- Confirm 60/60 tests pass
- Run `pnpm run test:e2e:guard`
- Confirm anti-skip guard passes

**Owner:** QA Lead

**Estimated Duration:** 1-2 hours

### Phase 3: Backend-Gated j11 Validation (After Phase 2)

**Objective:** Run j11 golden path against local L1-L6 seeded data.

**Actions:**
- Start local L1-L6 services with seeded test data
- Run `pnpm run test:e2e:journeys --file=j11-golden-path-business-lifecycle.spec.ts`
- Debug and fix any service contract mismatches
- Ensure tenant isolation holds with real services

**Owner:** Backend Lead + Platform/DevOps Lead

**Estimated Duration:** 2-3 days

### Phase 4: Backend-Integrated Suite (After Phase 3)

**Objective:** Address 61-test red-state backend-integrated suite.

**Actions:**
- Run `pytest tests/backend_integrated/`
- Classify failures by service layer (L1-L6)
- Fix service contract issues
- Ensure tenant isolation persistence
- Validate cross-layer data flow
- Confirm agent grounding with real tool contracts

**Owner:** Backend Lead + Platform/DevOps Lead

**Estimated Duration:** 5-7 days

### Do NOT Expand Into New Coverage Until:

- All 78 P0 deep frontend tests pass (0 flaky)
- Original 60 validation tests still pass
- Anti-skip guard passes
- Backend-gated j11 passes against local L1-L6
- Backend-integrated 61-test suite passes

**Only then** consider adding P1/P2 workflow coverage.

## Final Recommendation

**Continue P0 stabilization.**

The current state shows:
- 74.4% pass rate on P0 deep frontend tests (58/78 passing, 18 failing, 2 flaky)
- 3 suites fully passing (Calculation/Evidence 12/12, Approval Gates 10/10, Export 7/7)
- 4 suites with failures (Golden Path 7/15, Layer UI 9/12, Tenant Isolation 9/12, Agent Grounding 7/10)

**Rationale:**

1. **P0 is the production gate:** The 18 failing + 2 flaky P0 deep tests block production readiness. These tests validate critical workflows: account creation, ingestion, signal review, agent grounding, business case generation, and tenant isolation.

2. **Backend-integrated is not ready:** The backend-integrated 61-test suite is in red-state and requires stable L1-L6 services. Running backend-integrated validation before frontend P0 is stable would waste debugging cycles.

3. **Risk-based prioritization:** The failing P0 tests expose gaps in UI affordance (7 failures), data contract mismatches (6 failures), security edge cases (1 failure), and timing issues (2 flaky). These are higher risk than adding new P1/P2 coverage.

4. **TDD discipline:** The deep validation suite is in TDD red phase. The correct next step is to fix the red tests, not to add more tests. This maintains test integrity and prevents weakening the validation gate.

**Next Steps:**

1. Fix SEC-DEEP-007/008 flaky tests (timing race in role switching)
2. Fix 7 Category A failures (missing UI affordance)
3. Fix 6 Category B failures (data contract mismatch)
4. Fix 1 Category C failure (security edge case)
5. Confirm 60 validation tests still pass
6. Run backend-gated j11 against local L1-L6
7. Address backend-integrated 61-test suite

**Do not add new P1/P2 tests until all P0 frontend deep tests and backend-gated j11 are stable.**
