/**
 * Studio Enrichment Tab — DIL-native
 *
 * Account enrichment surface within the Value Studio context.
 * Uses DIL enrichment hooks for multi-source data enrichment.
 */
import { useState } from "react";
import { useParams } from "react-router-dom";
import {
  Database,
  Globe,
  FileSearch,
  Users2,
  Newspaper,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import ValueStudioShellComponent from "@/components/workspace/ValueStudioShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { SectionCard, MetricCard, Btn } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import {
  useEnrichAccount,
  useEnrichmentStatus,
  useEnrichmentDetails,
  type EnrichmentResult,
  type EnrichmentCoverageStats,
} from "@/hooks/useEnrichment";

// ── Source Config ──────────────────────────────────────────────────────────────
const SOURCE_CONFIG: Record<
  string,
  { label: string; icon: typeof Database; description: string }
> = {
  sec_edgar: {
    label: "SEC EDGAR",
    icon: FileSearch,
    description: "Financial filings, revenue, risk factors",
  },
  web_crawl: {
    label: "Web Crawl",
    icon: Globe,
    description: "Technology stack, company overview",
  },
  domain_lookup: {
    label: "Domain Lookup",
    icon: Users2,
    description: "Executive contacts, org structure",
  },
  news_scan: {
    label: "News Scan",
    icon: Newspaper,
    description: "Recent news, press releases, events",
  },
};

// ── Source Card ─────────────────────────────────────────────────────────────────
function SourceCard({
  sourceKey,
  status,
}: {
  sourceKey: string;
  status?: { completed: boolean; data_points: number; last_run?: string };
}) {
  const config = SOURCE_CONFIG[sourceKey];
  if (!config) return null;
  const Icon = config.icon;
  const completed = status?.completed ?? false;

  return (
    <div
      className={cn(
        "border rounded-md p-4",
        completed ? "border-green-200 bg-green-50/50" : "border-border"
      )}
    >
      <div className="flex items-start gap-3">
        <Icon
          size={16}
          className={cn(
            completed ? "text-green-600" : "text-muted-foreground"
          )}
        />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h4 className="text-[12px] font-semibold">{config.label}</h4>
            {completed ? (
              <CheckCircle2 size={12} className="text-green-600" />
            ) : (
              <AlertCircle size={12} className="text-muted-foreground" />
            )}
          </div>
          <p className="text-[10px] text-muted-foreground mt-0.5">
            {config.description}
          </p>
          {status && (
            <div className="flex items-center gap-3 mt-2 text-[10px]">
              <span className="font-medium">
                {status.data_points} data points
              </span>
              {status.last_run && (
                <span className="text-muted-foreground">
                  Last: {new Date(status.last_run).toLocaleDateString()}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function StudioEnrichmentTab() {
  const { accountId } = useParams<{ accountId: string }>();
  const { data: account } = useAccount(accountId ?? null);
  const { data: statusData } = useEnrichmentStatus();
  const { data: enrichmentDetails } = useEnrichmentDetails(accountId ?? null);
  const enrichMutation = useEnrichAccount();
  const [railMode, setRailMode] = useState<RightRailMode>("agent");

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "enrichment",
    accountName: account?.name ?? "Account",
  });

  const coverageStats = statusData as EnrichmentCoverageStats | undefined;
  const enrichedSources = enrichmentDetails?.sources_used ?? [];
  const totalDataPoints = enrichmentDetails?.fields_updated?.length ?? 0;
  const completedSources = enrichedSources.length;

  const handleEnrich = (force: boolean = false) => {
    if (!accountId) return;
    enrichMutation.mutate({ accountId, params: force ? { force: true } : undefined });
  };

  if (!account)
    return (
      <div className="p-6 text-sm text-muted-foreground">Loading account…</div>
    );

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
          activeTab="enrichment"
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
      <div className="grid grid-cols-4 gap-4 mb-6">
        <MetricCard label="Data Sources" value={`${completedSources}/4`} />
        <MetricCard label="Data Points" value={String(totalDataPoints)} />
        <MetricCard
          label="Enrichment Status"
          value={enrichmentDetails ? "Enriched" : "Not Enriched"}
        />
        <MetricCard
          label="Last Enriched"
          value={
            enrichmentDetails?.enriched_at
              ? new Date(enrichmentDetails.enriched_at).toLocaleDateString()
              : "Never"
          }
        />
      </div>

      {/* Actions */}
      <div className="flex gap-3 mb-6">
        <Btn
          variant="primary"
          className="gap-1.5"
          onClick={() => handleEnrich(false)}
          disabled={enrichMutation.isPending}
        >
          {enrichMutation.isPending ? (
            <>
              <RefreshCw size={12} className="animate-spin" />
              Enriching...
            </>
          ) : (
            <>
              <Database size={12} />
              Enrich Account
            </>
          )}
        </Btn>
        <Btn
          variant="outline"
          className="gap-1.5"
          onClick={() => handleEnrich(true)}
          disabled={enrichMutation.isPending}
        >
          <RefreshCw size={12} />
          Force Re-enrich
        </Btn>
      </div>

      {/* Source Grid */}
      <SectionCard title="Data Sources">
        <div className="grid grid-cols-2 gap-3">
          {Object.keys(SOURCE_CONFIG).map((key) => (
            <SourceCard
              key={key}
              sourceKey={key}
              status={
                enrichedSources.includes(key)
                  ? { completed: true, data_points: 0 }
                  : undefined
              }
            />
          ))}
        </div>
      </SectionCard>

      {/* Enrichment result */}
      {enrichMutation.isSuccess && (
        <SectionCard title="Enrichment Complete" className="mt-4">
          <div className="flex items-center gap-2 text-green-600 text-[12px]">
            <CheckCircle2 size={14} />
            <span>Account data enriched successfully. Refresh to see updated data across all tabs.</span>
          </div>
        </SectionCard>
      )}

      {enrichMutation.isError && (
        <SectionCard title="Enrichment Error" className="mt-4">
          <div className="flex items-center gap-2 text-destructive text-[12px]">
            <AlertCircle size={14} />
            <span>Failed to enrich account. Please try again.</span>
          </div>
        </SectionCard>
      )}
    </ValueStudioShellComponent>
  );
}
