import { useEffect, useMemo, useState } from "react";
import { useParams } from "wouter";
import { Settings2 } from "lucide-react";
import ValueStudioShellComponent from "@/components/workspace/ValueStudioShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentStream } from "@/hooks/useAgentStream";
import { useAccount } from "@/hooks/useAccounts";
import { useCanonicalCaseId, usePersistWorkspaceTab, useWorkspaceTabQuery, useGenerateWorkspaceIntelligence } from "@/hooks/useWorkspaceCase";
import { SectionCard, MetricCard, Btn } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";

type Scenario = "conservative" | "expected" | "optimistic";
interface ValueLine { id: string; driver: string; category: "hard" | "strategic"; conservative: number; expected: number; optimistic: number; source: string }

const SCENARIO_LABELS: Record<Scenario, string> = { conservative: "Conservative", expected: "Expected", optimistic: "Optimistic" };
const formatCurrency = (n: number) => (n >= 1_000_000 ? `$${(n / 1_000_000).toFixed(2)}M` : `$${Math.round(n).toLocaleString()}`);

export default function ValueModelTab() {
  const { accountId } = useParams<{ accountId: string }>();
  const { data: account } = useAccount(accountId ?? null);
  const { data: caseId } = useCanonicalCaseId(accountId ?? null);
  const { data, isLoading, error } = useWorkspaceTabQuery<{ valueLines: ValueLine[] }>(caseId ?? null, "value-model");
  const persistTab = usePersistWorkspaceTab("value-model");
  const [scenario, setScenario] = useState<Scenario>("expected");
  const [showStrategic, setShowStrategic] = useState(true);
  const [railMode, setRailMode] = useState<RightRailMode>("agent");
  useEffect(() => { if (caseId && data) persistTab.mutate({ caseId, payload: data }); }, [caseId, data]);

  const { messages, sendMessage, suggestedActions } = useAgentStream({ activeTab: "value-model", accountName: account?.name ?? "Account" });
  const lines = data?.valueLines ?? [];
  const visibleLines = useMemo(() => showStrategic ? lines : lines.filter((l) => l.category === "hard"), [showStrategic, lines]);
  const total = visibleLines.reduce((s, l) => s + l[scenario], 0);

  const generateMutation = useGenerateWorkspaceIntelligence();

  useEffect(() => {
    if (caseId && lines.length === 0 && !isLoading && !generateMutation.isPending) {
      generateMutation.mutate(caseId);
    }
  }, [caseId, lines.length, isLoading]);

  if (isLoading || generateMutation.isPending) return <div className="p-6 text-sm text-muted-foreground">{generateMutation.isPending ? "Generating value model..." : "Loading value model…"}</div>;
  if (error || !account) return <div className="p-6 text-sm text-destructive">Failed to load value model.</div>;

  return <ValueStudioShellComponent account={{ accountName: account.name, industry: account.industry ?? "Unknown", revenue: account.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "N/A" }} rightRail={<RightRail mode={railMode} onModeChange={setRailMode} activeTab="value-model" messages={messages} onSendMessage={sendMessage} suggestedActions={suggestedActions} />}>
    {lines.length === 0 ? <SectionCard title="Value Breakdown"><div className="text-sm text-muted-foreground">No value-model output available yet.</div></SectionCard> : <>
      <div className="grid grid-cols-4 gap-4 mb-6"><MetricCard label="Total Annual Value" value={formatCurrency(total)} trend={`${SCENARIO_LABELS[scenario]} scenario`} /><MetricCard label="Hard Savings" value={formatCurrency(lines.filter((l) => l.category === "hard").reduce((s, l) => s + l[scenario], 0))} /><MetricCard label="Strategic Value" value={formatCurrency(lines.filter((l) => l.category === "strategic").reduce((s, l) => s + l[scenario], 0))} /><MetricCard label="Value Lines" value={String(lines.length)} /></div>
      <div className="flex items-center justify-between mb-4"><div className="flex gap-2">{(Object.keys(SCENARIO_LABELS) as Scenario[]).map((s) => <button key={s} onClick={() => setScenario(s)} className={cn("px-3 py-1.5 text-[11px] font-semibold rounded-md", scenario === s ? "bg-primary text-primary-foreground" : "bg-muted")}>{SCENARIO_LABELS[s]}</button>)}</div><div className="flex gap-3 items-center"><label className="text-xs"><input type="checkbox" checked={showStrategic} onChange={(e) => setShowStrategic(e.target.checked)} /> Include strategic value</label><Btn variant="outline" className="gap-1.5"><Settings2 size={12} />Variables</Btn></div></div>
      <SectionCard title="Value Breakdown">{visibleLines.map((line) => <div key={line.id} className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-4 px-3 py-3 text-[12px] border-b border-border"><span>{line.driver}</span><span>{formatCurrency(line.conservative)}</span><span>{formatCurrency(line.expected)}</span><span>{formatCurrency(line.optimistic)}</span><span className="text-[10px] text-muted-foreground">{line.source}</span></div>)}</SectionCard>
    </>}
  </ValueStudioShellComponent>;
}
