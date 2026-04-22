/**
 * Intelligence → Stakeholders Tab
 *
 * Maps validated signals and drivers to prospect buyer personas.
 * Shows who cares about each finding and how to frame it for them.
 *
 * Migrated from: Stage5Narrative (stakeholder framing)
 */
import { useState } from "react";
import { useParams } from "wouter";
import { Users, ChevronRight, Target, Shield, DollarSign, Wrench } from "lucide-react";
import IntelligenceShell from "@/components/workspace/IntelligenceShell";
import RightRail, { type RightRailMode, type AgentMessage } from "@/components/workspace/RightRail";
import { SectionCard, MetricCard } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";

// ── Demo Data ─────────────────────────────────────────────────────────────────

const DEMO_ACCOUNT = {
  accountName: "Meridian Automotive Components",
  industry: "Manufacturing",
  revenue: "$4.2B",
};

type BuyerRole = "economic" | "technical" | "champion" | "influencer";

interface Stakeholder {
  id: string;
  name: string;
  title: string;
  role: BuyerRole;
  priorities: string[];
  relevantSignals: string[];
  engagementLevel: "high" | "medium" | "low";
}

const ROLE_CONFIG: Record<BuyerRole, { label: string; icon: typeof Target; color: string }> = {
  economic:   { label: "Economic Buyer",  icon: DollarSign, color: "text-green-600" },
  technical:  { label: "Technical Buyer", icon: Wrench,     color: "text-blue-600" },
  champion:   { label: "Champion",        icon: Target,     color: "text-purple-600" },
  influencer: { label: "Influencer",      icon: Shield,     color: "text-orange-600" },
};

const DEMO_STAKEHOLDERS: Stakeholder[] = [
  {
    id: "sh1", name: "Sarah Chen", title: "VP Manufacturing Operations", role: "economic",
    priorities: ["Cost reduction", "Throughput improvement", "Labor efficiency"],
    relevantSignals: ["Production Downtime", "Labor Shortage — Welders"],
    engagementLevel: "high",
  },
  {
    id: "sh2", name: "Marcus Rivera", title: "Director of Engineering", role: "technical",
    priorities: ["Equipment reliability", "Quality metrics", "Safety compliance"],
    relevantSignals: ["Quality Defect Rate", "Production Downtime"],
    engagementLevel: "medium",
  },
  {
    id: "sh3", name: "Jennifer Walsh", title: "CFO", role: "economic",
    priorities: ["ROI justification", "Payback period", "Risk mitigation"],
    relevantSignals: ["Energy Cost Surge", "Production Downtime"],
    engagementLevel: "low",
  },
  {
    id: "sh4", name: "David Park", title: "Plant Manager — Facility A", role: "champion",
    priorities: ["Operational uptime", "Worker safety", "Changeover speed"],
    relevantSignals: ["Production Downtime", "Labor Shortage — Welders", "Quality Defect Rate"],
    engagementLevel: "high",
  },
];

// ── Component ─────────────────────────────────────────────────────────────────

export default function StakeholdersTab() {
  const params = useParams<{ accountId: string }>();
  const [selectedStakeholder, setSelectedStakeholder] = useState<Stakeholder | null>(null);
  const [railMode, setRailMode] = useState<RightRailMode>("detail");
  const [messages, setMessages] = useState<AgentMessage[]>([]);

  const handleSendMessage = (msg: string) => {
    setMessages((prev) => [
      ...prev,
      { id: `u-${Date.now()}`, role: "user", content: msg, timestamp: "Now" },
    ]);
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { id: `a-${Date.now()}`, role: "agent", content: "Analyzing stakeholder alignment with validated signals…", timestamp: "Now" },
      ]);
    }, 800);
  };

  const detailContent = selectedStakeholder ? (() => {
    const rc = ROLE_CONFIG[selectedStakeholder.role];
    const RoleIcon = rc.icon;
    return (
      <div className="space-y-4">
        <div>
          <h3 className="text-[14px] font-bold text-foreground">{selectedStakeholder.name}</h3>
          <p className="text-[11px] text-muted-foreground mt-0.5">{selectedStakeholder.title}</p>
          <div className="flex items-center gap-1.5 mt-2">
            <RoleIcon size={12} className={rc.color} />
            <span className={cn("text-[10px] font-semibold", rc.color)}>{rc.label}</span>
          </div>
        </div>

        <div className="p-3 bg-muted/50 rounded-md">
          <div className="text-[10px] text-muted-foreground uppercase mb-1">Engagement Level</div>
          <div className="flex items-center gap-2">
            {(["high", "medium", "low"] as const).map((level) => (
              <div
                key={level}
                className={cn(
                  "flex-1 h-2 rounded-full",
                  selectedStakeholder.engagementLevel === level
                    ? level === "high" ? "bg-green-500" : level === "medium" ? "bg-yellow-500" : "bg-muted-foreground"
                    : "bg-muted"
                )}
              />
            ))}
            <span className="text-[11px] font-semibold text-foreground capitalize">
              {selectedStakeholder.engagementLevel}
            </span>
          </div>
        </div>

        <div>
          <h4 className="text-[12px] font-semibold text-foreground mb-2">Priorities</h4>
          <div className="space-y-1.5">
            {selectedStakeholder.priorities.map((p, i) => (
              <div key={i} className="flex items-center gap-2 text-[11px] text-muted-foreground">
                <ChevronRight size={10} className="shrink-0" />
                {p}
              </div>
            ))}
          </div>
        </div>

        <div>
          <h4 className="text-[12px] font-semibold text-foreground mb-2">Relevant Signals</h4>
          <div className="flex flex-wrap gap-1.5">
            {selectedStakeholder.relevantSignals.map((s) => (
              <span key={s} className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium">
                {s}
              </span>
            ))}
          </div>
        </div>

        <div>
          <h4 className="text-[12px] font-semibold text-foreground mb-1">Recommended Framing</h4>
          <p className="text-[11px] text-muted-foreground leading-relaxed">
            For {selectedStakeholder.name}, lead with {selectedStakeholder.priorities[0]?.toLowerCase()}.
            Connect the {selectedStakeholder.relevantSignals[0]} signal directly to their KPIs.
            {selectedStakeholder.role === "economic"
              ? " Emphasize payback period and total cost of ownership."
              : selectedStakeholder.role === "technical"
              ? " Provide technical specifications and integration requirements."
              : " Highlight quick wins and operational improvements."}
          </p>
        </div>
      </div>
    );
  })() : null;

  const rightRail = (
    <RightRail
      mode={railMode}
      onModeChange={setRailMode}
      detailContent={detailContent}
      activeTab="stakeholders"
      messages={messages}
      onSendMessage={handleSendMessage}
    />
  );

  return (
    <IntelligenceShell account={DEMO_ACCOUNT} rightRail={rightRail}>
      {/* Summary metrics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <MetricCard label="Stakeholders" value={String(DEMO_STAKEHOLDERS.length)} trend="Mapped to signals" />
        <MetricCard label="Economic Buyers" value="2" trend="Sarah Chen, Jennifer Walsh" />
        <MetricCard label="High Engagement" value="2" trend="Active in deal cycle" trendUp />
      </div>

      {/* Stakeholder list */}
      <SectionCard title="Buying Committee">
        <div className="space-y-1">
          {DEMO_STAKEHOLDERS.map((sh) => {
            const rc = ROLE_CONFIG[sh.role];
            const RoleIcon = rc.icon;
            return (
              <button
                key={sh.id}
                onClick={() => { setSelectedStakeholder(sh); setRailMode("detail"); }}
                className={cn(
                  "flex items-center gap-4 w-full px-3 py-3 rounded-md text-left transition-colors",
                  selectedStakeholder?.id === sh.id ? "bg-primary/5" : "hover:bg-muted/50"
                )}
              >
                <Users size={14} className="text-muted-foreground shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[12px] font-medium text-foreground">{sh.name}</span>
                    <span className={cn("flex items-center gap-1 text-[10px] font-semibold", rc.color)}>
                      <RoleIcon size={10} />
                      {rc.label}
                    </span>
                  </div>
                  <div className="text-[10px] text-muted-foreground mt-0.5">{sh.title}</div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <div className={cn(
                    "w-2 h-2 rounded-full",
                    sh.engagementLevel === "high" ? "bg-green-500"
                    : sh.engagementLevel === "medium" ? "bg-yellow-500"
                    : "bg-muted-foreground"
                  )} />
                  <span className="text-[10px] text-muted-foreground capitalize">{sh.engagementLevel}</span>
                </div>
                <ChevronRight size={12} className="text-muted-foreground shrink-0" />
              </button>
            );
          })}
        </div>
      </SectionCard>
    </IntelligenceShell>
  );
}
