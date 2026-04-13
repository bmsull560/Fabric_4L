/**
 * BenchmarkPolicies — Admin Tier 3 Page
 * 
 * Industry benchmark management:
 * - Benchmark Library (view and manage benchmarks)
 * - Policy Configuration (set thresholds, refresh cadence, fallback policies)
 * 
 * Features:
 * - Confidence scoring and source tracking
 * - Industry/vertical filtering
 * - Policy rule management
 */

import { useState, useMemo } from "react";
import { useLocation } from "wouter";
import {
  BarChart3, Plus, Search, Filter, Edit3, Trash2, Eye,
  Clock, Globe, Database, CheckCircle2, AlertTriangle, TrendingUp,
  Download, Settings2, Info, ChevronRight, AlertCircle, RefreshCw,
} from "lucide-react";
import { PageHeader, Btn } from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import ErrorBoundary from "@/components/ErrorBoundary";
import { cn } from "@/lib/utils";
import {
  useBenchmarks,
  useBenchmarkPolicies,
  useUpdateBenchmarkPolicy,
  type Benchmark,
  type BenchmarkPolicy,
  type ConfidenceLevel,
  type BenchmarkStatus,
} from "@/hooks/useBenchmarks";

// ── Helper Functions ───────────────────────────────────────────────────────────

function formatDate(dateStr?: string): string {
  if (!dateStr) return "—";
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

// ── Local Types ─────────────────────────────────────────────────────────────────

type PolicyType = BenchmarkPolicy["policy_type"];

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

const POLICY_TYPE_ICONS: Record<PolicyType, React.ReactNode> = {
  threshold: <BarChart3 size={14}/>,
  cadence: <Clock size={14}/>,
  fallback: <Database size={14}/>,
  override: <Settings2 size={14}/>,
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

function PolicyCard({ policy }: { policy: BenchmarkPolicy }) {
  return (
    <div className="bg-white border border-neutral-200 rounded-xl p-4 flex items-start gap-4">
      <div className="w-10 h-10 rounded-lg bg-neutral-100 flex items-center justify-center text-neutral-600 shrink-0">
        {POLICY_TYPE_ICONS[policy.policy_type]}
      </div>
      <div className="flex-1">
        <div className="flex items-start justify-between mb-1">
          <h4 className="text-[13px] font-semibold text-neutral-800">{policy.name}</h4>
          <span className={cn(
            "text-[10px] px-2 py-0.5 rounded-full",
            policy.is_enabled ? "bg-emerald-100 text-emerald-700" : "bg-neutral-100 text-neutral-500"
          )}>
            {policy.is_enabled ? "Enabled" : "Disabled"}
          </span>
        </div>
        <p className="text-[11px] text-neutral-500 mb-2">{policy.description}</p>
        <div className="flex items-center gap-3">
          <span className="text-[11px] font-medium text-neutral-700 bg-neutral-100 px-2 py-0.5 rounded">
            {policy.value}
          </span>
          <span className="text-[10px] text-neutral-400 uppercase tracking-wider">
            Scope: {policy.scope}
          </span>
        </div>
      </div>
    </div>
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

type TabType = "library" | "policies";

function BenchmarkPoliciesContent() {
  const [location] = useLocation();
  const initialTab: TabType = location.includes("/policies") ? "policies" : "library";
  const [activeTab, setActiveTab] = useState<TabType>(initialTab);
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
  
  const { 
    data: policies = [], 
    isLoading: policiesLoading,
    error: policiesError,
    refetch: refetchPolicies
  } = useBenchmarkPolicies();

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

  const isLoading = benchmarksLoading || policiesLoading;
  const error = benchmarksError || policiesError;

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
                onClick={() => { refetchBenchmarks(); refetchPolicies(); }}
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

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-neutral-200 mb-4">
        {[
          { id: "library" as const, label: "Benchmark Library", count: benchmarks.length },
          { id: "policies" as const, label: "Policy Configuration" },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "px-4 py-2.5 text-[12px] font-medium transition-colors relative",
              activeTab === tab.id
                ? "text-blue-700"
                : "text-neutral-500 hover:text-neutral-700"
            )}
          >
            <span className="flex items-center gap-2">
              {tab.label}
              {tab.count !== undefined && (
                <span className={cn(
                  "px-1.5 py-0.5 rounded text-[10px]",
                  activeTab === tab.id ? "bg-blue-100 text-blue-700" : "bg-neutral-100 text-neutral-600"
                )}>
                  {tab.count}
                </span>
              )}
            </span>
            {activeTab === tab.id && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-t-full" />
            )}
          </button>
        ))}
      </div>

      {activeTab === "library" ? (
        <>
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
        </>
      ) : (
        <>
          {/* Policy Configuration */}
          <div className="mb-6">
            <h3 className="text-[14px] font-semibold text-neutral-800 mb-4">Policy Rules</h3>
            <div className="grid grid-cols-2 gap-4">
              {policies.map(policy => (
                <PolicyCard 
                  key={policy.id} 
                  policy={policy}
                />
              ))}
            </div>
          </div>

          {/* Policy Audit Log */}
          <div className="bg-white border border-neutral-200 rounded-xl p-4">
            <h3 className="text-[14px] font-semibold text-neutral-800 mb-4">Recent Policy Changes</h3>
            <div className="space-y-3">
              {[
                { action: "Updated", target: "Default Confidence Threshold", from: "Low", to: "Medium", user: "Admin", time: "2 hours ago" },
                { action: "Enabled", target: "Low Confidence Fallback", from: "—", to: "Active", user: "Admin", time: "1 day ago" },
                { action: "Created", target: "Quarterly Review Cadence", from: "—", to: "Active", user: "System", time: "3 days ago" },
              ].map((log, i) => (
                <div key={i} className="flex items-center gap-3 text-[12px]">
                  <span className="text-neutral-400">{log.time}</span>
                  <span className="font-medium text-neutral-700">{log.action}</span>
                  <span className="text-neutral-600">{log.target}</span>
                  {log.from !== "—" && (
                    <>
                      <span className="text-neutral-400">from</span>
                      <span className="bg-neutral-100 px-1.5 py-0.5 rounded text-neutral-600">{log.from}</span>
                    </>
                  )}
                  <span className="text-neutral-400">to</span>
                  <span className="bg-blue-50 px-1.5 py-0.5 rounded text-blue-700">{log.to}</span>
                  <span className="text-neutral-400 ml-auto">by {log.user}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
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
