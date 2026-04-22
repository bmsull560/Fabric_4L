/**
 * Value Studio → Narrative Tab
 *
 * Stakeholder-ready packaging of the value model.
 * Generates persona-specific narratives for each member of the buying committee.
 * Supports export to PDF, PowerPoint, and email-ready formats.
 *
 * Migrated from: Stage5Narrative (stakeholder framing) + Stage6Tracking (deliverables)
 */
import { useState } from "react";
import { useParams } from "wouter";
import { FileText, Download, Mail, Users, Eye, RefreshCw } from "lucide-react";
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

interface NarrativeVersion {
  id: string;
  stakeholder: string;
  role: string;
  status: "ready" | "draft" | "generating";
  headline: string;
  summary: string;
  keyMetrics: { label: string; value: string }[];
  lastUpdated: string;
}

const DEMO_NARRATIVES: NarrativeVersion[] = [
  {
    id: "n1", stakeholder: "Sarah Chen", role: "VP Manufacturing Operations",
    status: "ready",
    headline: "Forge X1 Delivers $3.67M Annual Value Through Production Automation",
    summary: "By deploying Forge X1 cobot workcells on EV assembly lines 3 and 7, Meridian can address the $2.4M/yr production downtime problem at its root — aging manual weld stations. Combined with predictive maintenance and rapid changeover capabilities, the total expected value reaches $3.67M/yr with an 8.2-month payback period.",
    keyMetrics: [
      { label: "Total Annual Value", value: "$3.67M" },
      { label: "Payback Period", value: "8.2 months" },
      { label: "Labor Positions Augmented", value: "85" },
    ],
    lastUpdated: "2 hours ago",
  },
  {
    id: "n2", stakeholder: "Jennifer Walsh", role: "CFO",
    status: "ready",
    headline: "Risk-Adjusted ROI: 340% Over 3 Years with Conservative Assumptions",
    summary: "Using conservative estimates only, the Forge X1 deployment generates $6.68M in hard savings over 3 years against a $1.96M total investment. Even excluding strategic value (recall prevention, throughput uplift), the payback period is under 11 months. The investment qualifies for Section 179 accelerated depreciation.",
    keyMetrics: [
      { label: "3-Year Hard Savings", value: "$6.68M" },
      { label: "Total Investment", value: "$1.96M" },
      { label: "3-Year ROI", value: "340%" },
    ],
    lastUpdated: "2 hours ago",
  },
  {
    id: "n3", stakeholder: "Marcus Rivera", role: "Director of Engineering",
    status: "draft",
    headline: "Technical Integration: Forge X1 Compatibility with Existing PLC Infrastructure",
    summary: "The Forge X1 platform integrates with Meridian's existing Siemens S7-1500 PLC infrastructure via OPC UA. No forklift upgrade required. The SenseLink module provides real-time torque monitoring that feeds directly into the existing MES dashboard. Installation requires a 3-week line stoppage per cell.",
    keyMetrics: [
      { label: "Integration Protocol", value: "OPC UA" },
      { label: "Installation Time", value: "3 weeks/cell" },
      { label: "Defect Reduction", value: "Zero torque recalls" },
    ],
    lastUpdated: "5 hours ago",
  },
  {
    id: "n4", stakeholder: "David Park", role: "Plant Manager — Facility A",
    status: "generating",
    headline: "Generating narrative…",
    summary: "AI is generating a plant-manager-specific narrative focusing on operational uptime, worker safety improvements, and changeover speed gains.",
    keyMetrics: [],
    lastUpdated: "Generating…",
  },
];

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  ready:      { label: "Ready",      color: "text-green-600", bg: "bg-green-500" },
  draft:      { label: "Draft",      color: "text-orange-600", bg: "bg-orange-500" },
  generating: { label: "Generating", color: "text-blue-600", bg: "bg-blue-500" },
};

// ── Component ─────────────────────────────────────────────────────────────────

export default function NarrativeTab() {
  const params = useParams<{ accountId: string }>();
  const [selectedNarrative, setSelectedNarrative] = useState<NarrativeVersion | null>(DEMO_NARRATIVES[0]);
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
        { id: `a-${Date.now()}`, role: "agent", content: "Refining the narrative based on your feedback…", timestamp: "Now" },
      ]);
    }, 800);
  };

  const readyCount = DEMO_NARRATIVES.filter((n) => n.status === "ready").length;

  const detailContent = selectedNarrative ? (
    <div className="space-y-4">
      <div>
        <h3 className="text-[14px] font-bold text-foreground">{selectedNarrative.stakeholder}</h3>
        <p className="text-[11px] text-muted-foreground">{selectedNarrative.role}</p>
        <div className="flex items-center gap-1.5 mt-2">
          <div className={cn("w-1.5 h-1.5 rounded-full", STATUS_CONFIG[selectedNarrative.status].bg)} />
          <span className={cn("text-[10px] font-semibold", STATUS_CONFIG[selectedNarrative.status].color)}>
            {STATUS_CONFIG[selectedNarrative.status].label}
          </span>
          <span className="text-[10px] text-muted-foreground ml-2">Updated {selectedNarrative.lastUpdated}</span>
        </div>
      </div>

      {selectedNarrative.status !== "generating" && (
        <>
          <div>
            <h4 className="text-[12px] font-semibold text-foreground mb-1">Headline</h4>
            <p className="text-[11px] text-foreground font-medium bg-primary/5 px-3 py-2 rounded-md">
              {selectedNarrative.headline}
            </p>
          </div>

          <div>
            <h4 className="text-[12px] font-semibold text-foreground mb-1">Executive Summary</h4>
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              {selectedNarrative.summary}
            </p>
          </div>

          {selectedNarrative.keyMetrics.length > 0 && (
            <div>
              <h4 className="text-[12px] font-semibold text-foreground mb-2">Key Metrics</h4>
              <div className="space-y-1.5">
                {selectedNarrative.keyMetrics.map((m, i) => (
                  <div key={i} className="flex items-center justify-between text-[11px] py-1 border-b border-border last:border-0">
                    <span className="text-muted-foreground">{m.label}</span>
                    <span className="font-semibold text-foreground">{m.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-col gap-2 pt-2">
            <Btn variant="primary" className="w-full gap-1.5">
              <Download size={12} />
              Export PDF
            </Btn>
            <div className="flex gap-2">
              <Btn variant="outline" className="flex-1 gap-1.5">
                <Mail size={12} />
                Email
              </Btn>
              <Btn variant="outline" className="flex-1 gap-1.5">
                <Eye size={12} />
                Preview
              </Btn>
            </div>
          </div>
        </>
      )}

      {selectedNarrative.status === "generating" && (
        <div className="flex items-center justify-center py-8">
          <RefreshCw size={16} className="text-primary animate-spin mr-2" />
          <span className="text-[12px] text-muted-foreground">Generating narrative…</span>
        </div>
      )}
    </div>
  ) : null;

  const rightRail = (
    <RightRail
      mode={railMode}
      onModeChange={setRailMode}
      detailContent={detailContent}
      activeTab="narrative"
      messages={messages}
      onSendMessage={handleSendMessage}
      suggestedActions={[
        { label: "Regenerate all narratives", onClick: () => {} },
        { label: "Export full value case", onClick: () => {} },
      ]}
    />
  );

  return (
    <ValueStudioShellComponent account={DEMO_ACCOUNT} rightRail={rightRail}>
      {/* Summary metrics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <MetricCard label="Narrative Versions" value={String(DEMO_NARRATIVES.length)} trend="Persona-specific" />
        <MetricCard label="Ready to Send" value={String(readyCount)} trend={`Of ${DEMO_NARRATIVES.length} total`} trendUp />
        <MetricCard label="Buying Committee" value="4 members" trend="All mapped" />
      </div>

      {/* Narrative cards */}
      <SectionCard title="Stakeholder Narratives">
        <div className="space-y-1">
          {DEMO_NARRATIVES.map((narrative) => {
            const sc = STATUS_CONFIG[narrative.status];
            return (
              <button
                key={narrative.id}
                onClick={() => { setSelectedNarrative(narrative); setRailMode("detail"); }}
                className={cn(
                  "flex items-center gap-4 w-full px-3 py-3 rounded-md text-left transition-colors",
                  selectedNarrative?.id === narrative.id ? "bg-primary/5" : "hover:bg-muted/50"
                )}
              >
                <Users size={14} className="text-muted-foreground shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[12px] font-medium text-foreground">{narrative.stakeholder}</span>
                    <span className="text-[10px] text-muted-foreground">{narrative.role}</span>
                  </div>
                  <div className="text-[10px] text-muted-foreground mt-0.5 truncate">
                    {narrative.headline}
                  </div>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  <div className={cn("w-1.5 h-1.5 rounded-full", sc.bg)} />
                  <span className={cn("text-[10px] font-semibold", sc.color)}>{sc.label}</span>
                </div>
              </button>
            );
          })}
        </div>
      </SectionCard>
    </ValueStudioShellComponent>
  );
}
