/**
 * Wireframe UI primitives — deprecated compatibility surface
 *
 * This module is frozen to the legacy export set below. New adapters should not
 * be added here; migrate callers to direct imports from the canonical Fabric or
 * shadcn component modules instead.
 */

// Re-export from new Fabric primitives with legacy names
export { PageHeader } from "./ui/fabric/PageHeader";

// Backward-compatible SectionCard that accepts noPad and subtitle props
import { FabricCard } from "./ui/fabric/FabricCard";

export function SectionCard({
  title,
  subtitle,
  children,
  className,
  noPad,
}: {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
  noPad?: boolean;
}) {
  return (
    <FabricCard
      title={title}
      description={subtitle}
      className={className}
      padding={noPad ? "none" : "normal"}
    >
      {children}
    </FabricCard>
  );
}
export { FilterBar } from "./ui/fabric/FilterBar";

// Backward-compatible DataTable that accepts string columns
import { DataTable as FabricDataTable, type DataTableColumn } from "./ui/fabric/DataTable";

export function DataTable({
  columns,
  rows,
  emptyMessage = "No data found",
  onRowClick,
  selectedRowIndex,
  rowIds,
}: {
  columns: string[];
  rows: React.ReactNode[][];
  emptyMessage?: string;
  onRowClick?: (index: number, rowId?: string) => void;
  selectedRowIndex?: number;
  rowIds?: string[];
}) {
  // Convert string columns to DataTableColumn format
  const fabricColumns: DataTableColumn<React.ReactNode[]>[] = columns.map((col, index) => ({
    key: String(index),
    header: col,
    render: (row) => row[index],
  }));

  // Convert rows to data format
  const data = rows.map((row, index) => row);

  return (
    <FabricDataTable
      data={data}
      columns={fabricColumns}
      keyExtractor={(item: React.ReactNode[]) => {
        const index = data.indexOf(item);
        return rowIds?.[index] ?? String(index);
      }}
      emptyMessage={emptyMessage}
      onRowClick={onRowClick ? (item: React.ReactNode[]) => {
        const index = data.indexOf(item);
        onRowClick(index, rowIds?.[index]);
      } : undefined}
    />
  );
}
export { FabricDialog as Dialog } from "./ui/fabric/FabricDialog";
export { SidePanel } from "./ui/fabric/SidePanel";
// DEPRECATED: Use Skeleton from "@/components/ui/skeleton" (primitive) or
// SkeletonViews from "@/components/ui/SkeletonViews" (page-level)
// export { LoadingSkeleton as Skeleton } from "./ui/fabric/LoadingSkeleton";

// Backward-compatible StatusBadge that accepts status prop
import { StatusBadge as FabricStatusBadge } from "./ui/fabric/StatusBadge";
import { cn } from "@/lib/utils";

export type LegacyStatusType =
  | "created"
  | "queued"
  | "waiting_dependency"
  | "retrying"
  | "succeeded"
  | "failed_terminal"
  | "interrupted"
  | "completed"
  | "processing"
  | "failed"
  | "running"
  | "paused"
  | "pending"
  | "cancelled"
  | "success"
  | "error"
  | "warning"
  | "info";

const legacyStatusMap: Record<string, { variant: "success" | "warning" | "destructive" | "secondary" | "default" | "outline" | "info" | "pending"; label: string }> = {
  completed: { variant: "success", label: "Completed" },
  created: { variant: "secondary", label: "Created" },
  queued: { variant: "pending", label: "Queued" },
  waiting_dependency: { variant: "pending", label: "Waiting" },
  retrying: { variant: "warning", label: "Retrying" },
  succeeded: { variant: "success", label: "Succeeded" },
  success: { variant: "success", label: "Success" },
  running: { variant: "warning", label: "Running" },
  processing: { variant: "warning", label: "Processing" },
  failed: { variant: "destructive", label: "Failed" },
  failed_terminal: { variant: "destructive", label: "Failed" },
  error: { variant: "destructive", label: "Error" },
  paused: { variant: "secondary", label: "Paused" },
  interrupted: { variant: "secondary", label: "Interrupted" },
  pending: { variant: "pending", label: "Pending" },
  cancelled: { variant: "secondary", label: "Cancelled" },
  warning: { variant: "warning", label: "Warning" },
  info: { variant: "info", label: "Info" },
};

export function StatusBadge({ status, className }: { status: LegacyStatusType; className?: string }) {
  const mapped = legacyStatusMap[status] || { variant: "default", label: status };
  return (
    <FabricStatusBadge variant={mapped.variant} className={cn("text-[10px]", className)}>
      {mapped.label}
    </FabricStatusBadge>
  );
}

// Backward-compatible MetricCard that accepts string trend prop
import { MetricCard as FabricMetricCard } from "./ui/fabric/MetricCard";

export function MetricCard({
  label,
  value,
  trend,
  trendUp,
}: {
  label: string;
  value: string;
  trend?: string;
  trendUp?: boolean;
}) {
  // Convert legacy trend props to new format
  const trendProp = trend
    ? {
        value: trend,
        positive: trendUp === undefined ? null : trendUp,
      }
    : undefined;

  return <FabricMetricCard label={label} value={value} trend={trendProp} />;
}

// Keep legacy components that don't have Fabric equivalents yet
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";

/* ── Legacy Btn component (wraps shadcn Button) ── */
export function Btn({
  children,
  variant = "ghost",
  onClick,
  className,
  disabled,
}: {
  children: React.ReactNode;
  variant?: "primary" | "ghost" | "outline" | "danger";
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
}) {
  const variantMap = {
    primary: "default" as const,
    ghost: "ghost" as const,
    outline: "outline" as const,
    danger: "destructive" as const,
  };
  
  return (
    <Button
      onClick={onClick}
      disabled={disabled}
      variant={variantMap[variant]}
      size="sm"
      className={cn("text-[12px] font-semibold", className)}
    >
      {children}
    </Button>
  );
}

/* ── Legacy SearchInput component (wraps shadcn Input) ── */
export function SearchInput({
  placeholder,
  value,
  onChange,
}: {
  placeholder?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
}) {
  return (
    <div className="relative flex items-center">
      <Search className="absolute left-3 h-4 w-4 text-muted-foreground" />
      <Input
        type="text"
        value={value || ''}
        onChange={onChange}
        placeholder={placeholder ?? "Search…"}
        className="pl-9 h-8 text-[12px]"
      />
    </div>
  );
}

/* ── Legacy Tabs component ── */
export function Tabs({
  tabs,
  active,
  onChange,
}: {
  tabs: string[];
  active: string;
  onChange: (t: string) => void;
}) {
  return (
    <div className="flex border-b border-border mb-4" role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab}
          onClick={() => onChange(tab)}
          role="tab"
          aria-selected={active === tab}
          className={cn(
            "px-4 py-2 text-[12px] font-semibold border-b-2 -mb-px transition-colors",
            active === tab
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
        >
          {tab}
        </button>
      ))}
    </div>
  );
}

/* ── Legacy Toolbar component ── */
export function Toolbar({ children }: { children: React.ReactNode }) {
  return <div className="flex items-center gap-2 flex-wrap mb-4">{children}</div>;
}

/* ── Legacy GraphLegend component ── */
export function GraphLegend() {
  return (
    <div className="flex gap-4 flex-wrap">
      {[
        { color: "bg-violet-400", label: "Capability" },
        { color: "bg-cyan-400", label: "Use Case" },
        { color: "bg-amber-400", label: "Persona" },
        { color: "bg-emerald-400", label: "Value Driver" },
      ].map(({ color, label }) => (
        <div key={label} className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <div className={cn("w-2.5 h-2.5 rounded-full", color)} />
          {label}
        </div>
      ))}
    </div>
  );
}

/* ── Legacy Callout component ── */
export function Callout({ children }: { children: React.ReactNode }) {
  return (
    <div className="border-l-2 border-border pl-3 py-1 bg-muted/50 text-[11px] text-muted-foreground rounded-r mt-3">
      {children}
    </div>
  );
}

// Backward-compatible EntityBadge that accepts label prop
import { EntityBadge as FabricEntityBadge } from "@/lib/entity-colors";

export function EntityBadge({ type, label }: { type: string; label?: string }) {
  return <FabricEntityBadge type={type}>{label}</FabricEntityBadge>;
}

export { StatusBadgeEntity as StatusBadgeLegacy, type StatusType } from "@/lib/entity-colors";
export type { EntityColorScheme } from "@/lib/entity-colors";

// Keep legacy EntityType for backward compatibility
export type EntityType = "capability" | "usecase" | "persona" | "valuedriver";
