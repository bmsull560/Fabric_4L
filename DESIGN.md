# Value Fabric Frontend Governance and Design System

**Status:** active

**Scope:** `apps/web/` and any user-facing frontend assets, tests, generated API clients, or documentation changed as part of frontend work.

**Audience:** human contributors and AI coding agents.

> This document is the production frontend governance contract for Value Fabric. It combines implementation rules, design-system tokens, quality gates, and review expectations so that humans and AI coding agents can make frontend changes consistently and safely.

## Operating Rules for Coding Agents

Before changing frontend code, read this file and inspect the existing implementation in `apps/web/`. A coding agent must preserve the current product architecture, reuse existing components and hooks, and keep each change scoped to the user request. The goal is not to redesign the product; the goal is to make the smallest high-quality change that satisfies the task while improving consistency, accessibility, and maintainability.

| Rule | Required Behavior |
|---|---|
| Start from context | Read `DESIGN.md`, the affected route, the nearest component README if present, the relevant hooks, and related tests before editing. |
| Reuse before creating | Prefer existing domain components, layout primitives, shadcn/ui wrappers, hooks, query keys, schemas, and utilities. Create a new pattern only when no suitable pattern exists. |
| Keep scope tight | Do not redesign unrelated screens, rewrite unrelated component trees, or rename public APIs during a scoped fix. |
| Preserve contracts | Treat generated API types, OpenAPI-derived clients, Zod schemas, tenant context, and route contracts as boundaries. Do not bypass validation to make UI work. |
| Verify behavior | Run focused typecheck, lint, tests, and smoke checks for the changed area. If a gate cannot run locally, record why and identify the smallest follow-up validation. |
| Report risk | Summarize affected files, user-visible behavior, validation performed, and remaining risks in the final handoff. |

## Stack Conventions

Value Fabric frontend work uses the existing React application under `apps/web/`. New work must fit the established stack rather than introducing alternative frameworks, state libraries, styling systems, or component registries without an explicit architecture decision.

| Concern | Convention |
|---|---|
| Runtime | React with Vite and TypeScript. |
| Styling | Tailwind CSS using semantic tokens and existing design-system utilities. |
| Components | shadcn/ui and Radix-based primitives wrapped by local components in `apps/web/src/components/`. |
| Server state | TanStack Query hooks with centralized query keys, API adapters, and explicit loading, empty, error, and success states. |
| Client state | Local state first; Zustand only for cross-route client state that cannot be derived from server data or URL state. |
| Runtime validation | Zod or domain parsers at network boundaries before UI components consume backend data. |
| Forms | React Hook Form-compatible patterns where already used, with schema validation, accessible labels, field-level errors, and submission state. |
| Testing | Unit/component tests for logic and rendering, Playwright smoke tests for critical user flows, and accessibility-oriented checks for interactive UI. |

## Component Architecture

Components should be composed from stable primitives and domain-specific wrappers. A page should orchestrate data loading, permissions, and route state, while presentational components should receive typed domain data and callbacks. Shared UI primitives belong in `apps/web/src/components/ui/`; product-specific components belong near their domain or route; one-off layout glue should remain local until repeated use justifies extraction.

| Layer | Responsibility | Anti-Drift Rule |
|---|---|---|
| Page or route | Fetches data through hooks, handles route params, chooses page-level states, and composes sections. | Do not put reusable visual primitives or API transformation logic directly in the page. |
| Domain component | Encapsulates product behavior for accounts, governance, intelligence, formula workflows, or billing. | Do not duplicate an existing domain component with a slightly different name or style. |
| UI primitive | Provides reusable Button, Card, Dialog, Table, Form, Badge, Toast, and layout primitives. | Do not fork shadcn/ui behavior or hard-code one-off variants outside the design system. |
| Hook or adapter | Owns server interaction, parsing, cache keys, mutations, and invalidation. | Do not call raw endpoints from components when an adapter or hook pattern exists. |

## State and Data Management

TanStack Query is the default tool for server state. Hooks should expose domain-safe data, typed loading states, mutation status, and normalized errors. Components must never silently discard backend failures or present stale data as successful completion. When backend data enters the frontend, prefer an explicit parser or mapper so UI code does not depend on raw transport DTOs.

| State Type | Preferred Location | Requirements |
|---|---|---|
| Server data | TanStack Query hooks under domain hook modules. | Stable query keys, typed responses, validation or mapping, and explicit error handling. |
| Route state | URL params, search params, or router state. | Deep-linkable where user-visible state matters. |
| Form state | Form-local state with schema-backed validation. | Show field errors, submission progress, and server rejection messages. |
| Cross-route UI state | Existing Zustand stores only when local or URL state is insufficient. | Keep stores small and avoid duplicating server state. |

### API Client Typing

All new and refactored TanStack Query hooks must use the typed wrappers exported from `@/api/typedClient.ts` instead of calling `apiClient` directly. The wrappers require an explicit response-type generic and prevent the default `unknown` fallback that allows unsafe casts to propagate.

| Wrapper | Use When |
|---|---|
| `apiGet<TResponse>(layer, path, config?)` | Fetching data |
| `apiPost<TResponse>(layer, path, data?, config?)` | Creating resources or triggering actions |
| `apiPut<TResponse>(layer, path, data?, config?)` | Full entity replacements |
| `apiPatch<TResponse>(layer, path, data?, config?)` | Partial updates |
| `apiDelete<TResponse>(layer, path, config?)` | Deletions |

Prefer generated OpenAPI schema types (`layer1_ingestion`, `layer2_extraction`, `layer4_agents`, etc.) as the generic argument when the endpoint has a defined schema. Where the spec returns `unknown` or lacks a schema, define a local frontend interface and use it as the explicit generic rather than falling back to `unknown` or `Record<string, unknown>`.

Runtime parsers (Zod, `safeParse`, manual mappers) must remain in place; the wrappers only remove compile-time `as` casts on API responses. The `src/hooks/` directory is guarded by `pnpm run check:no-raw-api-client-in-hooks` to prevent backsliding.

## Typography Rules

Value Fabric uses a compact, data-oriented typography system. Use `Inter` for UI text unless an existing file already defines a compatible system stack. Reserve `JetBrains Mono` or system monospace fonts for code, identifiers, and technical data.

| Level | Size | Weight | Line Height | Letter Spacing | Use Case |
|---|---:|---:|---:|---:|---|
| Display XL | 32px | 800 | 1.2 | -0.02em | Page titles and hero headers. |
| Display L | 28px | 700 | 1.25 | -0.015em | Section headers. |
| Display M | 24px | 600 | 1.3 | -0.01em | Card titles. |
| Heading XL | 20px | 600 | 1.4 | -0.005em | Modal headers. |
| Heading L | 18px | 600 | 1.4 | normal | Subsection headers. |
| Heading M | 16px | 600 | 1.45 | normal | Card subtitles. |
| Heading S | 14px | 600 | 1.5 | normal | Form labels. |
| Body L | 14px | 400 | 1.6 | normal | Primary body text. |
| Body M | 13px | 400 | 1.6 | -0.01em | Default body text. |
| Body S | 12px | 400 | 1.5 | normal | Secondary text. |
| Caption | 11px | 400 | 1.4 | normal | Helper text and metadata. |
| Micro | 10px | 500 | 1.3 | normal | Badges, tags, and tiny labels. |
| Mono S | 12px | 400 | 1.5 | normal | Code snippets. |
| Mono XS | 11px | 400 | 1.4 | normal | Inline code. |

Typography must remain readable and accessible. Maintain a minimum contrast ratio of 4.5:1 for normal text and 3:1 for large text. Do not mix unrelated font families within a component, stretch fonts, overuse all caps, or use font sizes smaller than 10px.

## Layout and Responsive Principles

The spacing system uses a 4px base unit. Prefer Tailwind spacing tokens and established layout primitives over hard-coded one-off sizes.

| Token | Value | Use Case |
|---|---:|---|
| `space-0` | 0px | No spacing. |
| `space-1` | 4px | Tight icon spacing. |
| `space-2` | 8px | Small gaps and icon-text spacing. |
| `space-3` | 12px | Compact padding. |
| `space-4` | 16px | Default padding for cards and buttons. |
| `space-5` | 20px | Section spacing. |
| `space-6` | 24px | Section padding. |
| `space-8` | 32px | Large gaps and card groups. |
| `space-10` | 40px | Section margins. |
| `space-12` | 48px | Page margins. |
| `space-16` | 64px | Large section spacing. |

| Breakpoint | Width Range | Target Device | Layout Rule |
|---|---|---|---|
| Mobile | 0px–767px | Phones | Four-column or stacked layout with touch-friendly controls. |
| Tablet | 768px–1023px | Tablets | Eight-column layout with condensed navigation where needed. |
| Desktop | 1024px–1279px | Laptops | Twelve-column layout with full navigation. |
| Desktop XL | 1280px–1535px | Desktops | Twelve-column layout with wider data density options. |
| Desktop 2XL | 1536px and above | Ultra-wide monitors | Preserve readable content widths and avoid uncontrolled stretching. |

Responsive changes should be mobile-first. Convert horizontal layouts to stacked layouts on small screens, use progressive disclosure for advanced controls, prefer modals over side panels below desktop widths, and truncate long text with tooltips or accessible disclosure when necessary.

## Visual System and Theming

Frontend changes must respect the existing visual language. Use Tailwind tokens, CSS variables, and existing component variants. Do not hard-code colors, spacing, typography, shadows, border radii, or z-index values when a token or variant exists. Dark mode must be supported for any visible surface touched by the change.

> A design improvement is acceptable only when it reinforces an existing pattern. A broad redesign during a scoped bug fix is not acceptable.

| Requirement | Quality Bar |
|---|---|
| Responsiveness | New or changed screens must remain usable at mobile, tablet, and desktop widths. |
| Dark mode | Text, surfaces, borders, focus rings, charts, and status colors must remain legible in dark mode. |
| Density | Data-heavy screens should use consistent table, card, filter, and toolbar spacing. |
| Feedback | Actions must provide loading, success, empty, and error feedback where relevant. |
| Consistency | Buttons, modals, cards, tabs, filters, badges, and toasts must reuse existing variants. |

### Semantic Color Tokens

| Token | Hex Reference | Light Mode | Dark Mode | Use Case |
|---|---|---|---|---|
| `primary` | `#007AFF` | `oklch(0.7212 0.1303 174.8407)` | `oklch(0.7212 0.1303 174.8407)` | Primary actions and links. |
| `primary-foreground` | `#FFFFFF` | `oklch(0.1023 0.0200 171.0469)` | `oklch(0.0865 0.0163 174.9583)` | Text on primary surfaces. |
| `background` | `#FFFFFF` | `oklch(1.0000 0 0)` | `oklch(0.1448 0 0)` | Page background. |
| `foreground` | `#0F172A` | `oklch(0.1448 0 0)` | `oklch(0.9851 0 0)` | Primary text. |
| `card` | `#FFFFFF` | `oklch(1.0000 0 0)` | `oklch(0.2046 0 0)` | Card backgrounds. |
| `card-foreground` | `#0F172A` | `oklch(0.1448 0 0)` | `oklch(1 0 0)` | Card text. |
| `border` | `#E2E8F0` | `oklch(0.9219 0 0)` | `oklch(0.2680 0.0070 34.2980)` | Borders and dividers. |
| `input` | `#E2E8F0` | `oklch(0.9219 0 0)` | `oklch(0.2046 0 0)` | Input borders. |
| `muted` | `#F8FAFC` | `oklch(0.9702 0 0)` | `oklch(0.2686 0 0)` | Disabled or subdued backgrounds. |
| `muted-foreground` | `#64748B` | `oklch(0.5555 0 0)` | `oklch(0.7090 0 0)` | Secondary text. |
| `destructive` | `#EF4444` | `oklch(0.5830 0.2387 28.4765)` | `oklch(0.7022 0.1892 22.2279)` | Delete and error states. |
| `success` | `#10B981` | `oklch(0.65 0.15 150)` | `oklch(0.65 0.15 150)` | Success states. |
| `warning` | `#F59E0B` | `oklch(0.70 0.15 60)` | `oklch(0.70 0.15 60)` | Warning states. |
| `info` | `#3B82F6` | `oklch(0.65 0.15 250)` | `oklch(0.65 0.15 250)` | Informational states. |

Use semantic colors for their intended meaning, keep neutral colors dominant for structure, and reserve semantic colors for status and action. Chart series should use the existing chart token sequence: `chart-1`, `chart-2`, `chart-3`, `chart-4`, and `chart-5`.

## Component Styling Rules

| Component | Required Pattern |
|---|---|
| Buttons | Use existing Button variants for primary, secondary, ghost, destructive, and icon actions. Buttons should use `rounded-lg`, expose hover/focus/disabled states, and maintain accessible labels. |
| Cards | Use `bg-card`, `text-card-foreground`, `border-border`, `rounded-lg`, and consistent padding. Interactive cards may add a subtle hover border using existing tokens. |
| Inputs | Use `bg-background`, `border-input`, `rounded-md`, focus rings, error states, and disabled states from the design system. |
| Navigation | Preserve active, inactive, collapsed, and mobile states with sidebar tokens and route-aware `aria-current` where applicable. |
| Data tables | Use compact body typography, clear headers, hover states, responsive overflow, sorting indicators, and accessible labels. |
| Modals and dialogs | Use existing Dialog or Sheet primitives, focus management, keyboard dismissal, and clear primary/secondary action placement. |

## Navigation and Information Architecture

Navigation changes must preserve route semantics, breadcrumbs, active states, and deep links. Do not move screens, rename routes, or change information hierarchy unless the task explicitly requires it. When adding a new surface, connect it to the nearest existing navigation pattern and verify that keyboard users can reach, operate, and leave the surface.

## Forms and Validation

Forms must be resilient to user error and backend rejection. Every input needs an accessible label or labelled association, clear validation feedback, disabled or pending state during submission, and safe recovery when a request fails. Required fields, destructive actions, and irreversible workflow steps need explicit copy.

| Form Concern | Required Treatment |
|---|---|
| Validation | Use existing schema or form validation patterns; display field-level errors and form-level backend rejection messages. |
| Submission | Show pending state, prevent duplicate submissions, and preserve user-entered data after recoverable failures. |
| Accessibility | Connect labels, descriptions, and errors with appropriate ARIA attributes. |
| Security | Do not leak secrets, tokens, tenant IDs, or internal error traces into user-visible UI. |

## Content and Microcopy

Microcopy should be concise, product-specific, and action-oriented. Error messages should explain what happened, what the user can do next, and whether retrying is safe. Empty states should tell users why no data is visible and how to create or discover the first item. Loading text should reflect the actual operation rather than using generic placeholders.

| Content Type | Guidance |
|---|---|
| Button labels | Use verbs that match the action, such as “Create formula,” “Run validation,” or “Save policy.” |
| Errors | Avoid blaming users; include recovery action and preserve technical detail in logs rather than UI copy. |
| Empty states | Explain the state and offer the next useful action. |
| Confirmation copy | Make destructive or irreversible outcomes explicit before submission. |

## Security and Privacy

Frontend code must preserve tenant isolation, authentication state, and privacy boundaries. Do not place secrets in frontend bundles, local storage, logs, telemetry payloads, screenshots, or documentation. Do not bypass authorization checks in UI to make a route appear accessible; UI affordances must reflect backend permissions but backend permissions remain authoritative.

| Risk | Required Guardrail |
|---|---|
| Tenant leakage | Never mix tenant-scoped cache keys, route params, or persisted UI state without tenant context. |
| Sensitive data | Mask credentials, tokens, PII, and internal identifiers unless the product explicitly requires display. |
| API errors | Normalize errors before display; do not show stack traces or raw gateway payloads. |
| Telemetry | Avoid recording secrets or raw user-entered confidential content. |

## Anti-Patterns

The following behaviors are not acceptable in frontend changes because they create drift, regressions, or production risk.

| Anti-Pattern | Why It Is Rejected |
|---|---|
| Hard-coding colors, spacing, shadows, or typography | It bypasses the design system and breaks dark mode or consistency. |
| Creating duplicate Button, Card, Dialog, Table, Form, Badge, or Toast patterns | It fragments the UI and makes maintenance harder. |
| Hiding API errors or replacing failures with silent success | It misleads users and masks production incidents. |
| Broad redesigns during scoped fixes | It increases review risk and causes unrelated regressions. |
| Introducing a new state library or UI framework | It creates architectural drift without an explicit decision record. |
| Adding `any`, unsafe casts, or unvalidated network data | It weakens TypeScript and moves runtime failures into user flows. |
| Inline styles or one-off arbitrary Tailwind values where tokens exist | It makes styling hard to maintain and inconsistent across themes. |
| Ignoring keyboard navigation, focus states, or screen readers | It makes the product inaccessible. |
| Deeply nesting components or mixing unrelated responsibilities | It makes pages hard to reason about and test. |

## Definition of Done

A frontend change is complete only when the affected user experience, implementation quality, and validation evidence are all addressed. If a requirement is not applicable, the handoff should say so explicitly.

| Area | Completion Requirement |
|---|---|
| Scope | The change solves the requested problem without unrelated redesigns or public API churn. |
| Reuse | Existing components, hooks, query keys, schemas, and utilities are reused where appropriate. |
| Responsiveness | The changed UI is usable on mobile, tablet, and desktop widths. |
| Dark mode | The changed UI works in light and dark themes without hard-coded incompatible colors. |
| States | Loading, empty, success, error, disabled, optimistic, and retry states are handled where relevant. |
| Accessibility | Keyboard navigation, focus visibility, labels, aria associations, and semantic markup are preserved. |
| Type safety | TypeScript remains strict; no new `any`, unsafe casts, or unvalidated network responses are introduced. |
| Tests | Unit, component, integration, or E2E coverage is updated when behavior changes. |
| Security | Tenant, auth, privacy, and error-disclosure boundaries remain intact. |
| Handoff | Final notes list affected files, validation commands, observed results, and remaining risks. |

## Enforcement Hooks

Use the smallest reliable set of checks for the changed surface. Prefer existing package scripts and CI commands over inventing new local-only commands.

| Gate | When To Run | Expected Evidence |
|---|---|---|
| Typecheck | Any TypeScript, generated client, schema, hook, or component change. | Command and pass/fail result. |
| Lint | Any source, test, or styling change. | Command and pass/fail result. |
| Unit or component tests | Any changed logic, hooks, forms, or reusable components. | Relevant test target and result. |
| E2E smoke | Navigation, auth, tenant, workflow, or route-level behavior changes. | Critical path tested and result. |
| Accessibility smoke | New interactive elements, dialogs, tables, forms, or navigation. | Keyboard/focus/label checks performed. |
| Bundle or performance check | New dependency, heavy visualization, large route, or repeated render-sensitive change. | Bundle, dependency, or performance note. |

## Agent Handoff Template

Agents should include a concise handoff with every frontend change. The handoff should name the touched areas, explain why the implementation followed existing patterns, and report validation evidence.

| Field | Required Content |
|---|---|
| Summary | User-visible behavior changed and the reason for the change. |
| Files changed | Routes, components, hooks, schemas, tests, and docs touched. |
| Pattern reuse | Existing components, hooks, tokens, or conventions reused. |
| Validation | Commands run and their results. |
| Risks | Known limitations, skipped checks, follow-up recommendations, or deployment considerations. |

## Agent Prompt Guide

Use these prompts as scaffolding when asking an AI agent to work on the frontend. The agent must still inspect the actual code before editing.

| Task | Prompt Scaffold |
|---|---|
| New component | Create a component that follows `DESIGN.md`, reuses existing UI primitives, supports light and dark mode, includes accessible labels, handles loading and error states where relevant, and includes focused tests. |
| Form styling | Style this form with existing form primitives, schema validation, accessible labels, field-level errors, pending submission state, and backend rejection handling. |
| Data table | Build or update a table using existing table primitives, compact typography, sorting indicators, responsive overflow, keyboard-accessible controls, and empty/error states. |
| Modal | Use existing Dialog or Sheet primitives, include focus management, keyboard dismissal, clear headings, responsive behavior, and explicit primary/secondary actions. |
| Navigation | Preserve route semantics, active state, deep links, breadcrumbs where applicable, mobile behavior, and keyboard reachability. |

## Design Principles Summary

| Principle | Meaning |
|---|---|
| Consistency | Use defined tokens and existing patterns for all design decisions. |
| Accessibility | Preserve WCAG-aware contrast, keyboard navigation, screen reader semantics, and focus management. |
| Responsiveness | Build mobile-first and progressively enhance larger layouts. |
| Performance | Avoid unnecessary dependencies, heavy rerenders, unoptimized images, and route-level bloat. |
| Maintainability | Keep component responsibilities clear and reuse stable primitives. |
| User experience | Provide clear feedback, intuitive actions, and fast recovery from errors. |
| Brand alignment | Use the primary blue and semantic colors consistently. |
| Dark mode | Support dark mode for every changed visible surface. |

## Version History

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-05-06 | Initial design-system definition. |
| v1.1 | 2026-05-06 | Merged production frontend governance rules, agent operating instructions, definition of done, anti-patterns, stack conventions, and enforcement hooks. |
