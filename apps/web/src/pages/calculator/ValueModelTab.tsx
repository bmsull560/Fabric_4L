/**
 * ValueModelTab — Quantitative Value Model
 *
 * Workspace tab for the Calculator workspace.
 */
import { useEffect, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import { BarChart3 } from "lucide-react";
import CalculatorShell from "@/components/workspace/CalculatorShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
import { LoadingState, ErrorState } from "@/components/states";
import { SectionCard, MetricCard } from "@/components/WfPrimitives";
import { useWorkspaceSelectionStore } from "@/stores/workspaceSelectionStore";

export default function CalcValueModelTab() {
  const params = useParams<{ accountId: string }>();
  const accountId = params.accountId ?? null;
  const location = useLocation();
  const setSelection = useWorkspaceSelectionStore((state) => state.setSelection);
  const getSelection = useWorkspaceSelectionStore((state) => state.getSelection);
  const [activeTreeId, setActiveTreeId] = useState<string | null>(null);
  const [activeValueModelId, setActiveValueModelId] = useState<string | null>(null);
  const { data: account, isLoading: accountLoading } = useAccount(accountId);

  useEffect(() => {
    if (!accountId) return;
    const params = new URLSearchParams(location.search);
    const queryTreeId = params.get("tree_id");
    const queryValueModelId = params.get("value_model_id");
    if (queryTreeId || queryValueModelId) {
      setSelection(accountId, { treeId: queryTreeId, valueModelId: queryValueModelId });
      setActiveTreeId(queryTreeId);
      setActiveValueModelId(queryValueModelId);
      return;
    }
    const persisted = getSelection(accountId);
    setActiveTreeId(persisted.treeId);
    setActiveValueModelId(persisted.valueModelId);
  }, [accountId, location.search, getSelection, setSelection]);

  const [railMode, setRailMode] = useState<RightRailMode>("agent");

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "value-model",
    accountName: account?.name ?? "Account",
    accountId: accountId ?? undefined,
  });

  if (!accountId) {
    return <AccountRequiredGuard accountId={accountId} />;
  }

  if (accountLoading) {
    return <LoadingState message="Loading account…" fullPage />;
  }

  if (!account) {
    return <ErrorState title="Account not found" description="Select a valid account to continue in this workspace." fullPage />;
  }

  return (
    <CalculatorShell
      account={{
        accountName: account?.name ?? "Account",
        industry: account?.industry ?? "Unknown",
        revenue: account?.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "N/A",
      }}
      rightRail={
        <RightRail
          mode={railMode}
          onModeChange={setRailMode}
          activeTab="value-model"
          messages={messages}
          onSendMessage={sendMessage}
          suggestedActions={suggestedActions}
          steps={steps}
          isStreaming={isStreaming}
          runMetadata={metadata}
        />
      }
    >
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">Value Model</h2>
            <p className="text-sm text-muted-foreground">
              Quantitative value lines mapped to business drivers and evidence
            </p>
          </div>
        </div>

        <div className="rounded border border-border p-3 text-xs text-muted-foreground">
          Active selection · Tree: {activeTreeId ?? "None"} · Value model: {activeValueModelId ?? "None"}
        </div>

        <div className="grid grid-cols-3 gap-4">
          <MetricCard label="Hard Savings" value="—" />
          <MetricCard label="Strategic Value" value="—" />
          <MetricCard label="Total Annual Value" value="—" />
        </div>

        <SectionCard title="Value Lines">
          <div className="rounded-lg border border-dashed border-border p-8 text-center">
            <p className="text-sm text-muted-foreground">
              Value model will be available once driver tree and hypotheses are approved.
            </p>
            <p className="text-xs text-muted-foreground/60 mt-2">
              Quantified value lines with conservative, expected, and optimistic scenarios.
            </p>
          </div>
        </SectionCard>
      </div>
    </CalculatorShell>
  );
}
