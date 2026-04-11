/**
 * Screen — Value Packs
 * Design: Refined Enterprise SaaS
 * Spec: Value Packs as first-class product objects — reusable domain-specific
 * packages combining ontology, value drivers, formulas, benchmarks, and workflows.
 */
import { useState, useMemo, useCallback } from "react";
import { PageHeader, Btn, StatusBadge } from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import ErrorBoundary from "@/components/ErrorBoundary";
import {
  useValuePacks,
  useApplyValuePack,
  type ValuePack,
  type PackStatus,
} from "@/hooks/useValuePacks";
import {
  Sparkles, Package, GitBranch, FlaskConical, BarChart3, Bot,
  ChevronRight, Search, Filter, Lock, Globe, AlertCircle,
  RefreshCw, Loader2,
} from "lucide-react";

const INDUSTRIES = ["All Industries", "SaaS / B2B", "Infrastructure / DevOps", "Financial Services", "Healthcare"];

function formatLastUpdated(dateStr: string | undefined): string {
  if (!dateStr) return "Unknown";
  const date = new Date(dateStr);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  return date.toLocaleDateString();
}

function getStatusColor(status: PackStatus): "completed" | "processing" | "failed" {
  switch (status) {
    case "active":
    case "published":
      return "completed";
    case "draft":
      return "processing";
    case "archived":
      return "failed";
    default:
      return "processing";
  }
}

interface PackCardProps {
  pack: ValuePack;
  onApply?: (id: string) => void;
  isApplying?: boolean;
}

function PackCard({ pack, onApply, isApplying }: PackCardProps) {
  const statusColor = getStatusColor(pack.status);
  const lastUpdated = formatLastUpdated(pack.updated_at);

  return (
    <div className="bg-white border border-neutral-200 rounded-xl shadow-sm hover:shadow-md hover:border-neutral-300 transition-all cursor-pointer group">
      {/* Header */}
      <div className="px-5 pt-5 pb-4 border-b border-neutral-100">
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center">
              <Sparkles size={14} className="text-blue-600"/>
            </div>
            <div>
              <h3 className="text-[13px] font-bold text-neutral-900 leading-tight">{pack.name}</h3>
              <p className="text-[10px] text-neutral-400 mt-0.5">{pack.industry}</p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            {pack.scope === "global"
              ? <span title="Global pack" className="text-neutral-300"><Globe size={12}/></span>
              : <span title="Tenant pack" className="text-neutral-300"><Lock size={12}/></span>
            }
            <StatusBadge status={statusColor}/>
          </div>
        </div>
        <p className="text-[11px] text-neutral-500 leading-relaxed">{pack.description || "No description available"}</p>
      </div>

      {/* Composition stats */}
      <div className="px-5 py-3 grid grid-cols-4 gap-2">
        {[
          { icon: <GitBranch size={11}/>, label: "Drivers",    value: pack.driver_count ?? 0 },
          { icon: <FlaskConical size={11}/>, label: "Formulas", value: pack.formula_count ?? 0 },
          { icon: <BarChart3 size={11}/>, label: "Benchmarks", value: pack.benchmark_count ?? 0 },
          { icon: <Bot size={11}/>, label: "Workflows",        value: pack.workflow_count ?? 0 },
        ].map(s => (
          <div key={s.label} className="text-center">
            <div className="flex items-center justify-center gap-1 text-neutral-400 mb-0.5">
              {s.icon}
            </div>
            <p className="text-[14px] font-bold text-neutral-800">{s.value}</p>
            <p className="text-[9px] text-neutral-400 uppercase tracking-wide">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-neutral-100 flex items-center justify-between">
        <span className="text-[10px] text-neutral-400">Updated {lastUpdated}</span>
        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <button className="text-[11px] text-blue-600 font-medium hover:underline">Preview</button>
          <button 
            onClick={(e) => {
              e.stopPropagation();
              onApply?.(pack.pack_id);
            }}
            disabled={isApplying}
            className="text-[11px] bg-blue-600 text-white px-2.5 py-1 rounded-md font-medium hover:bg-blue-700 transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isApplying ? (
              <><Loader2 size={10} className="animate-spin" /> Applying...</>
            ) : (
              <>Apply <ChevronRight size={10}/></>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

function PackCardSkeleton() {
  return (
    <div className="bg-white border border-neutral-200 rounded-xl shadow-sm">
      {/* Header */}
      <div className="px-5 pt-5 pb-4 border-b border-neutral-100">
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center gap-2.5">
            <Skeleton className="w-8 h-8 rounded-lg" />
            <div className="space-y-1">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-3 w-20" />
            </div>
          </div>
          <Skeleton className="h-5 w-16 rounded-full" />
        </div>
        <Skeleton className="h-3 w-full mt-2" />
        <Skeleton className="h-3 w-2/3 mt-1" />
      </div>

      {/* Composition stats */}
      <div className="px-5 py-3 grid grid-cols-4 gap-2">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="text-center space-y-1">
            <Skeleton className="h-4 w-8 mx-auto" />
            <Skeleton className="h-2 w-12 mx-auto" />
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-neutral-100 flex items-center justify-between">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-6 w-16 rounded" />
      </div>
    </div>
  );
}

function ValuePacksContent() {
  const [industry, setIndustry] = useState("All Industries");
  const [search, setSearch] = useState("");
  
  // Memoize filter config to prevent unnecessary query re-fetches
  const filters = useMemo(() => ({
    industry: industry === "All Industries" ? "all" : industry,
    search: search || undefined,
  }), [industry, search]);
  
  const { data: packs = [], isLoading, error, refetch } = useValuePacks(filters);
  const applyMutation = useApplyValuePack();

  // Client-side filtering for industry/search (API returns all, we filter)
  const filtered = useMemo(() => {
    const searchLower = search.toLowerCase();
    return packs.filter(p =>
      (industry === "All Industries" || p.industry === industry) &&
      (search === "" || 
       p.name.toLowerCase().includes(searchLower) || 
       p.description?.toLowerCase().includes(searchLower))
    );
  }, [packs, industry, search]);

  const handleApply = useCallback(async (packId: string) => {
    try {
      await applyMutation.mutateAsync(packId);
      // Success feedback could be added here (toast, etc.)
    } catch (err) {
      console.error("Failed to apply pack:", err);
      // Error is handled by mutation state
    }
  }, [applyMutation]);

  return (
    <div className="p-6 max-w-5xl">
      <div className="flex items-start justify-between mb-6">
        <PageHeader
          title="Value Packs"
          subtitle="Reusable domain packages combining value drivers, formulas, benchmarks, and workflows."
        />
        <Btn variant="primary">
          <Package size={13} className="mr-1.5"/> New Pack
        </Btn>
      </div>

      {/* What is a Value Pack — info banner */}
      <div className="bg-blue-50 border border-blue-100 rounded-xl px-5 py-4 mb-6 flex items-start gap-4">
        <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shrink-0 mt-0.5">
          <Sparkles size={14} className="text-white"/>
        </div>
        <div>
          <h3 className="text-[13px] font-bold text-blue-900 mb-1">What is a Value Pack?</h3>
          <p className="text-[12px] text-blue-700 leading-relaxed max-w-2xl">
            A Value Pack is a pre-built, reusable package for a specific industry or use case. Each pack bundles
            an ontology slice, value drivers, governed formula logic, benchmark relationships, and workflow
            orchestration — so you can go from a domain to a business case in minutes, not weeks.
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-5">
        <div className="flex items-center gap-2 flex-1 max-w-xs bg-white border border-neutral-200 rounded-lg px-3 py-2">
          <Search size={12} className="text-neutral-400 shrink-0"/>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search packs…"
            className="flex-1 text-[12px] bg-transparent outline-none text-neutral-600 placeholder:text-neutral-400"
          />
        </div>
        <div className="flex items-center gap-1.5">
          <Filter size={12} className="text-neutral-400"/>
          {INDUSTRIES.map(ind => (
            <button
              key={ind}
              onClick={() => setIndustry(ind)}
              className={`text-[11px] px-2.5 py-1 rounded-full border transition-colors font-medium ${
                industry === ind
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white text-neutral-500 border-neutral-200 hover:border-neutral-300"
              }`}
            >
              {ind}
            </button>
          ))}
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-4 mb-4">
          <div className="flex items-start gap-3">
            <AlertCircle size={18} className="text-red-500 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-[13px] font-medium text-red-800">Failed to load value packs</p>
              <p className="text-[12px] text-red-600 mt-1">
                {error instanceof Error ? error.message : "An unexpected error occurred"}
              </p>
              <button 
                onClick={() => refetch()}
                className="mt-3 flex items-center gap-1.5 text-[12px] font-medium text-red-700 hover:text-red-800"
              >
                <RefreshCw size={12} /> Try again
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Loading state with skeletons */}
      {isLoading && (
        <div className="grid grid-cols-2 gap-4">
          {[1, 2, 3, 4].map(i => (
            <PackCardSkeleton key={i} />
          ))}
        </div>
      )}
      
      {/* Pack grid */}
      {!isLoading && !error && (
        <div className="grid grid-cols-2 gap-4">
          {filtered.map(pack => (
            <PackCard 
              key={pack.pack_id} 
              pack={pack} 
              onApply={handleApply}
              isApplying={applyMutation.isPending}
            />
          ))}
          {filtered.length === 0 && (
            <div className="col-span-2 text-center py-16 text-neutral-400 text-[13px]">
              <Package size={48} className="mx-auto mb-4 text-neutral-300"/>
              <p>No value packs match your filters.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ValuePacks() {
  return (
    <ErrorBoundary>
      <ValuePacksContent />
    </ErrorBoundary>
  );
}
