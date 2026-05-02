# UI Design Stack — Designer Onboarding Guide

**Value Fabric Frontend** | React + Vite + TypeScript | Last Updated: April 2026

---

## At a Glance

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Framework** | React 19 + Vite | SPA (not Next.js), fast dev server |
| **Styling** | Tailwind CSS v4 | Utility-first with CSS variables |
| **Components** | shadcn/ui + Radix | 50+ primitives, accessible, composable |
| **Custom Layer** | Fabric Components | Domain-specific: `FabricCard`, `DataTable`, `StatusBadge` |
| **Primitives** | WfPrimitives | Workflow-specific: `SectionCard`, `Btn`, `SearchInput` |
| **Icons** | Lucide React | 1000+ consistent line icons |
| **Theme** | Tweakcn Generated | Blue-tinted neutral palette, oklch colors |
| **Registry** | @shadcnuikit | Premium blocks: hero sections, pricing tables, etc. |

---

## Product Architecture — Navigation Model

Value Fabric uses a **Progressive Synthesis** navigation model. The user journey flows from understanding the prospect's world to proving the vendor's product solves their problems.

### Primary Domains (Left Rail)

| Domain | Purpose | Tier |
|--------|---------|------|
| **Home** | Dashboard with active cases and KPIs | Standard |
| **Accounts** | Prospect/customer records; entry point for all value cases | Standard |
| **Intelligence** | Discover and validate what matters to the prospect | Standard |
| **Value Studio** | Build the "Why Us" business case using validated intelligence | Standard |
| **Context Engine** | Vendor's own knowledge: Value Packs, formulas, case studies | Advanced |
| **Deliverables** | Artifact library: exported business cases, presentations | Standard |
| **Governance** | Audit trails, compliance, evidence lineage | Advanced |
| **Settings** | Admin control plane: roles, variables, integrations | Admin |

### Workspace Tabs

**Intelligence** (account-scoped: `/intelligence/:accountId/...`)

| Tab | Purpose |
|-----|---------|
| **Signals** | AI-surfaced pain points ranked by confidence and estimated impact |
| **Drivers** | Root cause analysis connecting signals to underlying factors |
| **Evidence** | Source documents, benchmarks, confidence grading |
| **Stakeholders** | Persona-mapped framing of validated findings |

**Value Studio** (account-scoped: `/studio/:accountId/...`)

| Tab | Purpose |
|-----|---------|
| **Action Plan** | Product-anchored recommendations: "Our capability solves your pain" |
| **Value Model** | Quantified business case with variable-driven calculation |
| **Narrative** | Stakeholder-ready packaging of the model |

### Three-Layer UI Structure

The UI follows a strict three-layer separation:

1. **Left Rail** — Product-level navigation (where am I?)
2. **Center Canvas** — Workspace tabs and content (what am I doing?)
3. **Right Rail** — Contextual support with two modes:
   - **Detail Panel** — Inspect metadata, evidence, confidence for selected item
   - **Agent Stream** — Conversational co-pilot with structured actions

### Key Interaction: "Add to Model"

The bridge between Intelligence and Value Studio is the **"Add to Model"** action. When a user validates a signal in Intelligence, they can add it to the Value Model, which carries the signal, its drivers, and its evidence into the business case.

---

## Design System Overview

### Philosophy

1. **Compose, don't customize** — Stack shadcn primitives (`Card` + `Tabs` + `Form`) rather than writing custom CSS
2. **Semantic tokens** — Use `bg-primary` not `bg-blue-500` for theme adaptability
3. **Dark mode first** — Every component supports `.dark` class toggle
4. **Fabric patterns** — Use domain components for consistent product UX
5. **WfPrimitives for workflows** — Use `SectionCard`, `Btn`, `SearchInput`, `DataTable` from `WfPrimitives.tsx` in all workflow/studio pages

### Visual Language

- **Clean, minimal, enterprise** — Inspired by Linear, Vercel, Clerk
- **Blue primary** — `oklch(0.6112 0.1217 248.9572)` — professional, trustworthy
- **High contrast text** — WCAG AA compliant ratios
- **Subtle shadows** — 2px-4px depth, not heavy elevation
- **Generous spacing** — 16px-24px gaps, not cramped

---

## Color System (oklch)

All colors use **oklch** for perceptual uniformity and better dark mode transitions.

### Semantic Tokens

| Token | Light Value | Dark Value | Usage |
|-------|-------------|------------|-------|
| `background` | `oklch(0.9581)` near-white | `oklch(0.1776)` near-black | Page background |
| `foreground` | `oklch(0.3134)` dark gray | `oklch(0.7905)` light gray | Primary text |
| `primary` | `oklch(0.6112)` blue | `oklch(0.6576)` lighter blue | CTAs, links, active states |
| `secondary` | `oklch(0.9122)` subtle gray | `oklch(0.9774)` off-white | Secondary backgrounds |
| `muted` | `oklch(0.9209)` light gray | `oklch(0.2171)` dark gray | Subtle backgrounds |
| `muted-foreground` | `oklch(0.6027)` medium gray | `oklch(0.7559)` light gray | Secondary text |
| `border` | `oklch(0.8840)` light border | `oklch(0.3506)` dark border | Dividers, input borders |
| `destructive` | `oklch(0.1931)` dark red | `oklch(0.6368)` bright red | Errors, delete actions |

### Usage in Code

```tsx
// ✅ Correct — semantic token
<div className="bg-primary text-primary-foreground">

// ❌ Wrong — raw color
<div className="bg-blue-500 text-white">
```

---

## Typography

| Element | Spec |
|---------|------|
| **Font Family** | Inter (sans-serif), Georgia (serif), monospace (code) |
| **Base Size** | 13px (compact for data-dense UI) |
| **Letter Spacing** | -0.01em (slightly tighter for modern feel) |
| **Weights** | 400 (body), 500 (medium), 600 (semibold), 700 (bold) |

### Type Scale (via Tailwind)

- `text-xs` — 12px — captions, badges
- `text-sm` — 13px — body text
- `text-base` — 14px — emphasized body
- `text-lg` — 16px — card titles
- `text-xl` — 20px — page titles
- `text-2xl` — 24px — hero headings

---

## Component Library

### shadcn/ui Primitives (50+)

Located in `@/components/ui/`. Key categories:

**Layout**: `Card`, `Separator`, `ScrollArea`, `Resizable`

**Forms**: `Input`, `Textarea`, `Select`, `Combobox`, `Checkbox`, `RadioGroup`, `Switch`, `Slider`, `Form`

**Overlays**: `Dialog`, `Sheet`, `Drawer`, `AlertDialog`, `Popover`, `Tooltip`, `HoverCard`

**Navigation**: `Sidebar`, `Tabs`, `Breadcrumb`, `NavigationMenu`, `Command`

**Data Display**: `Table`, `Badge`, `Avatar`, `Skeleton`, `Chart`

**Feedback**: `sonner`, `Alert`, `Progress`, `Spinner`

### Fabric Custom Components

Located in `@/components/ui/fabric/`. Domain-specific patterns:

| Component | Purpose | When to Use |
|-----------|---------|-------------|
| `FabricCard` | Entity display cards | Any entity detail/summary view |
| `DataTable` | Tabular data with features | Lists with sorting, filtering, pagination |
| `StatusBadge` | Standardized status | Active, pending, error, warning states |
| `FilterBar` | Search + filters layout | Any list or table view |
| `PageHeader` | Page structure | All pages (breadcrumb + title + actions) |
| `FabricDialog` | Confirmation dialogs | Delete, confirm, warn actions |
| `LoadingSkeleton` | Page-level loading | Initial page load states |

### WfPrimitives (Workflow Components)

Located in `@/components/WfPrimitives.tsx`. Used in all Intelligence and Value Studio pages:

| Component | Purpose | When to Use |
|-----------|---------|-------------|
| `SectionCard` | Panel container with title and optional subtitle | Any panel in Intelligence or Value Studio |
| `Btn` | Standardized button with variant support | All action buttons in workflow pages |
| `SearchInput` | Search field with icon | Any searchable list in workflow pages |
| `DataTable` | Lightweight table with consistent styling | Data tables in workflow pages |

---

## File Structure

```
frontend/client/src/
├── components/
│   ├── ui/                    # shadcn primitives (50+ files)
│   ├── ui/fabric/             # Fabric custom components
│   ├── navigation/
│   │   └── TieredNav.tsx      # Left rail navigation
│   ├── AppShell.tsx           # Main layout shell (header + sidebar + main)
│   ├── WfPrimitives.tsx       # Workflow primitive components
│   └── ...
├── hooks/                     # React Query hooks
├── lib/
│   └── utils.ts               # cn() utility for class merging
├── pages/
│   ├── intelligence/          # Intelligence workspace tabs (planned)
│   ├── value-studio/          # Value Studio workspace tabs
│   └── ...                    # Other page components
├── workflow/                  # Legacy 7-step workflow (being migrated)
├── stores/                    # Zustand state
└── index.css                  # Global styles + theme variables
```

---

## Design Tokens Reference

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `radius-sm` | `calc(var(--radius) - 4px)` ≈ 0.25rem | Small elements |
| `radius-md` | `calc(var(--radius) - 2px)` ≈ 0.375rem | Inputs, buttons |
| `radius-lg` | `var(--radius)` ≈ 0.5rem | Cards, dialogs |
| `radius-xl` | `calc(var(--radius) + 4px)` ≈ 0.75rem | Large containers |

### Shadows

| Token | Light Mode | Dark Mode |
|-------|------------|-----------|
| `shadow-sm` | Subtle 2px | Subtle 4px |
| `shadow` | Standard | Elevated |
| `shadow-lg` | Elevated | Heavy |

### Z-Index Scale

Components manage their own stacking. Don't add manual z-index:
- `Dialog`, `Sheet`, `Popover` — handled by Radix
- Only use `z-*` for custom absolute positioning

---

## Dark Mode

Toggle via `.dark` class on root element:

```tsx
// In your app
<html className={isDark ? "dark" : ""}>

// Or toggle programmatically
document.documentElement.classList.toggle("dark")
```

All components automatically adapt via CSS variables.

---

## Design Resources

### Internal
- **Navigation Architecture Spec** — `docs/NAVIGATION_ARCHITECTURE.md`
- **Implementation Plan** — `docs/IMPLEMENTATION_PLAN.md`
- **Component Examples** — Existing pages in `frontend/client/src/pages/`

### External
- **shadcn/ui Docs** — https://ui.shadcn.com/docs
- **Lucide Icons** — https://lucide.dev/icons/
- **Tailwind Docs** — https://tailwindcss.com/docs
- **Radix Primitives** — https://www.radix-ui.com/primitives
- **Tweakcn Themes** — https://tweakcn.com

---

## Common Tasks for Designers

### 1. Create a New Page Layout

Use `PageShell` + `PageHeader` + domain components:

```tsx
import { PageShell, PageHeader } from "@/components"
import { FabricCard, DataTable, FilterBar } from "@/components/ui/fabric"

export default function EntityListPage() {
  return (
    <PageShell>
      <PageHeader
        title="Entities"
        description="Manage all entities in the system"
        actions={[{ label: "Create", onClick: handleCreate }]}
      />
      <FilterBar
        search={{ placeholder: "Search entities..." }}
        filters={[/* filter config */]}
      />
      <DataTable data={data} columns={columns} />
    </PageShell>
  )
}
```

### 2. Add a Custom Component

1. Create file in `@/components/ui/fabric/MyComponent.tsx`
2. Use shadcn primitives as building blocks
3. Follow existing patterns (props interface, forwardRef, cn())
4. Add to `components/ui/fabric/index.ts` barrel export
5. Document in skill file if widely used

### 3. Modify the Theme

Edit `frontend/client/src/index.css`:

```css
:root {
  --primary: oklch(0.6112 0.1217 248.9572); /* Change hue for new brand color */
}
```

Regenerate via Tweakcn if doing major changes: https://tweakcn.com

### 4. Add Icons

1. Find icon at https://lucide.dev/icons/
2. Import: `import { IconName } from "lucide-react"`
3. Use in components

---

*This is a living document. Update as the design system evolves.*
