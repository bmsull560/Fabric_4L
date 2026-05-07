import { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Filter, Activity, ArrowRight } from "lucide-react";
import IntelligenceShell from "@/components/workspace/IntelligenceShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { usePromoteSignal } from "@/hooks/useHypotheses";
import { useNavigation } from "@/hooks";
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
import { LoadingState, EmptyState, ErrorState } from "@/components/states";
import { useCanonicalCaseId, usePersistWorkspaceTab, useWorkspaceTabQuery, useGenerateWorkspaceIntelligence } from "@/hooks/useWorkspaceCase";
import { SectionCard, Btn, MetricCard } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";
import { useQueryClient } from "@tanstack/react-query";

export type ValuePathCategory = 'revenue_uplift' | 'cost_savings' | 'risk_reduction' | 'blended';

interface Signal {
  id: string;
  name: string;
  category: string;
  confidence: number;
  impact: string;
  trend?: string;
}

const CATEGORY_COLORS: Record<string, string> = {
  Operational: "bg-red-500",
  Workforce: "bg-orange-500",
  Quality: "bg-yellow-500",
  Cost: "bg-blue-500",
  "Supply Chain": "bg-purple-500",
  Risk: "bg-pink-500",
};

export default function SignalsTab() {
  const queryClient = useQueryClient();
  const params = useParams<{ accountId: string }>();
  const accountId = params.accountId ?? null;
  const { data: account, isLoading: accountLoading, error: accountError } = useAccount(accountId);
  const { data: caseId, isLoading: caseIdLoading, error: caseIdError, refetch: refetchCaseId } = useCanonicalCaseId(accountId);
  const { data, isLoading, error, refetch: refetchSignals } = useWorkspaceTabQuery<{ signals: Signal[] }>(caseId ?? null, "signals");
  const persistTab = usePersistWorkspaceTab("signals");

  const signals = useMemo(() => data?.signals ?? [], [data]);
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);
  const [railMode, setRailMode] = useState<RightRailMode>("agent");

  useEffect(() => {
    if (!caseId || !data) return;
    persistTab.mutate({ caseId, payload: data });
  }, [caseId, data, persistTab.mutate]);

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "signals",
    accountName: account?.name ?? "Account",
    accountId: accountId ?? undefined,
    selectedSignalId: selectedSignal?.id,
  });

  const generateMutation = useGenerateWorkspaceIntelligence();

  // Auto-generate workspace data if empty
  useEffect(() => {
    if (caseId && signals.length === 0 && !isLoading && !generateMutation.isPending) {
      generateMutation.mutate(caseId);
    }
  }, [caseId, signals.length, isLoading]);

  const handleRetry = () => {
    if (caseIdError) refetchCaseId();
    if (error) refetchSignals();
    queryClient.invalidateQueries({ queryKey: ['workspace', 'tab', caseId, 'signals'] });
  };

  const hasError = accountError || error || caseIdError || generateMutation.isError;
  const isDataLoading = accountLoading || isLoading || caseIdLoading;
  const isGenerating = generateMutation.isPending;

  if (!accountId) {
    return <AccountRequiredGuard accountId={accountId} />;
  }

  const promoteMutation = usePromoteSignal();
  const { navigateTo } = useNavigation();
  const [selectedValuePath, setSelectedValuePath] = useState<ValuePathCategory | ''>('');

  const handlePromoteSignal = async (signalId: string) => {
    if (!accountId || !selectedValuePath) return;
    await promoteMutation.mutateAsync({
      account_id: accountId,
      signal_id: signalId,
      value_path_category: selectedValuePath,
    });
  };

  const detailContent = selectedSignal ? (
    <div className="space-y-4">
      <h3 className="text-[14px] font-bold text-foreground">{selectedSignal.name}</h3>
      <div className="grid grid-cols-3 gap-2">
        <div className="text-center p-2 bg-muted/50 rounded-md"><div className="text-[10px]">Confidence</div><div className="text-[14px] font-bold">{selectedSignal.confidence}%</div></div>
        <div className="text-center p-2 bg-muted/50 rounded-md"><div className="text-[10px]">Impact</div><div className="text-[14px] font-bold">{selectedSignal.impact}</div></div>
        <div className="text-center p-2 bg-muted/50 rounded-md"><div className="text-[10px]">Trend</div><div className="text-[14px] font-bold">{selectedSignal.trend ?? "—"}</div></div>
      </div>
      {/* Value Path Classification */}
      <div className="space-y-2 pt-2">
        <label className="text-[11px] font-medium text-muted-foreground">Value Path</label>
        <select
          className="w-full h-8 px-2 text-[12px] rounded-md border border-border bg-background text-foreground"
          value={selectedValuePath}
          onChange={(e) => setSelectedValuePath(e.target.value as ValuePathCategory)}
        >
          <option value="">Select value path...</option>
          <option value="revenue_uplift">Revenue Uplift</option>
          <option value="cost_savings">Cost Savings</option>
          <option value="risk_reduction">Risk Reduction</option>
          <option value="blended">Blended</option>
        </select>
        <Btn
          variant="primary"
          className="w-full"
          disabled={!selectedValuePath || promoteMutation.isPending}
          onClick={() => handlePromoteSignal(selectedSignal.id)}
        >
          {promoteMutation.isPending ? 'Promoting...' : 'Promote to Value Path'}
        </Btn>
        {promoteMutation.isSuccess && (
          <Btn
            variant="ghost"
            className="w-full text-primary"
            onClick={() => navigateTo('hypothesis', { accountId })}
          >
            View Hypothesis <ArrowRight size={12} />
          </Btn>
        )}
      </div>
    </div>
  ) : null;

  return (
    <IntelligenceShell
      account={{
        accountName: account?.name ?? "Account",
        industry: account?.industry ?? "Unknown",
        revenue: account?.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "N/A",
      }}
      rightRail={<RightRail mode={railMode} onModeChange={setRailMode} detailContent={detailContent} activeTab="signals" messages={messages} onSendMessage={sendMessage} suggestedActions={suggestedActions} steps={steps} isStreaming={isStreaming} runMetadata={metadata} />}
    >
      {isDataLoading ? (
        <LoadingState message={isGenerating ? "Generating intelligence..." : "Loading signals..."} />
      ) : hasError ? (
        <ErrorState
          title="Signals could not be loaded"
          description="The app could not retrieve intelligence signals for the current account. Check that the backend API is running."
          error={error || accountError || caseIdError}
          onRetry={handleRetry}
          retryLabel="Retry"
          fallbackAction={
            <Link to="/accounts">
              <Btn variant="outline">Go to Accounts</Btn>
            </Link>
          }
        />
      ) : signals.length === 0 ? (
        <EmptyState
          title="No signals yet"
          description="Select an account or run intelligence gathering to generate market, account, and pain signals."
          icon={Activity}
          action={
            <Btn onClick={() => caseId && generateMutation.mutate(caseId)} disabled={generateMutation.isPending}>
              Generate Signals
            </Btn>
          }
        />
      ) : (
        <>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <MetricCard label="Signals Detected" value={String(signals.length)} trend="Account-scoped" trendUp />
            <MetricCard label="Avg Confidence" value={`${Math.round(signals.reduce((s, x) => s + x.confidence, 0) / signals.length)}%`} />
            <MetricCard label="Categories" value={String(new Set(signals.map((s) => s.category)).size)} />
          </div>
          <SectionCard title="Pain Signal List">
            <div className="flex items-center justify-between mb-3"><span className="text-[11px] text-muted-foreground">{signals.length} detected</span><Btn variant="outline" className="gap-1.5"><Filter size={12} />Filters</Btn></div>
            {signals.map((signal, i) => (
              <button key={signal.id} onClick={() => { setSelectedSignal(signal); setRailMode("detail"); }} className={cn("grid grid-cols-[auto_1fr_auto_auto_auto] gap-4 px-3 py-3 text-[12px] border-b border-border last:border-0 w-full text-left", selectedSignal?.id === signal.id ? "bg-primary/5" : "hover:bg-muted/50")}>
                <span className="w-6 text-muted-foreground font-medium">{i + 1}</span>
                <div className="flex items-center gap-2"><div className={cn("w-1 h-6 rounded-full", CATEGORY_COLORS[signal.category] || "bg-muted-foreground")} /><span className="font-medium">{signal.name}</span></div>
                <span className="w-24 text-right">{signal.confidence}%</span><span className="w-24 text-right">{signal.impact}</span><span className="w-6">›</span>
              </button>
            ))}
          </SectionCard>
        </>
      )}
    </IntelligenceShell>
  );
}
