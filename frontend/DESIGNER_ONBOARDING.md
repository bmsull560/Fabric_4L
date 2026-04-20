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
| **Icons** | Lucide React | 1000+ consistent line icons |
| **Theme** | Tweakcn Generated | Blue-tinted neutral palette, oklch colors |
| **Registry** | @shadcnuikit | Premium blocks: hero sections, pricing tables, etc. |

---

## Design System Overview

### Philosophy

1. **Compose, don't customize** — Stack shadcn primitives (`Card` + `Tabs` + `Form`) rather than writing custom CSS
2. **Semantic tokens** — Use `bg-primary` not `bg-blue-500` for theme adaptability
3. **Dark mode first** — Every component supports `.dark` class toggle
4. **Fabric patterns** — Use domain components for consistent product UX

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

**Layout**
- `Card` — containers with Header/Content/Footer structure
- `Separator` — horizontal/vertical dividers
- `ScrollArea` — custom scrollbars
- `Resizable` — draggable panes

**Forms**
- `Input`, `Textarea` — text entry
- `Select`, `Combobox` — dropdowns (Combobox = searchable)
- `Checkbox`, `RadioGroup`, `Switch` — boolean/option selection
- `Slider` — range selection
- `Form` — react-hook-form integration

**Overlays**
- `Dialog` — modal windows
- `Sheet` — slide-out panels (right/left/top/bottom)
- `Drawer` — mobile-style bottom sheets
- `AlertDialog` — confirmation dialogs
- `Popover`, `Tooltip`, `HoverCard` — contextual info

**Navigation**
- `Sidebar` — collapsible navigation
- `Tabs` — content switching
- `Breadcrumb` — path navigation
- `NavigationMenu` — mega menus
- `Command` — command palette

**Data Display**
- `Table` — HTML tables with shadcn styling
- `Badge` — status labels
- `Avatar` — user/profile images
- `Skeleton` — loading placeholders
- `Chart` — Recharts wrapper

**Feedback**
- `sonner` — toast notifications
- `Alert` — callout messages
- `Progress` — loading bars
- `Spinner` — loading indicators

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

### Key Patterns

```tsx
// Card with full composition
<Card>
  <CardHeader>
    <CardTitle>Entity Name</CardTitle>
    <CardDescription>Entity details and metadata</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Main content */}
  </CardContent>
  <CardFooter className="flex justify-end gap-2">
    <Button variant="outline">Cancel</Button>
    <Button>Save</Button>
  </CardFooter>
</Card>

// Form with validation
<Form {...form}>
  <form onSubmit={form.handleSubmit(onSubmit)}>
    <FormField
      control={form.control}
      name="email"
      render={({ field }) => (
        <FormItem>
          <FormLabel>Email</FormLabel>
          <FormControl>
            <Input {...field} />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  </form>
</Form>

// Status indicators
<StatusBadge status="active" />     // Green
<StatusBadge status="pending" />    // Yellow
<StatusBadge status="error" />      // Red
<StatusBadge status="warning" />    // Orange
```

---

## Iconography

- **Library**: Lucide React (`lucide-react`)
- **Style**: Consistent 24x24 grid, 2px stroke, rounded caps
- **Usage**: Pass as components, not strings

```tsx
import { SearchIcon, CheckIcon, AlertCircleIcon } from "lucide-react"

// In buttons — use data-icon prop
<Button>
  <SearchIcon data-icon="inline-start" />
  Search
</Button>

// Icon-only button
<Button size="icon" aria-label="Close">
  <XIcon />
</Button>

// Standalone icons
<AlertCircleIcon className="size-5 text-muted-foreground" />
```

---

## Spacing & Layout

**Principles**:
- Use `gap-*` for spacing (not `space-x-*` or `space-y-*`)
- Use `size-*` for equal width/height (not `w-* h-*`)
- Use `flex` and `grid` for layouts

### Common Patterns

```tsx
// Vertical stack
div className="flex flex-col gap-4">

// Horizontal row
div className="flex items-center gap-4">

// Grid layout
div className="grid grid-cols-3 gap-4">

// Container with padding
div className="p-4 md:p-6 lg:p-8">

// Full-height layout with sidebar
<div className="flex h-screen">
  <Sidebar />
  <main className="flex-1 overflow-auto">
    {/* Page content */}
  </main>
</div>
```

---

## The shadcn Registry System

### Adding Components

```bash
# From official shadcn/ui registry
npx shadcn@latest add button
npx shadcn@latest add dialog table select

# From @shadcnuikit (premium blocks)
npx shadcn add @shadcnuikit/hero-section
npx shadcn add @shadcnuikit/pricing-table
npx shadcn add @shadcnuikit/feature-section
```

### Available Block Categories (shadcnuikit)

- **Hero Sections** (14 blocks) — Landing page headers
- **Pricing Tables** (7 blocks) — SaaS pricing layouts
- **Feature Sections** (13 blocks) — Product feature showcases
- **Testimonials** (15 blocks) — Social proof layouts
- **CTA Sections** (10 blocks) — Call-to-action blocks
- **Team Sections** (5 blocks) — Team/company pages
- **Footers** (5 blocks) — Site footer patterns
- **Checkout Pages** (5 blocks) — E-commerce checkout

### After Adding Components

1. **Review the files** — Check `@/components/ui/` for new component
2. **Verify imports** — Ensure paths use `@/components/ui/*`
3. **Update icons** — Replace any non-lucide icons with lucide equivalents
4. **Test in both themes** — Verify light and dark mode appearance

---

## File Structure

```
frontend/client/src/
├── components/
│   ├── ui/                    # shadcn primitives
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   └── ... (50+ files)
│   ├── ui/fabric/             # Fabric custom components
│   │   ├── FabricCard.tsx
│   │   ├── DataTable.tsx
│   │   ├── StatusBadge.tsx
│   │   └── ...
│   ├── AppShell.tsx           # Main layout shell
│   ├── PageShell.tsx          # Page wrapper
│   ├── TieredNav.tsx          # Navigation component
│   └── ...
├── hooks/                     # React Query hooks
├── lib/
│   └── utils.ts               # cn() utility for class merging
├── pages/                     # Route components
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
- **shadcn-fabric Skill** — `.windsurf/skills/shadcn-fabric/SKILL.md`
- **Styling Rules** — `.windsurf/skills/shadcn-fabric/rules/styling.md`
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

## Questions?

- Check existing pages for patterns
- Review `SKILL.md` and rule files in `.windsurf/skills/shadcn-fabric/`
- Run `npx shadcn@latest info` to see installed components
- Use `npx shadcn@latest docs <component>` for API reference

---

*This is a living document. Update as the design system evolves.*
