# Frontend Settings & Configuration Center — Comprehensive Audit Report

**Project:** Fabric_4L Frontend (`value-fabric-wireframes`)  
**Date:** 2026-04-30  
**Auditor:** Senior Software Engineer (AI Agent)  
**Scope:** Dependency analysis, configuration review, architecture compliance, performance & security  

---

## Executive Summary

The frontend is a modern React 19 + Vite 7 + Tailwind CSS v4 application with strong architectural foundations. It uses **wouter** for routing (not React Router as specified in the target schema), a **custom ThemeContext** alongside **next-themes** (creating a dual-theme risk), and has a **fragmented Settings/Configuration implementation** that does not align with the provided five-category schema.

**Critical Finding:** The current Settings routes (`/settings/content/*`, `/settings/data/*`, `/settings/access/*`, `/settings/system/*`) are admin-only and lack Personal Settings entirely. The recommended schema introduces `/personal/*`, `/settings/billing/*`, `/settings/team/*`, `/settings/data/*`, and `/settings/governance/*` — requiring significant routing refactoring.

**Security Posture:** 49 vulnerabilities detected (0 critical, 17 high, 31 moderate, 1 low). Most high-severity issues are in devDependencies (`pnpm`, `esbuild`) or build tools (`rollup`, `tar`), but `axios` has a production-relevant DoS vulnerability.

| Grade | Area |
|-------|------|
| B+ | Dependencies (modern stack, minor version drift) |
| B | Configuration (Tailwind v4 migration complete, TS strict, ESLint contract-enforced) |
| C+ | Architecture (Radix/RHF/Zod integration is excellent, but routing & theming diverge from schema) |
| C | Settings Schema Compliance (significant gaps vs. target layout) |
| B- | Security (devDependency vulnerabilities dominate, but axios & path-to-regexp need attention) |

---

## 1. Dependency Analysis

### 1.1 Current Stack Compatibility

| Package | Installed | Status | Notes |
|---------|-----------|--------|-------|
| `react` / `react-dom` | `^19.2.1` | ✅ Modern | Latest stable; Radix primitives compatible |
| `vite` | `^7.1.7` | ⚠️ Patch needed | `fs.deny` bypass on Windows (CVE, fixed in 7.1.11) |
| `typescript` | `5.6.3` | ✅ Stable | One minor behind 5.8.x; no breaking concerns |
| `tailwindcss` | `^4.1.14` | ✅ Modern | v4 CSS-native config; `@tailwindcss/vite` plugin aligned |
| `@tailwindcss/vite` | `^4.1.3` | ✅ Aligned | Slight patch drift from tailwindcss core; harmless |
| `zod` | `^4.1.12` | ✅ Modern | Latest major; `@hookform/resolvers@5.2.2` compatible |
| `react-hook-form` | `^7.64.0` | ✅ Latest | Well-integrated with custom `Form` UI wrapper |
| `@hookform/resolvers` | `^5.2.2` | ✅ Latest | Supports Zod 4 |
| `wouter` | `^3.3.5` (resolved `3.7.1`) | ⚠️ Schema mismatch | **Project uses wouter, not React Router** |
| `next-themes` | `^0.4.6` | ⚠️ Underutilized | Only consumed by `sonner.tsx`; custom `ThemeContext` used elsewhere |
| `framer-motion` | `^12.23.22` | ✅ Latest | No compatibility issues |
| `@tanstack/react-query` | `^5.97.0` | ✅ Latest | Devtools included; no concerns |
| `axios` | `^1.12.0` | ❌ Vulnerable | DoS via `__proto__` key (high severity) |

### 1.2 Version Conflicts & Deprecated Packages

- **`pnpm` override mismatch:** `package.json` declares `"wouter": "^3.3.5"`, but the pnpm lockfile resolves to `wouter@3.7.1` and applies a patch for `3.7.1`. The `packageManager` field specifies `pnpm@10.18.1`, which itself has **multiple high-severity vulnerabilities** (lockfile integrity bypass, command injection, path traversal). Upgrade to `pnpm@10.28.2+` immediately.
- **`tailwindcss>nanoid` override:** Forces `nanoid@3.3.7` to satisfy an older dependency. Nanoid 5.x is the current line; this override is benign but should be re-evaluated after dependency updates.
- **`@types/express` pinned to `4.17.21`:** Express is `^4.21.2`. The types pin is intentional but may lag behind patch releases.

### 1.3 Missing Peer Dependencies

No missing peer dependency warnings were detected. The `onlyBuiltDependencies` list correctly includes `@tailwindcss/oxide`, `esbuild`, and `msw`.

### 1.4 Bundle Size & Optimization

- **No explicit bundle analyzer** is configured in `vite.config.ts`. Recommendation: add `rollup-plugin-visualizer` to CI builds.
- **Code splitting is present** via `React.lazy()` for all major routes in `App.tsx`. This is excellent.
- **Tree-shaking:** ESM-only (`"type": "module"`) with Vite’s native ESBuild/Rollup pipeline; optimal for dead-code elimination.

---

## 2. Configuration Review

### 2.1 Vite Configuration (`vite.config.ts`)

**Strengths:**
- Multi-layer API proxy unified under `/api/v1/*` (ports 8001–8006) for local dev.
- `strictPort: true` ensures Playwright E2E reliability.
- `fs.strict: true` with `deny: ["**/.*"]` is a good security baseline (but see Windows bypass CVE above).
- Path aliases (`@`, `@shared`, `@assets`) are cleanly mapped.
- Custom Manus debug collector plugin is development-only (guarded by `NODE_ENV`).

**Issues:**
| Issue | Severity | Details |
|-------|----------|---------|
| Vite Windows `fs.deny` bypass | **High** | CVE in `vite@7.1.0–7.1.10`. Upgrade to `7.1.11` or `7.2.x`. |
| Missing build output analysis | Low | No bundle size reporting or visualizer step. |
| `test` block inside Vite config | Low | Vitest config duplicated in standalone `vitest.config.ts`. Pick one source of truth. |

### 2.2 TypeScript Configuration (`tsconfig.json`)

**Strengths:**
- `strict: true` is enabled.
- `moduleResolution: bundler` aligns with Vite.
- `allowImportingTsExtensions: true` matches `noEmit` mode.

**Issues:**
- `incremental: true` with `tsBuildInfoFile: "./node_modules/typescript/tsbuildinfo"` places build metadata inside `node_modules`. While functional, this is unusual; prefer `".tsbuildinfo"` in project root or `dist/`.
- No `exactOptionalPropertyTypes` or `noUncheckedIndexedAccess` enabled. These are optional strictness flags but valuable for a settings/configuration center handling many forms.

### 2.3 ESLint Configuration (`.eslintrc.js`)

**Strengths:**
- Custom `plugin:fabric-contracts/service-frontend` enforces cross-layer architectural contracts (`no-raw-tenant-query`, `no-imperative-navigation`, `no-url-concatenation` at `error` level). This is excellent for a multi-tenant system.
- `react-refresh/only-export-components` prevents HMR issues.

**Issues:**
| Issue | Severity | Details |
|-------|----------|---------|
| `@typescript-eslint/no-explicit-any: "off"` | **Medium** | Allows gradual migration but weakens type safety for a settings center handling complex Zod schemas. Recommend `"warn"` with a sunset date. |
| `ecmaVersion: 2020` | Low | Should be `2022` or `2023` to match TS target and Vite’s ESBuild target. |
| No `import/no-cycle` or `boundaries` rules | Medium | Settings/Configuration Center will have deeply nested imports; architectural boundaries should be linted. |

### 2.4 Tailwind CSS Configuration (`client/src/index.css`)

**Assessment:** Tailwind CSS v4 is configured entirely via CSS (`@import "tailwindcss"`, `@theme inline`). This is the canonical v4 approach.

**Strengths:**
- `oklch()` color tokens for perceptually uniform theming.
- Custom `@layer components` for entity badges and terminal cursor.
- `dark` class strategy with `.dark` selector.

**Issues:**
| Issue | Severity | Details |
|-------|----------|---------|
| `@custom-variant dark (&:is(.dark *))` | Low | Correct, but verify it integrates with `next-themes` attribute strategy if you migrate. |
| Font size `13px` on `body` | Low | Non-standard base size; ensure all Radix primitives and form inputs scale correctly. |
| No `@tailwindcss/forms` plugin | Low | Form elements (inputs, checkboxes) may have browser-native styling inconsistencies. |

---

## 3. Architecture Compliance

### 3.1 Radix UI Best Practices

**Status: ✅ Excellent**

The `components/ui/` directory contains 55 primitive wrappers built on Radix UI:
- All major primitives present: Dialog, Dropdown Menu, Tabs, Tooltip, Select, Accordion, etc.
- `Slot` from `@radix-ui/react-slot` is used for polymorphic components (Button, FormControl).
- `cn()` utility from `tailwind-merge` + `clsx` ensures class composition without conflicts.
- `cva` (class-variance-authority) is used consistently for variant-driven components.

**Minor Gap:** No `data-slot` naming convention is formally documented in `AGENTS.md`, but it is used pervasively (e.g., `data-slot="form-item"`). Ensure E2E tests do not rely on these attributes without explicit contract documentation.

### 3.2 Form Validation: Zod + React Hook Form

**Status: ✅ Excellent**

- `form.tsx` provides a complete typed wrapper around `react-hook-form`:
  - `FormField` uses `Controller` with context for id generation.
  - `FormLabel`, `FormControl`, `FormDescription`, `FormMessage` are all Radix-aware (`aria-describedby`, `aria-invalid`).
- Zod 4 is installed and `@hookform/resolvers@5` supports it.

**Minor Gap:** No global form-error boundary or server-error-to-Zod mapping utility is visible. A settings center will have many server-validated fields (e.g., workspace name uniqueness, API key validation). Recommend adding a `serverErrorsToFieldErrors()` helper.

### 3.3 Routing Configuration

**Status: ❌ Does Not Match Schema**

**Current State:** The application uses **`wouter`** (v3.7.1 patched), not React Router.

| Requirement (Schema) | Actual Implementation | Gap |
|----------------------|----------------------|-----|
| React Router | `wouter` | **Major** — Different API, no nested `<Outlet>`, no `useLoaderData`. |
| `/personal/*` routes | Redirect to `/accounts` | **Critical** — Personal Settings does not exist. |
| `/settings/billing/*` | `/settings/system/billing/*` | **Medium** — Path prefix mismatch; redirects from `/organization-admin/billing`. |
| `/settings/team/*` | `/settings/access/*` | **Medium** — Naming mismatch (`team` vs `access`). |
| `/settings/data/*` | `/settings/data/*` | **Partial** — Current subroutes (`variables`, `bindings`, `quality`) differ from schema (`sources`, `integrations`, `variables`, `value-packs`, `ingestion-rules`). |
| `/settings/governance/*` | `/governance/*` | **Medium** — Governance is a top-level namespace, not under `/settings`. |

**Wouter-Specific Concerns:**
- No built-in route ranking; order in `<Switch>` matters strictly. The current `App.tsx` has 1000+ lines of route declarations — already difficult to maintain.
- No `<Outlet>` or nested layout routes. Each settings category would need manual layout composition.
- `useParams` is available but typed manually.

### 3.4 Theme Management (`next-themes`)

**Status: ⚠️ Conflicting Implementation**

- `next-themes` is installed and used **only** in `components/ui/sonner.tsx`.
- Everywhere else, the app uses a **custom `ThemeContext`** (`contexts/ThemeContext.tsx`) that:
  - Stores theme in `localStorage` under key `"theme"`.
  - Toggles `.dark` class on `document.documentElement`.
  - Supports `switchable` prop but defaults to `false`.

**Risk:** If `next-themes` is configured with a different attribute strategy (e.g., `data-theme`) or storage key, `sonner.tsx` may read a different theme value than the rest of the app. Currently, `sonner.tsx` imports `useTheme` from `next-themes`, which may return `"system"` while the custom context returns `"light"` or `"dark"`.

**Recommendation:** Consolidate to one system. Since `next-themes` is the industry standard for React and supports `attribute="class"`, migrate the custom `ThemeContext` to `next-themes` and remove the custom implementation.

---

## 4. Performance & Security

### 4.1 Security Vulnerabilities (pnpm audit)

**Summary:** 49 total vulnerabilities — 0 critical, 17 high, 31 moderate, 1 low.

| Severity | Package | CVE / Issue | Scope | Action |
|----------|---------|-------------|-------|--------|
| **High** | `axios@1.12.0` | DoS via `__proto__` key in `mergeConfig` | **Runtime** | Upgrade to `axios@1.14.0+` |
| **High** | `pnpm@10.18.1` | Lockfile integrity bypass, command injection | Dev only | Upgrade to `pnpm@10.28.2+` |
| **High** | `tar@<7.5.10` | Arbitrary file overwrite / hardlink traversal | Build/CI | Upgrade transitive dep |
| **High** | `rollup@<4.59.0` | Arbitrary file write via path traversal | Build | Upgrade to `rollup@4.59.0+` |
| **High** | `esbuild@<=0.24.2` | Dev server CSRF (any website → dev server) | Dev only | Upgrade to `esbuild@0.25.3+` |
| **High** | `path-to-regexp@<0.1.13` | ReDoS via multiple route parameters | **Runtime** | Upgrade transitive dep (Express) |
| Moderate | `vite@7.1.7` | `fs.deny` bypass on Windows | Dev only | Upgrade to `vite@7.1.11+` |
| Moderate | `dompurify@<3.3.2` | Mutation-XSS via re-contextualization | **Runtime** | Upgrade to `dompurify@3.3.2+` |
| Moderate | `lodash` / `lodash-es` | Prototype pollution in `_.unset` / `_.omit` | **Runtime** | Upgrade to `4.17.21+` |

### 4.2 Code Splitting & Lazy Loading

**Status: ✅ Good**

- `App.tsx` uses `React.lazy()` for every major page component.
- `Suspense` wraps the router with a minimal `PageLoader` spinner.
- No route-based preloading is configured. For the Settings/Configuration Center, consider adding `prefetch` on sidebar navigation items using `wouter`'s `useRoute` or `<Link prefetch>` if available.

### 4.3 Accessibility (a11y)

**Status: ✅ Good**

- Radix UI primitives provide baseline accessibility (keyboard navigation, focus trapping, ARIA attributes).
- `@axe-core/playwright` is installed for E2E a11y scanning.
- Dedicated scripts: `test:a11y:components`, `test:a11y:pages`, `test:a11y:gate`.
- `FormControl` correctly wires `aria-describedby`, `aria-invalid`, and error message ids.

**Gap:** No `skip-to-content` link or landmark region (`<main>`) enforcement is visible in the layout components. A settings center with many form sections should have clear heading hierarchy (`h1` → `h2` → `h3`).

### 4.4 Error Handling & Validation Patterns

**Status: ⚠️ Partial**

- `ErrorBoundary` wraps authenticated routes.
- API client (`api/client.ts`) likely has interceptors, but no global error-to-toast mapping is visible in the configs.
- Zod schemas are present but no centralized settings-schema file exists for the proposed Settings/Configuration Center.

---

## 5. Settings / Configuration Center Schema Gap Analysis

The following table maps the **recommended schema** (provided in audit requirements) against the **current implementation**.

| Category (Schema) | Schema Routes | Current Routes | Match |
|-------------------|---------------|----------------|-------|
| **Personal Settings** | `/personal/profile`, `/personal/security`, `/personal/preferences`, `/personal/notifications`, `/personal/sessions` | Redirect to `/accounts` | ❌ **Missing entirely** |
| **Account & Billing** | `/settings/billing/subscription`, `/settings/billing/usage`, `/settings/billing/payment-methods`, `/settings/billing/invoices` | `/settings/system/billing/*` | ⚠️ Prefix mismatch |
| **Team & Access** | `/settings/team`, `/settings/team/invitations`, `/settings/team/roles`, `/settings/team/permissions`, `/settings/team/api-keys` | `/settings/access/roles`, `/settings/access/teams`, `/settings/access/keys` | ⚠️ Naming mismatch |
| **Data & Integrations** | `/settings/data/sources`, `/settings/data/integrations`, `/settings/data/variables`, `/settings/data/value-packs`, `/settings/data/ingestion-rules` | `/settings/data/variables`, `/settings/data/bindings`, `/settings/data/quality` | ⚠️ Subroute mismatch |
| **Governance** | `/settings/governance/policies`, `/settings/governance/compliance`, `/settings/governance/health`, `/settings/governance/audit-trail`, `/settings/governance/admin-controls` | `/governance/*` (top-level) | ⚠️ Namespace mismatch |

**RBAC Schema:** The current `RouteGuard` uses a `UserTier` model (`standard`, `advanced`, `admin`) with `requiredTier`. The proposed `settingsAccessRules` uses a more granular role-based model (`viewer`, `editor`, `admin`, `owner`, `billing_admin`, `platform_admin`, `governance_admin`) with `partialAccess` arrays. This is a significant authorization model change.

---

## 6. Prioritized Recommendations

### 🔴 Critical (Address within 1–2 weeks)

1. **Fix axios DoS vulnerability**
   - `pnpm add axios@latest` (upgrade to `^1.14.0` or higher).
   - Run contract tests to verify interceptor behavior.

2. **Consolidate theme system**
   - Remove custom `ThemeContext.tsx`.
   - Configure `next-themes` in `App.tsx` with `attribute="class"` and `defaultTheme="light"`.
   - Ensure `sonner.tsx` continues to work without change.

3. **Add Personal Settings route namespace**
   - Create `/personal/*` routes per schema: `profile`, `security`, `preferences`, `notifications`, `sessions`.
   - Scope: `user` (all authenticated users).
   - Use existing `RouteGuard` or introduce `PersonalSettingsRoute` wrapper.

4. **Upgrade pnpm to 10.28.2+**
   - Update `packageManager` field in `package.json`.
   - Re-run `pnpm install` to regenerate lockfile metadata.

### 🟠 High (Address within 1 month)

5. **Upgrade Vite to 7.1.11+ (or 7.2.x)**
   - Resolves Windows `fs.deny` bypass.
   - Verify proxy configuration still functions after upgrade.

6. **Refactor Settings routes to match schema**
   - Rename `/settings/system/billing/*` → `/settings/billing/*`.
   - Rename `/settings/access/*` → `/settings/team/*`.
   - Add missing subroutes: `sources`, `integrations`, `value-packs`, `ingestion-rules` under `/settings/data/*`.
   - Move `/governance/*` under `/settings/governance/*` **OR** update the schema to keep governance top-level.
   - Update all `<Navigate>` aliases in `App.tsx`.

7. **Resolve wouter version / patch drift**
   - `package.json` specifies `^3.3.5`, but patch is for `3.7.1`. Update `package.json` to `"wouter": "^3.7.1"` for clarity.
   - If migrating to React Router is required by the schema, plan a separate migration sprint (see below).

8. **Enable stricter ESLint rules**
   - Change `@typescript-eslint/no-explicit-any` from `"off"` to `"warn"`.
   - Add `@typescript-eslint/strict-boolean-expressions` for settings forms.

### 🟡 Medium (Address within 2–3 months)

9. **Implement RBAC schema for Settings**
   - Replace `UserTier` (`standard`/`advanced`/`admin`) with the proposed `settingsAccessRules`.
   - Add `partialAccess` support (e.g., `editor` can `members:view` but not grant roles).
   - Update `RouteGuard` or create `SettingsRouteGuard`.

10. **Add bundle analyzer to CI**
    - Install `rollup-plugin-visualizer`.
    - Add `vite build --mode analyze` step to build pipeline.
    - Set budget thresholds for the Settings/Configuration Center chunk.

11. **Standardize `tsBuildInfoFile` location**
    - Move from `node_modules/typescript/tsbuildinfo` to `.tsbuildinfo` in project root.

12. **Add server-error mapping for forms**
    - Create `lib/form-errors.ts` with `serverErrorsToFieldErrors()` to map API 422 responses to React Hook Form `setError` calls.

### 🟢 Low (Nice to have)

13. **Evaluate React Router migration**
    - If the organization standardizes on React Router, plan a migration from `wouter`.
    - Impact: High (1000+ lines of routes in `App.tsx`, no nested outlet support in wouter).
    - Effort: 2–3 developer-weeks.

14. **Add `@tailwindcss/forms` plugin**
    - Normalize form input styling across browsers.

15. **Increase test coverage thresholds**
    - Current: 35% lines/functions/statements, 25% branches.
    - Target for Settings module: 60% lines, 50% branches.

---

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| axios DoS exploited in production | Medium | High | Upgrade immediately; monitor for suspicious `__proto__` payloads |
| Theme inconsistency between Sonner and UI | High | Medium | Consolidate on `next-themes` within one sprint |
| Settings route refactor breaks bookmarks/redirects | Medium | Medium | Maintain `<Navigate>` aliases for at least one release cycle |
| pnpm vulnerability in CI/CD | Medium | Medium | Upgrade pnpm; verify lockfile integrity in CI |
| Wouter → React Router migration delay | Medium | High | Document decision; if staying on wouter, update schema docs |
| RBAC model change causes authorization bugs | Medium | High | Add exhaustive unit tests for `settingsAccessRules` before rollout |

---

## 8. Suggested Timeline

| Week | Focus |
|------|-------|
| **Week 1** | Security patches (axios, pnpm, vite), theme consolidation |
| **Week 2** | Personal Settings routes + screens, ESLint strictness |
| **Week 3** | Settings route refactoring (`/settings/billing`, `/settings/team`, `/settings/data`) |
| **Week 4** | Governance namespace migration, RBAC schema implementation |
| **Week 5–6** | React Router evaluation / migration spike (if approved) |
| **Week 7+** | Coverage thresholds, bundle analysis, a11y enhancements |

---

## Appendix: Files Audited

- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/vitest.config.ts`
- `frontend/playwright.config.ts`
- `frontend/tsconfig.json`
- `frontend/.eslintrc.js`
- `frontend/.prettierrc`
- `frontend/client/src/index.css`
- `frontend/client/src/App.tsx`
- `frontend/client/src/routes/personal.tsx`
- `frontend/client/src/routes/governance.tsx`
- `frontend/client/src/routes/workspace.tsx`
- `frontend/client/src/routes/deprecationMap.ts`
- `frontend/client/src/contexts/ThemeContext.tsx`
- `frontend/client/src/components/ui/form.tsx`
- `frontend/client/src/components/ui/button.tsx`
- `frontend/client/src/components/ui/sonner.tsx`
- `frontend/test/setup.ts`
- `frontend/pnpm-lock.yaml` (selected entries)
