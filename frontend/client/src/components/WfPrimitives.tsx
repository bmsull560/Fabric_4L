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
type StatusType = "completed" | "processing" | "failed" | "running" | "paused" | "pending" | "cancelled";
const STATUS_STYLES: Record<StatusType, string> = {
  completed:  "bg-emerald-100 text-emerald-800 border-emerald-200",
  running:    "bg-amber-100   text-amber-800   border-amber-200",
  processing: "bg-amber-100   text-amber-800   border-amber-200",
  failed:     "bg-red-100     text-red-800     border-red-200",
  paused:     "bg-neutral-100 text-neutral-600 border-neutral-200",
  pending:    "bg-blue-100    text-blue-800    border-blue-200",
  cancelled:  "bg-gray-100    text-gray-600    border-gray-200",
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
    <div className="bg-white border border-neutral-200 rounded-lg p-4 flex-1">
      <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 mb-1">{label}</div>
      <div className="text-[26px] font-extrabold text-neutral-900 leading-none">{value}</div>
      {trend && (
        <div className={cn("text-[11px] mt-1", trendUp ? "text-emerald-600" : "text-neutral-500")}>
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
        <div className="flex items-center gap-1 text-[11px] text-neutral-400 mb-2">
          {breadcrumbs.map((b, i) => (
            <span key={i} className="flex items-center gap-1">
              {i > 0 && <ChevronRight size={10}/>}
              <span className={i === breadcrumbs.length - 1 ? "text-neutral-600" : ""}>{b}</span>
            </span>
          ))}
        </div>
      )}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-[20px] font-extrabold text-neutral-900 tracking-tight">{title}</h1>
          {subtitle && <p className="text-[12px] text-neutral-500 mt-0.5">{subtitle}</p>}
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
    <div className={cn("bg-white border border-neutral-200 rounded-lg shadow-sm", className)}>
      {title && (
        <div className="px-4 pt-3 pb-2 border-b border-neutral-100">
          <span className="text-[13px] font-bold text-neutral-800">{title}</span>
        </div>
      )}
      <div className={noPad ? "" : "p-4"}>{children}</div>
    </div>
  );
}

/* ── Data table ── */
export function DataTable({
  columns, rows,
}: {
  columns: string[];
  rows: React.ReactNode[][];
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[12px]">
        <thead>
          <tr className="bg-neutral-50">
            {columns.map((col, i) => (
              <th key={i} className="text-left px-4 py-2.5 text-[10px] font-bold uppercase tracking-wider text-neutral-400 border-b border-neutral-200">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} className="border-b border-neutral-100 hover:bg-neutral-50 transition-colors last:border-0">
              {row.map((cell, ci) => (
                <td key={ci} className="px-4 py-3 text-neutral-700 align-middle">{cell}</td>
              ))}
            </tr>
          ))}
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
    primary: "bg-blue-700 text-white hover:bg-blue-800 border-blue-700 disabled:bg-blue-300 disabled:border-blue-300",
    ghost:   "bg-white text-neutral-600 hover:bg-neutral-100 border-neutral-200 disabled:text-neutral-300",
    outline: "bg-transparent text-neutral-600 hover:bg-neutral-100 border-neutral-300 disabled:text-neutral-300",
    danger:  "bg-white text-red-600 hover:bg-red-50 border-red-200 disabled:text-red-300",
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
    <div className="flex items-center gap-2 h-8 px-3 bg-white border border-neutral-200 rounded-md text-[12px] min-w-[200px]">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-neutral-400">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
      </svg>
      <input
        type="text"
        value={value || ''}
        onChange={onChange}
        placeholder={placeholder ?? "Search…"}
        className="flex-1 bg-transparent outline-none text-neutral-700 placeholder:text-neutral-400"
      />
    </div>
  );
}

/* ── Tabs ── */
export function Tabs({
  tabs, active, onChange,
}: { tabs: string[]; active: string; onChange: (t: string) => void }) {
  return (
    <div className="flex border-b border-neutral-200 mb-4">
      {tabs.map(tab => (
        <button
          key={tab}
          onClick={() => onChange(tab)}
          className={cn(
            "px-4 py-2 text-[12px] font-semibold border-b-2 -mb-px transition-colors",
            active === tab
              ? "border-blue-600 text-blue-700"
              : "border-transparent text-neutral-500 hover:text-neutral-800"
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
        <div key={label} className="flex items-center gap-1.5 text-[11px] text-neutral-600">
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
    <div className="border-l-2 border-neutral-300 pl-3 py-1 bg-neutral-50 text-[11px] text-neutral-500 rounded-r mt-3">
      {children}
    </div>
  );
}
