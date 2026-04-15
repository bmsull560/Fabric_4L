/**
 * Wireframe UI primitives — shared across all 10 screens
 * Design: Refined Enterprise SaaS — greyscale + 4 entity tints
 */
import { cn } from "@/lib/utils";
import { ChevronRight } from "lucide-react";

/* ── Entity type badge ── */
export type EntityType = "capability" | "usecase" | "persona" | "valuedriver";

const ENTITY_STYLES: Record<EntityType, string> = {
  capability:  "bg-violet-100 text-violet-800 border-violet-200",
  usecase:     "bg-cyan-100   text-cyan-800   border-cyan-200",
  persona:     "bg-amber-100  text-amber-800  border-amber-200",
  valuedriver: "bg-emerald-100 text-emerald-800 border-emerald-200",
};
const ENTITY_LABELS: Record<EntityType, string> = {
  capability: "Capability", usecase: "Use Case", persona: "Persona", valuedriver: "Value Driver",
};

export function EntityBadge({ type, label }: { type: EntityType; label?: string }) {
  return (
    <span className={cn(
      "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border",
      ENTITY_STYLES[type]
    )}>
      {label ?? ENTITY_LABELS[type]}
    </span>
  );
}

/* ── Status badge ── */
export type StatusType = "completed" | "processing" | "failed" | "running" | "paused" | "pending" | "cancelled";
const STATUS_STYLES: Record<StatusType, string> = {
  completed:  "bg-emerald-100 text-emerald-800 border-emerald-200",
  running:    "bg-amber-100   text-amber-800   border-amber-200",
  processing: "bg-amber-100   text-amber-800   border-amber-200",
  failed:     "bg-destructive/10 text-destructive border-destructive/20",
  paused:     "bg-muted text-muted-foreground border-border",
  pending:    "bg-primary/10 text-primary border-primary/20",
  cancelled:  "bg-muted/50 text-muted-foreground border-border",
};
const STATUS_ICONS: Record<StatusType, string> = {
  completed: "✓", running: "↻", processing: "↻", failed: "✕", paused: "⏸", pending: "…", cancelled: "⊘",
};

export function StatusBadge({ status }: { status: StatusType }) {
  return (
    <span className={cn(
      "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border",
      STATUS_STYLES[status]
    )}>
      {STATUS_ICONS[status]} {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

/* ── Metric card ── */
export function MetricCard({
  label, value, trend, trendUp,
}: { label: string; value: string; trend?: string; trendUp?: boolean }) {
  return (
    <div className="bg-card border border-border rounded-lg p-4 flex-1">
      <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">{label}</div>
      <div className="text-[26px] font-extrabold text-foreground leading-none">{value}</div>
      {trend && (
        <div className={cn("text-[11px] mt-1", trendUp ? "text-emerald-600" : "text-muted-foreground")}>
          {trendUp && "↗ "}{trend}
        </div>
      )}
    </div>
  );
}

/* ── Page header ── */
export function PageHeader({
  title, subtitle, actions, breadcrumbs,
}: {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  breadcrumbs?: string[];
}) {
  return (
    <div className="mb-5">
      {breadcrumbs && (
        <div className="flex items-center gap-1 text-[11px] text-muted-foreground mb-2">
          {breadcrumbs.map((b, i) => (
            <span key={i} className="flex items-center gap-1">
              {i > 0 && <ChevronRight size={10}/>}
              <span className={i === breadcrumbs.length - 1 ? "text-foreground" : ""}>{b}</span>
            </span>
          ))}
        </div>
      )}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-[20px] font-extrabold text-foreground tracking-tight">{title}</h1>
          {subtitle && <p className="text-[12px] text-muted-foreground mt-0.5">{subtitle}</p>}
        </div>
        {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
      </div>
    </div>
  );
}

/* ── Section card ── */
export function SectionCard({
  title, children, className, noPad,
}: { title?: string; children: React.ReactNode; className?: string; noPad?: boolean }) {
  return (
    <div className={cn("bg-card border border-border rounded-lg shadow-sm", className)}>
      {title && (
        <div className="px-4 pt-3 pb-2 border-b border-border/50">
          <span className="text-[13px] font-bold text-foreground">{title}</span>
        </div>
      )}
      <div className={noPad ? "" : "p-4"}>{children}</div>
    </div>
  );
}

/* ── Data table ── */
export function DataTable({
  columns, rows, emptyMessage = "No data found",
}: {
  columns: string[];
  rows: React.ReactNode[][];
  emptyMessage?: string;
}) {
  // Check if rows is empty or contains only empty row placeholder
  const isEmpty = rows.length === 0 || (rows.length === 1 && rows[0].length === 0);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[12px]">
        <thead>
          <tr className="bg-muted/50">
            {columns.map((col, i) => (
              <th key={i} className="text-left px-4 py-2.5 text-[10px] font-bold uppercase tracking-wider text-muted-foreground border-b border-border">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {isEmpty ? (
            <tr className="border-b border-border/50">
              <td colSpan={columns.length} className="px-4 py-8 text-center text-muted-foreground">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map((row, ri) => (
              <tr key={ri} className="border-b border-border/50 hover:bg-muted/50 transition-colors last:border-0">
                {row.map((cell, ci) => (
                  <td key={ci} className="px-4 py-3 text-foreground align-middle">{cell}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

/* ── Toolbar row ── */
export function Toolbar({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 flex-wrap mb-4">
      {children}
    </div>
  );
}

/* ── Ghost / primary buttons ── */
export function Btn({
  children, variant = "ghost", onClick, className, disabled,
}: {
  children: React.ReactNode;
  variant?: "primary" | "ghost" | "outline" | "danger";
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
}) {
  const styles = {
    primary: "bg-primary text-primary-foreground hover:bg-primary/90 border-primary disabled:bg-primary/50 disabled:border-primary/50",
    ghost:   "bg-card text-muted-foreground hover:bg-muted border-border disabled:text-muted-foreground/50",
    outline: "bg-transparent text-muted-foreground hover:bg-muted border-border disabled:text-muted-foreground/50",
    danger:  "bg-card text-destructive hover:bg-destructive/10 border-destructive/20 disabled:text-destructive/50",
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[12px] font-semibold border transition-colors disabled:cursor-not-allowed",
        styles[variant],
        className
      )}
    >
      {children}
    </button>
  );
}

/* ── Search input ── */
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
    <div className="flex items-center gap-2 h-8 px-3 bg-card border border-border rounded-md text-[12px] min-w-[200px]">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-muted-foreground">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
      </svg>
      <input
        type="text"
        value={value || ''}
        onChange={onChange}
        placeholder={placeholder ?? "Search…"}
        className="flex-1 bg-transparent outline-none text-foreground placeholder:text-muted-foreground"
      />
    </div>
  );
}

/* ── Tabs ── */
export function Tabs({
  tabs, active, onChange,
}: { tabs: string[]; active: string; onChange: (t: string) => void }) {
  return (
    <div className="flex border-b border-border mb-4" role="tablist">
      {tabs.map(tab => (
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

/* ── Graph legend ── */
export function GraphLegend() {
  return (
    <div className="flex gap-4 flex-wrap">
      {[
        { color: "bg-violet-400", label: "Capability" },
        { color: "bg-cyan-400",   label: "Use Case" },
        { color: "bg-amber-400",  label: "Persona" },
        { color: "bg-emerald-400",label: "Value Driver" },
      ].map(({ color, label }) => (
        <div key={label} className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <div className={cn("w-2.5 h-2.5 rounded-full", color)}/>
          {label}
        </div>
      ))}
    </div>
  );
}

/* ── Callout ── */
export function Callout({ children }: { children: React.ReactNode }) {
  return (
    <div className="border-l-2 border-border pl-3 py-1 bg-muted/50 text-[11px] text-muted-foreground rounded-r mt-3">
      {children}
    </div>
  );
}
