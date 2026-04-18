# Fabric Theme Implementation — Autonomous Production Prompt
## Value Fabric Platform UI Consistency Deployment

**Objective:** Deploy the Fabric theme as the canonical UI baseline across the entire Value Fabric Platform frontend. Transform ad-hoc styling into a token-driven, component-based design system. Do not stop until all pages pass the consistency audit.

**Source Spec:** `/mnt/okcomputer/output/fabric_ui_consistency_spec.md`
**Target Project:** `frontend/client/src/`
**Stack:** Vite + React + TypeScript + Tailwind CSS + shadcn/ui

═══════════════════════════════════════════════════════════════════
STOP CONDITIONS
═══════════════════════════════════════════════════════════════════

**STOP WITH SUCCESS:**
- Fabric CSS tokens active in the global stylesheet
- All 10 shared primitives created and functional
- Every audited page refactored to use primitives (no ad-hoc styling)
- Zero drift patterns remaining
- All TypeScript compiles, zero lint errors
- Visual smoke test passes in browser
- Dark mode renders correctly on all pages

**STOP WITH BLOCKER:**
- shadcn/ui cannot be installed (version conflict)
- Tailwind v4 not compatible with project config
- Cannot access frontend source directory

═══════════════════════════════════════════════════════════════════
PREREQUISITE CHECK (Execute First)
═══════════════════════════════════════════════════════════════════

Verify before starting:

[ ] 1. Project location confirmed: `frontend/client/src/` exists
[ ] 2. Tailwind CSS installed: `tailwind.config.ts` or `tailwind.config.js` exists
[ ] 3. shadcn/ui initialized: `components.json` exists in `frontend/client/`
[ ] 4. CSS entry point located: `src/index.css` or `src/globals.css` or `src/App.css`
[ ] 5. Component directory: `src/components/` or `src/components/ui/` exists
[ ] 6. Package manager: `package-lock.json` (npm), `pnpm-lock.yaml` (pnpm), or `yarn.lock`

If any check fails → STOP WITH BLOCKER (document missing item)

═══════════════════════════════════════════════════════════════════
EXECUTION PHASES (Strict Order)
═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: THEME TOKEN DEPLOYMENT                                 │
└─────────────────────────────────────────────────────────────────┘

**Goal:** Fabric oklch tokens are the active color system.

[ ] 1.1 BACK UP EXISTING CSS
      Copy current global CSS to `src/styles/backup-original.css`

[ ] 1.2 DEPLOY FABRIC TOKENS
      Open the global CSS file (index.css / globals.css / App.css)
      Replace the entire :root section with the Fabric light-mode tokens:

```css
@import "tailwindcss";

@custom-variant dark (&:is(.dark *));

:root {
  --background: oklch(0.9581 0 0);
  --foreground: oklch(0.3134 0.0234 253.6270);
  --card: oklch(0.9774 0.0042 236.4961);
  --card-foreground: oklch(0.2022 0.0110 151.1628);
  --popover: oklch(1.0000 0 0);
  --popover-foreground: oklch(0.2505 0.0149 235.6259);
  --primary: oklch(0.6112 0.1217 248.9572);
  --primary-foreground: oklch(1.0000 0 0);
  --secondary: oklch(0.9122 0.0111 243.6627);
  --secondary-foreground: oklch(0.4186 0.0133 235.1330);
  --muted: oklch(0.9209 0.0128 244.2626);
  --muted-foreground: oklch(0.6027 0.0062 211.0375);
  --accent: oklch(0.9122 0.0111 243.6627);
  --accent-foreground: oklch(0.2505 0.0149 235.6259);
  --destructive: oklch(0.1931 0.0037 164.6298);
  --destructive-foreground: oklch(1.0000 0 0);
  --border: oklch(0.8840 0.0067 208.7806);
  --input: oklch(0.7450 0.0121 252.1201);
  --ring: oklch(0.6112 0.1217 248.9572);
  --chart-1: oklch(0.5098 0.1320 257.5458);
  --chart-2: oklch(0.7360 0.1191 266.5038);
  --chart-3: oklch(0.8467 0.0177 248.0373);
  --chart-4: oklch(0.8977 0.0274 260.3158);
  --chart-5: oklch(0.4893 0.1504 261.9302);
  --radius: 0.5rem;
  --font-sans: Inter, system-ui, -apple-system, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, monospace;
  --font-serif: Georgia, serif;
  --tracking-normal: -0.01em;
}

.dark {
  --background: oklch(0.1776 0 0);
  --foreground: oklch(0.7905 0.0126 259.8241);
  --card: oklch(0.2638 0.0024 247.9155);
  --card-foreground: oklch(0.9755 0.0045 258.3245);
  --popover: oklch(0.3046 0.0023 247.9001);
  --popover-foreground: oklch(0.9176 0.0026 228.7865);
  --primary: oklch(0.6576 0.1208 252.0832);
  --primary-foreground: oklch(1.0000 0 0);
  --secondary: oklch(0.9774 0.0042 236.4961);
  --secondary-foreground: oklch(0.3046 0.0023 247.9001);
  --muted: oklch(0.2171 0.0025 247.9411);
  --muted-foreground: oklch(0.7559 0.0125 239.9659);
  --accent: oklch(0.2038 0.0067 258.3676);
  --accent-foreground: oklch(0.9590 0.0059 239.8204);
  --destructive: oklch(0.6368 0.2078 25.3313);
  --destructive-foreground: oklch(1.0000 0 0);
  --border: oklch(0.3506 0.0066 248.0169);
  --input: oklch(0.4217 0.0084 248.0280);
  --ring: oklch(0.6576 0.1208 252.0832);
  --chart-1: oklch(0.5098 0.1320 257.5458);
  --chart-2: oklch(0.7360 0.1191 266.5038);
  --chart-3: oklch(0.2038 0.0067 258.3676);
  --chart-4: oklch(0.3361 0.0333 253.9085);
  --chart-5: oklch(0.4893 0.1504 261.9302);
}
```

[ ] 1.3 ADD @theme INLINE MAPPING (Tailwind v4)
      Append after the .dark block:

```css
@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-destructive-foreground: var(--destructive-foreground);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);
  --color-chart-1: var(--chart-1);
  --color-chart-2: var(--chart-2);
  --color-chart-3: var(--chart-3);
  --color-chart-4: var(--chart-4);
  --color-chart-5: var(--chart-5);
  --font-sans: var(--font-sans);
  --font-mono: var(--font-mono);
  --font-serif: var(--font-serif);
  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);
}

@layer base {
  * { @apply border-border; }
  body {
    @apply bg-background text-foreground;
    font-family: var(--font-sans);
    letter-spacing: var(--tracking-normal);
  }
}
```

[ ] 1.4 VERIFY FONT AVAILABILITY
      Ensure Inter font is loaded. If using Google Fonts in index.html:
      ```html
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
      ```
      Or if using @fontsource: `npm install @fontsource/inter`

[ ] 1.5 BUILD CHECK
      Run `npm run build` (or pnpm/yarn equivalent)
      Must compile without errors. If errors → fix before proceeding.

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: SHARED PRIMITIVES CREATION                             │
└─────────────────────────────────────────────────────────────────┘

**Goal:** All 10 Fabric primitives exist in `src/components/ui/fabric/`

Create directory: `src/components/ui/fabric/`

[ ] 2.1 PageHeader

```tsx
// src/components/ui/fabric/PageHeader.tsx
import { ChevronRight, Home } from "lucide-react";
import { cn } from "@/lib/utils";

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  breadcrumbs?: BreadcrumbItem[];
  className?: string;
}

export function PageHeader({ title, subtitle, actions, breadcrumbs, className }: PageHeaderProps) {
  return (
    <div className={cn("pb-6 mb-6 border-b border-border", className)}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="flex items-center gap-1.5 text-[12px] text-muted-foreground mb-3">
          <Home className="h-3.5 w-3.5" />
          {breadcrumbs.map((crumb, i) => (
            <span key={i} className="flex items-center gap-1.5">
              <ChevronRight className="h-3 w-3" />
              {crumb.href ? (
                <a href={crumb.href} className="hover:text-foreground transition-colors">
                  {crumb.label}
                </a>
              ) : (
                <span className="text-foreground">{crumb.label}</span>
              )}
            </span>
          ))}
        </nav>
      )}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h1 className="text-[24px] font-semibold tracking-[-0.01em] text-foreground leading-[1.2]">
            {title}
          </h1>
          {subtitle && (
            <p className="text-[13px] text-muted-foreground mt-1 leading-relaxed">
              {subtitle}
            </p>
          )}
        </div>
        {actions && (
          <div className="flex items-center gap-3 flex-shrink-0">{actions}</div>
        )}
      </div>
    </div>
  );
}
```

[ ] 2.2 FabricCard (wraps shadcn Card with Fabric padding/shadow defaults)

```tsx
// src/components/ui/fabric/FabricCard.tsx
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface FabricCardProps {
  children: React.ReactNode;
  className?: string;
  padding?: "none" | "compact" | "normal" | "loose";
  shadow?: "none" | "sm" | "md" | "lg";
  title?: string;
  description?: string;
  headerActions?: React.ReactNode;
}

const paddingMap = {
  none: "",
  compact: "p-4",
  normal: "p-6",
  loose: "p-8",
};

const shadowMap = {
  none: "",
  sm: "shadow-sm",
  md: "shadow-md",
  lg: "shadow-lg",
};

export function FabricCard({
  children,
  className,
  padding = "normal",
  shadow = "sm",
  title,
  description,
  headerActions,
}: FabricCardProps) {
  return (
    <Card className={cn("border-border", shadowMap[shadow], className)}>
      {(title || description || headerActions) && (
        <CardHeader className={cn("flex flex-row items-start justify-between", padding !== "none" && paddingMap[padding])}>
          <div className="flex-1 min-w-0">
            {title && <CardTitle className="text-[16px] font-semibold">{title}</CardTitle>}
            {description && (
              <CardDescription className="text-[13px] mt-1">{description}</CardDescription>
            )}
          </div>
          {headerActions && <div className="flex items-center gap-2 flex-shrink-0">{headerActions}</div>}
        </CardHeader>
      )}
      <CardContent className={cn(padding !== "none" && !title && !description && paddingMap[padding])}>
        {children}
      </CardContent>
    </Card>
  );
}
```

[ ] 2.3 FilterBar

```tsx
// src/components/ui/fabric/FilterBar.tsx
import { Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";

interface FilterBarProps {
  searchPlaceholder?: string;
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  filters?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
  activeFilterCount?: number;
}

export function FilterBar({
  searchPlaceholder = "Search...",
  searchValue,
  onSearchChange,
  filters,
  actions,
  className,
  activeFilterCount,
}: FilterBarProps) {
  return (
    <div className={cn("flex flex-wrap items-center gap-3 p-4 border-b border-border bg-card", className)}>
      {(searchValue !== undefined || onSearchChange) && (
        <div className="relative flex-1 max-w-sm min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={searchPlaceholder}
            value={searchValue}
            onChange={(e) => onSearchChange?.(e.target.value)}
            className="h-8 pl-9 text-sm"
          />
        </div>
      )}
      {filters && <div className="flex items-center gap-2">{filters}</div>}
      {activeFilterCount !== undefined && activeFilterCount > 0 && (
        <span className="text-[11px] px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground font-medium">
          {activeFilterCount} active
        </span>
      )}
      {actions && <div className="flex items-center gap-2 ml-auto">{actions}</div>}
    </div>
  );
}
```

[ ] 2.4 StatusBadge

```tsx
// src/components/ui/fabric/StatusBadge.tsx
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type StatusVariant = "default" | "secondary" | "outline" | "destructive" | "success" | "warning" | "info";

interface StatusBadgeProps {
  children: React.ReactNode;
  variant?: StatusVariant;
  className?: string;
}

const variantStyles: Record<StatusVariant, string> = {
  default: "",
  secondary: "",
  outline: "",
  destructive: "",
  success: "bg-emerald-100 text-emerald-800 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-300",
  warning: "bg-amber-100 text-amber-800 hover:bg-amber-100 dark:bg-amber-900/30 dark:text-amber-300",
  info: "bg-sky-100 text-sky-800 hover:bg-sky-100 dark:bg-sky-900/30 dark:text-sky-300",
};

export function StatusBadge({ children, variant = "default", className }: StatusBadgeProps) {
  return (
    <Badge
      variant={variant === "success" || variant === "warning" || variant === "info" ? "secondary" : variant}
      className={cn(
        "text-[11px] px-2 py-0.5 rounded-full font-medium",
        variantStyles[variant],
        className
      )}
    >
      {children}
    </Badge>
  );
}
```

[ ] 2.5 MetricCard

```tsx
// src/components/ui/fabric/MetricCard.tsx
import { FabricCard } from "./FabricCard";
import { cn } from "@/lib/utils";
import { TrendingDown, TrendingUp } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: string;
  trend?: {
    value: string;
    positive: boolean;
  };
  className?: string;
}

export function MetricCard({ label, value, trend, className }: MetricCardProps) {
  return (
    <FabricCard padding="normal" shadow="sm" className={cn("h-full", className)}>
      <p className="text-[12px] font-medium text-muted-foreground uppercase tracking-wider">
        {label}
      </p>
      <p className="text-[28px] font-bold tracking-[-0.02em] text-foreground mt-1 leading-[1.1]">
        {value}
      </p>
      {trend && (
        <div className={cn("flex items-center gap-1 mt-2 text-[12px] font-medium", trend.positive ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400")}>
          {trend.positive ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
          {trend.value}
        </div>
      )}
    </FabricCard>
  );
}
```

[ ] 2.6 DataTable (wraps shadcn Table with Fabric defaults)

```tsx
// src/components/ui/fabric/DataTable.tsx
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

interface DataTableProps<T> {
  data: T[];
  columns: {
    key: keyof T | string;
    header: string;
    render?: (item: T) => React.ReactNode;
    className?: string;
  }[];
  keyExtractor: (item: T) => string;
  emptyMessage?: string;
  className?: string;
  onRowClick?: (item: T) => void;
  selectedKey?: string;
}

export function DataTable<T>({
  data,
  columns,
  keyExtractor,
  emptyMessage = "No data available",
  className,
  onRowClick,
  selectedKey,
}: DataTableProps<T>) {
  return (
    <div className={cn("rounded-lg border border-border overflow-hidden", className)}>
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50 hover:bg-muted/50">
            {columns.map((col) => (
              <TableHead
                key={String(col.key)}
                className={cn("h-10 px-4 text-[12px] font-medium text-muted-foreground uppercase tracking-wider", col.className)}
              >
                {col.header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.length === 0 ? (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-32 text-center text-muted-foreground text-sm">
                {emptyMessage}
              </TableCell>
            </TableRow>
          ) : (
            data.map((item) => (
              <TableRow
                key={keyExtractor(item)}
                onClick={() => onRowClick?.(item)}
                className={cn(
                  "h-12 border-t border-border hover:bg-muted/30 transition-colors",
                  onRowClick && "cursor-pointer",
                  selectedKey === keyExtractor(item) && "bg-primary/5"
                )}
              >
                {columns.map((col) => (
                  <TableCell key={String(col.key)} className={cn("px-4 text-[13px] text-foreground", col.className)}>
                    {col.render ? col.render(item) : String((item as Record<string, unknown>)[col.key as string] ?? "")}
                  </TableCell>
                ))}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
```

[ ] 2.7 SidePanel (wraps shadcn Sheet with Fabric defaults)

```tsx
// src/components/ui/fabric/SidePanel.tsx
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

interface SidePanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
  width?: "sm" | "md" | "lg" | "xl";
}

const widthMap = {
  sm: "sm:max-w-[350px]",
  md: "sm:max-w-[400px]",
  lg: "sm:max-w-[500px]",
  xl: "sm:max-w-[600px]",
};

export function SidePanel({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
  className,
  width = "md",
}: SidePanelProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className={cn("w-full sm:max-w-[400px] flex flex-col p-0", widthMap[width], className)}>
        <SheetHeader className="px-6 py-4 border-b border-border">
          <SheetTitle className="text-[16px] font-semibold">{title}</SheetTitle>
          {description && <SheetDescription className="text-[13px]">{description}</SheetDescription>}
        </SheetHeader>
        <div className="flex-1 overflow-y-auto px-6 py-6">{children}</div>
        {footer && (
          <div className="px-6 py-4 border-t border-border flex items-center justify-end gap-3">
            {footer}
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
```

[ ] 2.8 Dialog (use existing shadcn Dialog — verify it matches Fabric)
      If the existing Dialog differs from spec, wrap it:

```tsx
// src/components/ui/fabric/FabricDialog.tsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

interface FabricDialogProps {
  trigger?: React.ReactNode;
  title: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  className?: string;
}

export function FabricDialog({
  trigger,
  title,
  description,
  children,
  footer,
  open,
  onOpenChange,
  className,
}: FabricDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {trigger && <DialogTrigger asChild>{trigger}</DialogTrigger>}
      <DialogContent className={cn("sm:max-w-lg", className)}>
        <DialogHeader>
          <DialogTitle className="text-[18px] font-semibold">{title}</DialogTitle>
          {description && <DialogDescription className="text-[13px]">{description}</DialogDescription>}
        </DialogHeader>
        <div className="py-2">{children}</div>
        {footer && <div className="flex justify-end gap-3 pt-4">{footer}</div>}
      </DialogContent>
    </Dialog>
  );
}
```

[ ] 2.9 TeamMemberList

```tsx
// src/components/ui/fabric/TeamMemberList.tsx
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { StatusBadge } from "./StatusBadge";
import { cn } from "@/lib/utils";

interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: string;
  avatar?: string;
}

interface TeamMemberListProps {
  members: TeamMember[];
  className?: string;
  onMemberClick?: (member: TeamMember) => void;
  actions?: (member: TeamMember) => React.ReactNode;
}

export function TeamMemberList({ members, className, onMemberClick, actions }: TeamMemberListProps) {
  return (
    <div className={cn("divide-y divide-border", className)}>
      {members.map((member) => (
        <div
          key={member.id}
          onClick={() => onMemberClick?.(member)}
          className={cn(
            "flex items-center gap-4 py-3 px-4",
            onMemberClick && "cursor-pointer hover:bg-muted/30 transition-colors"
          )}
        >
          <Avatar className="h-8 w-8 bg-muted">
            {member.avatar ? (
              <img src={member.avatar} alt={member.name} />
            ) : (
              <AvatarFallback className="text-[12px] font-medium bg-muted text-muted-foreground">
                {member.name.split(" ").map(n => n[0]).join("").toUpperCase()}
              </AvatarFallback>
            )}
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="text-[14px] font-medium text-foreground truncate">{member.name}</p>
            <p className="text-[12px] text-muted-foreground truncate">{member.email}</p>
          </div>
          <StatusBadge variant="secondary">{member.role}</StatusBadge>
          {actions && <div className="flex-shrink-0">{actions(member)}</div>}
        </div>
      ))}
    </div>
  );
}
```

[ ] 2.10 LoadingSkeleton

```tsx
// src/components/ui/fabric/LoadingSkeleton.tsx
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface LoadingSkeletonProps {
  variant?: "card" | "table" | "metric" | "form" | "page";
  count?: number;
  className?: string;
}

export function LoadingSkeleton({ variant = "card", count = 1, className }: LoadingSkeletonProps) {
  if (variant === "metric") {
    return (
      <div className={cn("p-6 rounded-lg border border-border bg-card shadow-sm", className)}>
        <Skeleton className="h-3 w-24 mb-3" />
        <Skeleton className="h-8 w-32 mb-2" />
        <Skeleton className="h-3 w-20" />
      </div>
    );
  }

  if (variant === "table") {
    return (
      <div className={cn("rounded-lg border border-border overflow-hidden", className)}>
        <div className="h-10 bg-muted/50 px-4 flex items-center gap-4">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-3 w-32" />
          <Skeleton className="h-3 w-20" />
        </div>
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="h-12 border-t border-border px-4 flex items-center gap-4">
            <Skeleton className="h-3 w-28" />
            <Skeleton className="h-3 w-40" />
            <Skeleton className="h-3 w-16" />
          </div>
        ))}
      </div>
    );
  }

  if (variant === "form") {
    return (
      <div className={cn("space-y-4 p-6", className)}>
        <div className="space-y-2">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-9 w-full" />
        </div>
        <div className="space-y-2">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-9 w-full" />
        </div>
        <div className="space-y-2">
          <Skeleton className="h-3 w-14" />
          <Skeleton className="h-20 w-full" />
        </div>
      </div>
    );
  }

  // Default card
  return (
    <div className={cn("p-6 rounded-lg border border-border bg-card shadow-sm space-y-3", className)}>
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  );
}

// Create barrel export
// src/components/ui/fabric/index.ts
```

[ ] 2.11 Create barrel export file `src/components/ui/fabric/index.ts`:

```tsx
export { PageHeader } from "./PageHeader";
export { FabricCard } from "./FabricCard";
export { FilterBar } from "./FilterBar";
export { StatusBadge } from "./StatusBadge";
export { MetricCard } from "./MetricCard";
export { DataTable } from "./DataTable";
export { SidePanel } from "./SidePanel";
export { FabricDialog } from "./FabricDialog";
export { TeamMemberList } from "./TeamMemberList";
export { LoadingSkeleton } from "./LoadingSkeleton";
```

[ ] 2.12 BUILD CHECK — must compile without errors

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: PAGE AUDIT & DRIFT INVENTORY                           │
└─────────────────────────────────────────────────────────────────┘

**Goal:** Identify every instance of ad-hoc styling across all pages.

[ ] 3.1 Scan all page files for drift patterns:

Search these patterns across `src/pages/` and `src/components/`:

```bash
# Magic color values (NOT using tokens)
grep -rn "bg-\[#\|bg-gray-\|bg-slate-\|bg-zinc-\|bg-neutral-\|bg-blue-\|bg-green-\|bg-red-\|bg-amber-\|bg-yellow-" src/pages/ src/components/ | grep -v "bg-muted\|bg-accent\|bg-primary\|bg-secondary\|bg-destructive\|bg-background\|bg-card\|bg-popover"

# Magic spacing
grep -rn "p-\[\|m-\[\|w-\[\|h-\[\|gap-\[" src/pages/ src/components/

# Custom shadows
grep -rn "shadow-\[" src/pages/ src/components/

# Custom border radius
grep -rn "rounded-\[" src/pages/ src/components/

# Direct text colors not using tokens
grep -rn "text-gray-\|text-slate-\|text-blue-\|text-green-\|text-red-" src/pages/ src/components/ | grep -v "text-muted-foreground\|text-primary\|text-secondary\|text-accent\|text-destructive\|text-foreground\|text-card-foreground"

# Inline styles
grep -rn "style={{" src/pages/ src/components/

# Font sizes outside scale
grep -rn "text-\[\|font-size" src/pages/ src/components/
```

[ ] 3.2 For each page file found, create a drift report entry:

| File | Pattern Found | Current Value | Should Be | Fix Required |
|------|---------------|---------------|-----------|-------------|
| Pages/AgentPage.tsx:45 | bg-gray-100 | bg-gray-100 | bg-muted | Y |
| Pages/Dashboard.tsx:23 | shadow-md ad-hoc | custom | shadow-sm | Y |

[ ] 3.3 Prioritize pages by traffic/importance:
1. Dashboard / Home
2. Agent workflows
3. Library / Packs
4. Settings / Admin
5. Auth pages

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: PAGE REFACTORING                                       │
└─────────────────────────────────────────────────────────────────┘

**Goal:** Every page uses Fabric primitives. No ad-hoc styling remains.

For EACH page in priority order:

[ ] 4.1 Replace page header:
```tsx
// BEFORE (ad-hoc)
<div className="mb-6">
  <h1 className="text-2xl font-bold">Dashboard</h1>
  <p className="text-gray-500 mt-1">Overview of your value fabric</p>
</div>

// AFTER (Fabric primitive)
<PageHeader
  title="Dashboard"
  subtitle="Overview of your value fabric"
/>
```

[ ] 4.2 Replace card containers:
```tsx
// BEFORE
<div className="bg-white rounded-xl shadow-sm border p-6">

// AFTER
<FabricCard>
  {/* content */}
</FabricCard>
```

[ ] 4.3 Replace metric displays:
```tsx
// BEFORE
<div className="bg-white p-6 rounded-lg">
  <p className="text-sm text-gray-500">Total Revenue</p>
  <p className="text-3xl font-bold">$15,231</p>
</div>

// AFTER
<MetricCard
  label="Total Revenue"
  value="$15,231"
  trend={{ value: "+20.1% from last month", positive: true }}
/>
```

[ ] 4.4 Replace tables:
```tsx
// BEFORE (ad-hoc table or inconsistent shadcn Table)
<Table>
  <TableHeader className="bg-gray-50">
    ...
  </TableHeader>

// AFTER
<DataTable
  data={items}
  columns={[...]}
  keyExtractor={(item) => item.id}
/>
```

[ ] 4.5 Replace status badges:
```tsx
// BEFORE
<span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">
  Active
</span>

// AFTER
<StatusBadge variant="success">Active</StatusBadge>
```

[ ] 4.6 Replace filter bars:
```tsx
// BEFORE
<div className="flex gap-2 mb-4 p-4 bg-gray-50">
  <input className="border rounded px-3 py-2" placeholder="Search" />

// AFTER
<FilterBar
  searchPlaceholder="Search items..."
  searchValue={search}
  onSearchChange={setSearch}
  filters={...}
  actions={...}
/>
```

[ ] 4.7 Replace dialogs and side panels:
```tsx
// BEFORE (inline Dialog or custom overlay)
{showPanel && (
  <div className="fixed right-0 top-0 w-96 h-full bg-white shadow-xl z-50">

// AFTER
<SidePanel
  open={showPanel}
  onOpenChange={setShowPanel}
  title="Item Details"
>
  {/* content */}
</SidePanel>
```

[ ] 4.8 Replace loading states:
```tsx
// BEFORE
<div className="flex justify-center p-8">
  <Spinner className="h-8 w-8 animate-spin" />
</div>

// AFTER
<LoadingSkeleton variant="table" count={5} />
```

[ ] 4.9 Remove all inline styles and magic values found in Phase 3

[ ] 4.10 After each page: BUILD CHECK — must compile

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 5: VALIDATION & SIGNOFF                                   │
└─────────────────────────────────────────────────────────────────┘

[ ] 5.1 TypeScript compilation: `npx tsc --noEmit` → 0 errors
[ ] 5.2 Lint: `npm run lint` → 0 errors
[ ] 5.3 Build: `npm run build` → successful
[ ] 5.4 Dev server: `npm run dev` → loads without console errors
[ ] 5.5 Visual smoke test:
      - Open each major page in browser
      - Verify colors match Fabric theme (warm gray background, blue primary)
      - Verify cards have consistent padding and shadows
      - Verify typography uses Inter font
      - Verify no broken layouts
[ ] 5.6 Dark mode test:
      - Toggle dark mode (or add class="dark" to html)
      - Verify all pages render correctly in dark mode
      - Verify no hardcoded light colors showing
[ ] 5.7 Re-run drift scan (Phase 3 commands) → should find zero issues

═══════════════════════════════════════════════════════════════════
DELIVERABLES
═══════════════════════════════════════════════════════════════════

Save to `frontend/FABRIC_THEME_DEPLOYMENT_REPORT.md`:

```markdown
# Fabric Theme Deployment Report
## Value Fabric Platform

### Deployment Status: [COMPLETE / PARTIAL / BLOCKED]

### Phase 1: Theme Tokens
- [x] CSS tokens deployed to [file path]
- [x] Light mode: [N] tokens active
- [x] Dark mode: [N] tokens active
- [x] Font: Inter loaded via [method]

### Phase 2: Shared Primitives
| Component | File | Status |
|-----------|------|--------|
| PageHeader | src/components/ui/fabric/PageHeader.tsx | Created/Updated |
| FabricCard | src/components/ui/fabric/FabricCard.tsx | Created/Updated |
| FilterBar | src/components/ui/fabric/FilterBar.tsx | Created/Updated |
| StatusBadge | src/components/ui/fabric/StatusBadge.tsx | Created/Updated |
| MetricCard | src/components/ui/fabric/MetricCard.tsx | Created/Updated |
| DataTable | src/components/ui/fabric/DataTable.tsx | Created/Updated |
| SidePanel | src/components/ui/fabric/SidePanel.tsx | Created/Updated |
| FabricDialog | src/components/ui/fabric/FabricDialog.tsx | Created/Updated |
| TeamMemberList | src/components/ui/fabric/TeamMemberList.tsx | Created/Updated |
| LoadingSkeleton | src/components/ui/fabric/LoadingSkeleton.tsx | Created/Updated |

### Phase 3: Drift Inventory
Total drift patterns found: [N]
[Table of all found issues]

### Phase 4: Page Refactoring
| Page | Status | Primitives Used | Remaining Drift |
|------|--------|-----------------|-----------------|
| Home/Dashboard | ✅ Refactored | PageHeader, MetricCard, FabricCard | 0 |
| Agent Workflow | ✅ Refactored | PageHeader, FabricCard, DataTable | 0 |
| ... | ... | ... | ... |

### Phase 5: Validation
- [x] TypeScript: 0 errors
- [x] ESLint: 0 errors
- [x] Build: successful
- [x] Dev server: clean
- [x] Visual smoke test: passed
- [x] Dark mode: all pages verified
- [x] Drift re-scan: 0 issues

### Remaining Work
[If any]
```

═══════════════════════════════════════════════════════════════════
WORKING LOG FORMAT
═══════════════════════════════════════════════════════════════════

```
═══════════════════════════════════════════════════════════════════
PHASE [N]: [Name] — [Step]
═══════════════════════════════════════════════════════════════════

FILES: [created/modified]
GATE: TypeScript | Lint | Build | Visual
RESULT: PASS / FAIL

[If FAIL]
ERROR: [description]
FIX: [what was changed]
RETRY: [new result]

NEXT: [next step]
```

═══════════════════════════════════════════════════════════════════
FINAL CHECKLIST
═══════════════════════════════════════════════════════════════════

Before declaring deployment complete:

THEME:
[ ] Fabric oklch tokens in global CSS
[ ] @theme inline mapping present
[ ] Dark mode tokens present
[ ] Inter font loaded

PRIMITIVES:
[ ] All 10 components created in src/components/ui/fabric/
[ ] Barrel export file exists
[ ] All components compile

PAGES:
[ ] All major pages refactored
[ ] No ad-hoc colors remaining
[ ] No ad-hoc spacing remaining
[ ] No inline styles remaining
[ ] All pages use PageHeader for titles
[ ] All cards use FabricCard
[ ] All tables use DataTable or consistent shadcn Table
[ ] All badges use StatusBadge

VALIDATION:
[ ] TypeScript compiles
[ ] ESLint passes
[ ] Build succeeds
[ ] Dev server runs clean
[ ] Visual inspection passes
[ ] Dark mode verified
[ ] Zero drift in re-scan

DOCUMENTATION:
[ ] Deployment report created
[ ] Component usage documented

═══════════════════════════════════════════════════════════════════
BEGIN EXECUTION
═══════════════════════════════════════════════════════════════════

Start with Phase 1: Theme Token Deployment.

Copy the Fabric CSS tokens into the global stylesheet, verify the build compiles, then proceed to primitives creation.

Report first phase completion before continuing.
