/**
 * CompetitiveTab — Competitive Intelligence Dashboard
 *
 * DIL-backed tab wired to the Competitive Intelligence Analyzer (L3).
 * Uses: useCompetitors, useLandscape, useBattlecards, useWinLossSummary
 *       from useCompetitiveIntel hook.
 *
 * Shows competitor landscape, win/loss records, battlecards, and threat analysis.
 */
import { useState, useMemo } from "react";
import { useParams } from "wouter";
import {
  Swords,
  Trophy,
  Shield,
  AlertTriangle,
  ChevronRight,
  Loader2,
  BarChart3,
  Target,
  XCircle,
} from "lucide-react";
import IntelligenceShell from "@/components/workspace/IntelligenceShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { SectionCard, MetricCard } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";
import {
  useCompetitors,
  useLandscape,
  useBattlecards,
  useWinLossSummary,
  type Competitor,
  type Battlecard,
  type LandscapeEntry,
} from "@/hooks/useCompetitiveIntel";

// ── Helpers ──────────────────────────────────────────────────────────────────

function threatColor(level: string): string {
  switch (level) {
    case "high":     return "text-red-600 bg-red-50";
    case "medium":   return "text-amber-600 bg-amber-50";
    case "low":      return "text-green-600 bg-green-50";
    default:         return "text-muted-foreground bg-muted";
  }
}

function winRateColor(rate: number): string {
  if (rate >= 0.6) return "text-green-600";
  if (rate >= 0.4) return "text-amber-600";
  return "text-red-600";
}

// ── Competitor Row ───────────────────────────────────────────────────────────

function CompetitorRow({
  competitor,
  landscapeEntry,
  isSelected,
  onSelect,
}: {
  competitor: Competitor;
  landscapeEntry?: LandscapeEntry;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const winRate = landscapeEntry?.win_rate ?? 0;
  const threat = landscapeEntry?.threat_level ?? "unknown";

  return (
    <button
      onClick={onSelect}
      className={cn(
        "flex items-center gap-4 w-full px-4 py-3 rounded-md text-left transition-colors",
        isSelected ? "bg-primary/5 ring-1 ring-primary/20" : "hover:bg-muted/50"
      )}
    >
      <Swords size={14} className="text-muted-foreground shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="text-xs font-semibold">{competitor.name}</div>
        <div className="text-[10px] text-muted-foreground">
          {competitor.market_position ?? "Unknown position"} · {competitor.pricing_tier ?? "Unknown tier"}
        </div>
      </div>
      <div className="flex items-center gap-3 shrink-0">
        {/* Win rate from landscape */}
        <div className="flex items-center gap-1">
          <Trophy size={10} className={winRateColor(winRate)} />
          <span className={cn("text-[10px] font-semibold", winRateColor(winRate))}>
            {Math.round(winRate * 100)}%
          </span>
        </div>
        {/* Threat level from landscape */}
        <span className={cn("px-1.5 py-0.5 rounded text-[10px] font-semibold", threatColor(threat))}>
          {threat}
        </span>
        <ChevronRight size={12} className="text-muted-foreground" />
      </div>
    </button>
  );
}

// ── Battlecard Panel ─────────────────────────────────────────────────────────

function BattlecardPanel({ battlecards }: { battlecards: Battlecard[] }) {
  if (!battlecards.length) {
    return (
      <div className="text-xs text-muted-foreground">
        No battlecards available for this competitor.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {battlecards.map((bc) => (
        <div key={bc.id} className="space-y-2">
          <div className="flex items-center gap-2">
            <Shield size={12} className="text-primary" />
            <span className="text-xs font-semibold">Product {bc.product_id}</span>
          </div>

          {/* Key differentiators */}
          {bc.key_differentiators && bc.key_differentiators.length > 0 && (
            <div className="space-y-1">
              <span className="text-[10px] font-semibold text-muted-foreground">Differentiators</span>
              {bc.key_differentiators.map((d: string, i: number) => (
                <div key={i} className="flex items-start gap-1.5 text-[10px]">
                  <Target size={8} className="mt-0.5 text-green-500 shrink-0" />
                  <span>{d}</span>
                </div>
              ))}
            </div>
          )}

          {/* Talk tracks */}
          {bc.talk_tracks && bc.talk_tracks.length > 0 && (
            <div className="space-y-1">
              <span className="text-[10px] font-semibold text-muted-foreground">Talk Tracks</span>
              {bc.talk_tracks.map((t: string, i: number) => (
                <div key={i} className="flex items-start gap-1.5 text-[10px]">
                  <AlertTriangle size={8} className="mt-0.5 text-amber-500 shrink-0" />
                  <span>{t}</span>
                </div>
              ))}
            </div>
          )}

          {/* Objection handlers */}
          {bc.objection_handlers && Object.keys(bc.objection_handlers).length > 0 && (
            <div className="space-y-1">
              <span className="text-[10px] font-semibold text-muted-foreground">Objection Handlers</span>
              {Object.entries(bc.objection_handlers).map(([objection, response], i) => (
                <div key={i} className="text-[10px] border-l-2 border-primary/30 pl-2">
                  <div className="font-semibold text-foreground">"{objection}"</div>
                  <div className="text-muted-foreground mt-0.5">{response}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Main Component ───────────────────────────────────────────────────────────

export default function CompetitiveTab() {
  const { accountId } = useParams<{ accountId: string }>();
  const { data: account } = useAccount(accountId ?? null);
  const { data: competitorsData, isLoading: competitorsLoading } = useCompetitors();
  const { data: landscape, isLoading: landscapeLoading } = useLandscape();
  const { data: winLossRecords } = useWinLossSummary();

  // Aggregate win/loss stats from array of per-competitor summaries
  const winLossAgg = useMemo(() => {
    if (!winLossRecords || winLossRecords.length === 0) return null;
    const totalWins = winLossRecords.reduce((s, r) => s + r.wins, 0);
    const totalLosses = winLossRecords.reduce((s, r) => s + r.losses, 0);
    const total = totalWins + totalLosses;
    return { wins: totalWins, losses: totalLosses, win_rate: total > 0 ? totalWins / total : 0 };
  }, [winLossRecords]);

  const [selectedCompetitorId, setSelectedCompetitorId] = useState<string | null>(null);
  const [railMode, setRailMode] = useState<RightRailMode>("detail");

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "competitive",
    accountName: account?.name ?? "Account",
  });

  // Fetch battlecards for selected competitor
  const { data: battlecardsData } = useBattlecards(selectedCompetitorId);

  const isLoading = competitorsLoading || landscapeLoading;
  const competitors: Competitor[] = competitorsData?.competitors ?? [];
  const landscapeEntries: LandscapeEntry[] = landscape ?? [];
  const battlecards: Battlecard[] = battlecardsData ?? [];
  const selectedCompetitor = competitors.find((c) => c.id === selectedCompetitorId) ?? null;

  // Build a lookup from competitor_id to landscape entry
  const landscapeMap = new Map(landscapeEntries.map((e) => [e.competitor_id, e]));

  // Landscape stats
  const avgWinRate = landscapeEntries.length
    ? landscapeEntries.reduce((sum, e) => sum + e.win_rate, 0) / landscapeEntries.length
    : 0;
  const topThreatEntry = landscapeEntries.find((e) => e.threat_level === "high");
  const topThreat = topThreatEntry?.competitor_name ?? "None";
  const totalCompetitors = competitors.length;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 gap-2 text-sm text-muted-foreground">
        <Loader2 size={16} className="animate-spin" />
        Loading competitive intelligence…
      </div>
    );
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
          activeTab="competitive"
          detailContent={
            selectedCompetitor ? (
              <div className="space-y-3">
                <h3 className="text-sm font-bold">{selectedCompetitor.name}</h3>
                <p className="text-[10px] text-muted-foreground">
                  {selectedCompetitor.market_position} · {selectedCompetitor.pricing_tier}
                </p>
                <BattlecardPanel battlecards={battlecards} />
              </div>
            ) : (
              <div className="text-xs text-muted-foreground">
                Select a competitor to view battlecards.
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
        <MetricCard label="Competitors" value={String(totalCompetitors)} />
        <MetricCard
          label="Avg Win Rate"
          value={`${Math.round(avgWinRate * 100)}%`}
        />
        <MetricCard
          label="Top Threat"
          value={topThreat}
        />
        <MetricCard
          label="Battlecards"
          value={String(battlecards.length)}
        />
      </div>

      {/* Competitor list */}
      {competitors.length === 0 ? (
        <SectionCard title="Competitive Landscape">
          <div className="text-center py-8">
            <Swords size={32} className="mx-auto text-muted-foreground mb-3" />
            <p className="text-sm text-muted-foreground mb-2">
              No competitors tracked yet.
            </p>
            <p className="text-xs text-muted-foreground">
              Add competitors through the Intelligence API to start building battlecards.
            </p>
          </div>
        </SectionCard>
      ) : (
        <>
          <SectionCard title={`Competitors (${totalCompetitors})`} className="mb-4">
            <div className="space-y-1">
              {competitors.map((comp) => (
                <CompetitorRow
                  key={comp.id}
                  competitor={comp}
                  landscapeEntry={landscapeMap.get(comp.id)}
                  isSelected={selectedCompetitorId === comp.id}
                  onSelect={() => setSelectedCompetitorId(comp.id)}
                />
              ))}
            </div>
          </SectionCard>

          {/* Win/Loss summary */}
          {winLossAgg && (
            <SectionCard title="Win/Loss Analysis">
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-1 text-center">
                  <Trophy size={16} className="mx-auto text-green-600" />
                  <div className="text-lg font-bold text-green-600">
                    {winLossAgg.wins}
                  </div>
                  <div className="text-[10px] text-muted-foreground">Wins</div>
                </div>
                <div className="space-y-1 text-center">
                  <XCircle size={16} className="mx-auto text-red-500" />
                  <div className="text-lg font-bold text-red-500">
                    {winLossAgg.losses}
                  </div>
                  <div className="text-[10px] text-muted-foreground">Losses</div>
                </div>
                <div className="space-y-1 text-center">
                  <BarChart3 size={16} className="mx-auto text-primary" />
                  <div className="text-lg font-bold text-primary">
                    {Math.round(winLossAgg.win_rate * 100)}%
                  </div>
                  <div className="text-[10px] text-muted-foreground">Overall Rate</div>
                </div>
              </div>
            </SectionCard>
          )}
        </>
      )}
    </IntelligenceShell>
  );
}
