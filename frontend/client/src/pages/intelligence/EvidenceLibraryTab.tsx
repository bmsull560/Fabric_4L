/**
 * EvidenceLibraryTab — DIL-backed Evidence Library
 *
 * Replaces the generic workspace EvidenceTab with purpose-built DIL hooks.
 * Uses: useCaseStudies, useEvidenceSearch, useCaseStudy from useEvidence hook.
 *
 * Full-text search, industry/product filtering, outcome tracking with
 * before/after metrics and improvement percentages.
 */
import { useState, useMemo } from "react";
import { useParams } from "react-router-dom";
import {
  FileText,
  Search,
  Filter,
  CheckCircle2,
  TrendingUp,
  Building2,
  Tag,
  Loader2,
  ChevronRight,
  BookOpen,
  BarChart3,
} from "lucide-react";
import IntelligenceShell from "@/components/workspace/IntelligenceShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
import { CenteredLoader } from "@/components/CenteredLoader";
import { SectionCard, MetricCard } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";
import {
  useCaseStudies,
  useEvidenceSearch,
  type CaseStudy,
} from "@/hooks/useEvidence";

// ── Helpers ──────────────────────────────────────────────────────────────────

function improvementBadge(pct: number | undefined) {
  if (pct == null) return null;
  const color = pct > 0 ? "text-green-600 bg-green-50" : "text-red-500 bg-red-50";
  return (
    <span className={cn("inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-semibold", color)}>
      <TrendingUp size={10} />
      {pct > 0 ? "+" : ""}{pct.toFixed(0)}%
    </span>
  );
}

/** Compute average improvement across all metrics_before → metrics_after */
function computeAvgImprovement(study: CaseStudy): number | null {
  if (!study.improvement_pct || Object.keys(study.improvement_pct).length === 0) return null;
  const vals = Object.values(study.improvement_pct);
  return vals.reduce((a, b) => a + b, 0) / vals.length;
}

// ── Evidence Card ────────────────────────────────────────────────────────────

function EvidenceCard({
  study,
  isSelected,
  onSelect,
}: {
  study: CaseStudy;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const avgImprov = computeAvgImprovement(study);

  return (
    <button
      onClick={onSelect}
      className={cn(
        "flex items-start gap-3 w-full px-4 py-3 rounded-md text-left transition-colors",
        isSelected ? "bg-primary/5 ring-1 ring-primary/20" : "hover:bg-muted/50"
      )}
    >
      <FileText size={14} className="text-primary mt-0.5 shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="text-xs font-semibold">{study.title}</div>
        <div className="text-[10px] text-muted-foreground mt-0.5 line-clamp-2">
          {study.challenge}
        </div>
        <div className="flex items-center gap-2 mt-1.5 flex-wrap">
          {study.industry && (
            <span className="inline-flex items-center gap-0.5 text-[10px] text-muted-foreground">
              <Building2 size={8} />
              {study.industry}
            </span>
          )}
          {study.product_ids && study.product_ids.length > 0 && (
            <span className="inline-flex items-center gap-0.5 text-[10px] text-muted-foreground">
              <Tag size={8} />
              {study.product_ids.length} product{study.product_ids.length !== 1 ? "s" : ""}
            </span>
          )}
          {study.improvement_pct && Object.keys(study.improvement_pct).length > 0 && (
            <span className="inline-flex items-center gap-0.5 text-[10px] text-muted-foreground">
              <BarChart3 size={8} />
              {Object.keys(study.improvement_pct).length} metric{Object.keys(study.improvement_pct).length !== 1 ? "s" : ""}
            </span>
          )}
        </div>
      </div>
      <div className="flex flex-col items-end gap-1 shrink-0">
        {avgImprov != null && improvementBadge(avgImprov)}
        <ChevronRight size={12} className="text-muted-foreground" />
      </div>
    </button>
  );
}

// ── Detail Panel ─────────────────────────────────────────────────────────────

function EvidenceDetailPanel({ study }: { study: CaseStudy }) {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-bold">{study.title}</h3>

      {/* Challenge / Solution / Outcome */}
      <div className="space-y-2">
        {study.challenge && (
          <div>
            <span className="text-[10px] font-semibold text-muted-foreground">Challenge</span>
            <p className="text-xs mt-0.5">{study.challenge}</p>
          </div>
        )}
        {study.solution && (
          <div>
            <span className="text-[10px] font-semibold text-muted-foreground">Solution</span>
            <p className="text-xs mt-0.5">{study.solution}</p>
          </div>
        )}
        {study.outcome && (
          <div>
            <span className="text-[10px] font-semibold text-muted-foreground">Outcome</span>
            <p className="text-xs mt-0.5">{study.outcome}</p>
          </div>
        )}
      </div>

      {/* Metadata */}
      <div className="space-y-1.5 text-[10px]">
        {study.customer_name && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Customer</span>
            <span className="font-semibold">{study.customer_name}</span>
          </div>
        )}
        {study.industry && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Industry</span>
            <span className="font-semibold">{study.industry}</span>
          </div>
        )}
        {study.created_at && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Created</span>
            <span className="font-semibold">{new Date(study.created_at).toLocaleDateString()}</span>
          </div>
        )}
        <div className="flex justify-between">
          <span className="text-muted-foreground">Published</span>
          <span className="font-semibold">{study.published ? "Yes" : "No"}</span>
        </div>
      </div>

      {/* Metrics Before/After */}
      {study.metrics_before && Object.keys(study.metrics_before).length > 0 && (
        <div className="space-y-2">
          <span className="text-[10px] font-semibold text-muted-foreground">Metrics</span>
          {Object.keys(study.metrics_before).map((key) => (
            <div key={key} className="border-l-2 border-primary/30 pl-2 space-y-0.5">
              <div className="text-[10px] font-semibold">{key.replace(/_/g, " ")}</div>
              <div className="flex items-center gap-2 text-[10px]">
                <span className="text-muted-foreground">
                  {study.metrics_before[key]} → {study.metrics_after?.[key] ?? "N/A"}
                </span>
                {study.improvement_pct?.[key] != null && improvementBadge(study.improvement_pct[key])}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tags */}
      {study.tags && study.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {study.tags.map((tag) => (
            <span
              key={tag}
              className="px-1.5 py-0.5 rounded-full bg-muted text-[10px] text-muted-foreground"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main Component ───────────────────────────────────────────────────────────

export default function EvidenceLibraryTab() {
  const { accountId } = useParams<{ accountId: string }>();
  const { data: account, isLoading: accountLoading } = useAccount(accountId ?? null);

  const [searchQuery, setSearchQuery] = useState("");
  const [industryFilter, setIndustryFilter] = useState<string>("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [railMode, setRailMode] = useState<RightRailMode>("detail");

  // Use search when query is present, otherwise list all
  const searchHook = useEvidenceSearch();
  const { data: allStudies, isLoading: listLoading } = useCaseStudies(
    { industry: industryFilter || undefined }
  );

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "evidence-library",
    accountName: account?.name ?? "Account",
  });

  const isLoading = listLoading || searchHook.isPending;
  const studies: CaseStudy[] = allStudies?.case_studies ?? [];

  // Filter locally by search query when less than API threshold
  const filteredStudies = useMemo(() => {
    if (!searchQuery) return studies;
    const q = searchQuery.toLowerCase();
    return studies.filter(
      (s) =>
        s.title.toLowerCase().includes(q) ||
        s.customer_name?.toLowerCase().includes(q) ||
        s.industry?.toLowerCase().includes(q) ||
        s.challenge?.toLowerCase().includes(q) ||
        s.outcome?.toLowerCase().includes(q)
    );
  }, [studies, searchQuery]);

  const selected = filteredStudies.find((s) => s.id === selectedId) ?? null;

  // Compute stats
  const totalMetrics = filteredStudies.reduce(
    (sum, s) => sum + Object.keys(s.improvement_pct ?? {}).length,
    0
  );
  const industries = useMemo(
    () => Array.from(new Set(filteredStudies.map((s) => s.industry).filter(Boolean))),
    [filteredStudies]
  );
  const avgImprovement = useMemo(() => {
    const improvements = filteredStudies
      .flatMap((s) => Object.values(s.improvement_pct ?? {}))
      .filter((v): v is number => v != null);
    return improvements.length
      ? improvements.reduce((a, b) => a + b, 0) / improvements.length
      : 0;
  }, [filteredStudies]);

  if (!accountId) {
    return <AccountRequiredGuard accountId={accountId} />;
  }

  if (accountLoading) {
    return <CenteredLoader message="Loading account…" />;
  }

  if (!account) {
    return <div className="p-6 text-sm text-destructive">Account not found.</div>;
  }

  return (
    <IntelligenceShell
      account={{
        accountName: account.name,
        industry: account.industry ?? "Unknown",
        revenue: account.annual_revenue
          ? `$${account.annual_revenue.toLocaleString()}`
          : "N/A",
      }}
      rightRail={
        <RightRail
          mode={railMode}
          onModeChange={setRailMode}
          activeTab="evidence-library"
          detailContent={
            selected ? (
              <EvidenceDetailPanel study={selected} />
            ) : (
              <div className="text-xs text-muted-foreground">
                Select a case study to view details and outcomes.
              </div>
            )
          }
          messages={messages}
          onSendMessage={sendMessage}
          suggestedActions={suggestedActions}
            steps={steps}
            isStreaming={isStreaming}
            runMetadata={metadata}
        />
      }
    >
      {/* Header metrics */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <MetricCard label="Case Studies" value={String(filteredStudies.length)} />
        <MetricCard label="Tracked Metrics" value={String(totalMetrics)} />
        <MetricCard
          label="Avg Improvement"
          value={`${avgImprovement > 0 ? "+" : ""}${avgImprovement.toFixed(0)}%`}
        />
        <MetricCard label="Industries" value={String(industries.length)} />
      </div>

      {/* Search & filter bar */}
      <div className="flex items-center gap-3 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search evidence library…"
            className="w-full pl-9 pr-3 py-2 rounded-md border border-border bg-background text-xs focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        {/* Industry filter */}
        <div className="flex items-center gap-1">
          <Filter size={12} className="text-muted-foreground" />
          <select
            value={industryFilter}
            onChange={(e) => setIndustryFilter(e.target.value)}
            className="px-2 py-1.5 rounded border border-border bg-background text-[10px] focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">All Industries</option>
            {industries.map((ind) => (
              <option key={ind} value={ind}>{ind}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Evidence list */}
      {isLoading ? (
        <div className="flex items-center justify-center h-32 gap-2 text-sm text-muted-foreground">
          <Loader2 size={16} className="animate-spin" />
          Searching evidence library…
        </div>
      ) : filteredStudies.length === 0 ? (
        <SectionCard title="Evidence Library">
          <div className="text-center py-8">
            <BookOpen size={32} className="mx-auto text-muted-foreground mb-3" />
            <p className="text-sm text-muted-foreground mb-2">
              {searchQuery
                ? "No case studies match your search."
                : "No case studies available yet."}
            </p>
            <p className="text-xs text-muted-foreground">
              {searchQuery
                ? "Try broadening your search terms."
                : "Add case studies through the Evidence API to build your library."}
            </p>
          </div>
        </SectionCard>
      ) : (
        <SectionCard title={`Evidence Library (${filteredStudies.length})`}>
          <div className="space-y-1">
            {filteredStudies.map((study) => (
              <EvidenceCard
                key={study.id}
                study={study}
                isSelected={selectedId === study.id}
                onSelect={() => setSelectedId(study.id)}
              />
            ))}
          </div>
        </SectionCard>
      )}
    </IntelligenceShell>
  );
}
