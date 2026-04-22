/**
 * Value Studio → Action Plan Tab
 *
 * Product-anchored recommendations: maps validated prospect pain signals
 * to specific vendor product capabilities backed by proof points.
 * This is the "Why Us" argument.
 *
 * Each recommendation traces back to:
 *   - Prospect Pain (from Intelligence → Signals)
 *   - Root Driver (from Intelligence → Drivers)
 *   - Our Capability (from Context Engine)
 *   - Proof Points (from Intelligence → Evidence)
 *   - Projected Value (feeds into Value Model)
 */
import { useState } from "react";
import { useParams } from "wouter";
import { Zap, CheckCircle2, AlertCircle, ChevronDown, ChevronUp, FileText } from "lucide-react";
import ValueStudioShellComponent from "@/components/workspace/ValueStudioShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentStream } from "@/hooks/useAgentStream";
import { SectionCard, MetricCard, Btn } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";

// ── Demo Data ─────────────────────────────────────────────────────────────────

const DEMO_ACCOUNT = {
  accountName: "Meridian Automotive Components",
  industry: "Manufacturing",
  revenue: "$4.2B",
};

type Priority = "critical" | "high" | "medium";
type Confidence = "high" | "medium" | "low";

interface Recommendation {
  id: string;
  title: string;
  priority: Priority;
  prospectPain: string;
  rootDriver: string;
  ourCapability: string;
  proofPoints: { source: string; detail: string }[];
  projectedValue: string;
  confidence: Confidence;
  horizon: string;
}

const PRIORITY_CONFIG: Record<Priority, { label: string; color: string; bg: string }> = {
  critical: { label: "Critical", color: "text-red-600",    bg: "bg-red-500" },
  high:     { label: "High",     color: "text-orange-600", bg: "bg-orange-500" },
  medium:   { label: "Medium",   color: "text-yellow-600", bg: "bg-yellow-500" },
};

const CONFIDENCE_CONFIG: Record<Confidence, { label: string; color: string }> = {
  high:   { label: "High — multiple verified sources",   color: "text-green-600" },
  medium: { label: "Medium — partial verification",       color: "text-orange-600" },
  low:    { label: "Low — AI-inferred, needs validation", color: "text-muted-foreground" },
};

const DEMO_RECOMMENDATIONS: Recommendation[] = [
  {
    id: "r1", title: "Deploy Forge X1 Cobot Workcells on EV Assembly Lines 3 & 7",
    priority: "critical",
    prospectPain: "Production Downtime (94% confidence, $2.4M/yr impact)",
    rootDriver: "Aging manual weld stations (45% contribution)",
    ourCapability: "Forge X1 adaptive cobot workcells — replace manual stations with 24/7 automated cells",
    proofPoints: [
      { source: "Continental AG Case Study", detail: "23% cycle time reduction in 4 months" },
      { source: "Tier 1 Auto Benchmark", detail: "96% uptime vs. 81% for manual lines" },
    ],
    projectedValue: "$2.4M/yr",
    confidence: "high",
    horizon: "0–6 months",
  },
  {
    id: "r2", title: "Implement Predictive Maintenance on Weld Controllers",
    priority: "high",
    prospectPain: "Quality Defect Rate (88% confidence, $890K/yr impact)",
    rootDriver: "Torque inconsistency from operator fatigue (55% contribution)",
    ourCapability: "Forge X1 SenseLink module — real-time torque monitoring with closed-loop correction",
    proofPoints: [
      { source: "Continental AG Case Study", detail: "Zero torque-related recalls post-deployment" },
    ],
    projectedValue: "$890K/yr",
    confidence: "high",
    horizon: "3–9 months",
  },
  {
    id: "r3", title: "Rapid Changeover Kit for Multi-SKU Lines",
    priority: "medium",
    prospectPain: "Production Downtime — Changeover component (30% contribution)",
    rootDriver: "Manual tooling swaps averaging 45 min/SKU",
    ourCapability: "Forge X1 QuickSwap tooling system — automated changeover in under 12 minutes",
    proofPoints: [
      { source: "Internal Engineering Data", detail: "12 min average across 12 SKU variants" },
    ],
    projectedValue: "$380K/yr",
    confidence: "medium",
    horizon: "6–12 months",
  },
];

// ── Component ─────────────────────────────────────────────────────────────────

export default function ActionPlanTab() {
  const params = useParams<{ accountId: string }>();
  const [expandedId, setExpandedId] = useState<string | null>("r1");
  const [railMode, setRailMode] = useState<RightRailMode>("agent");
  const { messages, sendMessage, suggestedActions } = useAgentStream({
    activeTab: "action-plan",
    accountName: DEMO_ACCOUNT.accountName,
  });

  const totalValue = "$3.67M/yr";

  const rightRail = (
    <RightRail
      mode={railMode}
      onModeChange={setRailMode}
      activeTab="action-plan"
      messages={messages}
      onSendMessage={sendMessage}
      suggestedActions={suggestedActions}
    />
  );

  return (
    <ValueStudioShellComponent account={DEMO_ACCOUNT} rightRail={rightRail}>
      {/* Summary metrics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <MetricCard label="Recommendations" value={String(DEMO_RECOMMENDATIONS.length)} trend="Product-anchored" />
        <MetricCard label="Total Projected Value" value={totalValue} trend="Across all recommendations" trendUp />
        <MetricCard label="Avg Confidence" value="High" trend="2 of 3 fully verified" trendUp />
      </div>

      {/* Recommendation cards */}
      <div className="space-y-3">
        {DEMO_RECOMMENDATIONS.map((rec) => {
          const isExpanded = expandedId === rec.id;
          const pc = PRIORITY_CONFIG[rec.priority];
          const cc = CONFIDENCE_CONFIG[rec.confidence];

          return (
            <SectionCard key={rec.id}>
              {/* Header row */}
              <button
                onClick={() => setExpandedId(isExpanded ? null : rec.id)}
                className="flex items-start gap-3 w-full text-left"
              >
                <div className={cn("w-1 h-12 rounded-full shrink-0 mt-0.5", pc.bg)} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={cn("text-[10px] font-bold uppercase tracking-wider", pc.color)}>
                      {pc.label}
                    </span>
                    <span className="text-[10px] text-muted-foreground">·</span>
                    <span className="text-[10px] text-muted-foreground">{rec.horizon}</span>
                  </div>
                  <h3 className="text-[13px] font-bold text-foreground leading-snug">{rec.title}</h3>
                  <div className="flex items-center gap-4 mt-1.5">
                    <span className="text-[11px] font-semibold text-primary">{rec.projectedValue}</span>
                    <span className={cn("text-[10px] font-medium", cc.color)}>{rec.confidence} confidence</span>
                  </div>
                </div>
                {isExpanded ? (
                  <ChevronUp size={14} className="text-muted-foreground shrink-0 mt-1" />
                ) : (
                  <ChevronDown size={14} className="text-muted-foreground shrink-0 mt-1" />
                )}
              </button>

              {/* Expanded detail */}
              {isExpanded && (
                <div className="mt-4 pt-4 border-t border-border space-y-3 ml-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-[10px] font-semibold text-muted-foreground uppercase mb-1">Prospect Pain</div>
                      <p className="text-[11px] text-foreground">{rec.prospectPain}</p>
                    </div>
                    <div>
                      <div className="text-[10px] font-semibold text-muted-foreground uppercase mb-1">Root Driver</div>
                      <p className="text-[11px] text-foreground">{rec.rootDriver}</p>
                    </div>
                  </div>

                  <div>
                    <div className="text-[10px] font-semibold text-muted-foreground uppercase mb-1">Our Capability</div>
                    <p className="text-[11px] text-primary font-medium bg-primary/5 px-3 py-2 rounded-md">
                      <Zap size={11} className="inline mr-1" />
                      {rec.ourCapability}
                    </p>
                  </div>

                  <div>
                    <div className="text-[10px] font-semibold text-muted-foreground uppercase mb-1">Proof Points</div>
                    <div className="space-y-1.5">
                      {rec.proofPoints.map((pp, i) => (
                        <div key={i} className="flex items-center gap-2 text-[11px]">
                          <FileText size={10} className="text-muted-foreground shrink-0" />
                          <span className="font-medium text-foreground">{pp.source}:</span>
                          <span className="text-muted-foreground">{pp.detail}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-2">
                    <Btn variant="primary" className="gap-1.5">
                      <CheckCircle2 size={12} />
                      Accept → Value Model
                    </Btn>
                    <Btn variant="outline">Modify</Btn>
                    <Btn variant="ghost" className="text-muted-foreground">Exclude</Btn>
                  </div>
                </div>
              )}
            </SectionCard>
          );
        })}
      </div>
    </ValueStudioShellComponent>
  );
}
