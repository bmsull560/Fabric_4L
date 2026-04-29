# Audit Stream A — Core Workflow & Accounts
**Date:** 2026-04-28  
**App:** Value Fabric Intelligence Platform @ http://localhost:3001

---

## /home — Home Page

**Status:** ✅ Partially Working

### Working
- Page renders correctly
- Form fields functional (Company details, Buying context, Stakeholders)
- Dashboard empty state displays

### Broken
- **"Launch" button fails**
  - Error: "Failed to launch intelligence"
  - Impact: Primary CTA non-functional
  - Users can fill out the entire form but cannot execute

### UI Issues
- Dashboard stats show misleading percentages on zero values (e.g., "0 (+12%)")

---

## /accounts — Account Selection

**Status:** 🔴 Critical — Complete Failure

### Error
```
Failed to load accounts — Request failed with status code 500
```

### Impact
- **Cascading failure** — This is the single biggest blocker
- Intelligence and Studio sections (31+ routes) use `WorkspaceContextRedirect`
- All redirect to /accounts to pick account context
- Since /accounts is broken, entire Intelligence → Studio → Deliverables workflow is dead

### Affected Routes
- All `/intelligence/*` routes (20 routes)
- All `/studio/*` routes (23 routes)
- `/model/value-studio/*`
- `/workflow/intelligence`

### Additional Issues
- Export button generates `accounts-2026-04-28.csv` even on 500 error
- Likely exports empty or header-only file

---

## /login — Authentication

**Status:** ✅ Working

- Dev Bypass button functional
- OAuth buttons render
- Form validation works

---

## /signup — Registration

**Status:** ✅ Working

- Registration page renders correctly

---

## Auth Persistence — Cross-Cutting Issue

**Status:** 🔴 Critical

### Behavior
- Auth token lives only in React state
- Full page reload or direct URL navigation drops session
- Redirects to /login

### Impact
- Users cannot bookmark pages
- Cannot share links
- Cannot refresh without losing session
- Breaks navigation to /context/* routes when entered directly

---

## Summary

| Page | Status | Blocker Level |
|------|--------|---------------|
| /home | ⚠️ Partial | P1 |
| /accounts | 🔴 Broken | P0 |
| /login | ✅ Working | — |
| /signup | ✅ Working | — |
| Auth Persistence | 🔴 Broken | P0 |
