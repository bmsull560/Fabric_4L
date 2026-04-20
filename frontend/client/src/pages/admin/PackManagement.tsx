/**
 * PackManagement — Admin Tier 3 Page
 *
 * Value Pack lifecycle management:
 * - Pack Library (view all packs with status & industry)
 * - Composition details (drivers, formulas, benchmarks)
 *
 * Features:
 * - Search and filter by industry, status
 * - Fork / execute pack actions
 * - Composition counts
 */

import { useState, useMemo } from "react";
import {
  FolderKanban, Plus, Search, Eye, Edit3, GitBranch,
  CheckCircle2, Clock, AlertCircle, Archive, RefreshCw,
  Loader2, BarChart3, FlaskConical, ListChecks,
} from "lucide-react";
import { PageHeader, Btn } from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/formatters";
import ErrorBoundary from "@/components/ErrorBoundary";
import { cn } from "@/lib/utils";
import {
  useValuePacks,
  type ValuePack,
  type PackStatus,
} from "@/hooks/useValuePacks";

// ── Styling Constants ───────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<PackStatus, { color: string; icon: React.ReactNode; label: string }> = {
  published: { color: "bg-emerald-50 text-emerald-700 border-emerald-200", icon: <CheckCircle2 size={11}/>, label: "Published" },
  active:    { color: "bg-emerald-50 text-emerald-700 border-emerald-200", icon: <CheckCircle2 size={11}/>, label: "Active" },
  draft:     { color: "bg-neutral-100 text-neutral-600 border-neutral-200", icon: <Clock size={11}/>, label: "Draft" },
  archived:  { color: "bg-red-50 text-red-500 border-red-200", icon: <Archive size={11}/>, label: "Archived" },
};

// ── Sub-components ─────────────────────────────────────────────────────────────

function PackStatusChip({ status }: { status: PackStatus }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.draft;
  return (
    <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border ${cfg.color}`}>
      {cfg.icon} {cfg.label}
    </span>
  );
}


function PackManagementSkeleton() {
  return (
    <div className="p-6 max-w-6xl">
      <div className="flex items-start justify-between mb-6">
        <div>
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-72" />
        </div>
        <Skeleton className="h-9 w-32" />
      </div>
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="bg-white border border-neutral-200 rounded-xl px-4 py-3">
            <Skeleton className="h-4 w-28 mb-2" />
            <Skeleton className="h-7 w-12" />
          </div>
        ))}
      </div>
      <div className="bg-white border border-neutral-200 rounded-xl shadow-sm overflow-hidden">
        {[1, 2, 3, 4, 5].map(i => (
          <div key={i} className="px-4 py-4 border-b border-neutral-100 flex gap-4">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-16" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────

function PackManagementContent() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | PackStatus>("all");
  const [industryFilter, setIndustryFilter] = useState<"all" | string>("all");

  const {
    data: packs = [],
    isLoading,
    error,
    refetch,
  } = useValuePacks({
    status: statusFilter === "all" ? undefined : statusFilter,
    search: search || undefined,
  });

  const industries = useMemo(() =>
    Array.from(new Set(packs.map(p => p.industry))),
    [packs]
  );

  const filteredPacks = useMemo(() =>
    industryFilter === "all"
      ? packs
      : packs.filter(p => p.industry === industryFilter),
    [packs, industryFilter]
  );

  const stats = useMemo(() => ({
    total: packs.length,
    published: packs.filter(p => p.status === "published" || p.status === "active").length,
    draft: packs.filter(p => p.status === "draft").length,
    totalDrivers: packs.reduce((s, p) => s + (p.driver_count || 0), 0),
  }), [packs]);

  if (isLoading) return <PackManagementSkeleton />;

  if (error) {
    return (
      <div className="p-6 max-w-6xl">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-8 h-8 text-red-500 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-[14px] font-semibold text-red-800 mb-1">Failed to load packs</h3>
              <p className="text-[12px] text-red-600">
                {error instanceof Error ? error.message : "An unexpected error occurred"}
              </p>
              <button
                onClick={() => refetch()}
                className="mt-4 flex items-center gap-1.5 px-3 py-1.5 bg-red-100 text-red-700 text-[12px] font-medium rounded-lg hover:bg-red-200 transition-colors"
              >
                <RefreshCw size={14} /> Try again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <PageHeader
          title="Pack Management"
          subtitle="Create, manage, and publish value packs across industries and segments."
        />
        <Btn variant="primary"><Plus size={13} className="mr-1" /> New Pack</Btn>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: "Total Packs", value: stats.total, icon: <FolderKanban size={14} /> },
          { label: "Published", value: stats.published, icon: <CheckCircle2 size={14} />, color: "text-emerald-600" },
          { label: "Drafts", value: stats.draft, icon: <Clock size={14} />, color: "text-amber-600" },
          { label: "Total Drivers", value: stats.totalDrivers, icon: <ListChecks size={14} />, color: "text-violet-600" },
        ].map(s => (
          <div key={s.label} className="bg-white border border-neutral-200 rounded-xl px-4 py-3">
            <div className="flex items-center gap-2 mb-1">
              <span className={s.color || "text-neutral-500"}>{s.icon}</span>
              <span className="text-[10px] uppercase tracking-wider text-neutral-400 font-semibold">{s.label}</span>
            </div>
            <p className={`text-[22px] font-extrabold ${s.color || "text-neutral-800"}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex items-center gap-2 bg-white border border-neutral-200 rounded-lg px-3 py-2 max-w-sm flex-1">
          <Search size={12} className="text-neutral-400 shrink-0" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search packs..."
            className="flex-1 text-[12px] bg-transparent outline-none text-neutral-600 placeholder:text-neutral-400"
          />
        </div>
        <div className="flex items-center gap-1.5">
          {(["all", "published", "draft", "archived"] as const).map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={cn(
                "text-[11px] px-2.5 py-1 rounded-full border capitalize transition-colors font-medium",
                statusFilter === s
                  ? "bg-neutral-800 text-white border-neutral-800"
                  : "bg-white text-neutral-500 border-neutral-200 hover:border-neutral-300"
              )}
            >
              {s}
            </button>
          ))}
        </div>
        <select
          value={industryFilter}
          onChange={e => setIndustryFilter(e.target.value)}
          className="px-3 py-2 text-[11px] border border-neutral-200 rounded-lg bg-white text-neutral-600 outline-none focus:border-blue-300"
        >
          <option value="all">All Industries</option>
          {industries.map(ind => (
            <option key={ind} value={ind}>{ind}</option>
          ))}
        </select>
      </div>

      {/* Pack Table */}
      <div className="bg-white border border-neutral-200 rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-[12px]">
          <thead>
            <tr className="border-b border-neutral-100 bg-neutral-50">
              {["Pack", "Industry", "Status", "Drivers", "Formulas", "Benchmarks", "Version", "Updated", ""].map(h => (
                <th key={h} className="text-left px-4 py-3 text-[10px] uppercase tracking-wider text-neutral-400 font-semibold">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {filteredPacks.map(p => (
              <tr key={p.id} className="hover:bg-neutral-50 transition-colors group">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <FolderKanban size={14} className="text-blue-500 shrink-0" />
                    <div>
                      <span className="font-medium text-neutral-800 block">{p.name}</span>
                      {p.description && (
                        <span className="text-[10px] text-neutral-400 line-clamp-1">{p.description}</span>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3 text-neutral-500">{p.industry}</td>
                <td className="px-4 py-3"><PackStatusChip status={p.status} /></td>
                <td className="px-4 py-3 text-neutral-600">
                  <span className="flex items-center gap-1"><ListChecks size={11} /> {p.driver_count || 0}</span>
                </td>
                <td className="px-4 py-3 text-neutral-600">
                  <span className="flex items-center gap-1"><FlaskConical size={11} /> {p.formula_count || 0}</span>
                </td>
                <td className="px-4 py-3 text-neutral-600">
                  <span className="flex items-center gap-1"><BarChart3 size={11} /> {p.benchmark_count || 0}</span>
                </td>
                <td className="px-4 py-3 font-mono text-[11px] text-neutral-500">{p.version || "—"}</td>
                <td className="px-4 py-3 text-neutral-400">{formatDate(p.updated_at)}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-1.5 rounded hover:bg-neutral-100 text-neutral-400 hover:text-neutral-700" title="View">
                      <Eye size={13} />
                    </button>
                    <button className="p-1.5 rounded hover:bg-neutral-100 text-neutral-400 hover:text-neutral-700" title="Edit">
                      <Edit3 size={13} />
                    </button>
                    <button className="p-1.5 rounded hover:bg-neutral-100 text-neutral-400 hover:text-blue-600" title="Fork">
                      <GitBranch size={13} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredPacks.length === 0 && (
          <div className="text-center py-12 text-neutral-400 text-[12px]">
            <FolderKanban size={32} className="mx-auto mb-3 text-neutral-300" />
            No packs match your filters.
          </div>
        )}
      </div>
    </div>
  );
}

export default function PackManagement() {
  return (
    <ErrorBoundary>
      <PackManagementContent />
    </ErrorBoundary>
  );
}
