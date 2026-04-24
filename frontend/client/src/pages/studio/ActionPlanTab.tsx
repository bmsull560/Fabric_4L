import { useEffect, useMemo, useState } from "react";
import { useParams } from "wouter";
import { ChevronDown, ChevronUp } from "lucide-react";
import ValueStudioShellComponent from "@/components/workspace/ValueStudioShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentStream } from "@/hooks/useAgentStream";
import { useAccount } from "@/hooks/useAccounts";
import { useCanonicalCaseId, usePersistWorkspaceTab, useWorkspaceTabQuery, useGenerateWorkspaceIntelligence } from "@/hooks/useWorkspaceCase";
import { SectionCard, MetricCard, Btn } from "@/components/WfPrimitives";

interface Recommendation { id: string; title: string; priority: "critical" | "high" | "medium"; projectedValue: string; confidence: "high" | "medium" | "low"; horizon: string; prospectPain: string; rootDriver: string; ourCapability: string }

export default function ActionPlanTab() {
  const { accountId } = useParams<{ accountId: string }>();
  const { data: account } = useAccount(accountId ?? null);
  const { data: caseId } = useCanonicalCaseId(accountId ?? null);
  const { data, isLoading, error } = useWorkspaceTabQuery<{ recommendations: Recommendation[] }>(caseId ?? null, "action-plan");
  const persistTab = usePersistWorkspaceTab("action-plan");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [railMode, setRailMode] = useState<RightRailMode>("agent");
  useEffect(() => { if (caseId && data) persistTab.mutate({ caseId, payload: data }); }, [caseId, data]);

  const recommendations = data?.recommendations ?? [];
  const totalValue = useMemo(() => recommendations.reduce((sum, rec) => sum + Number((rec.projectedValue || "").replace(/[^\d.-]/g, "")), 0), [recommendations]);
  const { messages, sendMessage, suggestedActions } = useAgentStream({ activeTab: "action-plan", accountName: account?.name ?? "Account" });

  const generateMutation = useGenerateWorkspaceIntelligence();

  useEffect(() => {
    if (caseId && recommendations.length === 0 && !isLoading && !generateMutation.isPending) {
      generateMutation.mutate(caseId);
    }
  }, [caseId, recommendations.length, isLoading]);

  if (isLoading || generateMutation.isPending) return <div className="p-6 text-sm text-muted-foreground">{generateMutation.isPending ? "Generating action plan..." : "Loading action plan…"}</div>;
  if (error || generateMutation.isError || !account) return <div className="p-6 text-sm text-destructive">Failed to load action plan.</div>;

  return <ValueStudioShellComponent account={{ accountName: account.name, industry: account.industry ?? "Unknown", revenue: account.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "N/A" }} rightRail={<RightRail mode={railMode} onModeChange={setRailMode} activeTab="action-plan" messages={messages} onSendMessage={sendMessage} suggestedActions={suggestedActions} />}>
    {recommendations.length === 0 ? <SectionCard title="Recommendations"><div className="text-sm text-muted-foreground">No action-plan outputs available for this case yet.</div></SectionCard> : <>
      <div className="grid grid-cols-3 gap-4 mb-6"><MetricCard label="Recommendations" value={String(recommendations.length)} /><MetricCard label="Total Projected Value" value={`$${totalValue.toLocaleString()}`} /><MetricCard label="Avg Confidence" value={`${Math.round((recommendations.filter((r) => r.confidence === "high").length / recommendations.length) * 100)}% high`} /></div>
      <div className="space-y-3">{recommendations.map((rec) => { const expanded = expandedId === rec.id; return <SectionCard key={rec.id}><button onClick={() => setExpandedId(expanded ? null : rec.id)} className="flex items-start gap-3 w-full text-left"><div className="flex-1"><h3 className="text-[13px] font-bold">{rec.title}</h3><div className="text-xs text-muted-foreground">{rec.horizon} · {rec.projectedValue}</div></div>{expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}</button>{expanded && <div className="mt-3 text-xs space-y-2"><p><b>Prospect Pain:</b> {rec.prospectPain}</p><p><b>Root Driver:</b> {rec.rootDriver}</p><p><b>Capability:</b> {rec.ourCapability}</p><Btn variant="primary">Accept → Value Model</Btn></div>}</SectionCard>; })}</div>
    </>}
  </ValueStudioShellComponent>;
}
