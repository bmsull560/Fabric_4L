# Value Fabric Design System

**Frontend Design Reference** | React + Tailwind + shadcn/ui | Last Updated: April 2026

---

## 1. Design Philosophy

### Core Principles

1. **Compose, don't customize** — Stack shadcn primitives (`Card` + `Tabs` + `Form`) rather than writing custom CSS. Use domain components for consistent product UX.

2. **Semantic tokens** — Use `bg-primary` not `bg-blue-500` for theme adaptability across light/dark modes.

3. **Dark mode first** — Every component supports `.dark` class toggle. Test both modes during development.

4. **Progressive synthesis** — The UI follows a cognitive spine from Signal → Explanation → Proof → Translation → Intervention → Quantified Value.

5. **Enterprise-grade aesthetic** — Clean, minimal design inspired by Linear, Vercel, and Clerk. Professional without being boring.

### Visual Language

| Aspect | Specification |
|--------|---------------|
| **Primary** | Blue `oklch(0.6112 0.1217 248.9572)` — professional, trustworthy |
| **Contrast** | WCAG AA compliant ratios for all text |
| **Shadows** | Subtle 2px-4px depth, never heavy elevation |
| **Spacing** | Generous 16px-24px gaps, never cramped |
| **Typography** | Inter font family, -0.01em letter-spacing for modern feel |

---

## 2. Visual Foundation

### Color System (oklch)

All colors use **oklch** for perceptual uniformity and smooth dark mode transitions.

#### Light Mode

| Token | Value | Usage |
|-------|-------|-------|
| `--background` | `oklch(0.9581)` | Page background (near-white) |
| `--foreground` | `oklch(0.3134)` | Primary text (dark gray) |
| `--primary` | `oklch(0.6112)` | CTAs, links, active states (blue) |
| `--primary-foreground` | `oklch(1.0)` | Text on primary backgrounds |
| `--secondary` | `oklch(0.9122)` | Secondary backgrounds (subtle gray) |
| `--muted` | `oklch(0.9209)` | Subtle backgrounds (light gray) |
| `--muted-foreground` | `oklch(0.6027)` | Secondary text (medium gray) |
| `--border` | `oklch(0.8840)` | Dividers, input borders |
| `--destructive` | `oklch(0.1931)` | Errors, delete actions (dark red) |
| `--card` | `oklch(0.9774)` | Card backgrounds |
| `--popover` | `oklch(1.0)` | Popover/dropdown backgrounds |

#### Dark Mode

| Token | Value | Usage |
|-------|-------|-------|
| `--background` | `oklch(0.1776)` | Page background (near-black) |
| `--foreground` | `oklch(0.7905)` | Primary text (light gray) |
| `--primary` | `oklch(0.6576)` | CTAs, links (lighter blue) |
| `--secondary` | `oklch(0.9774)` | Secondary backgrounds (off-white) |
| `--muted` | `oklch(0.2171)` | Subtle backgrounds (dark gray) |
| `--muted-foreground` | `oklch(0.7559)` | Secondary text (light gray) |
| `--border` | `oklch(0.3506)` | Dividers, input borders |
| `--destructive` | `oklch(0.6368)` | Errors, delete actions (bright red) |
| `--card` | `oklch(0.2638)` | Card backgrounds |
| `--popover` | `oklch(0.3046)` | Popover/dropdown backgrounds |

### Typography

| Element | Specification |
|---------|---------------|
| **Font Family** | Inter (sans-serif), Georgia (serif), monospace (code) |
| **Base Size** | 13px (compact for data-dense UI) |
| **Letter Spacing** | -0.01em (slightly tighter) |
| **Weights** | 400 (body), 500 (medium), 600 (semibold), 700 (bold) |

#### Type Scale

| Token | Size | Usage |
|-------|------|-------|
| `text-xs` | 12px | Captions, badges |
| `text-sm` | 13px | Body text |
| `text-base` | 14px | Emphasized body |
| `text-lg` | 16px | Card titles |
| `text-xl` | 20px | Page titles |
| `text-2xl` | 24px | Hero headings |

### Spacing System

Based on 4px grid (`--spacing: 0.25rem`):

| Token | Value | Usage |
|-------|-------|-------|
| `gap-4` | 16px | Standard component gaps |
| `gap-6` | 24px | Section separations |
| `p-4` | 16px | Standard padding |
| `p-6` | 24px | Card padding |

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `radius-sm` | ~0.25rem | Small elements |
| `radius-md` | ~0.375rem | Inputs, buttons |
| `radius-lg` | ~0.5rem | Cards, dialogs |
| `radius-xl` | ~0.75rem | Large containers |

---

## 3. Component Architecture

### shadcn/ui Primitives (50+)

Located in `@/components/ui/`. Import via barrel export:

```tsx
import { Card, Button, Dialog, Tabs } from "@/components"
```

**Layout**: `Card`, `Separator`, `ScrollArea`, `Resizable`

**Forms**: `Input`, `Textarea`, `Select`, `Combobox`, `Checkbox`, `RadioGroup`, `Switch`, `Slider`, `Form`

**Overlays**: `Dialog`, `Sheet`, `Drawer`, `AlertDialog`, `Popover`, `Tooltip`, `HoverCard`

**Navigation**: `Sidebar`, `Tabs`, `Breadcrumb`, `NavigationMenu`, `Command`

**Data Display**: `Table`, `Badge`, `Avatar`, `Skeleton`, `Chart`

**Feedback**: `sonner` (toasts), `Alert`, `Progress`, `Spinner`

### Fabric Custom Components

Located in `@/components/ui/fabric/`. Domain-specific patterns:

| Component | Purpose | When to Use |
|-----------|---------|-------------|
| `FabricCard` | Entity display cards | Any entity detail/summary view |
| `DataTable` | Tabular data with features | Lists with sorting, filtering |
| `StatusBadge` | Standardized status | Active, pending, error, warning |
| `FilterBar` | Search + filters layout | Any list or table view |
| `PageHeader` | Page structure | All pages (breadcrumb + title + actions) |
| `FabricDialog` | Confirmation dialogs | Delete, confirm, warn actions |
| `LoadingSkeleton` | Page-level loading | Initial page load states |

### WfPrimitives (Workflow Components)

Located in `@/components/WfPrimitives.tsx`. Used in Intelligence and Value Studio:

| Component | Purpose | When to Use |
|-----------|---------|-------------|
| `SectionCard` | Panel container with title | Any panel in workflow pages |
| `Btn` | Standardized button | All action buttons |
| `SearchInput` | Search field with icon | Any searchable list |
| `DataTable` | Lightweight table | Data tables in workflow pages |

### Component Usage Patterns

```tsx
// Correct — semantic tokens
<div className="bg-primary text-primary-foreground">

// Wrong — raw colors
<div className="bg-blue-500 text-white">
```

---

## 4. Layout Patterns

### Three-Layer UI Structure

The UI follows a strict three-layer separation:

```
┌─────────────────────────────────────────────────────────┐
│  Left Rail      │  Center Canvas      │  Right Rail    │
│  (Where am I?)  │  (What am I doing?) │  (Support)     │
├─────────────────────────────────────────────────────────┤
│  • Home         │  Workspace tabs     │  Detail Panel  │
│  • Accounts     │  Content area       │  Agent Stream  │
│  • Intelligence │                     │                │
│  • Value Studio │                     │                │
│  • Context Eng. │                     │                │
│  • Deliverables │                     │                │
│  • Governance   │                     │                │
│  • Settings     │                     │                │
└─────────────────────────────────────────────────────────┘
```

### Page Shell Pattern

```tsx
import { PageShell, PageHeader } from "@/components"
import { FabricCard, DataTable, FilterBar } from "@/components"

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

### Workspace Tabs Pattern

**Intelligence Workspace** (`/intelligence/:accountId/*`):
- **Signals** — AI-surfaced pain points (default landing)
- **Drivers** — Root cause analysis
- **Evidence** — Source documents, confidence grading
- **Stakeholders** — Persona-mapped findings

**Value Studio Workspace** (`/studio/:accountId/*`):
- **Action Plan** — Product-anchored recommendations
- **Value Model** — Quantified business case
- **Narrative** — Stakeholder-ready packaging

### Navigation Domains (Left Rail)

| Domain | Purpose | Tier |
|--------|---------|------|
| **Home** | Dashboard with KPIs | Standard |
| **Accounts** | Prospect/customer records | Standard |
| **Intelligence** | Discover and validate | Standard |
| **Value Studio** | Build business case | Standard |
| **Context Engine** | Vendor knowledge base | Advanced |
| **Deliverables** | Artifact library | Standard |
| **Governance** | Audit trails, compliance | Advanced |
| **Settings** | Admin control plane | Admin |

---

## 5. Theme Implementation

### CSS Variable System

Theme variables are defined in `frontend/client/src/index.css`:

```css
:root {
  --radius: 0.5rem;
  --primary: oklch(0.6112 0.1217 248.9572);
  --primary-foreground: oklch(1.0000 0 0);
  /* ... see full index.css for all variables */
}

.dark {
  --primary: oklch(0.6576 0.1208 252.0832);
  --primary-foreground: oklch(1.0000 0 0);
  /* ... dark mode overrides */
}
```

### ThemeContext Usage

```tsx
import { ThemeProvider, useTheme } from "@/contexts/ThemeContext"

// In app root
<ThemeProvider defaultTheme="light" switchable>
  <App />
</ThemeProvider>

// In components
const { theme, toggleTheme, switchable } = useTheme()

// Toggle programmatically
document.documentElement.classList.toggle("dark")
```

### Semantic Token Guidelines

| Context | Token | Example |
|---------|-------|---------|
| Primary actions | `bg-primary text-primary-foreground` | Submit buttons |
| Secondary actions | `bg-secondary text-secondary-foreground` | Cancel buttons |
| Destructive | `bg-destructive text-destructive-foreground` | Delete buttons |
| Muted text | `text-muted-foreground` | Descriptions |
| Borders | `border-border` | Dividers |
| Cards | `bg-card text-card-foreground` | Panels |

---

## 6. Code Patterns

### Import Patterns

**Preferred (consolidated):**
```tsx
import { AppShell, ErrorBoundary, Toaster, TooltipProvider } from "@/components"
import { useFormulas, type Formula, useUserTierStore, type UserTier } from "@/hooks"
```

**Legacy (avoid):**
```tsx
import { Toaster } from "@/components/ui/sonner"
import ErrorBoundary from "./components/ErrorBoundary"
import { useUserTierStore, type UserTier } from "./stores/userTierStore"
```

### Component Barrel Export

Add new components to `frontend/client/src/components/index.ts`:

```typescript
// Domain Components
export { default as PageHeader } from "./PageHeader"
export { default as FabricCard } from "./ui/fabric/FabricCard"

// UI Primitives (from shadcn)
export { Button, buttonVariants } from "./ui/button"
export { Card, CardContent, CardHeader } from "./ui/card"
```

### Error Boundary Pattern

```tsx
import { ErrorBoundary, ErrorFallback } from "@/components"

<ErrorBoundary fallback={ErrorFallback}>
  <PageContent />
</ErrorBoundary>
```

### Loading State Pattern

```tsx
import { SkeletonCard, SkeletonTable } from "@/components"

// Page-level loading
if (isLoading) {
  return (
    <div className="space-y-4">
      <SkeletonCard />
      <SkeletonTable rows={5} />
    </div>
  )
}
```

### Form Pattern with shadcn

```tsx
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components"
import { Input, Button } from "@/components"

<Form {...form}>
  <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
    <FormField
      control={form.control}
      name="email"
      render={({ field }) => (
        <FormItem>
          <FormLabel>Email</FormLabel>
          <FormControl>
            <Input placeholder="email@example.com" {...field} />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
    <Button type="submit">Submit</Button>
  </form>
</Form>
```

### TypeScript Patterns

**Generic hooks with proper typing:**
```tsx
interface ApproveFormulaParams {
  formulaId: string
  comments?: string
}

const useApproveFormula = () => {
  return useMutation<unknown, FormulaApiError, ApproveFormulaParams>({
    mutationFn: async ({ formulaId, comments }) => {
      // implementation
    },
    onError: (error) => {
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to approve formula:', error)
      }
    },
  })
}
```

**Type guards instead of assertions:**
```tsx
// Good
function hasPosition(node: GraphNode): node is GraphNode & { x: number; y: number } {
  return 'x' in node && 'y' in node
}

// Avoid
const x = (node as GraphNode & { x?: number }).x
```

---

## 7. Accessibility Requirements

### WCAG AA Compliance

| Requirement | Implementation |
|-------------|----------------|
| **Contrast** | All text meets 4.5:1 ratio (3:1 for large text) |
| **Focus** | Visible focus rings via `--ring` token |
| **Keyboard** | All interactive elements keyboard accessible |
| **Screen readers** | Semantic HTML, ARIA labels where needed |
| **Motion** | Respect `prefers-reduced-motion` |

### Accessibility Hooks

```tsx
import { usePrefersReducedMotion, useFocusTrap, useAnnouncer } from "@/hooks"

// Reduce motion for animations
const prefersReducedMotion = usePrefersReducedMotion()

// Trap focus in modals
useFocusTrap(dialogRef, isOpen)

// Announce changes to screen readers
const announce = useAnnouncer()
announce('Data loaded successfully')
```

---

## 8. Common Tasks

### 1. Create a New Page

```tsx
// pages/MyNewPage.tsx
import { PageShell, PageHeader, Card, CardContent } from "@/components"

export default function MyNewPage() {
  return (
    <PageShell>
      <PageHeader
        title="Page Title"
        description="What this page does"
        actions={[{ label: "Action", onClick: handleAction }]}
      />
      <Card>
        <CardContent className="p-6">
          Content here
        </CardContent>
      </Card>
    </PageShell>
  )
}
```

### 2. Add a Custom Component

```tsx
// components/ui/fabric/MyComponent.tsx
import { cn } from "@/lib/utils"
import { Card } from "@/components"

interface MyComponentProps {
  title: string
  className?: string
}

export function MyComponent({ title, className }: MyComponentProps) {
  return (
    <Card className={cn("p-4", className)}>
      <h3 className="text-lg font-medium">{title}</h3>
    </Card>
  )
}
```

Then add to barrel export:
```typescript
// components/index.ts
export { MyComponent } from "./ui/fabric/MyComponent"
```

### 3. Add a New Hook

```tsx
// hooks/useMyFeature.ts
import { useQuery } from "@tanstack/react-query"

export function useMyFeature(id: string) {
  return useQuery({
    queryKey: ["my-feature", id],
    queryFn: async () => {
      const response = await fetch(`/api/my-feature/${id}`)
      if (!response.ok) throw new Error("Failed to fetch")
      return response.json()
    },
  })
}
```

Then add to barrel export:
```typescript
// hooks/index.ts
export { useMyFeature } from "./useMyFeature"
```

### 4. Modify Theme Colors

Edit `frontend/client/src/index.css`:

```css
:root {
  /* Change hue for new brand color */
  --primary: oklch(0.6112 0.1217 180); /* Teal instead of blue */
}
```

For major changes, regenerate via Tweakcn: https://tweakcn.com

### 5. Add Icons

1. Find icon at https://lucide.dev/icons/
2. Import: `import { IconName } from "lucide-react"`
3. Use in components with semantic sizing:

```tsx
import { Search, ChevronRight } from "lucide-react"

<Search className="h-4 w-4" /> {/* Small inline */}
<ChevronRight className="h-5 w-5" /> {/* Standard */}
```

---

## 9. File Structure Reference

```
frontend/client/src/
├── components/
│   ├── ui/                    # shadcn primitives (50+ files)
│   ├── ui/fabric/             # Fabric custom components
│   ├── navigation/
│   │   └── TieredNav.tsx      # Left rail navigation
│   ├── AppShell.tsx           # Main layout shell
│   ├── WfPrimitives.tsx       # Workflow primitive components
│   └── index.ts               # Barrel exports
├── hooks/                     # React Query hooks
│   └── index.ts               # Barrel exports
├── lib/
│   └── utils.ts               # cn() utility for class merging
├── pages/                     # Route components
│   ├── intelligence/          # Intelligence workspace
│   ├── value-studio/          # Value Studio workspace
│   └── admin/                 # Admin pages
├── stores/                    # Zustand state
├── contexts/                  # React contexts (Theme, etc.)
└── index.css                  # Global styles + theme variables
```

---

## 10. Design Resources

### Internal Documentation
- **Designer Onboarding** — `frontend/DESIGNER_ONBOARDING.md`
- **Navigation Architecture** — `docs/NAVIGATION_ARCHITECTURE.md`
- **Implementation Plan** — `docs/IMPLEMENTATION_PLAN.md`

### External References
- **shadcn/ui** — https://ui.shadcn.com/docs
- **Tailwind CSS** — https://tailwindcss.com/docs
- **Lucide Icons** — https://lucide.dev/icons/
- **Radix Primitives** — https://www.radix-ui.com/primitives
- **Tweakcn Themes** — https://tweakcn.com

---

*This document is a living reference. Update as the design system evolves.*
