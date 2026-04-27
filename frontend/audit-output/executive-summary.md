# Tri-Track Audit: Executive Summary

**Date:** 2026-04-26
**Scope:** Frontend-Backend Integration Gap Analysis
**Auditor:** Automated Forensic Analysis

---

## The 40% Facade Problem: Actually 81%

The Fabric 4L frontend presents a visually complete application with **154 routes**, but the forensic audit reveals:

- **84 authenticated routes** — only **15** have live backend integration
- **81% facade rate** — routes rendering hardcoded data or no backend connection
- **236 orphan endpoints** — backend capabilities with zero frontend surface
- **8 connected endpoints** — only 3.3% of 244 backend endpoints are consumed

---

## Findings Summary

| Track | Finding | Severity | Metric |
|-------|---------|----------|--------|
| **A** | Route Facade Problem | CRITICAL | 81% of authenticated routes non-functional |
| **B** | API Integration Gap | CRITICAL | 96.7% of endpoints have no frontend surface |
| **C** | Contract Compliance | HIGH | 3 of 6 contracts ratified, 3 missing contracts |

---

## Track A: Route Integrity Matrix

### Data Source Distribution

| Color | Status | Count | Percentage |
|-------|--------|-------|------------|
| **GREEN** | Live backend integration | 16 | 10.4% |
| **YELLOW** | Generic endpoint passthrough | 0 | 0.0% |
| **RED** | Hardcoded mock/orphaned | 51 | 33.1% |
| **REDIRECT** | Legacy redirects | 70 | 45.5% |
| **UNKNOWN** | Unevaluated/incomplete | 17 | 11.0% |

### Key Red Routes (Hardcoded/Mock)

Pages with no backend integration detected:

1. **Intelligence Workspace Tabs** - SignalsTab, DriversTab, EvidenceTab, StakeholdersTab
2. **Value Studio Tabs** - ActionPlanTab, ValueModelTab, NarrativeTab
3. **Workspace Redirects** - Multiple redirects without data fetching

### Functional Green Routes (Live Integration)

Pages with verified backend integration:

1. **Accounts** - useAccounts, useCreateAccount
2. **FormulaBuilder/List** - useFormulas, useFormula, useSubmitFormula
3. **EntityBrowser** - useEntities
4. **GraphExplorer** - useGraphQuery, useSubgraph
5. **ValuePacks** - useValuePacks, useApplyValuePack
6. **IngestionJobs** - useIngestion
7. **Billing/Usage** - useBilling, useUsage
8. **AgentWorkflows** - useWorkflows
9. **DecisionTrace** - useProvenance
10. **Admin Pages** - useBenchmarks, usePlatformSettings, etc.

---

## Track B: API Archaeology

### Orphan Endpoints by Layer

| Layer | Total | Connected | Orphan | Rate |
|-------|-------|-----------|--------|------|
| Layer 1 (Ingestion) | 26 | 0 | 26 | 100% |
| Layer 2 (Extraction) | 29 | 7 | 22 | 75.9% |
| Layer 3 (Knowledge) | 89 | 1 | 88 | 98.9% |
| Layer 4 (Agents) | 84 | 0 | 84 | 100% |
| Layer 5 (Ground Truth) | 13 | 0 | 13 | 100% |
| Signals | 3 | 0 | 3 | 100% |

### Top 10 Orphaned Domains

| Domain | Orphan Endpoints | Potential Value |
|--------|------------------|-----------------|
| Accounts | 16 | CRM integration, account management |
| Ontology | 14 | Ontology CRUD operations |
| Ground Truth | 13 | Evaluation and evidence |
| State Inspector | 12 | Agent checkpoint/resume |
| Health | 12 | System health monitoring |
| Workflows | 9 | Agent workflow management |
| ValuePacks | 9 | Value pack management |
| Model Registry | 7 | Model versioning |
| Integrations | 6 | Third-party integrations |
| Checkpoints | 8 | Agent state checkpoints |

### Critical Missing Connections

1. **16 Account Endpoints** → Should power Accounts.tsx and CRM integration
2. **14 Ontology Endpoints** → Should power OntologyEditor.tsx
3. **12 Health Endpoints** → Should power HealthMonitor.tsx
4. **9 Workflow Endpoints** → Should power AgentWorkflows.tsx
5. **8 Checkpoint Endpoints** → Critical for agent resume functionality

---

## Track C: Contract Gap Analysis

### The 6 Canonical Contracts: Compliance

| Contract | Status | Compliance | Key Gap |
|----------|--------|------------|---------|
| 2.1 Tenant Context | Proposed | 60% | Not all hooks validate tenant |
| 2.2 DB Session | Ratified | 80% | Frontend doesn't manage sessions |
| 2.3 Middleware/Auth | Ratified | 90% | Rate limiting not visible |
| 2.4 Tool Boundary | Proposed | 30% | No frontend ToolRegistry |
| 2.5 Agent Output | Proposed | 40% | Outputs not typed |
| 2.6 UI State | Proposed | 70% | Some server state outside RQ |

### Missing Contracts (Frontend-Backend Boundary)

1. **API Boundary Contract** — No standardized error handling, pagination, filtering
2. **Type Synchronization Contract** — No automated OpenAPI → TypeScript generation
3. **Hook Architecture Contract** — Inconsistent React Query patterns across 47 hooks

---

## Recommendations

### Immediate (Week 1-2)

1. **Enable 16 Account/CRM Endpoints** — Connect Accounts.tsx to real backend
2. **Enable 9 Workflow Endpoints** — Unblock agent checkpoint/resume
3. **Enable 12 Health Endpoints** — Make HealthMonitor.tsx functional

### Short Term (Month 1)

1. **Generate Types from OpenAPI** — Automate TypeScript type creation
2. **Standardize Error Handling** — Implement useApiShared across all hooks
3. **Connect Ontology Endpoints** — Enable full OntologyEditor functionality

### Medium Term (Month 2-3)

1. **Implement 3 Missing Contracts** — API Boundary, Type Sync, Hook Architecture
2. **Build Frontend ToolRegistry** — Enable Contract 2.4 compliance
3. **Type Agent Outputs** — Enable Contract 2.5 compliance
4. **Connect All Layer 3 Endpoints** — Knowledge graph full functionality

---

## Metrics

| Metric | Current | Target | Impact |
|--------|---------|--------|--------|
| Route Facade Rate | 81% | <20% | +67 functional pages |
| Orphan Endpoints | 236 | <50 | +186 connected capabilities |
| Connected Hooks | 26/44 | 44/44 | +18 working features |
| Contract Compliance | ~60% | 100% | Maintainable architecture |

---

## Conclusion

The Fabric 4L frontend presents a **visual facade**: 154 routes with tiered navigation,
role-based access control, and polished UI components. However, **81% of authenticated
routes are non-functional** — they render hardcoded data, mocks, or have no backend
connection. The 244 backend endpoints represent significant investment in DIL services,
yet **only 8 are consumed by the frontend**.

This is not a 'some features missing' problem. This is a **systemic integration failure**
requiring focused engineering effort to connect frontend surfaces to backend capabilities.

The 3 missing frontend-backend contracts (API Boundary, Type Synchronization, Hook
Architecture) must be defined and ratified to prevent recurrence and enable sustainable
development velocity.

---

## Artifacts

| File | Description |
|------|-------------|
| `track-a-route-matrix.csv` | Machine-readable route audit (154 routes) |
| `track-a-route-matrix.md` | Human-readable route summary |
| `track-a-hook-analysis.json` | 47 hooks with data source classification |
| `track-b-orphan-registry.json` | Machine-readable endpoint audit (244 endpoints) |
| `track-b-orphan-registry.md` | Domain-entity orphan analysis |
| `track-c-contract-gaps.md` | 6 canonical contracts + 3 missing contracts |
| `executive-summary.md` | This document |