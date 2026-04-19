/**
 * Screen — Value Packs
 * Design: Refined Enterprise SaaS — wireframe-aligned layout
 * Spec: Value Packs as first-class product objects — reusable domain-specific
 * packages combining ontology, value drivers, formulas, benchmarks, and workflows.
 *
 * Layout: 2-column grid (main + 280px sidebar).
 *   Main:    Filter bar → 3-col pack grid → My Packs row
 *   Sidebar: Preview panel → Pack actions
 */
import { useState, useMemo, useCallback } from "react";
import { PageHeader, Btn } from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import ErrorBoundary from "@/components/ErrorBoundary";
import {
  useValuePacks,
  useValuePack,
  useApplyValuePack,
  type ValuePack,
  type PackStatus,
} from "@/hooks/useValuePacks";
import {
  Package, Search, Filter, AlertCircle, RefreshCw, Loader2,
  Upload, Eye,
} from "lucide-react";

// ── Constants ────────────────────────────────────────────────────────────────

/** Layout constants for consistent sizing */
const LAYOUT = {
  MAX_WIDTH: "1280px",
  SIDEBAR_WIDTH: "280px",
  PACK_GRID_COLS: 3,
  MY_PACKS_SLOTS: 4,
} as const;

/** Industry filter options */
const INDUSTRIES = ["All", "SaaS / B2B", "Infrastructure / DevOps", "Financial Services", "Healthcare"];
const STATUSES: Array<"all" | PackStatus> = ["all", "active", "draft", "published", "archived"];
const STATUS_LABELS: Record<string, string> = {
  all: "All Statuses", active: "Active", draft: "Draft", published: "Published", archived: "Archived",
};

// ── Helpers ──────────────────────────────────────────────────────────────────

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

// ── Pack Card (simplified per wireframe) ─────────────────────────────────────

interface PackCardProps {
  pack: ValuePack;
  isSelected?: boolean;
  onSelect?: (id: string) => void;
}

function PackCard({ pack, isSelected, onSelect }: PackCardProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect?.(pack.pack_id)}
      className={`text-left bg-card border rounded-lg shadow-sm hover:shadow-md transition-all cursor-pointer group w-full ${
        isSelected
          ? "border-primary ring-2 ring-primary/10"
          : "border-border hover:border-border/80"
      }`}
    >
      {/* Title + description */}
      <div className="px-4 pt-4 pb-3">
        <h3 className="text-[13px] font-bold text-foreground leading-tight mb-1.5 truncate">
          {pack.name}
        </h3>
        <div className="space-y-1">
          <p className="text-[11px] text-muted-foreground/60 leading-relaxed line-clamp-2">
            {pack.description || "No description available"}
          </p>
        </div>
      </div>

      {/* Tags: industry + version */}
      <div className="px-4 pb-3 flex items-center gap-2">
        <span className="text-[10px] font-medium text-muted-foreground bg-muted border border-border px-2 py-0.5 rounded">
          {pack.industry}
        </span>
        {pack.version && (
          <span className="text-[10px] font-medium text-muted-foreground bg-muted/20 border border-border px-2 py-0.5 rounded">
            v{pack.version}
          </span>
        )}
      </div>
    </button>
  );
}

function PackCardSkeleton() {
  return (
    <div className="bg-card border border-border rounded-lg shadow-sm">
      <div className="px-4 pt-4 pb-3 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-2/3" />
      </div>
      <div className="px-4 pb-3 flex items-center gap-2">
        <Skeleton className="h-5 w-16 rounded" />
        <Skeleton className="h-5 w-10 rounded" />
      </div>
    </div>
  );
}

// ── Preview Panel ────────────────────────────────────────────────────────────

function PreviewPanel({ packId }: { packId: string | null }) {
  const { data: pack, isLoading } = useValuePack(packId);

  if (isLoading) return <PreviewPanelSkeleton />;

  if (!pack) {
    return (
      <div className="border border-border rounded-lg bg-card p-4" data-testid="preview-panel">
        <h4 className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground/60 mb-3">Preview Panel</h4>
        <div className="space-y-2.5">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-3 bg-muted/30 rounded w-full" />
          ))}
        </div>
        <p className="text-[11px] text-muted-foreground/60 mt-4 text-center">Select a pack to preview</p>
      </div>
    );
  }

  return (
    <div className="border border-border rounded-lg bg-card p-4" data-testid="preview-panel">
      <h4 className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground/60 mb-3">Preview Panel</h4>
      <h3 className="text-[14px] font-bold text-foreground mb-1">{pack.name}</h3>
      <p className="text-[11px] text-muted-foreground mb-3 leading-relaxed">
        {pack.description || "No description available"}
      </p>
      <div className="space-y-2 text-[11px]">
        <div className="flex justify-between">
          <span className="text-muted-foreground/60">Industry</span>
          <span className="font-medium text-muted-foreground">{pack.industry}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground/60">Status</span>
          <span className="font-medium text-muted-foreground capitalize">{pack.status}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground/60">Version</span>
          <span className="font-medium text-muted-foreground">{pack.version || "—"}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground/60">Drivers</span>
          <span className="font-medium text-muted-foreground">{pack.driver_count}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground/60">Formulas</span>
          <span className="font-medium text-muted-foreground">{pack.formula_count}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground/60">Benchmarks</span>
          <span className="font-medium text-muted-foreground">{pack.benchmark_count}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground/60">Updated</span>
          <span className="font-medium text-muted-foreground">{formatLastUpdated(pack.updated_at)}</span>
        </div>
      </div>
    </div>
  );
}

function PreviewPanelSkeleton() {
  return (
    <div className="border border-border rounded-lg bg-card p-4">
      <Skeleton className="h-3 w-24 mb-3" />
      <Skeleton className="h-5 w-3/4 mb-1" />
      <Skeleton className="h-3 w-full mb-3" />
      <div className="space-y-2">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="flex justify-between">
            <Skeleton className="h-3 w-16" />
            <Skeleton className="h-3 w-12" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Pack Actions ─────────────────────────────────────────────────────────────

interface PackActionsProps {
  selectedPackId: string | null;
  onDeploy: (packId: string) => void;
  isDeploying: boolean;
  error?: string | null;
  onClearError?: () => void;
}

function PackActions({ selectedPackId, onDeploy, isDeploying, error, onClearError }: PackActionsProps) {
  return (
    <div className="border border-border rounded-lg bg-card p-4" data-testid="pack-actions">
      <h4 className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground/60 mb-3">Pack Actions</h4>

      {error && (
        <div className="mb-3 p-2 bg-destructive/10 border border-destructive/20 rounded text-[11px] text-destructive flex items-start gap-1.5">
          <AlertCircle size={12} className="shrink-0 mt-0.5" />
          <span className="flex-1">{error}</span>
          {onClearError && (
            <button onClick={onClearError} className="text-destructive/70 hover:text-destructive shrink-0">×</button>
          )}
        </div>
      )}

      <button
        onClick={() => selectedPackId && onDeploy(selectedPackId)}
        disabled={!selectedPackId || isDeploying}
        className="w-full text-[12px] font-semibold bg-primary text-primary-foreground py-2 px-3 rounded-md hover:bg-primary/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-1.5 mb-2"
      >
        {isDeploying ? (
          <><Loader2 size={12} className="animate-spin" /> Deploying...</>
        ) : (
          "Deploy to Account"
        )}
      </button>
      <button
        disabled={!selectedPackId}
        className="w-full text-[12px] font-medium text-muted-foreground hover:text-foreground transition-colors py-1.5 flex items-center justify-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <Eye size={12} /> View Details
      </button>
    </div>
  );
}

// ── My Packs Section ─────────────────────────────────────────────────────────

interface MyPacksSectionProps {
  /** All available packs - tenant-scoped packs will be displayed */
  packs: ValuePack[];
}

/**
 * Displays tenant-scoped packs ("My Packs") in a grid.
 * Shows up to LAYOUT.MY_PACKS_SLOTS packs with empty slot placeholders.
 */
function MyPacksSection({ packs }: MyPacksSectionProps) {
  const myPacks = useMemo(
    () => packs.filter(p => p.scope === "tenant").slice(0, LAYOUT.MY_PACKS_SLOTS),
    [packs]
  );

  const emptySlotCount = Math.max(0, LAYOUT.MY_PACKS_SLOTS - myPacks.length);

  return (
    <div data-testid="my-packs-section">
      <h4 className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground/60 mb-3">My Packs</h4>
      <div className={`grid grid-cols-${LAYOUT.MY_PACKS_SLOTS} gap-3`}>
        {myPacks.length === 0 && (
          <p className="col-span-4 text-[11px] text-muted-foreground/60 text-center py-4">No deployed packs yet.</p>
        )}
        {myPacks.map((pack) => (
          <div
            key={pack.pack_id}
            className="bg-card border border-border rounded-lg px-3 py-3"
            title={pack.name}
          >
            <h5 className="text-[12px] font-bold text-foreground truncate mb-1">
              {pack.name}
            </h5>
            <p className="text-[10px] text-muted-foreground/60 truncate">{pack.industry}</p>
            <div className="h-2 w-3/4 mt-2 bg-muted/30 rounded" />
          </div>
        ))}
        {/* Fill remaining slots with empty placeholders */}
        {emptySlotCount > 0 && Array.from({ length: emptySlotCount }).map((_, i) => (
          <div key={`empty-${i}`} className="bg-muted/20 border border-dashed border-border rounded-lg px-3 py-3">
            <p className="text-[11px] text-muted-foreground/40 text-center py-2">Empty slot</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function MyPacksSkeleton() {
  return (
    <div>
      <Skeleton className="h-3 w-28 mb-3" />
      <div className="grid grid-cols-4 gap-3">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="bg-card border border-border rounded-lg px-3 py-3 space-y-2">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-2 w-full" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main Content ─────────────────────────────────────────────────────────────

function ValuePacksContent() {
  const [industry, setIndustry] = useState("All");
  const [status, setStatus] = useState<"all" | PackStatus>("all");
  const [category, setCategory] = useState("All");
  const [search, setSearch] = useState("");
  const [selectedPackId, setSelectedPackId] = useState<string | null>(null);
  const [deployError, setDeployError] = useState<string | null>(null);

  // Memoize filter config to prevent unnecessary query re-fetches
  const filters = useMemo(() => ({
    industry: industry === "All" ? "all" as const : industry,
    status: status === "all" ? "all" as const : status,
    category: category === "All" ? "all" as const : category,
    search: search || undefined,
  }), [industry, status, category, search]);

  const { data: packs = [], isLoading, error, refetch } = useValuePacks(filters);
  const applyMutation = useApplyValuePack();

  // Derive unique categories from data
  const categories = useMemo(() => {
    const cats = Array.from(new Set(packs.map(p => p.category).filter(Boolean))) as string[];
    return ["All", ...cats];
  }, [packs]);

  // Client-side filtering for search + industry + status + category
  const filtered = useMemo(() => {
    const searchLower = search.toLowerCase();
    return packs.filter(p =>
      (industry === "All" || p.industry === industry) &&
      (status === "all" || p.status === status) &&
      (category === "All" || p.category === category) &&
      (search === "" ||
       p.name.toLowerCase().includes(searchLower) ||
       p.description?.toLowerCase().includes(searchLower))
    );
  }, [packs, industry, status, category, search]);

  const handleDeploy = useCallback(async (packId: string) => {
    setDeployError(null);
    try {
      await applyMutation.mutateAsync({ packId });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to deploy pack";
      setDeployError(message);
      // Error already logged by mutation's onError; UI handles display
    }
  }, [applyMutation]);

  const handleSelectPack = useCallback((packId: string) => {
    setSelectedPackId(prev => (prev === packId ? null : packId));
  }, []);

  return (
    <div className="p-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <PageHeader
          title="Value Packs"
          subtitle="Browse and deploy value pack content"
        />
        <div className="flex items-center gap-2 shrink-0">
          <Btn variant="ghost">
            <Filter size={13} className="mr-1" /> Filter
          </Btn>
          <Btn variant="primary">
            <Upload size={13} className="mr-1" /> Import Pack
          </Btn>
        </div>
      </div>

      {/* Two-column grid: main + sidebar */}
      <div className="grid gap-5 grid-cols-[1fr_280px]">
        {/* ── Left column: filter bar + pack grid + my packs ── */}
        <div className="min-w-0">
          {/* Filter Bar */}
          <div className="bg-card border border-border rounded-lg px-4 py-3 mb-5">
            <div className="flex items-center gap-3 flex-wrap">
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger className="h-8 text-[11px] min-w-[120px]">
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map(c => (
                    <SelectItem key={c} value={c} className="text-[11px]">{c === "All" ? "All Categories" : c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={industry} onValueChange={setIndustry}>
                <SelectTrigger className="h-8 text-[11px] min-w-[140px]">
                  <SelectValue placeholder="Industry" />
                </SelectTrigger>
                <SelectContent>
                  {INDUSTRIES.map(ind => (
                    <SelectItem key={ind} value={ind} className="text-[11px]">{ind === "All" ? "All Industries" : ind}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={status} onValueChange={v => setStatus(v as "all" | PackStatus)}>
                <SelectTrigger className="h-8 text-[11px] min-w-[120px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  {STATUSES.map(s => (
                    <SelectItem key={s} value={s} className="text-[11px]">{STATUS_LABELS[s]}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <div className="flex items-center gap-2 flex-1 min-w-[160px] bg-muted/20 border border-border rounded-md px-3 py-1.5">
                <Search size={12} className="text-muted-foreground/60 shrink-0" />
                <input
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  placeholder="Search packs…"
                  className="flex-1 text-[11px] bg-transparent outline-none text-muted-foreground placeholder:text-muted-foreground/60"
                />
              </div>
            </div>
          </div>

          {/* Error state */}
          {error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg px-4 py-4 mb-4">
              <div className="flex items-start gap-3">
                <AlertCircle size={18} className="text-destructive shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-[13px] font-medium text-destructive">Failed to load value packs</p>
                  <p className="text-[12px] text-destructive/80 mt-1">
                    {error instanceof Error ? error.message : "An unexpected error occurred"}
                  </p>
                  <button
                    onClick={() => refetch()}
                    className="mt-3 flex items-center gap-1.5 text-[12px] font-medium text-destructive hover:text-destructive/80"
                  >
                    <RefreshCw size={12} /> Try again
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Loading state */}
          {isLoading && (
            <div className="grid grid-cols-3 gap-4 mb-6" data-testid="packs-loading">
              {[1, 2, 3, 4, 5, 6].map(i => (
                <PackCardSkeleton key={i} />
              ))}
            </div>
          )}

          {/* Pack Grid */}
          {!isLoading && !error && (
            <>
              <div className="border border-border rounded-lg bg-muted/20 p-4 mb-6">
                <h4 className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground/60 mb-3">Pack Grid</h4>
                <div className="grid grid-cols-3 gap-3">
                  {filtered.map(pack => (
                    <PackCard
                      key={pack.pack_id}
                      pack={pack}
                      isSelected={selectedPackId === pack.pack_id}
                      onSelect={handleSelectPack}
                    />
                  ))}
                  {filtered.length === 0 && (
                    <div className="col-span-3 text-center py-12 text-muted-foreground/60 text-[13px]">
                      <Package size={36} className="mx-auto mb-3 text-muted-foreground/40" />
                      <p>No value packs match your filters.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* My Packs Section */}
              <MyPacksSection packs={packs} />
            </>
          )}

          {isLoading && <MyPacksSkeleton />}
        </div>

        {/* ── Right column: preview panel + pack actions ── */}
        <div className="space-y-4">
          <PreviewPanel packId={selectedPackId} />
          <PackActions
            selectedPackId={selectedPackId}
            onDeploy={handleDeploy}
            isDeploying={applyMutation.isPending}
            error={deployError}
            onClearError={() => setDeployError(null)}
          />
        </div>
      </div>
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
