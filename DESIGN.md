# Design System — Value Fabric

This file defines the design system and guardrails for AI coding agents building the Value Fabric UI. Follow these rules to ensure consistent, pixel-perfect output without requiring Figma exports or JSON schemas.

---

## Typography Rules

### Font Families

- **Primary (Sans):** `Inter` (Google Fonts), falling back to system sans-serif stack
- **Secondary (Mono):** `JetBrains Mono`, falling back to system monospace stack
- **Tertiary (Serif):** Georgia, Cambria, "Times New Roman" (rare use cases only)

### Text Hierarchy

| Level | Size | Weight | Line Height | Letter Spacing | Use Case |
|-------|------|--------|-------------|----------------|----------|
| Display XL | 32px | 800 | 1.2 | -0.02em | Page titles, hero headers |
| Display L | 28px | 700 | 1.25 | -0.015em | Section headers |
| Display M | 24px | 600 | 1.3 | -0.01em | Card titles |
| Heading XL | 20px | 600 | 1.4 | -0.005em | Modal headers |
| Heading L | 18px | 600 | 1.4 | normal | Subsection headers |
| Heading M | 16px | 600 | 1.45 | normal | Card subtitles |
| Heading S | 14px | 600 | 1.5 | normal | Form labels |
| Body L | 14px | 400 | 1.6 | normal | Primary body text |
| Body M | 13px | 400 | 1.6 | -0.01em | Default body text (base) |
| Body S | 12px | 400 | 1.5 | normal | Secondary text |
| Caption | 11px | 400 | 1.4 | normal | Helper text, metadata |
| Micro | 10px | 500 | 1.3 | normal | Badges, tags, tiny labels |
| Mono S | 12px | 400 | 1.5 | normal | Code snippets |
| Mono XS | 11px | 400 | 1.4 | normal | Inline code |

### Typography Do's

- Use `Inter` for all UI text unless otherwise specified
- Maintain minimum contrast ratio of 4.5:1 for normal text, 3:1 for large text
- Use letter spacing adjustments only for headings (never body text)
- Reserve mono font for code, data, and technical content
- Never use font sizes smaller than 10px

### Typography Don'ts

- Don't mix font families within the same component
- Don't use bold weights for body text (medium/semibold max)
- Don't stretch or condense fonts
- Don't use all caps except for badges and micro labels
- Don't use serif fonts outside of approved use cases

---

## Layout & Responsive Principles

### Spacing Scale

Base unit: 4px (0.25rem)

| Token | Value | Use Case |
|-------|-------|----------|
| space-0 | 0px | No spacing |
| space-1 | 4px | Tight icon spacing |
| space-2 | 8px | Small gaps, icon-text spacing |
| space-3 | 12px | Compact padding |
| space-4 | 16px | Default padding (cards, buttons) |
| space-5 | 20px | Section spacing |
| space-6 | 24px | Section padding |
| space-8 | 32px | Large gaps, card groups |
| space-10 | 40px | Section margins |
| space-12 | 48px | Page margins |
| space-16 | 64px | Large section spacing |

### Grid System

- **Desktop:** 12-column grid, 80px max-width gutters
- **Tablet:** 8-column grid, 24px gutters
- **Mobile:** 4-column grid, 16px gutters
- **Container max-widths:** 768px (md), 1024px (lg), 1280px (xl), 1536px (2xl)

### Device Breakpoints

| Breakpoint | Min Width | Max Width | Target Device |
|------------|-----------|-----------|----------------|
| mobile | 0px | 767px | Phones |
| tablet | 768px | 1023px | Tablets |
| desktop | 1024px | 1279px | Laptops |
| desktop-xl | 1280px | 1535px | Desktops |
| desktop-2xl | 1536px+ | Ultra-wide monitors |

### Collapsing Strategies

1. **Mobile-first:** Start with mobile layout, enhance for larger screens
2. **Progressive disclosure:** Hide advanced features behind toggles on mobile
3. **Horizontal to vertical:** Convert horizontal layouts to stacked on mobile
4. **Icon-only navigation:** Collapse sidebar to icon rail on small screens
5. **Modal over panel:** Use modals instead of side panels on screens < 1024px
6. **Truncate with tooltips:** Long text truncates with ellipsis, shows full text on hover

### Whitespace Philosophy

- **Breathing room:** Minimum 16px padding around content areas
- **Visual hierarchy:** Use spacing to group related elements
- **Consistent rhythm:** Maintain 8px baseline grid where possible
- **Negative space:** Don't fear whitespace—it improves readability
- **Density balance:** Higher density for data-dense views, lower for content pages

---

## Component & Color Rules

### Color Palette (Semantic)

#### Primary Colors
| Token | Hex | Light Mode | Dark Mode | Use Case |
|-------|-----|------------|-----------|----------|
| primary | `#007AFF` | oklch(0.7212 0.1303 174.8407) | oklch(0.7212 0.1303 174.8407) | Primary actions, links |
| primary-foreground | `#FFFFFF` | oklch(0.1023 0.0200 171.0469) | oklch(0.0865 0.0163 174.9583) | Text on primary |

#### Neutral Colors
| Token | Hex | Light Mode | Dark Mode | Use Case |
|-------|-----|------------|-----------|----------|
| background | `#FFFFFF` | oklch(1.0000 0 0) | oklch(0.1448 0 0) | Page background |
| foreground | `#0F172A` | oklch(0.1448 0 0) | oklch(0.9851 0 0) | Primary text |
| card | `#FFFFFF` | oklch(1.0000 0 0) | oklch(0.2046 0 0) | Card backgrounds |
| card-foreground | `#0F172A` | oklch(0.1448 0 0) | oklch(1 0 0) | Card text |
| border | `#E2E8F0` | oklch(0.9219 0 0) | oklch(0.2680 0.0070 34.2980) | Borders, dividers |
| input | `#E2E8F0` | oklch(0.9219 0 0) | oklch(0.2046 0 0) | Input borders |
| muted | `#F8FAFC` | oklch(0.9702 0 0) | oklch(0.2686 0 0) | Disabled backgrounds |
| muted-foreground | `#64748B` | oklch(0.5555 0 0) | oklch(0.7090 0 0) | Secondary text |

#### Semantic Colors
| Token | Hex | Light Mode | Dark Mode | Use Case |
|-------|-----|------------|-----------|----------|
| destructive | `#EF4444` | oklch(0.5830 0.2387 28.4765) | oklch(0.7022 0.1892 22.2279) | Delete, error states |
| destructive-foreground | `#FFFFFF` | oklch(1.0000 0 0) | oklch(1.0000 0 0) | Text on destructive |
| success | `#10B981` | oklch(0.65 0.15 150) | oklch(0.65 0.15 150) | Success states |
| warning | `#F59E0B` | oklch(0.70 0.15 60) | oklch(0.70 0.15 60) | Warning states |
| info | `#3B82F6` | oklch(0.65 0.15 250) | oklch(0.65 0.15 250) | Info states |

#### Accent Colors
| Token | Hex | Light Mode | Dark Mode | Use Case |
|-------|-----|------------|-----------|----------|
| accent | `#0EA5E9` | oklch(0.8609 0.1108 169.8822) | oklch(0.7801 0.1194 170.2059) | Hover states, highlights |
| accent-foreground | `#FFFFFF` | oklch(0.1198 0.0231 172.5034) | oklch(0.0865 0.0163 174.9583) | Text on accent |

#### Sidebar Colors
| Token | Hex | Light Mode | Dark Mode | Use Case |
|-------|-----|------------|-----------|----------|
| sidebar | `#F8FAFC` | oklch(0.9851 0 0) | oklch(0.2046 0 0) | Sidebar background |
| sidebar-foreground | `#0F172A` | oklch(0.1448 0 0) | oklch(0.9851 0 0) | Sidebar text |
| sidebar-primary | `#007AFF` | oklch(0.7212 0.1303 174.8407) | oklch(0.7212 0.1303 174.8407) | Sidebar active state |
| sidebar-accent | `#F1F5F9` | oklch(0.9702 0 0) | oklch(0.2686 0 0) | Sidebar hover |

#### Chart Colors
| Token | Hex | Use Case |
|-------|-----|----------|
| chart-1 | `#007AFF` | Primary data series |
| chart-2 | `#10B981` | Secondary data series |
| chart-3 | `#F59E0B` | Tertiary data series |
| chart-4 | `#EF4444` | Quaternary data series |
| chart-5 | `#8B5CF6` | Quinary data series |

### Component Styling Rules

#### Buttons
- **Primary:** `bg-primary text-primary-foreground hover:bg-primary/90`
- **Secondary:** `bg-secondary text-secondary-foreground hover:bg-secondary/80`
- **Ghost:** `hover:bg-accent hover:text-accent-foreground`
- **Destructive:** `bg-destructive text-destructive-foreground hover:bg-destructive/90`
- **Size variants:** sm (h-8 px-3 text-xs), default (h-9 px-4 text-sm), lg (h-10 px-6 text-base)
- **Radius:** All buttons use `rounded-lg` (0.625rem)
- **Icon buttons:** Use `w-8 h-8` or `w-10 h-10` with centered content

#### Cards
- **Background:** `bg-card text-card-foreground`
- **Border:** `border border-border`
- **Radius:** `rounded-lg` (0.625rem)
- **Padding:** `p-4` (compact), `p-6` (default), `p-8` (spacious)
- **Shadow:** `shadow-sm` (default), `shadow-md` (elevated), `shadow-lg` (modal)
- **Hover:** Add `hover:border-primary/50` for interactive cards

#### Inputs
- **Background:** `bg-background`
- **Border:** `border border-input`
- **Radius:** `rounded-md` (0.5rem)
- **Padding:** `px-3 py-2` (default)
- **Focus:** `focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2`
- **Error state:** `border-destructive focus:ring-destructive`
- **Disabled:** `opacity-50 cursor-not-allowed`

#### Navigation States
- **Active:** `bg-sidebar-primary/15 text-sidebar-primary font-semibold`
- **Inactive:** `text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent`
- **Collapsed:** Icon-only with tooltips on hover
- **Mobile:** Icon rail (w-20) with touch targets min-h-[56px]

### Color Usage Rules
- **Accessibility:** Always maintain WCAG AA contrast (4.5:1 for text, 3:1 for large text)
- **Semantic use:** Use semantic colors for their intended purpose (success for success, not for decoration)
- **Brand consistency:** Primary blue (#007AFF) is the brand color—use it for primary actions
- **Dark mode:** All colors must have dark mode equivalents defined in oklch
- **Neutral dominance:** Use neutral colors for structure, semantic colors for meaning

---

## Do's and Don'ts

### Do's
- ✅ Use the defined spacing scale consistently
- ✅ Maintain 8px baseline grid alignment
- ✅ Use responsive breakpoints (sm, md, lg, xl, 2xl)
- ✅ Provide hover, focus, and disabled states for all interactive elements
- ✅ Use semantic color tokens instead of hard-coded hex values
- ✅ Include proper aria labels for accessibility
- ✅ Test dark mode compatibility for all components
- ✅ Use flexbox and grid for layout (avoid float)
- ✅ Implement mobile-first responsive design
- ✅ Use Tailwind utility classes for all styling
- ✅ Maintain consistent border radius (0.625rem default)
- ✅ Provide loading states for async operations
- ✅ Use truncate with tooltips for long text
- ✅ Implement proper error boundaries
- ✅ Follow the component hierarchy (atoms → molecules → organisms)

### Don'ts
- ❌ Use hard-coded pixel values (use rem or Tailwind spacing)
- ❌ Mix light/dark mode colors in the same component
- ❌ Use inline styles (use Tailwind classes)
- ❌ Create custom color values (use defined tokens)
- ❌ Use fixed widths (use max-width or responsive classes)
- ❌ Ignore accessibility (contrast, keyboard navigation, screen readers)
- ❌ Skip hover/focus states
- ❌ Use arbitrary values in Tailwind (e.g., `w-[327px]`)
- ❌ Nest components deeper than 4 levels
- ❌ Use !important (except for utility overrides)
- ❌ Skip responsive design (assume mobile users)
- ❌ Use deprecated or experimental CSS features
- ❌ Mix design systems (stick to Tailwind + Radix UI)
- ❌ Create duplicate components (reuse existing ones)
- ❌ Ignore performance (lazy load images, code split routes)

---

## Agent Prompt Guide

### Quick Color Reference
```
Primary action: bg-primary text-primary-foreground
Secondary action: bg-secondary text-secondary-foreground
Destructive action: bg-destructive text-destructive-foreground
Card: bg-card border border-border rounded-lg
Input: border border-input rounded-md focus:ring-2 focus:ring-ring
Sidebar active: bg-sidebar-primary/15 text-sidebar-primary
Sidebar inactive: text-sidebar-foreground/70 hover:bg-sidebar-accent
```

### Ready-to-Use Prompts

#### For Creating a New Component
```
Create a [component name] component following the Value Fabric design system:
- Use Inter font, 13px base size, -0.01em letter spacing
- Apply rounded-lg (0.625rem) border radius
- Use semantic color tokens from DESIGN.md
- Include responsive breakpoints (mobile-first approach)
- Add hover, focus, and disabled states
- Ensure WCAG AA contrast ratios
- Support dark mode with oklch color equivalents
- Use Tailwind utility classes only
- Implement proper aria labels for accessibility
```

#### For Styling a Form
```
Style this form following Value Fabric design system:
- Use rounded-md (0.5rem) for input fields
- Apply border border-input with focus:ring-2 focus:ring-ring
- Use semantic colors for validation states
- Maintain 8px vertical rhythm between fields
- Add proper error messaging with destructive color
- Ensure labels use Heading S (14px, 600 weight)
- Use Caption (11px) for helper text
- Make all inputs fully responsive
```

#### For Building a Data Table
```
Build a data table component following Value Fabric design system:
- Use Body M (13px) for cell text
- Apply border border-border for table structure
- Use Heading S (14px, 600) for column headers
- Add subtle hover states (bg-muted/50)
- Implement proper sorting indicators
- Use chart color palette for status badges
- Ensure horizontal scroll on mobile (overflow-x-auto)
- Maintain minimum 44px touch targets
```

#### For Creating a Modal
```
Create a modal component following Value Fabric design system:
- Use bg-card with shadow-lg and rounded-lg
- Apply Heading XL (20px, 600) for modal title
- Use Body L (14px) for modal content
- Add backdrop blur overlay (bg-background/80)
- Implement proper focus trap
- Ensure close button is top-right with icon
- Use primary action on right, secondary on left
- Make responsive (full width on mobile, centered on desktop)
```

#### For Navigation Elements
```
Style this navigation element following Value Fabric design system:
- Use sidebar color tokens for navigation
- Apply bg-sidebar-primary/15 for active state
- Use text-sidebar-foreground/70 for inactive state
- Add hover:bg-sidebar-accent for hover state
- Implement icon-only collapsed state with tooltips
- Ensure min-h-[56px] touch targets on mobile
- Use Heading M (16px, 600) for section labels
- Apply proper aria-current="page" for active links
```

### Design Token Quick Reference
```
Spacing: space-1 (4px) to space-16 (64px) in 4px increments
Radius: rounded-md (0.5rem), rounded-lg (0.625rem), rounded-xl (0.75rem)
Font: Inter (sans), JetBrains Mono (mono)
Shadows: shadow-sm, shadow-md, shadow-lg, shadow-xl, shadow-2xl
Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px), 2xl (1536px)
Z-index: 0 (base), 10 (dropdown), 20 (sticky), 30 (fixed), 40 (modal), 50 (tooltip)
```

---

## Component Library Reference

### Required UI Components
All components must use Radix UI primitives as the foundation, styled with Tailwind CSS according to this design system.

- **Buttons:** Button (primary, secondary, ghost, destructive)
- **Inputs:** Input, Textarea, Select, Checkbox, Radio, Switch
- **Navigation:** Navigation Menu, Breadcrumb, Tabs, Pagination
- **Feedback:** Toast, Alert, Progress, Skeleton
- **Layout:** Card, Dialog, Sheet, Scroll Area, Separator
- **Data:** Table, Badge, Avatar, Tooltip, Popover
- **Forms:** Label, Form Field, Form Message

### Custom Components
Build custom components only when Radix UI primitives don't provide the necessary functionality. Always follow the design system rules for styling.

---

## Design Principles Summary

1. **Consistency:** Use defined tokens for all design decisions
2. **Accessibility:** WCAG AA compliance, keyboard navigation, screen reader support
3. **Responsiveness:** Mobile-first, progressive enhancement
4. **Performance:** Lazy loading, code splitting, optimized images
5. **Maintainability:** Clear component hierarchy, reusable patterns
6. **User Experience:** Clear feedback, intuitive interactions, fast load times
7. **Brand Alignment:** Consistent use of primary blue and semantic colors
8. **Dark Mode:** Full support with proper color contrast

---

## Version History
- **v1.0** (2026-05-06): Initial design system definition
