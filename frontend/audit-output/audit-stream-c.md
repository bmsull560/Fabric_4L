# Audit Stream C — Governance, Settings, Edge Cases
**Date:** 2026-04-28  
**Routes Audited:** 27

---

## Governance Section (9 Routes)

| Route | Status | Issue |
|-------|--------|-------|
| /governance | ✅ Working | Main governance page |
| /governance/traces | ✅ Working | Decision Traces with filters, empty data |
| /governance/evidence | ⚠️ Partial | Page renders but "Loading truths..." spinner never resolves |
| /governance/provenance | 👻 Ghost | Silently renders Home page |
| /governance/integrity | 👻 Ghost | Silently renders Home page |
| /governance/compliance | 👻 Ghost | Silently renders Home page |
| /governance/benchmarks | 👻 Ghost | Silently renders Home page |
| /governance/audit/log | 👻 Ghost | Silently renders Home page |
| /governance/audit/changes | 👻 Ghost | Silently renders Home page |
| /governance/health | 👻 Ghost | Silently renders Home page |

### /governance/evidence — Infinite Spinner Details

**Issue:** "Loading truths..." spinner runs forever

**Problems:**
- No timeout
- No error fallback
- Page never resolves
- No way for user to recover

---

## Settings Section (14 Routes)

**Status:** 👻 ALL Ghost Routes

All `/settings/*` routes are defined in the router but no page components exist. They silently render the Home page with a misleading URL.

### Affected Routes

| Route | Expected Content |
|-------|------------------|
| /settings | Settings dashboard |
| /settings/formulas | Formula management |
| /settings/versions | Version control |
| /settings/approvals | Approval workflows |
| /settings/variables | Variable configuration |
| /settings/bindings | Data bindings |
| /settings/quality | Quality settings |
| /settings/roles | Role management |
| /settings/teams | Team configuration |
| /settings/keys | API keys |
| /settings/system | System settings |
| /settings/billing | Billing management |
| /settings/billing/plans | Plan selection |
| /settings/billing/usage | Usage tracking |
| /settings/billing/invoices | Invoice history |

---

## Dev Section (1 Route)

| Route | Status | Issue |
|-------|--------|-------|
| /dev/integration | 👻 Ghost | Silently renders Home page |

---

## Edge Cases & UI Issues

### CO-PILOT Feature

**Status:** 🟡 Non-Functional

- Shows as label with green status dot in sidebar
- **Not clickable**
- No way to open AI assistant panel

---

### User Profile Dropdown

**Status:** 🟡 Non-Functional

- Shows "Dev / dev@example.com" with dropdown chevron
- **Clicking does nothing**
- Dropdown does not open

---

### Support & Feedback Buttons

**Status:** 🟡 Non-Functional

- Both buttons present in sidebar
- **No visible response on click**
- No modals, toasts, or navigation

---

### Sync CRM Button

**Status:** 🟡 No Feedback

- Button clicks
- Shows brief spinner
- **Then nothing** — no success/failure toast or status update

---

## Ghost Routes Summary

**Definition:** Routes defined in router but no page component exists. Instead of showing 404, they silently render the Home page.

| Section | Ghost Routes |
|---------|-------------|
| Governance | 7 |
| Settings | 14 |
| Dev | 1 |
| **TOTAL** | **22** |

---

## 404 Handling

**Status:** ✅ Working

- Catch-all 404 route functional
- Shows proper 404 page for undefined routes

**Issue:** Ghost routes bypass 404 handling because they ARE defined in router (just without components).

---

## Summary

| Category | Total | Working | Broken | Ghost |
|----------|-------|---------|--------|-------|
| Governance | 9 | 2 | 1 | 7 |
| Settings | 14 | 0 | 0 | 14 |
| Dev | 1 | 0 | 0 | 1 |
| **TOTAL** | **24** | **2** | **1** | **22** |
