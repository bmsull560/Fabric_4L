/**
 * Intelligence → Evidence Tab
 *
 * Source documents, benchmarks, and case studies that validate signals and drivers.
 * Shows confidence grading and source provenance for each evidence item.
 *
 * Migrated from: Stage4Validation (evidence verification)
 */
import { useState } from "react";
import { useParams } from "wouter";
import { FileText, ExternalLink, CheckCircle2, AlertCircle, ChevronRight } from "lucide-react";
import IntelligenceShell from "@/components/workspace/IntelligenceShell";
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

type EvidenceType = "case_study" | "benchmark" | "document" | "crm_note" | "ai_inferred";
type VerificationState = "verified" | "partial" | "unverified";

interface EvidenceItem {
  id: string;
  title: string;
  type: EvidenceType;
  source: string;
  matchScore: number;
  verification: VerificationState;
  linkedSignals: string[];
  excerpt: string;
}

const TYPE_LABELS: Record<EvidenceType, string> = {
  case_study:   "Case Study",
  benchmark:    "Benchmark",
  document:     "Document",
  crm_note:     "CRM Note",
  ai_inferred:  "AI Inferred",
};

const VERIFICATION_CONFIG: Record<VerificationState, { label: string; icon: typeof CheckCircle2; color: string }> = {
  verified:   { label: "Verified",   icon: CheckCircle2, color: "text-green-600" },
  partial:    { label: "Partial",    icon: AlertCircle,  color: "text-orange-600" },
  unverified: { label: "Unverified", icon: AlertCircle,  color: "text-muted-foreground" },
};

const DEMO_EVIDENCE: EvidenceItem[] = [
  {
    id: "e1", title: "Continental AG — Cobot Deployment", type: "case_study",
    source: "Internal Case Study Library", matchScore: 95, verification: "verified",
    linkedSignals: ["Production Downtime", "Labor Shortage"],
    excerpt: "Continental AG deployed X1 cobot workcells on 4 assembly lines, achieving 23% cycle time reduction within 4 months and reducing manual labor dependency by 40%.",
  },
  {
    id: "e2", title: "Tier 1 Auto Benchmark — Uptime", type: "benchmark",
    source: "Industry Benchmark Database", matchScore: 88, verification: "verified",
    linkedSignals: ["Production Downtime"],
    excerpt: "Tier 1 automotive manufacturers with cobot-augmented lines average 96% uptime vs. 81% for manual-only lines (n=47 plants, 2024 survey).",
  },
  {
    id: "e3", title: "Meridian 2025 Annual Report", type: "document",
    source: "Public Filing — SEC EDGAR", matchScore: 82, verification: "verified",
    linkedSignals: ["Energy Cost Surge", "Quality Defect Rate"],
    excerpt: "Energy costs increased 18% YoY driven by natural gas price volatility. Quality-related warranty claims rose to $890K, up from $720K in prior year.",
  },
  {
    id: "e4", title: "CRM Note — VP Ops Meeting", type: "crm_note",
    source: "Salesforce — Opportunity MAC-2026-0417", matchScore: 76, verification: "partial",
    linkedSignals: ["Labor Shortage — Welders"],
    excerpt: "VP mentioned 340 unfilled positions and 18% turnover. Expressed urgency around Q3 production targets. Open to automation discussion.",
  },
  {
    id: "e5", title: "Changeover Time Estimate", type: "ai_inferred",
    source: "AI Analysis — Based on industry patterns", matchScore: 68, verification: "unverified",
    linkedSignals: ["Production Downtime"],
    excerpt: "Based on plant configuration data and industry patterns, estimated changeover time of 45 min/SKU vs. 12 min/SKU benchmark for automated lines.",
  },
];

// ── Component ─────────────────────────────────────────────────────────────────

export default function EvidenceTab() {
  const params = useParams<{ accountId: string }>();
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceItem | null>(null);
  const [railMode, setRailMode] = useState<RightRailMode>("detail");
  const { messages, sendMessage, suggestedActions } = useAgentStream({
    activeTab: "evidence",
    accountName: DEMO_ACCOUNT.accountName,
  });

  const verified = DEMO_EVIDENCE.filter((e) => e.verification === "verified").length;
  const avgMatch = Math.round(DEMO_EVIDENCE.reduce((s, e) => s + e.matchScore, 0) / DEMO_EVIDENCE.length);

  const detailContent = selectedEvidence ? (
    <div className="space-y-4">
      <div>
        <h3 className="text-[14px] font-bold text-foreground mb-1">{selectedEvidence.title}</h3>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-[10px] font-semibold uppercase tracking-wider bg-muted px-1.5 py-0.5 rounded text-muted-foreground">
            {TYPE_LABELS[selectedEvidence.type]}
          </span>
          {(() => {
            const vc = VERIFICATION_CONFIG[selectedEvidence.verification];
            const Icon = vc.icon;
            return (
              <span className={cn("flex items-center gap-1 text-[10px] font-semibold", vc.color)}>
                <Icon size={10} />
                {vc.label}
              </span>
            );
          })()}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="text-center p-2 bg-muted/50 rounded-md">
          <div className="text-[10px] text-muted-foreground uppercase">Match Score</div>
          <div className="text-[14px] font-bold text-foreground">{selectedEvidence.matchScore}%</div>
        </div>
        <div className="text-center p-2 bg-muted/50 rounded-md">
          <div className="text-[10px] text-muted-foreground uppercase">Source</div>
          <div className="text-[11px] font-medium text-foreground truncate">{selectedEvidence.source}</div>
        </div>
      </div>

      <div>
        <h4 className="text-[12px] font-semibold text-foreground mb-1">Excerpt</h4>
        <p className="text-[11px] text-muted-foreground leading-relaxed bg-muted/30 p-3 rounded-md border-l-2 border-primary">
          "{selectedEvidence.excerpt}"
        </p>
      </div>

      <div>
        <h4 className="text-[12px] font-semibold text-foreground mb-2">Linked Signals</h4>
        <div className="flex flex-wrap gap-1.5">
          {selectedEvidence.linkedSignals.map((s) => (
            <span key={s} className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium">
              {s}
            </span>
          ))}
        </div>
      </div>

      <Btn variant="outline" className="w-full gap-1.5">
        <ExternalLink size={12} />
        View Full Source
      </Btn>
    </div>
  ) : null;

  const rightRail = (
    <RightRail
      mode={railMode}
      onModeChange={setRailMode}
      detailContent={detailContent}
      activeTab="evidence"
      messages={messages}
      onSendMessage={sendMessage}
      suggestedActions={suggestedActions}
    />
  );

  return (
    <IntelligenceShell account={DEMO_ACCOUNT} rightRail={rightRail}>
      {/* Summary metrics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <MetricCard label="Evidence Items" value={String(DEMO_EVIDENCE.length)} trend={`${verified} verified`} trendUp />
        <MetricCard label="Avg Match Score" value={`${avgMatch}%`} trend="Across all items" />
        <MetricCard label="Source Types" value="5" trend="Case studies, benchmarks, docs, CRM, AI" />
      </div>

      {/* Evidence list */}
      <SectionCard title="Evidence Library">
        <div className="space-y-1">
          {DEMO_EVIDENCE.map((item) => {
            const vc = VERIFICATION_CONFIG[item.verification];
            const Icon = vc.icon;
            return (
              <button
                key={item.id}
                onClick={() => { setSelectedEvidence(item); setRailMode("detail"); }}
                className={cn(
                  "flex items-center gap-4 w-full px-3 py-3 rounded-md text-left transition-colors",
                  selectedEvidence?.id === item.id ? "bg-primary/5" : "hover:bg-muted/50"
                )}
              >
                <FileText size={14} className="text-muted-foreground shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[12px] font-medium text-foreground">{item.title}</span>
                    <span className="text-[10px] font-semibold uppercase tracking-wider bg-muted px-1.5 py-0.5 rounded text-muted-foreground shrink-0">
                      {TYPE_LABELS[item.type]}
                    </span>
                  </div>
                  <div className="text-[10px] text-muted-foreground mt-0.5 truncate">
                    {item.linkedSignals.join(" · ")}
                  </div>
                </div>
                <span className={cn("flex items-center gap-1 text-[10px] font-semibold shrink-0", vc.color)}>
                  <Icon size={10} />
                  {item.matchScore}%
                </span>
                <ChevronRight size={12} className="text-muted-foreground shrink-0" />
              </button>
            );
          })}
        </div>
      </SectionCard>
    </IntelligenceShell>
  );
}
