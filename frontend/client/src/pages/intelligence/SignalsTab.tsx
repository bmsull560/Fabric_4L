/**
 * Intelligence → Signals Tab
 *
 * AI-surfaced pain signals ranked by confidence and estimated impact.
 * This is the default landing tab when entering Intelligence for an account.
 *
 * Migrated from: Stage1Discovery (pain point detection) + WorkflowIntelligence (signal ranking)
 */
import { useState } from "react";
import { useParams } from "wouter";
import { AlertTriangle, TrendingUp, Filter } from "lucide-react";
import IntelligenceShell from "@/components/workspace/IntelligenceShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentStream } from "@/hooks/useAgentStream";
import { SectionCard, Btn, MetricCard } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";

// ── Demo Data ─────────────────────────────────────────────────────────────────

const DEMO_ACCOUNT = {
  accountName: "Meridian Automotive Components",
  industry: "Manufacturing",
  revenue: "$4.2B",
};

interface Signal {
  id: string;
  name: string;
  category: string;
  confidence: number;
  impact: string;
  trend?: string;
}

const DEMO_SIGNALS: Signal[] = [
  { id: "s1", name: "Production Downtime",    category: "Operational",  confidence: 94, impact: "$2.4M/yr",     trend: "↑ 23% YoY" },
  { id: "s2", name: "Labor Shortage — Welders", category: "Workforce",  confidence: 91, impact: "12% capacity", trend: "↑ 8% YoY" },
  { id: "s3", name: "Quality Defect Rate",    category: "Quality",      confidence: 88, impact: "$890K/yr",     trend: "↑ 5% YoY" },
  { id: "s4", name: "Energy Cost Surge",      category: "Cost",         confidence: 85, impact: "$1.1M/yr",     trend: "↑ 18% YoY" },
  { id: "s5", name: "Supplier Delays",        category: "Supply Chain", confidence: 82, impact: "3–5 day slip", trend: "Stable" },
  { id: "s6", name: "Regulatory Compliance",  category: "Risk",         confidence: 78, impact: "Audit risk",   trend: "New" },
];

const CATEGORY_COLORS: Record<string, string> = {
  Operational:    "bg-red-500",
  Workforce:      "bg-orange-500",
  Quality:        "bg-yellow-500",
  Cost:           "bg-blue-500",
  "Supply Chain": "bg-purple-500",
  Risk:           "bg-pink-500",
};

// ── Component ─────────────────────────────────────────────────────────────────

export default function SignalsTab() {
  const params = useParams<{ accountId: string }>();
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);
  const [railMode, setRailMode] = useState<RightRailMode>("agent");
  const { messages, sendMessage, suggestedActions } = useAgentStream({
    activeTab: "signals",
    accountName: DEMO_ACCOUNT.accountName,
  });

  const handleSignalClick = (signal: Signal) => {
    setSelectedSignal(signal);
    setRailMode("detail");
  };

  // Detail panel for selected signal
  const detailContent = selectedSignal ? (
    <div className="space-y-4">
      <div>
        <div className="flex items-center gap-2 mb-2">
          <div className={cn("w-2.5 h-2.5 rounded-full", CATEGORY_COLORS[selectedSignal.category] || "bg-muted-foreground")} />
          <h3 className="text-[14px] font-bold text-foreground">{selectedSignal.name}</h3>
        </div>
        <span className="text-[10px] font-semibold uppercase tracking-wider text-destructive bg-destructive/10 px-2 py-0.5 rounded">
          {selectedSignal.category}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <div className="text-center p-2 bg-muted/50 rounded-md">
          <div className="text-[10px] text-muted-foreground uppercase">Confidence</div>
          <div className="text-[14px] font-bold text-foreground">{selectedSignal.confidence}%</div>
        </div>
        <div className="text-center p-2 bg-muted/50 rounded-md">
          <div className="text-[10px] text-muted-foreground uppercase">Impact</div>
          <div className="text-[14px] font-bold text-foreground">{selectedSignal.impact}</div>
        </div>
        <div className="text-center p-2 bg-muted/50 rounded-md">
          <div className="text-[10px] text-muted-foreground uppercase">Trend</div>
          <div className="text-[14px] font-bold text-foreground">{selectedSignal.trend}</div>
        </div>
      </div>

      <div>
        <h4 className="text-[12px] font-semibold text-foreground mb-1">Executive Hypothesis</h4>
        <p className="text-[11px] text-muted-foreground leading-relaxed">
          {DEMO_ACCOUNT.accountName} may be experiencing a widening operational performance gap
          driven by recurring unplanned downtime across its plant network. If confirmed, aging
          equipment, changeover inefficiency, and material-related interruptions are likely
          suppressing throughput, reducing labor productivity, and increasing cost pressure.
        </p>
      </div>

      <div>
        <h4 className="text-[12px] font-semibold text-foreground mb-2">Evidence Matches</h4>
        <div className="space-y-2">
          {[
            { source: "Case Study — Continental AG", match: 95, type: "High match" },
            { source: "Benchmark — Tier 1 Auto Average", match: 88, type: "High match" },
            { source: "ROI Calculator — Labor Efficiency", match: 82, type: "Medium match" },
          ].map((ev, i) => (
            <div key={i} className="flex items-center justify-between text-[11px] py-1.5 border-b border-border last:border-0">
              <span className="text-foreground">{ev.source}</span>
              <div className="flex items-center gap-2">
                <span className={cn(
                  "text-[10px] font-semibold",
                  ev.match >= 90 ? "text-green-600" : "text-orange-600"
                )}>
                  {ev.type}
                </span>
                <span className="text-muted-foreground">{ev.match}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="pt-2">
        <Btn variant="primary" className="w-full">Add to Model</Btn>
      </div>
    </div>
  ) : null;

  const rightRail = (
    <RightRail
      mode={railMode}
      onModeChange={setRailMode}
      detailContent={detailContent}
      activeTab="signals"
      messages={messages}
      onSendMessage={sendMessage}
      suggestedActions={suggestedActions}
    />
  );

  return (
    <IntelligenceShell account={DEMO_ACCOUNT} rightRail={rightRail}>
      {/* Summary metrics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <MetricCard label="Signals Detected" value="6" trend="$4.8M/yr total impact" trendUp />
        <MetricCard label="Avg Confidence" value="86%" trend="+3% from last scan" trendUp />
        <MetricCard label="Categories" value="6" trend="Across all domains" />
      </div>

      {/* Signal list */}
      <SectionCard title="Pain Signal List">
        <div className="flex items-center justify-between mb-3">
          <span className="text-[11px] text-muted-foreground">
            {DEMO_SIGNALS.length} detected · sorted by confidence
          </span>
          <Btn variant="outline" className="gap-1.5">
            <Filter size={12} />
            Filters
          </Btn>
        </div>

        {/* Table header */}
        <div className="grid grid-cols-[auto_1fr_auto_auto_auto] gap-4 px-3 py-2 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider border-b border-border">
          <span className="w-6">#</span>
          <span>Signal</span>
          <span className="w-24 text-right">Confidence</span>
          <span className="w-24 text-right">Impact</span>
          <span className="w-6" />
        </div>

        {/* Signal rows */}
        {DEMO_SIGNALS.map((signal, i) => (
          <button
            key={signal.id}
            onClick={() => handleSignalClick(signal)}
            className={cn(
              "grid grid-cols-[auto_1fr_auto_auto_auto] gap-4 px-3 py-3 text-[12px] border-b border-border last:border-0 w-full text-left transition-colors",
              selectedSignal?.id === signal.id
                ? "bg-primary/5"
                : "hover:bg-muted/50"
            )}
          >
            <span className="w-6 text-muted-foreground font-medium">{i + 1}</span>
            <div className="flex items-center gap-2">
              <div className={cn("w-1 h-6 rounded-full shrink-0", CATEGORY_COLORS[signal.category] || "bg-muted-foreground")} />
              <span className="font-medium text-foreground">{signal.name}</span>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                {signal.category}
              </span>
            </div>
            <span className="w-24 text-right text-foreground">{signal.confidence}%</span>
            <span className="w-24 text-right text-foreground">{signal.impact}</span>
            <span className="w-6 text-muted-foreground">›</span>
          </button>
        ))}
      </SectionCard>
    </IntelligenceShell>
  );
}
