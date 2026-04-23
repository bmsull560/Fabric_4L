import { useEffect, useMemo, useState } from "react";
import { useParams } from "wouter";
import { FileText, CheckCircle2, AlertCircle, ChevronRight } from "lucide-react";
import IntelligenceShell from "@/components/workspace/IntelligenceShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentStream } from "@/hooks/useAgentStream";
import { useAccount } from "@/hooks/useAccounts";
import { useCanonicalCaseId, usePersistWorkspaceTab, useValidateEvidenceClaim, useWorkspaceTabQuery } from "@/hooks/useWorkspaceCase";
import { SectionCard, MetricCard } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";

type VerificationState = "verified" | "partial" | "unverified";
interface EvidenceItem { id: string; title: string; type: string; source: string; matchScore: number; verification: VerificationState; linkedSignals: string[]; excerpt: string }
const VERIFICATION_CONFIG: Record<VerificationState, { icon: typeof CheckCircle2; color: string }> = { verified: { icon: CheckCircle2, color: "text-green-600" }, partial: { icon: AlertCircle, color: "text-orange-600" }, unverified: { icon: AlertCircle, color: "text-muted-foreground" } };

export default function EvidenceTab() {
  const { accountId } = useParams<{ accountId: string }>();
  const { data: account } = useAccount(accountId ?? null);
  const { data: caseId } = useCanonicalCaseId(accountId ?? null);
  const { data, isLoading, error } = useWorkspaceTabQuery<{ evidence: EvidenceItem[] }>(caseId ?? null, "evidence");
  const persistTab = usePersistWorkspaceTab("evidence");
  const validateClaim = useValidateEvidenceClaim();
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceItem | null>(null);
  const [railMode, setRailMode] = useState<RightRailMode>("detail");

  useEffect(() => { if (caseId && data) persistTab.mutate({ caseId, payload: data }); }, [caseId, data]);
  const evidence = data?.evidence ?? [];
  const verified = useMemo(() => evidence.filter((e) => e.verification === "verified").length, [evidence]);
  const avgMatch = evidence.length ? Math.round(evidence.reduce((s, e) => s + e.matchScore, 0) / evidence.length) : 0;

  const { messages, sendMessage, suggestedActions } = useAgentStream({ activeTab: "evidence", accountName: account?.name ?? "Account" });

  if (isLoading) return <div className="p-6 text-sm text-muted-foreground">Loading evidence…</div>;
  if (error || !account) return <div className="p-6 text-sm text-destructive">Failed to load evidence.</div>;

  return <IntelligenceShell account={{ accountName: account.name, industry: account.industry ?? "Unknown", revenue: account.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "N/A" }} rightRail={<RightRail mode={railMode} onModeChange={setRailMode} activeTab="evidence" detailContent={selectedEvidence ? <div className="space-y-2"><h3 className="text-sm font-bold">{selectedEvidence.title}</h3><p className="text-xs text-muted-foreground">{selectedEvidence.excerpt}</p></div> : null} messages={messages} onSendMessage={sendMessage} suggestedActions={suggestedActions} />}>
    {evidence.length === 0 ? <SectionCard title="Evidence Library"><div className="text-sm text-muted-foreground">No evidence has been returned for this case.</div></SectionCard> : <>
      <div className="grid grid-cols-3 gap-4 mb-6"><MetricCard label="Evidence Items" value={String(evidence.length)} trend={`${verified} verified`} /><MetricCard label="Avg Match Score" value={`${avgMatch}%`} /><MetricCard label="Source Types" value={String(new Set(evidence.map((e) => e.type)).size)} /></div>
      <SectionCard title="Evidence Library"><div className="space-y-1">{evidence.map((item) => { const vc = VERIFICATION_CONFIG[item.verification]; const Icon = vc.icon; return <button key={item.id} onClick={() => { setSelectedEvidence(item); if (caseId && item.verification === "verified") validateClaim.mutate({ caseId, evidenceId: item.id, claim: item.excerpt }); }} className={cn("flex items-center gap-4 w-full px-3 py-3 rounded-md text-left", selectedEvidence?.id === item.id ? "bg-primary/5" : "hover:bg-muted/50")}><FileText size={14} /><div className="flex-1"><div className="text-xs font-medium">{item.title}</div><div className="text-[10px] text-muted-foreground">{item.linkedSignals.join(" · ")}</div></div><span className={cn("flex items-center gap-1 text-[10px] font-semibold", vc.color)}><Icon size={10} />{item.matchScore}%</span><ChevronRight size={12} /></button>; })}</div></SectionCard>
    </>}
  </IntelligenceShell>;
}
