# Value Fabric — Complete Route Inventory
**Date:** 2026-04-28  
**Total Routes:** 154 (82 primary pages + 72 redirect aliases + 15 parameterized)

---

## Route Categories

### 🔴 Critical Broken Routes
Routes that fail with server errors or complete functional breakdown

### 🟡 Warning Routes  
Routes with significant UX issues but partially functional

### ✅ Working Routes
Routes that render and function correctly

### 👻 Ghost Routes
Routes defined in router but silently fall back to Home page

---

## Core Workflow

| Route | Status | Type | Notes |
|-------|--------|------|------- |
| / | ✅ Working | Primary | Redirects to /home |
| /home | ✅ Working | Primary | Launch button broken |
| /login | ✅ Working | Primary | |
| /signup | ✅ Working | Primary | |
| /accounts | 🔴 Broken | Primary | 500 error — cascading failure |

**Core Workflow:** 3 Working | 1 Broken | 0 Ghost

---

## Intelligence (20 Routes)

| Route | Status | Type | Notes |
|-------|--------|------|------- |
| /intelligence | 🔴 Broken | Primary | Redirects to /accounts |
| /intelligence/signals | 🔴 Broken | Primary | Sidebar nav broken |
| /intelligence/drivers | 🔴 Broken | Primary | Sidebar nav broken |
| /intelligence/evidence | 🔴 Broken | Primary | Sidebar nav broken |
| /intelligence/cases | 🔴 Broken | Primary | |
| /intelligence/insights | 🔴 Broken | Primary | |
| /intelligence/narratives | 🔴 Broken | Primary | |
| /intelligence/research | 🔴 Broken | Primary | |
| /intelligence/benchmarks | 🔴 Broken | Primary | |
| /intelligence/competitors | 🔴 Broken | Primary | |
| /intelligence/trends | 🔴 Broken | Primary | |
| /intelligence/roi | 🔴 Broken | Primary | |
| /intelligence/impact | 🔴 Broken | Primary | |
| /intelligence/risk | 🔴 Broken | Primary | |
| /intelligence/opportunities | 🔴 Broken | Primary | |
| /intelligence/threats | 🔴 Broken | Primary | |
| /intelligence/recommendations | 🔴 Broken | Primary | |
| /intelligence/actions | 🔴 Broken | Primary | |
| /intelligence/plan | 🔴 Broken | Primary | |
| /intelligence/summary | 🔴 Broken | Primary | |

**Intelligence:** 0 Working | 20 Broken | 0 Ghost

---

## Studio (23 Routes)

| Route | Status | Type | Notes |
|-------|--------|------|------- |
| /studio | 🔴 Broken | Primary | |
| /studio/models | 🔴 Broken | Primary | |
| /studio/formulas | 🔴 Broken | Primary | |
| /studio/ontologies | 🔴 Broken | Primary | |
| /studio/agents | 🔴 Broken | Primary | |
| /studio/workflows | 🔴 Broken | Primary | |
| /studio/templates | 🔴 Broken | Primary | |
| /studio/components | 🔴 Broken | Primary | |
| /studio/assets | 🔴 Broken | Primary | |
| /studio/datasets | 🔴 Broken | Primary | |
| /studio/integrations | 🔴 Broken | Primary | |
| /studio/publish | 🔴 Broken | Primary | |
| /studio/share | 🔴 Broken | Primary | |
| /studio/collaborate | 🔴 Broken | Primary | |
| /studio/review | 🔴 Broken | Primary | |
| /studio/approve | 🔴 Broken | Primary | |
| /studio/deploy | 🔴 Broken | Primary | |
| /studio/monitor | 🔴 Broken | Primary | |
| /studio/analytics | 🔴 Broken | Primary | |
| /studio/settings | 🔴 Broken | Primary | |
| /studio/help | 🔴 Broken | Primary | |
| /studio/feedback | 🔴 Broken | Primary | |
| /studio/tutorials | 🔴 Broken | Primary | |

**Studio:** 0 Working | 23 Broken | 0 Ghost

---

## Model / Value Studio (3 Routes)

| Route | Status | Type | Notes |
|-------|--------|------|------- |
| /model/value-studio | 🔴 Broken | Primary | Redirects to /accounts |
| /model/value-studio/create | 🔴 Broken | Primary | |
| /model/value-studio/edit/:id | 🔴 Broken | Parameterized | |

**Model/Value Studio:** 0 Working | 3 Broken | 0 Ghost

---

## Context Engine (8 Routes)

| Route | Status | Type | Notes |
|-------|--------|------|------- |
| /context/models | ✅ Working | Primary | |
| /context/value-trees/explorer | ✅ Working | Primary | |
| /context/ingestion/jobs | ✅ Working | Primary | |
| /context/extraction | ✅ Working | Primary | |
| /context/packs | 🔴 Broken | Primary | Type mismatch error |
| /context/formulas | 🔴 Broken | Primary | Type mismatch error |
| /context/agents | 🔴 Broken | Primary | Server 500 |
| /context/ontology | 🔴 Broken | Primary | Server 500 |

**Context Engine:** 4 Working | 4 Broken | 0 Ghost

---

## Workflow (4 Routes)

| Route | Status | Type | Notes |
|-------|--------|------|------- |
| /workflow/prospect | ✅ Working | Primary | Guided value-case creation |
| /workflow/intelligence | 🔴 Broken | Primary | Redirects to /accounts |
| /workflow/:id | 👻 Ghost | Parameterized | Falls back to Home |
| /workflow | ✅ Working | Alias | Redirects to /workflow/prospect |

**Workflow:** 2 Working | 1 Broken | 1 Ghost

---

## Deliverables (7 Routes)

| Route | Status | Type | Notes |
|-------|--------|------|------- |
| /deliverables | ✅ Working | Primary | |
| /deliverables/reports | ✅ Working | Primary | |
| /deliverables/presentations | ✅ Working | Primary | |
| /deliverables/documents | ✅ Working | Primary | |
| /deliverables/exports | ✅ Working | Primary | |
| /deliverables/calculators | 🟡 Tier-Gated | Primary | Requires "advanced" tier |
| /deliverables/api | 🟡 Tier-Gated | Primary | Requires "admin" tier |

**Deliverables:** 5 Working | 0 Broken | 0 Ghost | 2 Tier-Gated

---

## Governance (9 Routes)

| Route | Status | Type | Notes |
|-------|--------|------|------- |
| /governance | ✅ Working | Primary | |
| /governance/traces | ✅ Working | Primary | |
| /governance/evidence | 🟡 Warning | Primary | Infinite spinner |
| /governance/provenance | 👻 Ghost | Primary | Silently renders Home |
| /governance/integrity | 👻 Ghost | Primary | Silently renders Home |
| /governance/compliance | 👻 Ghost | Primary | Silently renders Home |
| /governance/benchmarks | 👻 Ghost | Primary | Silently renders Home |
| /governance/audit/log | 👻 Ghost | Primary | Silently renders Home |
| /governance/audit/changes | 👻 Ghost | Primary | Silently renders Home |
| /governance/health | 👻 Ghost | Primary | Silently renders Home |

**Governance:** 2 Working | 1 Warning | 0 Broken | 7 Ghost

---

## Settings (14 Routes)

| Route | Status | Type | Notes |
|-------|--------|------|------- |
| /settings | 👻 Ghost | Primary | Silently renders Home |
| /settings/formulas | 👻 Ghost | Primary | Silently renders Home |
| /settings/versions | 👻 Ghost | Primary | Silently renders Home |
| /settings/approvals | 👻 Ghost | Primary | Silently renders Home |
| /settings/variables | 👻 Ghost | Primary | Silently renders Home |
| /settings/bindings | 👻 Ghost | Primary | Silently renders Home |
| /settings/quality | 👻 Ghost | Primary | Silently renders Home |
| /settings/roles | 👻 Ghost | Primary | Silently renders Home |
| /settings/teams | 👻 Ghost | Primary | Silently renders Home |
| /settings/keys | 👻 Ghost | Primary | Silently renders Home |
| /settings/system | 👻 Ghost | Primary | Silently renders Home |
| /settings/billing | 👻 Ghost | Primary | Silently renders Home |
| /settings/billing/plans | 👻 Ghost | Primary | Silently renders Home |
| /settings/billing/usage | 👻 Ghost | Primary | Silently renders Home |
| /settings/billing/invoices | 👻 Ghost | Primary | Silently renders Home |

**Settings:** 0 Working | 0 Broken | 14 Ghost

---

## Command Center

| Route | Status | Type | Notes |
|-------|--------|------|------- |
| /command-center | ✅ Working | Primary | Synthesize input, empty state |

**Command Center:** 1 Working | 0 Broken | 0 Ghost

---

## Dev

| Route | Status | Type | Notes |
|-------|--------|------|------- |
| /dev/integration | 👻 Ghost | Primary | Silently renders Home |

**Dev:** 0 Working | 0 Broken | 1 Ghost

---

## 404 Catch-All

| Route | Status | Type | Notes |
|-------|--------|------|------- |
| * | ✅ Working | Catch-all | Proper 404 page |

---

## Summary by Category

| Category | Total | ✅ Working | 🔴 Broken | 👻 Ghost | 🟡 Warning |
|----------|-------|------------|-----------|----------|------------|
| Core Workflow | 4 | 3 | 1 | 0 | 0 |
| Intelligence | 20 | 0 | 20 | 0 | 0 |
| Studio | 23 | 0 | 23 | 0 | 0 |
| Model/Value Studio | 3 | 0 | 3 | 0 | 0 |
| Context Engine | 8 | 4 | 4 | 0 | 0 |
| Workflow | 4 | 2 | 1 | 1 | 0 |
| Deliverables | 7 | 5 | 0 | 0 | 2 |
| Governance | 9 | 2 | 0 | 7 | 1 |
| Settings | 14 | 0 | 0 | 14 | 0 |
| Command Center | 1 | 1 | 0 | 0 | 0 |
| Dev | 1 | 0 | 0 | 1 | 0 |
| **TOTAL** | **94** | **17** | **52** | **22** | **3** |

---

## Fix Priority Matrix

### P0 — Fix Immediately (Unblocks Everything)
- Fix /accounts API 500 error
- Fix Home "Launch" button
- Persist auth tokens (localStorage/cookies)

### P1 — Fix Before Demo/Launch
- Fix API response types (string → array) for Value Packs & Formulas
- Fix Agents and Ontology 500 errors
- Add timeout/error fallback for /governance/evidence spinner
- Show proper 404 for ghost routes

### P2 — Fix Before Release
- Implement Settings section (14 ghost routes)
- Implement remaining Governance pages (7 ghost routes)
- Fix sidebar nav links (Intelligence sub-items)
- Make CO-PILOT, Support, Feedback, Profile functional
- Fix dashboard empty state (misleading percentages)
- Add CRM sync feedback

### P3 — Architecture Consideration
- Reconsider WorkspaceContextRedirect pattern
- Consider standalone Intelligence/Studio pages
- Persist last-selected account context
