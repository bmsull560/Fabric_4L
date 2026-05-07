# Value Fabric - Figma Design Specification

## Overview

This document provides a comprehensive design specification for recreating the Value Fabric frontend UI in Figma. The design system is built on shadcn/ui components with Tailwind CSS v4, using OKLCH color space for accessibility and modern color management.

---

## Design Tokens

### Color System (OKLCH)

#### Light Mode Colors
```
Primary Blue:       oklch(0.7212 0.1303 174.8407)
Primary Foreground: oklch(0.1023 0.0200 171.0469)

Background:         oklch(1.0000 0 0)
Foreground:         oklch(0.1448 0 0)
Card:               oklch(1.0000 0 0)
Card Foreground:    oklch(0.1448 0 0)
Popover:            oklch(1.0000 0 0)
Popover Foreground: oklch(0.1448 0 0)

Secondary:          oklch(0.9702 0 0)
Secondary Foreground: oklch(0.2046 0 0)
Muted:              oklch(0.9702 0 0)
Muted Foreground:   oklch(0.5555 0 0)
Accent:             oklch(0.8609 0.1108 169.8822)
Accent Foreground:  oklch(0.1198 0.0231 172.5034)

Destructive:        oklch(0.5830 0.2387 28.4765)
Destructive Foreground: oklch(1.0000 0 0)

Border:             oklch(0.9219 0 0)
Input:              oklch(0.9219 0 0)
Ring:               oklch(0.7212 0.1303 174.8407)

Sidebar:            oklch(0.9851 0 0)
Sidebar Foreground: oklch(0.1448 0 0)
Sidebar Primary:    oklch(0.7212 0.1303 174.8407)
Sidebar Primary Foreground: oklch(0.1023 0.0200 171.0469)
Sidebar Accent:     oklch(0.9702 0 0)
Sidebar Accent Foreground: oklch(0.2046 0 0)
Sidebar Border:     oklch(0.9219 0 0)
```

#### Dark Mode Colors
```
Background:         oklch(0.1448 0 0)
Foreground:         oklch(0.9851 0 0)
Card:               oklch(0.2046 0 0)
Card Foreground:    oklch(1 0 0)
Popover:            oklch(0.2686 0 0)
Popover Foreground: oklch(0.9851 0 0)
Primary:            oklch(0.7212 0.1303 174.8407)
Primary Foreground: oklch(0.0865 0.0163 174.9583)
Secondary:          oklch(0.2686 0 0)
Secondary Foreground: oklch(0.9851 0 0)
Muted:              oklch(0.2686 0 0)
Muted Foreground:   oklch(0.7090 0 0)
Accent:             oklch(0.7801 0.1194 170.2059)
Accent Foreground:  oklch(0.0865 0.0163 174.9583)
Destructive:        oklch(0.7022 0.1892 22.2279)
Destructive Foreground: oklch(1.0000 0 0)
Border:             oklch(0.2680 0.0070 34.2980)
Input:              oklch(0.2046 0 0)
Ring:               oklch(0.7212 0.1303 174.8407)
```

#### Chart Colors
```
Chart 1: oklch(0.7212 0.1303 174.8407) - Primary Blue
Chart 2: oklch(0.7794 0.1205 154.9312) - Teal
Chart 3: oklch(0.8189 0.1100 134.9007) - Green
Chart 4: oklch(0.7606 0.1305 95.2156)  - Purple
Chart 5: oklch(0.7208 0.1003 204.3466) - Pink
```

#### Entity Type Badge Colors
```
CAP (Capability):   Violet - bg-violet-100 text-violet-800 border-violet-200
UC (Use Case):      Cyan - bg-cyan-100 text-cyan-800 border-cyan-200
PER (Persona):      Amber - bg-amber-100 text-amber-800 border-amber-200
VD (Value Driver):  Emerald - bg-emerald-100 text-emerald-800 border-emerald-200
```

### Typography

#### Font Families
```
Sans-serif: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif
Serif: ui-serif, Georgia, Cambria, "Times New Roman", Times, serif
Mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace
```

#### Font Sizes
```
Base: 13px
Small: 12px (xs)
Medium: 14px (sm)
Large: 16px (base)
```

#### Letter Spacing
```
Normal: -0.01em
Tighter: calc(-0.01em - 0.05em)
Tight: calc(-0.01em - 0.025em)
Wide: calc(-0.01em + 0.025em)
Wider: calc(-0.01em + 0.05em)
Widest: calc(-0.01em + 0.1em)
```

### Spacing

#### Base Spacing
```
Base Unit: 0.25rem (4px)
```

#### Radius
```
Base Radius: 0.625rem (10px)
SM: calc(0.625rem - 4px) = 6px
MD: calc(0.625rem - 2px) = 8px
LG: 0.625rem = 10px
XL: calc(0.625rem + 4px) = 14px
2XL: calc(0.625rem * 1.8) = 18px
3XL: calc(0.625rem * 2.2) = 22px
4XL: calc(0.625rem * 2.6) = 26px
```

### Shadows

#### Light Mode Shadows
```
2XS: 0px 2px 4px 0px hsl(0 0% 0% / 0.05)
XS:  0px 2px 4px 0px hsl(0 0% 0% / 0.05)
SM:  0px 2px 4px 0px hsl(0 0% 0% / 0.10), 0px 1px 2px -1px hsl(0 0% 0% / 0.10)
MD:  0px 2px 4px 0px hsl(0 0% 0% / 0.10), 0px 2px 4px -1px hsl(0 0% 0% / 0.10)
LG:  0px 2px 4px 0px hsl(0 0% 0% / 0.10), 0px 4px 6px -1px hsl(0 0% 0% / 0.10)
XL:  0px 2px 4px 0px hsl(0 0% 0% / 0.10), 0px 8px 10px -1px hsl(0 0% 0% / 0.10)
2XL: 0px 2px 4px 0px hsl(0 0% 0% / 0.25)
```

#### Dark Mode Shadows
```
2XS: 0px 4px 8px 0px hsl(0 0% 0% / 0.15)
XS:  0px 4px 8px 0px hsl(0 0% 0% / 0.15)
SM:  0px 4px 8px 0px hsl(0 0% 0% / 0.30), 0px 1px 2px -1px hsl(0 0% 0% / 0.30)
MD:  0px 4px 8px 0px hsl(0 0% 0% / 0.30), 0px 2px 4px -1px hsl(0 0% 0% / 0.30)
LG:  0px 4px 8px 0px hsl(0 0% 0% / 0.30), 0px 4px 6px -1px hsl(0 0% 0% / 0.30)
XL:  0px 4px 8px 0px hsl(0 0% 0% / 0.30), 0px 8px 10px -1px hsl(0 0% 0% / 0.30)
2XL: 0px 4px 8px 0px hsl(0 0% 0% / 0.75)
```

---

## Component Library

### Button

#### Variants
```
default:   bg-primary text-primary-foreground shadow hover:bg-primary/90
destructive: bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90
outline:   border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground
secondary: bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80
ghost:     hover:bg-accent hover:text-accent-foreground
link:      text-primary underline-offset-4 hover:underline
```

#### Sizes
```
default: h-9 px-4 py-2
sm:      h-8 rounded-md px-3 text-xs
lg:      h-10 rounded-md px-8
icon:    h-9 w-9
```

#### Base Styles
```
- inline-flex items-center justify-center gap-2
- whitespace-nowrap
- rounded-md
- text-sm font-medium
- transition-colors
- focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring
- disabled:pointer-events-none disabled:opacity-50
- SVG icons: size-4, pointer-events-none, shrink-0
```

### Card

#### Components
```
Card:         rounded-xl border bg-card text-card-foreground shadow
CardHeader:   flex flex-col space-y-1.5 p-6
CardTitle:    font-semibold leading-none tracking-tight
CardDescription: text-sm text-muted-foreground
CardContent:  p-6 pt-0
CardFooter:   flex items-center p-6 pt-0
```

### Input

#### Base Styles
```
- flex h-9 w-full
- rounded-md border border-input
- bg-transparent px-3 py-1
- text-base shadow-sm
- transition-colors
- placeholder:text-muted-foreground
- focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring
- disabled:cursor-not-allowed disabled:opacity-50
- md:text-sm
```

### Badge

#### Variants
```
default:     border-transparent bg-primary text-primary-foreground hover:bg-primary/90
secondary:   border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/90
destructive: border-transparent bg-destructive text-white hover:bg-destructive/90
outline:     text-foreground hover:bg-accent hover:text-accent-foreground
```

#### Base Styles
```
- inline-flex items-center justify-center
- rounded-md border
- px-2 py-0.5
- text-xs font-medium
- w-fit whitespace-nowrap shrink-0
- gap-1
- focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]
- SVG icons: size-3
```

### Tabs

#### Components
```
Tabs:         flex flex-col gap-2
TabsList:     bg-muted text-muted-foreground inline-flex h-9 w-fit items-center justify-center rounded-lg p-[3px]
TabsTrigger:  inline-flex h-[calc(100%-1px)] flex-1 items-center justify-center gap-1.5 rounded-md border border-transparent px-2 py-1 text-sm font-medium whitespace-nowrap
              - Active: bg-background shadow-sm
TabsContent:  flex-1 outline-none
```

### Dialog

#### Components
```
Dialog:       Root component
DialogOverlay: fixed inset-0 z-50 bg-black/50
DialogContent: fixed top-[50%] left-[50%] z-50 grid w-full max-w-[calc(100%-2rem)] translate-x-[-50%] translate-y-[-50%] gap-4 rounded-lg border p-6 shadow-lg
              - sm:max-w-lg
DialogHeader: flex flex-col gap-2 text-center sm:text-left
DialogTitle:  text-lg leading-none font-semibold
DialogDescription: text-muted-foreground text-sm
DialogFooter: flex flex-col-reverse gap-2 sm:flex-row sm:justify-end
```

#### Close Button
```
- absolute top-4 right-4
- rounded-xs opacity-70 transition-opacity hover:opacity-100
- focus:ring-2 focus:ring-offset-2 focus:ring-ring
```

### Select

#### Components
```
Select:         Root component
SelectTrigger:  flex w-fit items-center justify-between gap-2 rounded-md border bg-transparent px-3 py-2 text-sm whitespace-nowrap shadow-xs
                - Sizes: default (h-9), sm (h-8)
SelectContent: bg-popover text-popover-foreground relative z-50 max-h-(--radix-select-content-available-height) min-w-[8rem] overflow-x-hidden overflow-y-auto rounded-md border shadow-md
SelectItem:     relative flex cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-hidden select-none
```

### Table

#### Components
```
Table:         relative w-full overflow-x-auto caption-bottom text-sm
TableHeader:   [&_tr]:border-b
TableBody:     [&_tr:last-child]:border-0
TableRow:      hover:bg-muted/50 data-[state=selected]:bg-muted border-b transition-colors
TableHead:     text-foreground h-10 px-2 text-left align-middle font-medium whitespace-nowrap
TableCell:     p-2 align-middle whitespace-nowrap
```

### Dropdown Menu

#### Components
```
DropdownMenu:              Root component
DropdownMenuContent:       bg-popover text-popover-foreground z-50 max-h-(--radix-dropdown-menu-content-available-height) min-w-[8rem] overflow-x-hidden overflow-y-auto rounded-md border p-1 shadow-md
DropdownMenuItem:          relative flex cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-hidden select-none
                          - focus:bg-accent focus:text-accent-foreground
                          - destructive variant: text-destructive focus:bg-destructive/10
DropdownMenuSeparator:     h-px my-1 bg-border
DropdownMenuGroup:         Group items
DropdownMenuCheckboxItem:  With checkbox indicator
```

### Sidebar

#### Dimensions
```
Expanded Width:  16rem (256px)
Mobile Width:    18rem (288px)
Icon Width:      3rem (48px)
```

#### Components
```
Sidebar:         Fixed sidebar with expand/collapse
SidebarHeader:   Header section
SidebarContent:  Main content area
SidebarFooter:   Footer section
SidebarMenu:     Navigation menu
SidebarMenuItem: Individual menu items
```

#### States
```
Expanded:  Full width with labels
Collapsed: Icon-only mode
Mobile:    Sheet/drawer overlay
```

### Form Components

#### Label
```
- text-sm font-medium leading-none
- peer-disabled:cursor-not-allowed peer-disabled:opacity-70
```

#### Checkbox
```
- h-4 w-4 rounded border border-primary
- data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground
```

#### Switch
```
- h-5 w-9 rounded-full border-2 border-transparent
- data-[state=checked]:bg-primary
- thumb: h-4 w-4 rounded-full bg-background shadow
```

#### Radio Group
```
- h-4 w-4 rounded-full border border-primary
- data-[state=checked]:border-primary data-[state=checked]:bg-primary
```

### Other Components

#### Avatar
```
- h-10 w-10 rounded-full overflow-hidden
- flex items-center justify-center
- bg-muted text-muted-foreground
```

#### Skeleton
```
- animate-pulse
- bg-muted
- rounded-md
```

#### Separator
```
- h-px w-full border-b
- or vertical: h-full w-px border-r
```

#### Tooltip
```
- z-50 overflow-hidden rounded-md border bg-popover px-3 py-1.5 text-sm text-popover-foreground shadow-md
- fade-in zoom-in-95 duration-200
```

#### Progress
```
- h-2 w-full overflow-hidden rounded-full bg-primary/20
- Progress bar: h-full w-full flex-1 bg-primary transition-all duration-500 ease-in-out
```

#### Slider
```
- relative flex w-full touch-none select-none items-center
- h-5 w-full
- track: h-1.5 w-full grow rounded-full bg-primary/20
- thumb: h-4 w-4 rounded-full border border-primary/50 bg-background shadow
```

---

## Page Layouts

### Common Layout Patterns

#### Page Header
```
- Breadcrumb navigation (optional)
- Title (h1 or h2)
- Description (optional)
- Action buttons (right-aligned)
```

#### Section Card
```
- Rounded-xl border
- Card header with title
- Card content area
- Optional footer with actions
```

#### Data Table Layout
```
- Page header with title and actions
- Filter bar (horizontal chips)
- Search input
- Data table with pagination
- Row selection
```

### Key Pages

#### Accounts Page
```
Layout:
- Page header with title and actions (Add Account, Sync)
- Filter bar with dropdown chips (Provider, Status, Industry)
- Search input
- Data table with columns:
  - Account Name
  - Provider (Salesforce/HubSpot/Manual)
  - Industry
  - Status
  - Last Sync
  - Actions menu
- Pagination bar
- Account detail panel (slide-over or modal)
```

#### Business Case Viewer
```
Layout:
- Page header with title and actions (Export, Share, View Trace)
- Hero ROI card with gradient background
  - Total ROI metric
  - Supporting metrics (Timeframe, Confidence, Cases)
- Recommendations section
- Detailed sections (Value Drivers, Evidence, etc.)
- Interactive exploration option
```

#### Formula Builder
```
Layout:
- Page header with formula name and actions
- Three-panel layout:
  - Left: Dependency panel
  - Center: Formula editor
  - Right: Scenario panel
- Version history panel
- Save/Publish actions
```

---

## Icon System

### Icon Library
- **Library**: Lucide React
- **Size**: Default 16px (size-4), can be scaled
- **Color**: Inherits text color

### Common Icons
```
Navigation:   ChevronLeft, ChevronRight, Menu, PanelLeft
Actions:      Plus, Download, Share2, Search, Filter, RefreshCw
Status:       Check, X, AlertCircle, Loader2, CheckCircle2
Entities:     Building2, Users, Briefcase, FileText, DollarSign
UI:           XIcon, MoreHorizontal, Settings, User, Bell
```

---

## Responsive Breakpoints

```
sm:  640px
md:  768px
lg:  1024px
xl:  1280px
2xl: 1536px
```

### Container Max Widths
```
sm:  640px
md:  768px
lg:  1024px
xl:  1280px
2xl: 1536px
```

---

## Animation & Transitions

### Standard Transitions
```
transition-colors:  150ms
transition-all:     200ms
duration-200:      200ms
```

### Animations
```
fade-in:           opacity 0 → 1
zoom-in:           scale 0.95 → 1
slide-in-from-top: translateY -2px → 0
slide-in-from-bottom: translateY 2px → 0
blink:              opacity 1 → 0 → 1 (1s cycle)
```

---

## Accessibility

### Focus States
```
- focus-visible:outline-none
- focus-visible:ring-1 focus-visible:ring-ring
- focus-visible:ring-offset-2
- Ring color: --ring (primary blue)
```

### Disabled States
```
- disabled:cursor-not-allowed
- disabled:opacity-50
```

### ARIA Attributes
```
- All interactive elements have proper ARIA labels
- Dialogs have proper roles and descriptions
- Form inputs have associated labels
```

---

## Figma Implementation Guide

### Step 1: Create Design System File
1. Create a new Figma file for the design system
2. Set up pages:
   - Colors (light and dark mode)
   - Typography
   - Spacing & Layout
   - Shadows
   - Components
   - Icons

### Step 2: Create Color Styles
1. Convert OKLCH values to RGB/Hex for Figma
2. Create color styles for all semantic colors
3. Create separate styles for light and dark mode
4. Organize by category (Primary, Secondary, Semantic, etc.)

### Step 3: Create Typography Styles
1. Set up text styles for each size and weight
2. Include letter spacing values
3. Create styles for headings, body, and captions

### Step 4: Create Component Variants
1. Start with base components (Button, Input, Card)
2. Create variants for each component state
3. Use auto-layout for responsive components
4. Create component properties for variants

### Step 5: Build Page Templates
1. Create page layout templates
2. Include navigation, headers, and content areas
3. Use component instances for consistency
4. Create responsive variants

### Step 6: Document Interactions
1. Add prototype connections for navigation
2. Define hover and focus states
3. Create interaction flows for key user journeys

---

## OKLCH to RGB Conversion Guide

Since Figma doesn't natively support OKLCH, you'll need to convert the color values. Use these approximate RGB equivalents:

### Primary Colors (Light Mode)
```
Primary Blue:       #2563EB (approx)
Primary Foreground: #FFFFFF (approx)
Background:         #FFFFFF
Foreground:         #0F172A
Card:               #FFFFFF
Secondary:          #F1F5F9
Accent:             #0EA5E9
Destructive:        #DC2626
Border:             #E2E8F0
```

### Primary Colors (Dark Mode)
```
Background:         #0F172A
Foreground:         #F8FAFC
Card:               #1E293B
Primary:            #3B82F6
Secondary:          #334155
Accent:             #38BDF8
Destructive:        #EF4444
Border:             #334155
```

For accurate conversions, use an online OKLCH to RGB converter or a design tool that supports OKLCH.

---

## Component Priority

Build components in this order:

1. **Foundation**
   - Colors
   - Typography
   - Spacing
   - Shadows

2. **Basic Components**
   - Button
   - Input
   - Badge
   - Label

3. **Layout Components**
   - Card
   - Separator
   - Container

4. **Navigation Components**
   - Sidebar
   - Tabs
   - Breadcrumb

5. **Data Display**
   - Table
   - Avatar
   - Skeleton

6. **Overlay Components**
   - Dialog
   - Dropdown Menu
   - Tooltip

7. **Form Components**
   - Select
   - Checkbox
   - Switch
   - Radio Group

8. **Complex Components**
   - Form
   - Command
   - Calendar

---

## Notes

- The design system uses shadcn/ui as the base component library
- All components are built with accessibility in mind
- The color system uses OKLCH for better color consistency and accessibility
- Dark mode is fully supported with inverted color schemes
- Components are designed to be responsive and mobile-friendly
- All interactive elements have proper focus states for keyboard navigation

---

## Resources

- **shadcn/ui Documentation**: https://ui.shadcn.com
- **Tailwind CSS v4**: https://tailwindcss.com
- **Radix UI**: https://www.radix-ui.com
- **Lucide Icons**: https://lucide.dev
- **OKLCH Color Space**: https://oklch.com
