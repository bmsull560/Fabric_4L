/**
 * Value Studio → Value Model Tab
 *
 * Quantified business case: the CFO-grade financial model.
 * Shows the value of the vendor's solution broken down by driver,
 * with adjustable variables and scenario toggling.
 *
 * Migrated from: Stage3Modeling (financial logic) + Calculator
 */
import { useState } from "react";
import { useParams } from "wouter";
import { Calculator, TrendingUp, TrendingDown, Settings2 } from "lucide-react";
import ValueStudioShellComponent from "@/components/workspace/ValueStudioShell";
import RightRail, { type RightRailMode, type AgentMessage } from "@/components/workspace/RightRail";
import { SectionCard, MetricCard, Btn } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";

// ── Demo Data ─────────────────────────────────────────────────────────────────

const DEMO_ACCOUNT = {
  accountName: "Meridian Automotive Components",
  industry: "Manufacturing",
  revenue: "$4.2B",
};

type Scenario = "conservative" | "expected" | "optimistic";

interface ValueLine {
  id: string;
  driver: string;
  category: "hard" | "strategic";
  conservative: number;
  expected: number;
  optimistic: number;
  source: string;
}

const DEMO_VALUE_LINES: ValueLine[] = [
  { id: "v1", driver: "Avoided New Hires (85 assemblers)",    category: "hard",      conservative: 3200000, expected: 4250000, optimistic: 5100000, source: "Action Plan #1" },
  { id: "v2", driver: "Scrap & Rework Reduction",             category: "hard",      conservative: 680000,  expected: 890000,  optimistic: 1100000, source: "Action Plan #2" },
  { id: "v3", driver: "Energy Savings (automated idle mgmt)",  category: "hard",      conservative: 320000,  expected: 480000,  optimistic: 620000,  source: "Action Plan #1" },
  { id: "v4", driver: "Changeover Time Reduction",            category: "hard",      conservative: 280000,  expected: 380000,  optimistic: 510000,  source: "Action Plan #3" },
  { id: "v5", driver: "Recall Prevention",                    category: "strategic", conservative: 400000,  expected: 700000,  optimistic: 1200000, source: "Action Plan #2" },
  { id: "v6", driver: "Throughput Uplift (12% capacity gain)", category: "strategic", conservative: 1800000, expected: 2400000, optimistic: 3100000, source: "Action Plan #1" },
];

const SCENARIO_LABELS: Record<Scenario, string> = {
  conservative: "Conservative",
  expected:     "Expected",
  optimistic:   "Optimistic",
};

function formatCurrency(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n}`;
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function ValueModelTab() {
  const params = useParams<{ accountId: string }>();
  const [scenario, setScenario] = useState<Scenario>("expected");
  const [showStrategic, setShowStrategic] = useState(true);
  const [railMode, setRailMode] = useState<RightRailMode>("agent");
  const [messages, setMessages] = useState<AgentMessage[]>([
    {
      id: "1", role: "agent",
      content: "The value model is built from 3 accepted recommendations. Total expected value: $9.10M/yr. Hard savings: $5.99M/yr. Strategic value: $3.10M/yr.",
      timestamp: "Just now",
    },
  ]);

  const handleSendMessage = (msg: string) => {
    setMessages((prev) => [
      ...prev,
      { id: `u-${Date.now()}`, role: "user", content: msg, timestamp: "Now" },
    ]);
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { id: `a-${Date.now()}`, role: "agent", content: "Recalculating the model with your adjustments…", timestamp: "Now" },
      ]);
    }, 800);
  };

  const visibleLines = showStrategic
    ? DEMO_VALUE_LINES
    : DEMO_VALUE_LINES.filter((l) => l.category === "hard");

  const total = visibleLines.reduce((s, l) => s + l[scenario], 0);
  const hardTotal = DEMO_VALUE_LINES.filter((l) => l.category === "hard").reduce((s, l) => s + l[scenario], 0);
  const strategicTotal = DEMO_VALUE_LINES.filter((l) => l.category === "strategic").reduce((s, l) => s + l[scenario], 0);

  const rightRail = (
    <RightRail
      mode={railMode}
      onModeChange={setRailMode}
      activeTab="value-model"
      messages={messages}
      onSendMessage={handleSendMessage}
      suggestedActions={[
        { label: "Adjust variables", onClick: () => {} },
        { label: "Compare scenarios", onClick: () => {} },
        { label: "Export to Excel", onClick: () => {} },
      ]}
    />
  );

  return (
    <ValueStudioShellComponent account={DEMO_ACCOUNT} rightRail={rightRail}>
      {/* Summary metrics */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <MetricCard label="Total Annual Value" value={formatCurrency(total)} trend={`${SCENARIO_LABELS[scenario]} scenario`} trendUp />
        <MetricCard label="Hard Savings" value={formatCurrency(hardTotal)} trend="Budget-impacting" trendUp />
        <MetricCard label="Strategic Value" value={formatCurrency(strategicTotal)} trend="Risk avoidance" />
        <MetricCard label="Payback Period" value="8.2 mo" trend="At expected scenario" trendUp />
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {(Object.keys(SCENARIO_LABELS) as Scenario[]).map((s) => (
            <button
              key={s}
              onClick={() => setScenario(s)}
              className={cn(
                "px-3 py-1.5 text-[11px] font-semibold rounded-md transition-colors",
                scenario === s
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:text-foreground"
              )}
            >
              {SCENARIO_LABELS[s]}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-1.5 text-[11px] text-muted-foreground cursor-pointer">
            <input
              type="checkbox"
              checked={showStrategic}
              onChange={(e) => setShowStrategic(e.target.checked)}
              className="rounded border-border"
            />
            Include strategic value
          </label>
          <Btn variant="outline" className="gap-1.5">
            <Settings2 size={12} />
            Variables
          </Btn>
        </div>
      </div>

      {/* Value lines table */}
      <SectionCard title="Value Breakdown">
        {/* Table header */}
        <div className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-4 px-3 py-2 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider border-b border-border">
          <span>Value Driver</span>
          <span className="w-20 text-right">Conservative</span>
          <span className="w-20 text-right">Expected</span>
          <span className="w-20 text-right">Optimistic</span>
          <span className="w-20 text-right">Source</span>
        </div>

        {/* Value rows */}
        {visibleLines.map((line) => (
          <div
            key={line.id}
            className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-4 px-3 py-3 text-[12px] border-b border-border last:border-0 hover:bg-muted/30 transition-colors"
          >
            <div className="flex items-center gap-2">
              <div className={cn(
                "w-1.5 h-1.5 rounded-full shrink-0",
                line.category === "hard" ? "bg-primary" : "bg-purple-500"
              )} />
              <span className="text-foreground font-medium">{line.driver}</span>
              {line.category === "strategic" && (
                <span className="text-[9px] font-semibold uppercase tracking-wider text-purple-600 bg-purple-100 dark:bg-purple-900/30 px-1.5 py-0.5 rounded">
                  Strategic
                </span>
              )}
            </div>
            <span className={cn("w-20 text-right", scenario === "conservative" ? "font-semibold text-foreground" : "text-muted-foreground")}>
              {formatCurrency(line.conservative)}
            </span>
            <span className={cn("w-20 text-right", scenario === "expected" ? "font-semibold text-foreground" : "text-muted-foreground")}>
              {formatCurrency(line.expected)}
            </span>
            <span className={cn("w-20 text-right", scenario === "optimistic" ? "font-semibold text-foreground" : "text-muted-foreground")}>
              {formatCurrency(line.optimistic)}
            </span>
            <span className="w-20 text-right text-[10px] text-muted-foreground">{line.source}</span>
          </div>
        ))}

        {/* Total row */}
        <div className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-4 px-3 py-3 text-[12px] font-bold border-t-2 border-border bg-muted/30">
          <span className="text-foreground">Total Annual Value</span>
          <span className={cn("w-20 text-right", scenario === "conservative" ? "text-primary" : "text-muted-foreground")}>
            {formatCurrency(visibleLines.reduce((s, l) => s + l.conservative, 0))}
          </span>
          <span className={cn("w-20 text-right", scenario === "expected" ? "text-primary" : "text-muted-foreground")}>
            {formatCurrency(visibleLines.reduce((s, l) => s + l.expected, 0))}
          </span>
          <span className={cn("w-20 text-right", scenario === "optimistic" ? "text-primary" : "text-muted-foreground")}>
            {formatCurrency(visibleLines.reduce((s, l) => s + l.optimistic, 0))}
          </span>
          <span className="w-20" />
        </div>
      </SectionCard>
    </ValueStudioShellComponent>
  );
}
