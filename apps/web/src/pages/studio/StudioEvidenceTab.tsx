/**
 * Studio Evidence Tab — DIL-native
 *
 * Evidence library surface within the Value Studio context.
 * Uses DIL evidence hooks for case study browsing and search.
 */
import { useState } from "react";
import { useParams } from "react-router-dom";
import {
  BookOpen,
  Search,
  TrendingUp,
  Building2,
  Tag,
  ExternalLink,
} from "lucide-react";
import ValueStudioShellComponent from "@/components/workspace/ValueStudioShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { SectionCard, MetricCard, Btn } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
import { CenteredLoader } from "@/components/CenteredLoader";
import {
  useCaseStudies,
  useEvidenceSearch,
  type CaseStudy,
  type CaseStudyListResponse,
  type EvidenceSearchResult,
} from "@/hooks/useEvidence";

// ── Case Study Card ────────────────────────────────────────────────────────────
function CaseStudyCard({
  study,
  selected,
  onClick,
}: {
  study: CaseStudy;
  selected: boolean;
  onClick: () => void;
}) {
  const improvementKeys = Object.keys(study.improvement_pct ?? {});
  const topImprovement =
    improvementKeys.length > 0
      ? study.improvement_pct[improvementKeys[0]]
      : null;

  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-start gap-3 w-full px-3 py-3 rounded-md text-left border",
        selected
          ? "bg-primary/5 border-primary/20"
          : "border-transparent hover:bg-muted/50"
      )}
    >
      <BookOpen size={14} className="text-primary shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <div className="text-[12px] font-medium truncate">{study.title}</div>
        <div className="flex items-center gap-2 mt-0.5">
          {study.industry && (
            <span className="text-[10px] text-muted-foreground flex items-center gap-1">
              <Building2 size={9} />
              {study.industry}
            </span>
          )}
          {study.product_ids && study.product_ids.length > 0 && (
            <span className="text-[10px] text-muted-foreground flex items-center gap-1">
              <Tag size={9} />
              {study.product_ids[0]}
            </span>
          )}
        </div>
        {topImprovement != null && (
          <div className="flex items-center gap-1 mt-1">
            <TrendingUp size={10} className="text-green-600" />
            <span className="text-[10px] font-semibold text-green-600">
              {topImprovement.toFixed(0)}% improvement
            </span>
          </div>
        )}
      </div>
    </button>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function StudioEvidenceTab() {
  const { accountId } = useParams<{ accountId: string }>();
  const { data: account, isLoading: accountLoading } = useAccount(accountId ?? null);
  const [railMode, setRailMode] = useState<RightRailMode>("agent");
  const [searchQuery, setSearchQuery] = useState("");
  const [industryFilter, setIndustryFilter] = useState("");
  const [selectedStudy, setSelectedStudy] = useState<CaseStudy | null>(null);

  // DIL data — use industry filter from account if available
  const { data: studiesData, isLoading } = useCaseStudies({
    industry: industryFilter || undefined,
  });
  const evidenceSearch = useEvidenceSearch();

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "evidence",
    accountName: account?.name ?? "Account",
  });

  const listResponse = studiesData as CaseStudyListResponse | undefined;
  const studies = listResponse?.case_studies ?? [];
  const totalCount = listResponse?.total ?? studies.length;

  // Collect unique industries for filter
  const industries = Array.from(
    new Set(studies.map((s: CaseStudy) => s.industry).filter(Boolean))
  ) as string[];

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
    <ValueStudioShellComponent
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
          detailContent={
            selectedStudy ? (
              <div className="space-y-3">
                <h3 className="text-sm font-bold">{selectedStudy.title}</h3>
                {selectedStudy.industry && (
                  <p className="text-xs text-muted-foreground">
                    {selectedStudy.industry}
                  </p>
                )}
                {selectedStudy.challenge && (
                  <div>
                    <p className="text-[11px] font-semibold mb-1">Challenge</p>
                    <p className="text-xs">{selectedStudy.challenge}</p>
                  </div>
                )}
                {selectedStudy.solution && (
                  <div>
                    <p className="text-[11px] font-semibold mb-1">Solution</p>
                    <p className="text-xs">{selectedStudy.solution}</p>
                  </div>
                )}
                {selectedStudy.outcome && (
                  <div>
                    <p className="text-[11px] font-semibold mb-1">Outcome</p>
                    <p className="text-xs">{selectedStudy.outcome}</p>
                  </div>
                )}
                {Object.keys(selectedStudy.improvement_pct ?? {}).length > 0 && (
                  <div>
                    <p className="text-[11px] font-semibold mb-1">Improvements</p>
                    <div className="space-y-1">
                      {Object.entries(selectedStudy.improvement_pct).map(
                        ([metric, pct]: [string, number], i: number) => (
                          <div
                            key={i}
                            className="text-[10px] border border-border rounded px-2 py-1"
                          >
                            <span className="font-medium">{metric}: </span>
                            <span className="text-green-600">
                              +{pct.toFixed(0)}%
                            </span>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : null
          }
          activeTab="evidence"
          messages={messages}
          onSendMessage={sendMessage}
          suggestedActions={suggestedActions}
            steps={steps}
            isStreaming={isStreaming}
            runMetadata={metadata}
        />
      }
    >
      {/* Metrics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <MetricCard label="Case Studies" value={String(totalCount)} />
        <MetricCard
          label="Industries Covered"
          value={String(industries.length)}
        />
        <MetricCard
          label="Account Industry Match"
          value={
            account.industry
              ? studies.some(
                  (s: CaseStudy) => s.industry === account.industry
                )
                ? "Yes"
                : "No matches"
              : "N/A"
          }
        />
      </div>

      {/* Search & Filter */}
      <div className="flex gap-3 mb-4">
        <div className="relative flex-1">
          <Search
            size={13}
            className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground"
          />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search evidence (min 3 characters)..."
            className="w-full text-xs border border-border rounded-md pl-8 pr-3 py-1.5"
          />
        </div>
        <select
          value={industryFilter}
          onChange={(e) => setIndustryFilter(e.target.value)}
          className="text-xs border border-border rounded-md px-2 py-1.5"
        >
          <option value="">All Industries</option>
          {industries.map((ind) => (
            <option key={ind} value={ind}>
              {ind}
            </option>
          ))}
          {account.industry && !industries.includes(account.industry) && (
            <option value={account.industry}>
              {account.industry} (account)
            </option>
          )}
        </select>
      </div>

      {/* Case Studies List */}
      <SectionCard title="Evidence Library">
        {isLoading ? (
          <div className="text-[12px] text-muted-foreground py-4">
            Loading case studies…
          </div>
        ) : studies.length === 0 ? (
          <div className="text-[12px] text-muted-foreground py-4">
            {searchQuery.length >= 3
              ? `No results for "${searchQuery}"`
              : "No case studies available. Add evidence from the Intelligence Workspace."}
          </div>
        ) : (
          <div className="space-y-1 max-h-[400px] overflow-y-auto">
            {studies.map((study: CaseStudy) => (
              <CaseStudyCard
                key={study.id}
                study={study}
                selected={selectedStudy?.id === study.id}
                onClick={() => setSelectedStudy(study)}
              />
            ))}
          </div>
        )}
      </SectionCard>
    </ValueStudioShellComponent>
  );
}
