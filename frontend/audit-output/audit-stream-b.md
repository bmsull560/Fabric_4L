# Audit Stream B — Intelligence, Studio, Deliverables
**Date:** 2024-04-28  
**Routes Audited:** 58

---

## Intelligence Section (20 Routes)

**Status:** 🔴 All 20 Routes Broken

### Root Cause
All Intelligence routes use `WorkspaceContextRedirect` which sends users to `/accounts`. Since `/accounts` returns 500, these routes are inaccessible.

### Affected Routes

| Route | Expected | Actual Behavior |
|-------|----------|-----------------|
| /intelligence | Intelligence dashboard | Redirects to /accounts (500) |
| /intelligence/signals | Signals list | Redirects to /accounts (500) |
| /intelligence/drivers | Value drivers | Redirects to /accounts (500) |
| /intelligence/evidence | Evidence base | Redirects to /accounts (500) |
| /intelligence/cases | Value cases | Redirects to /accounts (500) |
| /intelligence/insights | AI insights | Redirects to /accounts (500) |
| /intelligence/narratives | Value narratives | Redirects to /accounts (500) |
| /intelligence/research | Research data | Redirects to /accounts (500) |
| /intelligence/benchmarks | Benchmark data | Redirects to /accounts (500) |
| /intelligence/competitors | Competitive intel | Redirects to /accounts (500) |
| /intelligence/trends | Market trends | Redirects to /accounts (500) |
| /intelligence/roi | ROI analysis | Redirects to /accounts (500) |
| /intelligence/impact | Impact assessment | Redirects to /accounts (500) |
| /intelligence/risk | Risk analysis | Redirects to /accounts (500) |
| /intelligence/opportunities | Opportunities | Redirects to /accounts (500) |
| /intelligence/threats | Threat detection | Redirects to /accounts (500) |
| /intelligence/recommendations | AI recommendations | Redirects to /accounts (500) |
| /intelligence/actions | Action items | Redirects to /accounts (500) |
| /intelligence/plan | Strategic plan | Redirects to /accounts (500) |
| /intelligence/summary | Executive summary | Redirects to /accounts (500) |

### Sidebar Mismatch
Clicking "Signals", "Drivers", "Evidence" in sidebar navigates to `/accounts` instead of the labeled destination.

---

## Studio Section (23 Routes)

**Status:** 🔴 All 23 Routes Broken

### Same Root Cause
Studio routes also use `WorkspaceContextRedirect` → `/accounts` (500 error)

### Affected Routes
All `/studio/*` routes including:
- /studio
- /studio/models
- /studio/formulas
- /studio/ontologies
- /studio/agents
- /studio/workflows
- /studio/templates
- /studio/components
- /studio/assets
- /studio/datasets
- /studio/integrations
- /studio/publish
- /studio/share
- /studio/collaborate
- /studio/review
- /studio/approve
- /studio/deploy
- /studio/monitor
- /studio/analytics
- /studio/settings
- /studio/help
- /studio/feedback
- /studio/tutorials

---

## Model/Value Studio (3 Routes)

**Status:** 🔴 All Broken

| Route | Behavior |
|-------|----------|
| /model/value-studio | Redirects to /accounts |
| /model/value-studio/create | Redirects to /accounts |
| /model/value-studio/edit/:id | Redirects to /accounts |

---

## Workflow/Intelligence (2 Routes)

| Route | Status | Notes |
|-------|--------|-------|
| /workflow/intelligence | 🔴 Broken | Redirects to /accounts |
| /workflow/prospect | ✅ Working | Guided value-case creation functional |

---

## Deliverables Section (7 Routes)

**Status:** 🟡 Partially Working

### Working Routes (~5)

| Route | Status | Notes |
|-------|--------|-------|
| /deliverables | ✅ Working | Main deliverables page |
| /deliverables/reports | ✅ Working | Reports list |
| /deliverables/presentations | ✅ Working | Presentations |
| /deliverables/documents | ✅ Working | Documents |
| /deliverables/exports | ✅ Working | Data exports |

### Tier-Gated Routes (Potentially Blocked)

| Route | Required Tier | Notes |
|-------|-------------|-------|
| /deliverables/calculators | "advanced" | Dev user is "standard" tier — may show access-denied |
| /deliverables/api | "admin" | Dev user is "standard" tier — may show access-denied |

---

## Summary

| Section | Total Routes | Working | Broken |
|---------|-------------|---------|--------|
| Intelligence | 20 | 0 | 20 |
| Studio | 23 | 0 | 23 |
| Model/Value Studio | 3 | 0 | 3 |
| Workflow/Intelligence | 2 | 1 | 1 |
| Deliverables | 7 | ~5 | 0 (2 tier-gated) |
| **TOTAL** | **55** | **~6** | **~47** |

---

## Key Issue

**WorkspaceContextRedirect Pattern Problem:**

All Intelligence and Studio routes require pre-selecting an account context. The redirect pattern:
1. User navigates to `/intelligence/signals`
2. `WorkspaceContextRedirect` checks for active account
3. No account selected → redirect to `/accounts`
4. `/accounts` returns 500
5. **Dead end** — user cannot proceed

**Recommendation:** 
- Fix `/accounts` API (immediate)
- OR implement standalone pages that don't require pre-selected account
- OR persist last-selected account context
