/**
 * BenchmarkPolicies — Admin Tier 3 Page
 * 
 * Industry benchmark management - Benchmark Library view.
 * 
 * Features:
 * - Confidence scoring and source tracking
 * - Industry/vertical filtering
 */

import { useState, useMemo } from "react";
import {
  BarChart3, Plus, Search, Edit3, Trash2, Eye,
  Globe, Database, CheckCircle2, AlertTriangle, TrendingUp,
  Download, Info, AlertCircle, RefreshCw,
} from "lucide-react";
import { PageHeader, Btn } from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import ErrorBoundary from "@/components/ErrorBoundary";
import { cn } from "@/lib/utils";
import {
  useBenchmarks,
  type Benchmark,
  type ConfidenceLevel,
  type BenchmarkStatus,
} from "@/hooks/useBenchmarks";
import { formatDate } from "@/lib/formatters";

// ── Styling Constants ───────────────────────────────────────────────────────────

const CONFIDENCE_STYLES: Record<ConfidenceLevel, { color: string; bg: string; icon: React.ReactNode }> = {
  High:   { color: "text-emerald-600", bg: "bg-emerald-50", icon: <CheckCircle2 size={12}/> },
  Medium: { color: "text-amber-600", bg: "bg-amber-50", icon: <Info size={12}/> },
  Low:    { color: "text-red-600", bg: "bg-red-50", icon: <AlertTriangle size={12}/> },
};

const STATUS_STYLES: Record<BenchmarkStatus, string> = {
  active: "bg-emerald-50 text-emerald-700 border-emerald-200",
  draft: "bg-neutral-100 text-neutral-600 border-neutral-200",
  deprecated: "bg-red-50 text-red-500 border-red-200",
};

// ── Sub-components ─────────────────────────────────────────────────────────────

function ConfidenceBadge({ level }: { level: ConfidenceLevel }) {
  const style = CONFIDENCE_STYLES[level];
  return (
    <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full ${style.bg} ${style.color}`}>
      {style.icon} {level}
    </span>
  );
}

function StatusBadge({ status }: { status: BenchmarkStatus }) {
  return (
    <span className={`inline-flex items-center text-[10px] font-semibold px-2 py-0.5 rounded-full border ${STATUS_STYLES[status]}`}>
      {status}
    </span>
  );
}

function BenchmarkPoliciesSkeleton() {
  return (
    <div className="p-6 max-w-6xl">
      <div className="flex items-start justify-between mb-6">
        <div>
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-72" />
        </div>
        <Skeleton className="h-9 w-32" />
      </div>

      {/* Stats Row Skeleton */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="bg-white border border-neutral-200 rounded-xl px-4 py-3">
            <Skeleton className="h-4 w-28 mb-2" />
            <Skeleton className="h-7 w-12" />
          </div>
        ))}
      </div>

      {/* Table Skeleton */}
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


function BenchmarkPoliciesContent() {
  const [search, setSearch] = useState("");
  const [confidenceFilter, setConfidenceFilter] = useState<"all" | ConfidenceLevel>("all");
  const [industryFilter, setIndustryFilter] = useState<"all" | string>("all");

  const { 
    data: benchmarks = [], 
    isLoading: benchmarksLoading, 
    error: benchmarksError,
    refetch: refetchBenchmarks
  } = useBenchmarks({
    confidence: confidenceFilter === "all" ? undefined : confidenceFilter,
    search: search || undefined,
  });

  const industries = useMemo(() => 
    Array.from(new Set(benchmarks.map((b: Benchmark) => b.industry))),
    [benchmarks]
  );

  const filteredBenchmarks = useMemo(() => 
    industryFilter === "all" 
      ? benchmarks 
      : benchmarks.filter((b: Benchmark) => b.industry === industryFilter),
    [benchmarks, industryFilter]
  );

  const stats = useMemo(() => ({
    total: benchmarks.length,
    highConfidence: benchmarks.filter((b: Benchmark) => b.confidence === "High").length,
    active: benchmarks.filter((b: Benchmark) => b.status === "active").length,
    totalUsage: benchmarks.reduce((s: number, b: Benchmark) => s + (b.usage_count || 0), 0),
  }), [benchmarks]);

  const isLoading = benchmarksLoading;
  const error = benchmarksError;

  if (isLoading) {
    return <BenchmarkPoliciesSkeleton />;
  }

  if (error) {
    return (
      <div className="p-6 max-w-6xl">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-8 h-8 text-red-500 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-[14px] font-semibold text-red-800 mb-1">Failed to load benchmark policies</h3>
              <p className="text-[12px] text-red-600">
                {error instanceof Error ? error.message : "An unexpected error occurred"}
              </p>
              <button 
                onClick={() => { refetchBenchmarks(); }}
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
          title="Benchmark Policies"
          subtitle="Define and manage industry benchmarks used in formula evaluation and business case generation."
        />
        <Btn variant="primary"><Plus size={13} className="mr-1"/> Add Benchmark</Btn>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: "Total Benchmarks", value: stats.total, icon: <BarChart3 size={14}/> },
          { label: "High Confidence", value: stats.highConfidence, icon: <CheckCircle2 size={14}/>, color: "text-emerald-600" },
          { label: "Active", value: stats.active, icon: <TrendingUp size={14}/>, color: "text-blue-600" },
          { label: "Total Usage", value: stats.totalUsage, icon: <Database size={14}/>, color: "text-violet-600" },
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
              <Search size={12} className="text-neutral-400 shrink-0"/>
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search benchmarks..."
                className="flex-1 text-[12px] bg-transparent outline-none text-neutral-600 placeholder:text-neutral-400"
              />
            </div>
            <select
              value={confidenceFilter}
              onChange={e => {
                const value = e.target.value;
                setConfidenceFilter(value === "all" ? "all" : value as ConfidenceLevel);
              }}
              className="px-3 py-2 text-[11px] border border-neutral-200 rounded-lg bg-white text-neutral-600 outline-none focus:border-blue-300"
            >
              <option value="all">All Confidence</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
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
            <div className="ml-auto flex items-center gap-2">
              <button className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium text-neutral-600 hover:bg-neutral-100 rounded-lg transition-colors">
                <Download size={12}/> Export
              </button>
            </div>
          </div>

          {/* Benchmark Table */}
          <div className="bg-white border border-neutral-200 rounded-xl shadow-sm overflow-hidden">
            <table className="w-full text-[12px]">
              <thead>
                <tr className="border-b border-neutral-100 bg-neutral-50">
                  {["Benchmark", "Industry", "Value Range", "Confidence", "Source", "Status", "Usage", ""].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-[10px] uppercase tracking-wider text-neutral-400 font-semibold">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {filteredBenchmarks.map(b => (
                  <tr key={b.id} className="hover:bg-neutral-50 transition-colors group">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <BarChart3 size={14} className="text-blue-500 shrink-0"/>
                        <div>
                          <span className="font-medium text-neutral-800 block">{b.name}</span>
                          {b.tags.length > 0 && (
                            <div className="flex items-center gap-1 mt-1">
                              {b.tags.map(tag => (
                                <span key={tag} className="text-[9px] px-1.5 py-0.5 bg-neutral-100 text-neutral-500 rounded">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-neutral-500">
                      {b.industry}
                      {b.vertical && <span className="text-neutral-400"> / {b.vertical}</span>}
                    </td>
                    <td className="px-4 py-3 font-mono text-[11px] text-neutral-700">{b.value_range}</td>
                    <td className="px-4 py-3"><ConfidenceBadge level={b.confidence}/></td>
                    <td className="px-4 py-3 text-neutral-500">
                      <div className="flex items-center gap-1">
                        <Globe size={10}/>
                        {b.source} {b.year}
                      </div>
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={b.status}/></td>
                    <td className="px-4 py-3 text-neutral-600">{b.usage_count || 0} formulas</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button className="p-1.5 rounded hover:bg-neutral-100 text-neutral-400 hover:text-neutral-700" title="View">
                          <Eye size={13}/>
                        </button>
                        <button className="p-1.5 rounded hover:bg-neutral-100 text-neutral-400 hover:text-neutral-700" title="Edit">
                          <Edit3 size={13}/>
                        </button>
                        <button className="p-1.5 rounded hover:bg-red-50 text-neutral-400 hover:text-red-500" title="Delete">
                          <Trash2 size={13}/>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filteredBenchmarks.length === 0 && (
              <div className="text-center py-12 text-neutral-400 text-[12px]">
                <BarChart3 size={32} className="mx-auto mb-3 text-neutral-300"/>
                No benchmarks match your filters.
              </div>
            )}
      </div>
    </div>
  );
}

export default function BenchmarkPolicies() {
  return (
    <ErrorBoundary>
      <BenchmarkPoliciesContent />
    </ErrorBoundary>
  );
}
