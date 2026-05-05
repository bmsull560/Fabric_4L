/**
 * Studio Competitive Tab — DIL-native
 *
 * Competitive intelligence surface within the Value Studio context.
 * Uses DIL competitive intel hooks for landscape analysis and battlecards.
 */
import { useState } from "react";
import { useParams } from "react-router-dom";
import {
  Swords,
  Shield,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import ValueStudioShellComponent from "@/components/workspace/ValueStudioShell";
import RightRail, {
  type RightRailMode,
} from "@/components/workspace/RightRail";
import { SectionCard, MetricCard, Btn } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
import { CenteredLoader } from "@/components/CenteredLoader";
import {
  useCompetitors,
  useLandscape,
  useBattlecards,
  useWinLossSummary,
  type Competitor,
  type LandscapeEntry,
  type Battlecard,
  type WinLossSummary,
} from "@/hooks/useCompetitiveIntel";

// ── Threat Badge ───────────────────────────────────────────────────────────────
const THREAT_COLORS: Record<string, string> = {
  high: "bg-red-100 text-red-700",
  medium: "bg-orange-100 text-orange-700",
  low: "bg-green-100 text-green-700",
};

function ThreatBadge({ level }: { level: string }) {
  return (
    <span
      className={cn(
        "text-[10px] px-1.5 py-0.5 rounded font-semibold",
        THREAT_COLORS[level.toLowerCase()] ?? "bg-gray-100 text-gray-600"
      )}
    >
      {level}
    </span>
  );
}

function getThreatLevel(entry?: LandscapeEntry): string {
  if (!entry) return "No data";
  if (entry.win_rate < 0.35 || entry.overlap_score >= 0.75) return "High";
  if (entry.win_rate < 0.6 || entry.overlap_score >= 0.4) return "Medium";
  return "Low";
}

function getBattlecardDifferentiators(bc: Battlecard): string[] {
  return [...(bc.differentiators ?? []), ...(bc.key_differentiators ?? [])];
}

function formatObjectionHandlers(
  handlers: Battlecard["objection_handlers"]
): Array<{ label: string; value: string }> {
  if (!handlers) return [];

  if (Array.isArray(handlers)) {
    return handlers.flatMap(handler => {
      if (typeof handler === "string") {
        const [label, ...valueParts] = handler.split(":");
        return [
          {
            label: valueParts.length > 0 ? label.trim() : "Objection",
            value:
              valueParts.length > 0 ? valueParts.join(":").trim() : handler,
          },
        ];
      }

      return Object.entries(handler).map(([label, value]) => ({
        label,
        value: String(value),
      }));
    });
  }

  return Object.entries(handlers).map(([label, value]) => ({
    label,
    value: String(value),
  }));
}

// ── Competitor Row ─────────────────────────────────────────────────────────────
function CompetitorRow({
  competitor,
  selected,
  onClick,
}: {
  competitor: Competitor;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-4 w-full px-3 py-3 rounded-md text-left",
        selected ? "bg-primary/5 ring-1 ring-primary/20" : "hover:bg-muted/50"
      )}
    >
      <Swords size={14} className="text-muted-foreground shrink-0" />
      <div className="flex-1 min-w-0">
        <span className="text-[12px] font-medium">{competitor.name}</span>
        <div className="text-[10px] text-muted-foreground">
          {competitor.market_position} · {competitor.pricing_tier}
        </div>
      </div>
      <ThreatBadge level={competitor.market_position ?? "medium"} />
    </button>
  );
}

// ── Battlecard Panel ───────────────────────────────────────────────────────────
function BattlecardPanel({ battlecards }: { battlecards: Battlecard[] }) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (battlecards.length === 0) {
    return (
      <div className="text-[12px] text-muted-foreground py-4">
        No battlecards for this competitor yet.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {battlecards.map(bc => {
        const expanded = expandedId === bc.id;
        const differentiators = getBattlecardDifferentiators(bc);
        const objectionHandlers = formatObjectionHandlers(
          bc.objection_handlers
        );
        return (
          <div key={bc.id} className="border border-border rounded-md">
            <button
              onClick={() => setExpandedId(expanded ? null : bc.id)}
              className="flex items-center gap-3 w-full px-3 py-2.5 text-left"
            >
              <Shield size={13} className="text-primary shrink-0" />
              <span className="text-[12px] font-medium flex-1">
                {bc.competitor_id} — {bc.product_id}
              </span>
              {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </button>
            {expanded && (
              <div className="px-3 pb-3 space-y-2 text-[11px]">
                {differentiators.length > 0 && (
                  <div>
                    <p className="font-semibold text-green-600 mb-1">
                      Key Differentiators
                    </p>
                    <ul className="list-disc pl-4 space-y-0.5 text-muted-foreground">
                      {differentiators.map((d: string, i: number) => (
                        <li key={i}>{d}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {objectionHandlers.length > 0 && (
                  <div>
                    <p className="font-semibold text-red-600 mb-1">
                      Objection Handlers
                    </p>
                    <ul className="list-disc pl-4 space-y-0.5 text-muted-foreground">
                      {objectionHandlers.map(({ label, value }, i: number) => (
                        <li key={i}>
                          <strong>{label}:</strong> {value}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {bc.talk_tracks && bc.talk_tracks.length > 0 && (
                  <div>
                    <p className="font-semibold text-primary mb-1">
                      Talk Tracks
                    </p>
                    <ul className="list-disc pl-4 space-y-0.5 text-muted-foreground">
                      {bc.talk_tracks.map((t: string, i: number) => (
                        <li key={i}>{t}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function StudioCompetitiveTab() {
  const { accountId } = useParams<{ accountId: string }>();
  const { data: account, isLoading: accountLoading } = useAccount(
    accountId ?? null
  );
  const { data: competitorsData } = useCompetitors();
  const { data: landscapeData } = useLandscape();
  const { data: winLossData } = useWinLossSummary();
  const [selectedCompetitor, setSelectedCompetitor] =
    useState<Competitor | null>(null);
  const [railMode, setRailMode] = useState<RightRailMode>("agent");

  // Fetch battlecards for selected competitor
  const { data: battlecardsData } = useBattlecards(
    selectedCompetitor?.id ?? null
  );

  const {
    messages,
    sendMessage,
    suggestedActions,
    steps,
    isStreaming,
    metadata,
  } = useAgentEvents({
    activeTab: "competitive",
    accountName: account?.name ?? "Account",
  });

  const competitors = competitorsData?.competitors ?? [];
  const landscape = landscapeData?.landscape ?? [];
  const winLoss = winLossData?.competitors ?? [];
  const battlecards = battlecardsData ?? [];

  // Aggregate win/loss stats
  const totalWins = winLoss.reduce((s, w) => s + (w.wins ?? 0), 0);
  const totalLosses = winLoss.reduce((s, w) => s + (w.losses ?? 0), 0);
  const overallWinRate =
    totalWins + totalLosses > 0
      ? Math.round((totalWins / (totalWins + totalLosses)) * 100)
      : 0;

  if (!accountId) {
    return <AccountRequiredGuard accountId={accountId} />;
  }

  if (accountLoading) {
    return <CenteredLoader message="Loading account…" />;
  }

  if (!account) {
    return (
      <div className="p-6 text-sm text-destructive">Account not found.</div>
    );
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
          activeTab="competitive"
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
        <MetricCard label="Competitors" value={String(competitors.length)} />
        <MetricCard label="Win Rate" value={`${overallWinRate}%`} />
        <MetricCard
          label="Wins / Losses"
          value={`${totalWins} / ${totalLosses}`}
        />
        <MetricCard
          label="Threat Level"
          value={
            landscape.length > 0
              ? getThreatLevel(landscape[0])
              : competitors.length > 0
                ? "Assessed"
                : "No data"
          }
        />
      </div>

      {/* Two-column layout: competitors list + battlecards */}
      <div className="grid grid-cols-[1fr_1fr] gap-4">
        {/* Competitors List */}
        <SectionCard title="Competitive Landscape">
          {competitors.length === 0 ? (
            <div className="text-[12px] text-muted-foreground py-4">
              No competitors tracked yet. Add competitors from the Intelligence
              Workspace.
            </div>
          ) : (
            <div className="space-y-1">
              {competitors.map((c: Competitor) => (
                <CompetitorRow
                  key={c.id}
                  competitor={c}
                  selected={selectedCompetitor?.id === c.id}
                  onClick={() => setSelectedCompetitor(c)}
                />
              ))}
            </div>
          )}
        </SectionCard>

        {/* Battlecards */}
        <SectionCard
          title={
            selectedCompetitor
              ? `Battlecards: ${selectedCompetitor.name}`
              : "Battlecards"
          }
        >
          {selectedCompetitor ? (
            <BattlecardPanel battlecards={battlecards} />
          ) : (
            <div className="text-[12px] text-muted-foreground py-4">
              Select a competitor to view battlecards.
            </div>
          )}
        </SectionCard>
      </div>

      {/* Win/Loss by Competitor */}
      {winLoss.length > 0 && (
        <SectionCard title="Win/Loss by Competitor" className="mt-4">
          <div className="space-y-2">
            {winLoss.map((w, i) => {
              const wr =
                (w.wins ?? 0) + (w.losses ?? 0) > 0
                  ? Math.round(
                      ((w.wins ?? 0) / ((w.wins ?? 0) + (w.losses ?? 0))) * 100
                    )
                  : 0;
              return (
                <div
                  key={i}
                  className="flex items-center gap-4 px-3 py-2 border border-border rounded-md text-[12px]"
                >
                  <span className="font-medium flex-1">
                    {w.competitor.name ?? "Unknown competitor"}
                  </span>
                  <div className="flex items-center gap-1">
                    <TrendingUp size={11} className="text-green-600" />
                    <span>{w.wins ?? 0}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <TrendingDown size={11} className="text-red-600" />
                    <span>{w.losses ?? 0}</span>
                  </div>
                  <span
                    className={cn(
                      "font-semibold",
                      wr >= 50 ? "text-green-600" : "text-red-600"
                    )}
                  >
                    {wr}%
                  </span>
                </div>
              );
            })}
          </div>
        </SectionCard>
      )}
    </ValueStudioShellComponent>
  );
}
