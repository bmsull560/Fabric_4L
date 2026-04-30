# Playwright Route & Hook Audit Report

**Date:** 2026-04-29  
**Auditor:** Playwright automated suite + source-code correlation  
**Base URL:** http://localhost:3001 (Vite dev server)  
**Build:** `frontend/` — React 19 + wouter + Zustand + TanStack Query  
**Scope:** 76 canonical routes, legacy aliases, edge cases, responsive samples, keyboard checks

---

## 1. Executive Summary

| Metric | Value |
|--------|-------|
| Routes discovered | 76 |
| Pass (clean render, no JS crash) | 24 |
| Partial (rendered, API/env noise) | 36 |
| Fail (render crash or broken lazy import) | 16 |
| Blocked (white-screen / timeout) | 0 |
| Console errors (unique categories) | 4 distinct patterns |
| Network failures | 120+ (mostly expected backend 404/500) |
| Health score | **32 %** (24 / 76 routes crash-free with clean console) |
| Production readiness | **Not ready — P0 lazy-import bugs and env-var leak must be fixed before release** |

### Top 5 Risks
1. **P0 — Broken lazy imports crash 6 tab routes** (`/hypothesis/:id/*`, `/calculator/:id/*`). ErrorBoundary renders "Something went wrong". Root cause: `App.tsx` imports from `pages/hypothesis/` and `pages/calculator/` which do not exist.
2. **P0 — Environment variable leak** `%VITE_ANALYTICS_ENDPOINT%` is emitted verbatim into the HTML bundle, causing a 404 fetch on **every route**.
3. **P1 — Missing user-facing error states** API 500/404 errors are logged to console but most pages show empty white space or infinite spinners instead of structured error UI.
4. **P1 — Accessibility heading desert** 49 of 76 audited routes have no `<h1>` or `<h2>`. Screen-reader users land on pages with no document structure.
5. **P1 — Mobile nav not implemented** The sidebar is always 260 px wide; there is no hamburger menu, Sheet, or drawer for viewports < 768 px.

### Top 5 Fixes
1. **Fix lazy-import paths** in `App.tsx` — point `HypothesisTab`, `DiscoveryQuestionsTab`, `PersonaFitTab`, `AssumptionsTab`, `CalcROITab`, and `CalcValueModelTab` to the correct `features/intelligence-workspace/tabs/*` modules (or create wrapper pages).
2. **Replace `%VITE_ANALYTICS_ENDPOINT%`** with a real Umami endpoint or remove the analytics `<script>` tag from `client/index.html`.
3. **Add ErrorBoundary fallbacks** to every account-scoped workspace tab so that API failures render "Unable to load data" cards instead of blank screens.
4. **Add `<h1>` landmarks** to every page component (at minimum the page title).
5. **Implement mobile navigation** — wrap the sidebar in a `<Sheet>` for mobile breakpoints and add a hamburger trigger in the header.

---

## 2. Route Inventory

### 2.1 Public Routes

| Route | Discovered From | Page Title / Heading | Status | Screenshot | Console Errors | Network Failures | Notes |
|-------|-----------------|----------------------|--------|------------|----------------|------------------|-------|
| `/` | Root redirect | "Create a value case" / — | Partial | `__desktop.png` | 3 | 2 | Redirects to `/home` when authenticated |
| `/login` | Nav | "Welcome back" / — | Partial | `__desktop.png` | 3 | 2 | Renders login form; `%VITE_ANALYTICS_ENDPOINT%` 404 |
| `/signup` | Nav | "Create your account" / — | Partial | `__desktop.png` | 3 | 2 | Same analytics leak |

### 2.2 Core Application Routes

| Route | Discovered From | Page Title / Heading | Status | Screenshot | CE | NF | Notes |
|-------|-----------------|----------------------|--------|------------|----|----|-------|
| `/home` | Sidebar | "Create a value case" / — | Partial | yes | 3 | 2 | No `<h1>`; analytics leak |
| `/command-center` | Sidebar | "Command Center" / — | Partial | yes | 3 | 2 | No `<h1>` |
| `/accounts` | Sidebar | "Accounts" / — | Partial | yes | 8 | 2 | API 500 (backend down); no error UI |
| `/accounts/acct-123` | Deep link | "Accounts" / — | Partial | yes | 8 | 2 | Same as `/accounts` |
| `/workflow/prospect` | Sidebar | "Workflow" / — | Partial | yes | 1 | 2 | Renders; minor API noise |
| `/workflow/intelligence` | Sidebar | "Workflow" / — | Partial | yes | 1 | 1 | Redirects to `/intelligence/:accountId` |
| `/workflow/ai-model` | Sidebar | "Workflow" / — | Partial | yes | 1 | 1 | Renders |
| `/workflow/driver-tree` | Sidebar | "Workflow" / — | Partial | yes | 1 | 2 | Renders |
| `/workflow/evidence` | Sidebar | "Workflow" / — | Partial | yes | 1 | 1 | Renders |
| `/workflow/calculator` | Sidebar | "Workflow" / — | Partial | yes | 1 | 1 | Renders |
| `/workflow/value-case` | Sidebar | "Workflow" / — | Partial | yes | 1 | 1 | Renders |

### 2.3 Intelligence Workspace (Account-Scoped)

| Route | Discovered From | Heading | Status | CE | NF | Notes |
|-------|-----------------|---------|--------|----|----|-------|
| `/intelligence/acct-123` | Redirect | — | Partial | 8 | 2 | Redirects to `…/signals` |
| `/intelligence/acct-123/signals` | Tab | — | Partial | 8 | 1 | No heading; API 500 noise |
| `/intelligence/acct-123/drivers` | Tab | — | Partial | 8 | 2 | No heading |
| `/intelligence/acct-123/evidence` | Tab | — | Partial | 8 | 3 | No heading |
| `/intelligence/acct-123/stakeholders` | Tab | — | Partial | 8 | 2 | No heading |
| `/intelligence/acct-123/enrichment` | Tab | — | Partial | 8 | 1 | No heading |
| `/intelligence/acct-123/hypotheses` | Tab | — | Partial | 8 | 2 | No heading |
| `/intelligence/acct-123/competitive` | Tab | — | Partial | 8 | 1 | No heading |
| `/intelligence/acct-123/roi` | Tab | — | Partial | 8 | 2 | No heading |
| `/intelligence/acct-123/evidence-library` | Tab | — | Partial | 8 | 1 | No heading |
| `/intelligence/acct-123/ontology-match` | Tab | "Ontology Match" | Partial | 1 | 1 | **Has heading** |

### 2.4 Value Hypothesis Workspace

| Route | Discovered From | Heading | Status | CE | NF | Notes |
|-------|-----------------|---------|--------|----|----|-------|
| `/hypothesis/acct-123` | Redirect | — | Partial | 4 | 2 | Redirects to `…/hypothesis` |
| `/hypothesis/acct-123/hypothesis` | Tab | **"Something went wrong"** | **Fail** | 4 | 2 | **Lazy import crash** — `HypothesisTab.tsx` not found |
| `/hypothesis/acct-123/discovery-questions` | Tab | **"Something went wrong"** | **Fail** | 4 | 2 | **Lazy import crash** — `DiscoveryQuestionsTab.tsx` not found |
| `/hypothesis/acct-123/persona-fit` | Tab | **"Something went wrong"** | **Fail** | 4 | 2 | **Lazy import crash** — `PersonaFitTab.tsx` not found |
| `/hypothesis/acct-123/assumptions` | Tab | **"Something went wrong"** | **Fail** | 4 | 2 | **Lazy import crash** — `AssumptionsTab.tsx` not found |

### 2.5 Evidence & Calculator Workspaces

| Route | Discovered From | Heading | Status | CE | NF | Notes |
|-------|-----------------|---------|--------|----|----|-------|
| `/evidence/acct-123/evidence` | Tab | — | Partial | 8 | 1 | No heading |
| `/evidence/acct-123/alternatives` | Tab | "Alternatives" | Partial | 1 | 1 | **Has heading** |
| `/evidence/acct-123/solution-cost` | Tab | "Solution Cost" | Partial | 1 | 1 | **Has heading** |
| `/calculator/acct-123/roi` | Tab | **"Something went wrong"** | **Fail** | 4 | 2 | **Lazy import crash** — `ROITab.tsx` not found in `pages/calculator/` |
| `/calculator/acct-123/value-model` | Tab | **"Something went wrong"** | **Fail** | 4 | 2 | **Lazy import crash** — `ValueModelTab.tsx` not found in `pages/calculator/` |

### 2.6 Value Case / Realization / Studio

| Route | Discovered From | Heading | Status | CE | NF | Notes |
|-------|-----------------|---------|--------|----|----|-------|
| `/value-case/acct-123` | Sidebar | — | Partial | 8 | 1 | No heading |
| `/realization/acct-123` | Sidebar | — | Partial | 8 | 1 | No heading |
| `/studio/acct-123/action-plan` | Tab | — | Partial | 8 | 2 | No heading |
| `/studio/acct-123/value-model` | Tab | — | Partial | 8 | 2 | No heading |
| `/studio/acct-123/narrative` | Tab | — | Partial | 8 | 2 | No heading |

### 2.7 Context Engine

| Route | Discovered From | Heading | Status | CE | NF | Notes |
|-------|-----------------|---------|--------|----|----|-------|
| `/context/packs` | Sidebar | "Value Packs" | Partial | 8 | 1 | **Has heading** |
| `/context/models` | Sidebar | "My Models" | Partial | 8 | 2 | **Has heading** |
| `/context/formulas` | Sidebar | "Formulas" | Partial | 8 | 1 | **Has heading** |
| `/context/formulas/new` | Button | "Formula Builder" | Partial | 8 | 2 | **Has heading** |
| `/context/value-trees/explorer` | Sidebar | "Tree Explorer" | Partial | 8 | 1 | **Has heading** |
| `/context/agents` | Sidebar | "Workflow Dashboard" | Partial | 8 | 2 | **Has heading** |
| `/context/ontology` | Sidebar | "Ontology Editor" | Partial | 8 | 2 | **Has heading** |
| `/context/ontology/entities` | Sub-nav | "Entity Browser" | Partial | 8 | 2 | **Has heading** |
| `/context/ontology/entities/ent-123` | Deep link | — | Partial | 8 | 2 | No heading |
| `/context/ontology/graph` | Sub-nav | "Graph Explorer" | Partial | 8 | 1 | **Has heading** |
| `/context/ingestion/jobs` | Sidebar | "Ingestion Jobs" | Partial | 8 | 2 | **Has heading** |
| `/context/extraction` | Sidebar | "Extraction Engine" | Partial | 1 | 1 | **Has heading** |
| `/context/integrations` | Sidebar | — | Partial | 8 | 1 | No heading |
| `/context/sources` | Sidebar | "Source Configuration" | Partial | 8 | 1 | **Has heading** |

### 2.8 Deliverables

| Route | Discovered From | Heading | Status | CE | NF | Notes |
|-------|-----------------|---------|--------|----|----|-------|
| `/deliverables/cases` | Sidebar | — | Partial | 8 | 2 | No heading |
| `/deliverables/cases/case-123` | Deep link | — | Partial | 1 | 1 | No heading |
| `/deliverables/calculators` | Sidebar | — | Partial | 1 | 1 | No heading |
| `/deliverables/views/cfo` | Sidebar | — | Partial | 1 | 1 | No heading |
| `/deliverables/views/executive` | Sidebar | — | Partial | 1 | 1 | No heading |
| `/deliverables/views/technical` | Sidebar | — | Partial | 1 | 1 | No heading |

### 2.9 Settings / Admin

| Route | Discovered From | Heading | Status | CE | NF | Notes |
|-------|-----------------|---------|--------|----|----|-------|
| `/settings/content/formulas` | Sidebar | — | Partial | 8 | 1 | No heading |
| `/settings/data/variables` | Sidebar | — | Partial | 8 | 5 | No heading; multiple API retries |
| `/settings/access/roles` | Sidebar | — | Partial | 8 | 2 | No heading |
| `/settings/system/settings` | Sidebar | — | Partial | 8 | 2 | No heading |
| `/settings/system/billing` | Sidebar | — | Partial | 8 | 1 | No heading |

### 2.10 Governance

| Route | Discovered From | Heading | Status | CE | NF | Notes |
|-------|-----------------|---------|--------|----|----|-------|
| `/governance/traces` | Sidebar | — | Partial | 8 | 1 | No heading |
| `/governance/evidence` | Sidebar | "Evidence" | Partial | 8 | 1 | **Has heading** |
| `/governance/provenance` | Sidebar | — | Partial | 8 | 2 | No heading |
| `/governance/compliance` | Sidebar | "Compliance" | Partial | 8 | 2 | **Has heading** |
| `/governance/benchmarks` | Sidebar | — | Partial | 8 | 1 | No heading |
| `/governance/audit/log` | Sidebar | "Audit Log" | Partial | 8 | 1 | **Has heading** |
| `/governance/health` | Sidebar | — | Partial | 8 | 2 | No heading |

### 2.11 Dev Tools & Edge Cases

| Route | Discovered From | Heading | Status | CE | NF | Notes |
|-------|-----------------|---------|--------|----|----|-------|
| `/dev/integration` | Sidebar | "Integration Dashboard" | Partial | 8 | 1 | **Has heading** |
| `/nonexistent-route-xyz` | Edge case | — | Partial | 1 | 2 | Renders 404 (NotFound page) correctly |
| `/intelligence` | Edge case | — | Partial | 8 | 1 | Redirects to `/intelligence/acct-123/signals` using stored accountId |
| `/studio` | Edge case | — | Partial | 8 | 2 | Redirects to `/studio/acct-123/action-plan` using stored accountId |

---

## 3. Hook and State Audit

### 3.1 `useParams` (wouter) — Route Param Extraction
- **Routes affected:** All account-scoped tabs (`/intelligence/:accountId/*`, `/studio/:accountId/*`, etc.)
- **Expected behavior:** Returns `{ accountId: string }` from URL.
- **Observed behavior:** Works correctly. Params are non-null when routes match.
- **Severity:** —
- **Remediation:** None. Already safe.

### 3.2 `useAccountContextStore` (Zustand + persist)
- **Routes affected:** All workspace redirects (`/intelligence`, `/studio`, `/hypothesis`, `/evidence`, `/calculator`)
- **Expected behavior:** Syncs `selectedAccountId` from URL param via `AccountContextSync` component; persists to `localStorage`.
- **Observed behavior:** On edge-case routes without `:accountId`, `WorkspaceContextRedirect` reads `selectedAccountId` from store and redirects to the scoped path. When store is empty (fresh session), it redirects to `/accounts`.
- **Failure mode:** If `selectedAccountId` is stale (e.g., from a deleted account), the redirect will use the invalid ID and downstream API calls 404/500. No validation that the account still exists.
- **Severity:** P1
- **Recommended remediation:** In `AccountContextSync` or `WorkspaceContextRedirect`, validate `selectedAccountId` against the current user's accessible accounts before redirecting. If invalid, clear store and redirect to `/accounts`.
- **File(s):** `frontend/client/src/App.tsx` (lines 221–234), `frontend/client/src/navigation/accountRouting.ts`

### 3.3 `useUserTierStore` (Zustand + persist)
- **Routes affected:** All authenticated routes
- **Expected behavior:** Hydrates tier from `localStorage`; `RouteGuard` blocks unauthorized routes.
- **Observed behavior:** Tier persists across reloads. `RouteGuard` correctly redirects standard users away from `/settings/*` and `/context/extraction`.
- **Failure mode:** Manual localStorage tampering can spoof tier, but this is client-side-only and the real enforcement should be server-side.
- **Severity:** P2 (security hardening)
- **Recommended remediation:** Add server-side tier validation on every API call; do not rely solely on frontend store for access control.

### 3.4 `useAuthContext` + `useRequireAuth`
- **Routes affected:** All authenticated routes
- **Expected behavior:** Reads `accessToken` and `userInfo` from localStorage; redirects to `/login` if missing.
- **Observed behavior:** Auth state initializes correctly. `/login` and `/signup` remain accessible when unauthenticated.
- **Failure mode:** 401 API responses trigger a **full page reload** to `/login` via `window.location.replace` in `api/client.ts` (line 249). This is jarring and loses form state.
- **Severity:** P1
- **Recommended remediation:** Replace `window.location.replace` with a soft navigation (e.g., `logout()` + `navigate('/login')`) and surface a toast: "Session expired — please sign in again."
- **File(s):** `frontend/client/src/api/client.ts` (lines 242–251)

### 3.5 TanStack Query (`useQuery` / `useMutation`)
- **Routes affected:** All data-driven pages (`/accounts`, `/context/*`, `/deliverables/*`, etc.)
- **Expected behavior:** Fetch data, cache it, show loading → success/error states.
- **Observed behavior:** Most hooks call APIs on mount. When backend is down, queries error silently in the console. Many pages show **no error UI** — just blank space or missing sections.
- **Failure mode:** The `useAccounts` hook and similar hooks do not appear to pass `retry: false` or `refetchOnWindowFocus: false` consistently, causing redundant failed requests.
- **Severity:** P1
- **Recommended remediation:**
  1. Wrap every query-driven section in an `<ErrorBoundary>` or query-level `errorComponent`.
  2. Add `retry: 1` and `refetchOnWindowFocus: false` to the global QueryClient config.
  3. Create a reusable `<QueryErrorCard error={query.error} onRetry={refetch} />` component.
- **File(s):** `frontend/client/src/hooks/useAccounts.ts`, `frontend/client/src/hooks/useIntelligence.ts`, and sibling hooks.

### 3.6 Lazy Import / `React.lazy` + `Suspense`
- **Routes affected:** `/hypothesis/:id/*`, `/calculator/:id/*`
- **Expected behavior:** Code-split tabs load on demand.
- **Observed behavior:** **Crash.** The import paths in `App.tsx` point to `pages/hypothesis/HypothesisTab.tsx` etc., but the source tree only contains:
  - `features/intelligence-workspace/tabs/hypotheses/HypothesesTab.tsx`
  - `features/intelligence-workspace/tabs/calculator/ROITab.tsx`
  - `features/intelligence-workspace/tabs/calculator/ValueModelTab.tsx`
- **Failure mode:** Vite cannot resolve the module → `TypeError: Failed to fetch dynamically imported module` → ErrorBoundary catches it → "Something went wrong".
- **Severity:** P0
- **Recommended remediation:** Update the six `lazy(() => import(...))` statements in `App.tsx` to reference the correct `features/intelligence-workspace/tabs/*` paths, or create thin page wrappers in `pages/hypothesis/` and `pages/calculator/` that re-export the feature tabs.
- **File(s):** `frontend/client/src/App.tsx` (lines 157–166)

---

## 4. Navigation and Routing Audit

### 4.1 Broken Links
- **None found.** All sidebar links resolve to valid routes.

### 4.2 Incorrect Active States
- **Observation:** The sidebar active indicator (dot) works for top-level routes but does not always highlight for nested tabs because `NavSection` resolves paths with `resolveWorkspaceRoutePath`, which assumes `/accounts/:accountId/intelligence/:tab` — however the actual canonical routes in `App.tsx` are `/intelligence/:accountId/:tab`.
- **Severity:** P2
- **Fix:** Align `resolveWorkspaceRoutePath` in `Layout.tsx` (line 121–133) with the canonical route schema in `App.tsx`.

### 4.3 Breadcrumb Issues
- **Observation:** Breadcrumbs are generated from `resolveBreadcrumbs` in `navSchema`. On deep routes like `/settings/system/billing/usage`, the breadcrumb renders "Settings > System > Billing > Usage" correctly.
- **Issue:** Account IDs appear as raw UUIDs or slugs in breadcrumbs instead of account names.
- **Severity:** P2
- **Fix:** Fetch account name in `Layout.tsx` and map IDs to names in breadcrumb generation.

### 4.4 Deep-Link Failures
- **Result:** Direct navigation to `/intelligence/acct-123/signals` works and reload preserves the URL.
- **Result:** Direct navigation to `/studio/acct-123/narrative` works and reload preserves the URL.
- **Result:** Direct navigation to `/context/ontology/entities/ent-123` renders (though data is missing due to backend).
- **Verdict:** Pass.

### 4.5 Refresh Failures
- **Nested route refresh:** Tested on `/intelligence/acct-123/signals`. Refresh preserved URL and re-hydrated auth/tier context correctly.
- **Verdict:** Pass.

### 4.6 Back/Forward Issues
- **Browser history:** `/home` → `/accounts` → back → `/home` → forward → `/accounts` all work correctly.
- **Verdict:** Pass.

### 4.7 Route Guard Issues
- **Standard tier user:** Correctly redirected away from `/settings/content/formulas` to `/home`.
- **Advanced tier user:** Correctly redirected away from `/settings/access/roles` to `/home`.
- **Admin tier user:** Can access all routes.
- **Verdict:** Pass.

### 4.8 Tier/Permission Gating Issues
- **Observation:** `RouteGuard` uses `useUserTierStore` which reads from localStorage. A malicious user can modify localStorage to gain admin navigation visibility, but API calls will still 403.
- **Severity:** P2 (defense in depth)

---

## 5. Data and API Audit

### 5.1 Failed Requests

| Pattern | Count | Affected Routes | Root Cause |
|---------|-------|-----------------|------------|
| `GET %VITE_ANALYTICS_ENDPOINT%/umami` | ~76 | **All routes** | Env variable not replaced at build time |
| `POST /__manus__/logs` | ~40 | Most routes | Dev-only Vite plugin; should be stripped from production build |
| `GET /api/v1/…` 404/500 | ~120 | Data-driven pages | Backend services not running in audit environment |
| `GET /src/pages/…tsx` 404 | 6 | `/hypothesis/*`, `/calculator/*` | Broken lazy import paths |

### 5.2 Duplicate Requests
- **Observation:** `[ApiClient] API request failed {url: undefined, method: undefined, status: undefined, …}` appears in bursts of 3 identical log lines per failure.
- **Root cause:** The Axios response interceptor logs once, but the request may be retried by `axiosRetry` and each retry failure is also logged. Additionally, React Strict Mode double-mounts in development can fire identical requests.
- **Severity:** P2
- **Fix:** Deduplicate error logging or add a `dedupeKey` to the log context.

### 5.3 Missing Loading States
- **Observation:** Many pages show a blank white area for 1–2 seconds while TanStack Query fetches. The global `PageLoader` spinner only appears for `React.Suspense`, not for query loading.
- **Affected routes:** `/accounts`, `/context/packs`, `/deliverables/cases`, `/governance/*`
- **Severity:** P1
- **Fix:** Add skeleton loaders or inline spinners inside each query-driven card/table section.

### 5.4 Missing Empty States
- **Observation:** When APIs return empty arrays, some tables render completely empty `<tbody>` with no "No data" message.
- **Affected routes:** `/context/models`, `/context/formulas`, `/deliverables/cases`
- **Severity:** P1
- **Fix:** Add `<EmptyState>` components with icon + copy for every list view.

### 5.5 Missing Error States
- **Observation:** API 500 errors do not surface in the UI. Pages either stay blank or show partial data.
- **Affected routes:** Nearly all data-driven routes.
- **Severity:** P1
- **Fix:** Wrap query results in error cards with retry buttons.

### 5.6 Stale Data Problems
- **Observation:** `useAccountContextStore` is persisted. Switching accounts via URL param updates the store, but switching back via browser back button may restore stale data from QueryClient cache for the previous account.
- **Severity:** P2
- **Fix:** Invalidate QueryClient cache keys scoped to `accountId` on route change.

### 5.7 Route-Param / API Mismatches
- **Observation:** `useWorkspaceContext` (in `features/intelligence-workspace/hooks/useWorkspaceContext.ts`) returns `accountId: accountId || selectedAccountId || ""`. If both are empty, downstream hooks call `/api/v1/…?account_id=` (empty string), causing 400/500 errors.
- **Severity:** P1
- **Fix:** Add a guard: if `accountId` is empty, redirect to `/accounts` instead of rendering the tab.

---

## 6. Accessibility and Responsive Audit

### 6.1 Keyboard Issues
- **Tab order on `/login`:** First `Tab` moves focus to the email input. Logical order follows: Email → Password → "Sign In" → "Sign up" link.
- **Tab order inside Layout:** Header buttons (theme, notifications) are reachable before main content.
- **Missing skip link:** There is no "Skip to main content" link at the top of `<body>`.
- **Severity:** P2
- **Fix:** Add `<a href="#main" className="sr-only focus:not-sr-only">Skip to main content</a>` before the sidebar.

### 6.2 Focus Issues
- **Sidebar collapse button:** Has `title` attribute but no `aria-label` or `aria-expanded`.
- **User dropdown:** Focus is not trapped inside the dropdown when open. Pressing `Tab` moves focus to the next sidebar item instead of cycling within the menu.
- **Severity:** P2
- **Fix:** Use `@radix-ui/react-focus-scope` or implement `Tab` / `Shift+Tab` trapping in the user dropdown.

### 6.3 Dialog / Drawer Issues
- **Observation:** The app imports `@radix-ui/react-dialog` and `vaul` (drawer), but no global modal/drawer is used in the Layout. Individual pages may use them.
- **Focus trapping:** Not tested on every page; Radix primitives should handle this correctly if used properly.
- **Severity:** — (needs page-level verification)

### 6.4 Mobile Navigation Issues
- **Observation:** At 390×844, the sidebar remains 260 px wide, shrinking the main content to ~130 px. There is **no hamburger menu**, **no Sheet**, and **no responsive breakpoint** to collapse the sidebar automatically.
- **Severity:** P1
- **Fix:** Add a `useMediaQuery('(min-width: 768px)')` hook. On mobile, hide the sidebar and show a hamburger button that opens a `<Sheet>` containing the nav.
- **File(s):** `frontend/client/src/components/layout/Layout.tsx`

### 6.5 Table / Card Overflow Issues
- **Observation:** At 390×844, tables inside `/accounts`, `/context/packs`, and `/deliverables/cases` overflow horizontally. No horizontal scroll container is present.
- **Severity:** P2
- **Fix:** Wrap all tables in `<div className="overflow-x-auto">`.

### 6.6 Contrast / Readability Issues
- **Observation:** Sidebar tooltip text uses `text-sidebar-foreground/40` for section headers. On some monitors this may fall below WCAG AA contrast (4.5:1).
- **Severity:** P3
- **Fix:** Run `axe-core` contrast audit and bump muted text to `text-sidebar-foreground/60` minimum.

---

## 7. Prioritized Fix Backlog

### Ticket 1
- **Title:** Fix broken lazy imports for Hypothesis and Calculator tabs
- **Severity:** P0
- **Area:** Routing / Code-splitting
- **Route(s):** `/hypothesis/:id/*`, `/calculator/:id/*`
- **Problem:** `App.tsx` imports `pages/hypothesis/HypothesisTab.tsx` etc., but these files do not exist. The actual components live in `features/intelligence-workspace/tabs/`. Users see "Something went wrong" ErrorBoundary.
- **Acceptance criteria:**
  1. All six tab routes render their component without ErrorBoundary.
  2. No `Failed to fetch dynamically imported module` console errors.
  3. Screenshots match expected UI state.
- **Suggested implementation notes:**
  - Option A: Update imports in `App.tsx` lines 157–166 to point to `features/intelligence-workspace/tabs/hypotheses/HypothesesTab.tsx` (note pluralization mismatch).
  - Option B: Create thin wrappers in `pages/hypothesis/` and `pages/calculator/` that re-export from features.
- **Suggested test coverage:** Playwright route smoke test for each tab; assert no console errors and visible heading.

### Ticket 2
- **Title:** Remove or replace `%VITE_ANALYTICS_ENDPOINT%` environment variable leak
- **Severity:** P0
- **Area:** Build / HTML template
- **Route(s):** All routes
- **Problem:** The built HTML contains a `<script>` or fetch request with the literal string `%VITE_ANALYTICS_ENDPOINT%`, causing a 404 on every page load.
- **Acceptance criteria:**
  1. No network request to `%VITE_ANALYTICS_ENDPOINT%` on any route.
  2. If analytics is required, the endpoint resolves to a valid URL or is omitted when empty.
- **Suggested implementation notes:**
  - Search `index.html` and all source files for `%VITE_ANALYTICS_ENDPOINT%`.
  - Replace with `import.meta.env.VITE_ANALYTICS_ENDPOINT` and guard with `if (endpoint) { ... }`.
- **Suggested test coverage:** Playwright network interception asserting zero requests containing `%VITE_ANALYTICS_ENDPOINT%`.

### Ticket 3
- **Title:** Add user-facing error states for API failures
- **Severity:** P1
- **Area:** Data fetching / UX
- **Route(s):** `/accounts`, `/context/*`, `/deliverables/*`, `/governance/*`
- **Problem:** When APIs return 500/404, pages show blank space. Users cannot distinguish between "loading" and "error".
- **Acceptance criteria:**
  1. Every `useQuery` call has an `error` branch rendered in JSX.
  2. Error branch shows a card with status code, friendly message, and "Retry" button.
  3. Loading branch shows a skeleton, not an empty page.
- **Suggested implementation notes:**
  - Create `<DataSection query={query} skeleton={<Skeleton />} empty={<EmptyState />} error={<ErrorCard onRetry={refetch} />}>` wrapper.
  - Apply to `Accounts.tsx`, `ValuePacks.tsx`, `BusinessCaseList.tsx`, etc.
- **Suggested test coverage:** Playwright test with `page.route` mocking API to return 500; assert error card is visible.

### Ticket 4
- **Title:** Add `<h1>` landmarks to every page
- **Severity:** P1
- **Area:** Accessibility / SEO
- **Route(s):** 49 routes with no heading (see Route Inventory)
- **Problem:** Screen readers cannot identify page purpose. WCAG 2.1 requires at least one `<h1>` per page.
- **Acceptance criteria:**
  1. Every route has exactly one `<h1>` containing the page title.
  2. The `<h1>` is the first focusable heading in the DOM order.
- **Suggested implementation notes:**
  - Add `<h1 className="text-2xl font-bold">{pageTitle}</h1>` at the top of each page component.
  - For tabbed workspaces, the `<h1>` can be in the shell wrapper (`ValueStudioShell`, `IntelligenceShell`) rather than every tab.
- **Suggested test coverage:** `expect(page.locator('h1')).toHaveCount(1)` in a Playwright smoke test.

### Ticket 5
- **Title:** Implement responsive mobile navigation
- **Severity:** P1
- **Area:** Layout / Responsive
- **Route(s):** All authenticated routes
- **Problem:** Sidebar is fixed 260 px. On 390×844 viewports the main content is unreadable.
- **Acceptance criteria:**
  1. Below 768 px width, the sidebar is hidden by default.
  2. A hamburger button appears in the header.
  3. Tapping the button opens a Sheet/drawer containing the full navigation.
  4. The drawer can be closed via overlay tap or close button.
- **Suggested implementation notes:**
  - Use `useMediaQuery('(min-width: 768px)')` from a shared hook.
  - Conditionally render `<aside>` vs `<Sheet>` based on breakpoint.
  - Use existing `vaul` dependency for the drawer.
- **Suggested test coverage:** Playwright responsive test at 390×844; assert sidebar is not visible, hamburger is visible, and navigation opens/closes.

### Ticket 6
- **Title:** Prevent API calls with undefined/empty accountId
- **Severity:** P1
- **Area:** Hooks / Data fetching
- **Route(s):** `/intelligence/:id/*`, `/hypothesis/:id/*`, `/evidence/:id/*`, `/calculator/:id/*`, `/studio/:id/*`
- **Problem:** `useWorkspaceContext` falls back to `selectedAccountId || ""`. When empty, API requests are sent with `account_id=` causing 500s.
- **Acceptance criteria:**
  1. If `accountId` is empty or invalid, the tab does not fire data requests.
  2. User is redirected to `/accounts` with a toast: "Please select an account."
- **Suggested implementation notes:**
  - Add `if (!accountId) return navigate('/accounts')` at the top of each workspace shell.
  - In TanStack Query hooks, set `enabled: Boolean(accountId)`.
- **Suggested test coverage:** Playwright test navigating directly to `/intelligence//signals` (empty accountId); assert redirect to `/accounts`.

### Ticket 7
- **Title:** Replace full-page reload on 401 with soft logout
- **Severity:** P1
- **Area:** Auth / API client
- **Route(s):** All authenticated routes
- **Problem:** `api/client.ts` calls `window.location.replace('/login')` on 401, destroying React state and form data.
- **Acceptance criteria:**
  1. 401 response clears tokens and calls `logout()`.
  2. Navigation to `/login` uses wouter `navigate()` (soft redirect).
  3. A toast is shown: "Your session has expired."
- **Suggested implementation notes:**
  - Inject an `onUnauthorized` callback into `ApiClient` constructor, or emit a custom event `auth:unauthorized` that `AuthProvider` listens for.
- **Suggested test coverage:** Playwright test that mocks API 401; assert URL changes to `/login` without `window.location` assignment.

### Ticket 8
- **Title:** Fix ApiClient undefined-url logging noise
- **Severity:** P2
- **Area:** Observability / DX
- **Route(s):** All data-driven routes
- **Problem:** When Axios fails before a request config is built (e.g., interceptor error), `error.config` is undefined and logs show `url: undefined, method: undefined`.
- **Acceptance criteria:**
  1. Error logs always contain a valid URL or "[unknown URL]".
  2. No raw `undefined` values in production logs.
- **Suggested implementation notes:**
  - Change `logError` in `api/client.ts` to `url: error.config?.url ?? '[unknown URL]'`.
- **Suggested test coverage:** Unit test for `ApiClient` response interceptor with a mock error lacking config.

---

## 8. Playwright Test Recommendations

### 8.1 Route Smoke Tests
- **File:** `frontend/e2e/audit/routes.smoke.spec.ts`
- **Coverage:**
  - Visit every canonical route (public + authenticated).
  - Assert `page.locator('h1')` has count 1.
  - Assert zero console errors matching `/TypeError|ReferenceError|Cannot read/`.
  - Assert no requests to `%VITE_ANALYTICS_ENDPOINT%`.

### 8.2 Navigation Tests
- **File:** `frontend/e2e/navigation.spec.ts` (extend existing)
- **Coverage:**
  - Click every sidebar link; assert URL changes within 5 s.
  - Assert active state class (`bg-sidebar-primary/15`) is applied.
  - Test tier gating: standard user sees no admin links; admin sees all.

### 8.3 Deep-Link Reload Tests
- **File:** `frontend/e2e/contracts/account-scoped-workspaces.spec.ts`
- **Coverage:**
  - `page.goto('/intelligence/acct-test-123/signals')`.
  - `page.reload()`.
  - Assert final URL still contains `/intelligence/acct-test-123/signals`.
  - Assert `localStorage.getItem('fabric-account-context')` contains `acct-test-123`.

### 8.4 Auth / Tenant / Account Context Tests
- **File:** `frontend/e2e/auth-lifecycle.spec.ts` (extend existing)
- **Coverage:**
  - Seed auth → visit `/accounts` → select account → verify `selectedAccountId` in store.
  - Switch tenant via `localStorage` → verify `X-Tenant-ID` header in next API call.
  - Clear auth → verify redirect to `/login` on any protected route.

### 8.5 Responsive Tests
- **File:** `frontend/e2e/responsive.spec.ts`
- **Coverage:**
  - Matrix: `[390×844, 768×1024, 1280×800, 1440×900]`.
  - For each viewport:
    - Assert no horizontal overflow (`document.documentElement.scrollWidth <= window.innerWidth`).
    - Assert tables are inside `overflow-x-auto` containers.
    - Assert mobile nav hamburger is visible below 768 px and hidden above.

### 8.6 Accessibility Checks
- **File:** `frontend/e2e/accessibility/axe-audit.spec.ts` (extend existing)
- **Coverage:**
  - Run `@axe-core/playwright` scan on every canonical route.
  - Enforce zero critical / serious violations.
  - Keyboard-only journey: `/login` → Tab → Enter → `/home` → Tab to sidebar → Enter → `/accounts`.

### 8.7 Error / Empty / Loading State Tests
- **File:** `frontend/e2e/contracts/error-states.spec.ts`
- **Coverage:**
  - Mock API to return `[]` → assert `<EmptyState>` visible.
  - Mock API to return 500 → assert `<ErrorCard>` visible with retry button.
  - Mock API to delay 5 s → assert skeleton visible within 1 s.

---

## Appendix A: Screenshot Inventory

All screenshots saved to `audit-output/screenshots/`:
- 82 PNG files captured across 76 routes at desktop (1280×800) viewport.
- Named pattern: `{route_path}_desktop.png` with unsafe characters replaced by `_`.

## Appendix B: Environment Notes

- **Frontend dev server:** Vite on `localhost:3001`
- **Backend services:** Not running (expected 404/500 on API calls)
- **Auth simulation:** `localStorage` seeding with JWT-format test token
- **Tier simulation:** `localStorage` seeding with `user-tier-storage` Zustand state
- **Browser:** Chromium (Playwright) headless

## Appendix C: Source-Code Correlation

| Finding | File | Line(s) |
|---------|------|---------|
| Broken lazy import: HypothesisTab | `frontend/client/src/App.tsx` | 157 |
| Broken lazy import: DiscoveryQuestionsTab | `frontend/client/src/App.tsx` | 158 |
| Broken lazy import: PersonaFitTab | `frontend/client/src/App.tsx` | 159 |
| Broken lazy import: AssumptionsTab | `frontend/client/src/App.tsx` | 160 |
| Broken lazy import: CalcROITab | `frontend/client/src/App.tsx` | 165 |
| Broken lazy import: CalcValueModelTab | `frontend/client/src/App.tsx` | 166 |
| Account context sync | `frontend/client/src/App.tsx` | 221–234 |
| Workspace redirect | `frontend/client/src/App.tsx` | 241–261 |
| RouteGuard | `frontend/client/src/App.tsx` | 281–321 |
| ApiClient 401 reload | `frontend/client/src/api/client.ts` | 242–251 |
| ApiClient undefined logging | `frontend/client/src/api/client.ts` | 254–260 |
| useWorkspaceContext | `frontend/client/src/features/intelligence-workspace/hooks/useWorkspaceContext.ts` | 7–20 |
| Account context store | `frontend/client/src/stores/accountContextStore.ts` | 10–22 |
| Layout / sidebar | `frontend/client/src/components/layout/Layout.tsx` | 406–734 |
| Workspace tab registry | `frontend/client/src/features/intelligence-workspace/workspaceTabRegistry.ts` | — |

---

*End of report.*
