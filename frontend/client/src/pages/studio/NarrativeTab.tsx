import { useEffect, useState } from "react";
import { useParams } from "wouter";
import { Users, Download, Mail, Eye, RefreshCw } from "lucide-react";
import ValueStudioShellComponent from "@/components/workspace/ValueStudioShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { SectionCard, MetricCard, Btn } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";
import { useAgentStream } from "@/hooks/useAgentStream";
import { useAccount } from "@/hooks/useAccounts";
import { useCanonicalCaseId, usePersistWorkspaceTab, useWorkspaceTabQuery } from "@/hooks/useWorkspaceCase";

interface NarrativeVersion { id: string; stakeholder: string; role: string; status: "ready" | "draft" | "generating"; headline: string; summary: string; keyMetrics: { label: string; value: string }[]; lastUpdated: string }
const STATUS_CONFIG: Record<NarrativeVersion["status"], { label: string; color: string; bg: string }> = { ready: { label: "Ready", color: "text-green-600", bg: "bg-green-500" }, draft: { label: "Draft", color: "text-orange-600", bg: "bg-orange-500" }, generating: { label: "Generating", color: "text-blue-600", bg: "bg-blue-500" } };

export default function NarrativeTab() {
  const { accountId } = useParams<{ accountId: string }>();
  const { data: account } = useAccount(accountId ?? null);
  const { data: caseId } = useCanonicalCaseId(accountId ?? null);
  const { data, isLoading, error } = useWorkspaceTabQuery<{ narratives: NarrativeVersion[] }>(caseId ?? null, "narrative");
  const persistTab = usePersistWorkspaceTab("narrative");
  const [selectedNarrative, setSelectedNarrative] = useState<NarrativeVersion | null>(null);
  const [railMode, setRailMode] = useState<RightRailMode>("detail");
  useEffect(() => { if (caseId && data) persistTab.mutate({ caseId, payload: data }); }, [caseId, data]);
  const narratives = data?.narratives ?? [];
  useEffect(() => { if (!selectedNarrative && narratives[0]) setSelectedNarrative(narratives[0]); }, [narratives, selectedNarrative]);

  const { messages, sendMessage, suggestedActions } = useAgentStream({ activeTab: "narrative", accountName: account?.name ?? "Account" });

  if (isLoading) return <div className="p-6 text-sm text-muted-foreground">Loading narratives…</div>;
  if (error || !account) return <div className="p-6 text-sm text-destructive">Failed to load narratives.</div>;

  const readyCount = narratives.filter((n) => n.status === "ready").length;
  const selectedStatus = selectedNarrative ? STATUS_CONFIG[selectedNarrative.status] : null;

  return <ValueStudioShellComponent account={{ accountName: account.name, industry: account.industry ?? "Unknown", revenue: account.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "N/A" }} rightRail={<RightRail mode={railMode} onModeChange={setRailMode} detailContent={selectedNarrative ? <div className="space-y-3"><h3 className="text-sm font-bold">{selectedNarrative.stakeholder}</h3><p className="text-xs text-muted-foreground">{selectedNarrative.role}</p>{selectedStatus && <span className={cn("text-[10px] font-semibold", selectedStatus.color)}>{selectedStatus.label}</span>}</div> : null} activeTab="narrative" messages={messages} onSendMessage={sendMessage} suggestedActions={suggestedActions} />}>
    {narratives.length === 0 ? <SectionCard title="Stakeholder Narratives"><div className="text-sm text-muted-foreground">No narrative output available yet for this case.</div></SectionCard> : <>
      <div className="grid grid-cols-3 gap-4 mb-6"><MetricCard label="Narrative Versions" value={String(narratives.length)} /><MetricCard label="Ready to Send" value={String(readyCount)} trend={`Of ${narratives.length}`} /><MetricCard label="Buying Committee" value={`${new Set(narratives.map((n) => n.stakeholder)).size} members`} /></div>
      <SectionCard title="Stakeholder Narratives"><div className="space-y-1">{narratives.map((narrative) => { const sc = STATUS_CONFIG[narrative.status]; return <button key={narrative.id} onClick={() => setSelectedNarrative(narrative)} className={cn("flex items-center gap-4 w-full px-3 py-3 rounded-md text-left", selectedNarrative?.id === narrative.id ? "bg-primary/5" : "hover:bg-muted/50")}><Users size={14} /><div className="flex-1"><div className="flex gap-2"><span className="text-xs font-medium">{narrative.stakeholder}</span><span className="text-[10px] text-muted-foreground">{narrative.role}</span></div><div className="text-[10px] text-muted-foreground truncate">{narrative.headline}</div></div><div className="flex items-center gap-1.5"><div className={cn("w-1.5 h-1.5 rounded-full", sc.bg)} /><span className={cn("text-[10px] font-semibold", sc.color)}>{sc.label}</span></div></button>; })}</div></SectionCard>
      {selectedNarrative?.status === "generating" ? <div className="flex items-center justify-center py-8"><RefreshCw size={16} className="animate-spin mr-2" />Generating narrative…</div> : selectedNarrative && <SectionCard title="Selected Narrative"><p className="text-sm mb-2">{selectedNarrative.summary}</p><div className="flex gap-2"><Btn variant="primary" className="gap-1.5"><Download size={12} />Export PDF</Btn><Btn variant="outline" className="gap-1.5"><Mail size={12} />Email</Btn><Btn variant="outline" className="gap-1.5"><Eye size={12} />Preview</Btn></div></SectionCard>}
    </>}
  </ValueStudioShellComponent>;
}
