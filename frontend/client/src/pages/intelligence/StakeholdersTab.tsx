import { useEffect, useState } from "react";
import { useParams } from "wouter";
import { Users, ChevronRight } from "lucide-react";
import IntelligenceShell from "@/components/workspace/IntelligenceShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { useCanonicalCaseId, usePersistWorkspaceTab, useWorkspaceTabQuery } from "@/hooks/useWorkspaceCase";
import { SectionCard, MetricCard } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";

interface Stakeholder { id: string; name: string; title: string; role: string; priorities: string[]; relevantSignals: string[]; engagementLevel: "high" | "medium" | "low" }

export default function StakeholdersTab() {
  const { accountId } = useParams<{ accountId: string }>();
  const { data: account } = useAccount(accountId ?? null);
  const { data: caseId } = useCanonicalCaseId(accountId ?? null);
  const { data, isLoading, error } = useWorkspaceTabQuery<{ stakeholders: Stakeholder[] }>(caseId ?? null, "stakeholders");
  const persistTab = usePersistWorkspaceTab("stakeholders");
  const [selectedStakeholder, setSelectedStakeholder] = useState<Stakeholder | null>(null);
  const [railMode, setRailMode] = useState<RightRailMode>("detail");
  useEffect(() => { if (caseId && data) persistTab.mutate({ caseId, payload: data }); }, [caseId, data]);

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({ activeTab: "stakeholders", accountName: account?.name ?? "Account" });
  const stakeholders = data?.stakeholders ?? [];

  if (isLoading) return <div className="p-6 text-sm text-muted-foreground">Loading stakeholders…</div>;
  if (error) return <div className="p-6 text-sm text-destructive">Failed to load stakeholders.</div>;

  return <IntelligenceShell account={{ accountName: account?.name ?? "Account", industry: account?.industry ?? "Unknown", revenue: account?.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "N/A" }} rightRail={<RightRail mode={railMode} onModeChange={setRailMode} activeTab="stakeholders" detailContent={selectedStakeholder ? <div><h3 className="text-sm font-bold">{selectedStakeholder.name}</h3><p className="text-xs text-muted-foreground">{selectedStakeholder.title}</p></div> : null} messages={messages} onSendMessage={sendMessage} suggestedActions={suggestedActions} steps={steps} isStreaming={isStreaming} runMetadata={metadata} />}>
    {stakeholders.length === 0 ? <SectionCard title="Buying Committee"><div className="text-sm text-muted-foreground">No stakeholder mapping exists yet for this case.</div></SectionCard> : <>
      <div className="grid grid-cols-3 gap-4 mb-6"><MetricCard label="Stakeholders" value={String(stakeholders.length)} /><MetricCard label="Economic Buyers" value={String(stakeholders.filter((s) => s.role === "economic").length)} /><MetricCard label="High Engagement" value={String(stakeholders.filter((s) => s.engagementLevel === "high").length)} trendUp /></div>
      <SectionCard title="Buying Committee"><div className="space-y-1">{stakeholders.map((sh) => <button key={sh.id} onClick={() => setSelectedStakeholder(sh)} className={cn("flex items-center gap-4 w-full px-3 py-3 rounded-md text-left", selectedStakeholder?.id === sh.id ? "bg-primary/5" : "hover:bg-muted/50")}><Users size={14} /><div className="flex-1"><div className="text-xs font-medium">{sh.name}</div><div className="text-[10px] text-muted-foreground">{sh.title}</div></div><span className="text-[10px] text-muted-foreground capitalize">{sh.engagementLevel}</span><ChevronRight size={12} /></button>)}</div></SectionCard>
    </>}
  </IntelligenceShell>;
}
