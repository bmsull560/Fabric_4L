# Value Fabric — UI Audit Executive Summary
**Date:** 2026-04-28  
**App:** Value Fabric Intelligence Platform @ http://localhost:3001  
**Auditor:** Frontend Audit System

---

## Overall Health Score: 🔴 Critical

**App is largely non-functional**

- **82 Primary Pages** audited
- **~12 Pages** render content without errors (15%)
- **~50 Pages** broken by server errors or redirects
- **22 Pages** silently fall back to Home (ghost routes)

---

## Critical Issues (Ship-Blockers)

### 1. /accounts API Returns 500 — Cascading Failure
**Impact:** 🔴 **HIGHEST**

The `/accounts` endpoint 500 error is the single biggest blocker. 31+ routes in Intelligence and Studio sections use `WorkspaceContextRedirect` which redirects to `/accounts` for account selection. With `/accounts` broken, the entire Intelligence → Studio → Deliverables workflow is dead.

**Affected:** All `/intelligence/*`, `/studio/*`, `/model/value-studio/*`, `/workflow/intelligence`

### 2. Home "Launch" Button Fails
**Impact:** 🔴 **HIGHEST**

The primary CTA of the app fails. Users can fill out the entire value case form but the final "Launch" action errors with "Failed to launch intelligence".

### 3. Auth Not Persisted — No Deep Linking
**Impact:** 🔴 **HIGH**

Auth tokens live only in React state. Page reloads or direct URL navigation drop the session, breaking bookmarks, shared links, and refresh functionality.

### 4. 22 Ghost Routes
**Impact:** 🟡 **MEDIUM**

Routes defined in router but no components exist. Instead of 404, they silently render Home with misleading URLs.
- **Governance:** 7 routes
- **Settings:** 14 routes (ALL of them)
- **Dev:** 1 route

### 5. Context Engine — 4 of 8 Pages Broken
**Impact:** 🟡 **MEDIUM**

| Page | Error |
|------|-------|
| Value Packs | Type mismatch: expected array, received string |
| Formulas | Type mismatch: expected array, received string |
| Agents | Server 500 |
| Ontology | Server 500 |

---

## Working Pages (What Functions)

| Page | Status | Notes |
|------|--------|-------|
| /home | ✅ | Form works, Launch fails, dashboard empty |
| /login | ✅ | Dev Bypass, OAuth, form all render |
| /signup | ✅ | Registration functional |
| /command-center | ✅ | Synthesize input, empty state |
| /workflow/prospect | ✅ | Guided value-case creation |
| /governance/traces | ✅ | Decision Traces with filters |
| /governance | ✅ | Main page renders |
| /context/models | ✅ | My Models with skeleton loading |
| /context/value-trees/explorer | ✅ | Tree Explorer |
| /context/ingestion/jobs | ✅ | Job queue |
| /context/extraction | ✅ | Extraction Engine |
| /deliverables | ✅ | Main page (5/7 routes working) |
| 404 catch-all | ✅ | Proper 404 page |

**~12 of 82 primary pages (15%) fully functional**

---

## By The Numbers

| Category | Total | Working | Broken | Ghost |
|----------|-------|---------|--------|-------|
| Core Workflow | 3 | 1 | 2 | 0 |
| Intelligence | 20 | 0 | 20 | 0 |
| Studio | 23 | 0 | 23 | 0 |
| Context Engine | 8 | 4 | 4 | 0 |
| Deliverables | 7 | ~5 | 0 | 0 |
| Governance | 9 | 2 | 0 | 7 |
| Settings | 14 | 0 | 0 | 14 |
| Workflow/Misc | 4 | 2 | 1 | 1 |
| Auth | 3 | 3 | 0 | 0 |
| **TOTAL** | **91** | **~17** | **~50** | **~22** |

---

## Recommended Fix Priority

### P0 — Fix Immediately
1. **Fix /accounts API 500 error** — Unblocks 31+ Intelligence/Studio routes
2. **Fix Home "Launch" button** — Primary app action must work
3. **Persist auth tokens in localStorage/cookies** — Enable deep linking and refresh

### P1 — Fix Before Demo
1. Fix API response types for Value Packs & Formulas (string → array)
2. Fix Agents and Ontology 500 errors in Context Engine
3. Add timeout/error fallback for /governance/evidence infinite spinner
4. Show proper 404 for unimplemented routes instead of silent Home fallback

### P2 — Fix Before Release
1. Implement Settings section (14 ghost routes)
2. Implement remaining Governance pages (7 ghost routes)
3. Fix sidebar nav links — Intelligence sub-items shouldn't navigate to /accounts
4. Make CO-PILOT, Support, Feedback, Profile dropdown functional
5. Fix dashboard empty state (remove misleading percentages on zero values)
6. Add CRM sync feedback and fix export-on-error behavior

### P3 — Architecture
- Reconsider `WorkspaceContextRedirect` pattern
- Consider standalone Intelligence/Studio pages
- Persist last-selected account context

---

## Raw Audit Data Files

- `audit-stream-a.md` — Home, Accounts, Auth
- `audit-stream-a-context.md` — Context Engine (8 pages)
- `audit-stream-b.md` — Intelligence, Studio, Deliverables (58 routes)
- `audit-stream-c.md` — Governance, Settings, Edge Cases (27 routes)
- `route-map.md` — Complete 154-route inventory

---

## Conclusion

**Current State:** The Value Fabric Intelligence Platform is in a critical state with only ~15% of pages fully functional. The cascading failure from the `/accounts` API 500 error blocks the majority of the app's core workflow (Intelligence → Studio → Deliverables).

**Immediate Action Required:** Fix the `/accounts` API, Home Launch button, and auth persistence to unblock the primary user journey.
