/**
 * ValueModelTab — persisted account value model.
 */
<<<<<<< ours
<<<<<<< ours
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { BarChart3, Calculator, Link2 } from "lucide-react";
=======
=======
>>>>>>> theirs
import { useEffect, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import { BarChart3 } from "lucide-react";
>>>>>>> theirs
import CalculatorShell from "@/components/workspace/CalculatorShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { useValueCase, type ValueCaseResponse } from "@/hooks/useCalculators";
import { useCanonicalCaseId, useWorkspaceTabQuery } from "@/hooks/useWorkspaceCase";
import { useNavigation } from "@/hooks";
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
<<<<<<< ours
import { LoadingState, ErrorState, EmptyState } from "@/components/states";
import { SectionCard, MetricCard, Btn } from "@/components/WfPrimitives";

interface PersistedValueModel {
  latest_value_case_id?: string;
  value_case?: ValueCaseResponse;
  evidence_links?: Array<{ evidence_id: string; driver_id?: string; lever_id?: string }>;
}

function currency(value: number): string {
  return `$${Math.round(value).toLocaleString()}`;
}
=======
import { LoadingState, ErrorState } from "@/components/states";
import { SectionCard, MetricCard } from "@/components/WfPrimitives";
import { useWorkspaceSelectionStore } from "@/stores/workspaceSelectionStore";
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs

export default function CalcValueModelTab() {
  const params = useParams<{ accountId: string }>();
  const accountId = params.accountId ?? null;
  const location = useLocation();
  const setSelection = useWorkspaceSelectionStore((state) => state.setSelection);
  const getSelection = useWorkspaceSelectionStore((state) => state.getSelection);
  const [activeTreeId, setActiveTreeId] = useState<string | null>(null);
  const [activeValueModelId, setActiveValueModelId] = useState<string | null>(null);
  const { data: account, isLoading: accountLoading } = useAccount(accountId);
<<<<<<< ours
<<<<<<< ours
  const { navigateTo } = useNavigation();
=======
=======
>>>>>>> theirs

  useEffect(() => {
    if (!accountId) return;
    const params = new URLSearchParams(location.search);
    const queryTreeId = params.get("tree_id") || null;
    const queryValueModelId = params.get("value_model_id") || null;
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

<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
  const [railMode, setRailMode] = useState<RightRailMode>("agent");

  const { data: caseId } = useCanonicalCaseId(accountId);
  const { data: persistedModel, isLoading: modelLoading } = useWorkspaceTabQuery<PersistedValueModel>(
    caseId ?? null,
    "value-model",
  );
  const latestCaseId = persistedModel?.latest_value_case_id ?? null;
  const { data: fetchedValueCase, isLoading: valueCaseLoading } = useValueCase(latestCaseId);
  const valueCase = fetchedValueCase ?? persistedModel?.value_case ?? null;

  const totals = useMemo(() => {
    const scenarios = valueCase?.scenarios ?? [];
    return {
      hardSavings: scenarios.find((scenario) => scenario.name === "Conservative")?.total_value ?? 0,
      expected: scenarios.find((scenario) => scenario.name === "Expected")?.total_value ?? 0,
      optimistic: scenarios.find((scenario) => scenario.name === "Optimistic")?.total_value ?? 0,
    };
  }, [valueCase]);

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "value-model",
    accountName: account?.name ?? "Account",
    accountId: accountId ?? undefined,
    selectedScenarioId: valueCase?.case_id,
    workspaceCaseId: caseId ?? undefined,
    entityContext: {
      valueCaseId: valueCase?.case_id,
      evidenceLinks: persistedModel?.evidence_links ?? [],
      scenarioTotals: totals,
    },
  });

  if (!accountId) {
    return <AccountRequiredGuard accountId={accountId} />;
  }

  if (accountLoading) {
    return <LoadingState message="Loading account..." fullPage />;
  }

  if (!account) {
    return <ErrorState title="Account not found" description="Select a valid account to continue in this workspace." fullPage />;
  }

  const isLoading = modelLoading || valueCaseLoading;

  return (
    <CalculatorShell
      account={{
        accountName: account.name,
        industry: account.industry ?? "Unknown",
        revenue: account.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "N/A",
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
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">Value Model</h2>
              <p className="text-sm text-muted-foreground">Persisted scenarios, lever breakdowns, and attached evidence.</p>
            </div>
          </div>
          <Btn variant="outline" onClick={() => navigateTo(`/calculator/${accountId}/roi`)}>
            <Calculator size={12} />
            Open ROI
          </Btn>
        </div>

<<<<<<< ours
        {isLoading ? (
          <LoadingState message="Loading value model..." />
        ) : !valueCase ? (
          <EmptyState
            title="No value case yet"
            description="Save a scenario in ROI to create the canonical value model for this account."
            icon={BarChart3}
          />
        ) : (
          <>
            <div className="grid grid-cols-3 gap-4">
              <MetricCard label="Conservative Value" value={currency(totals.hardSavings)} />
              <MetricCard label="Expected Value" value={currency(totals.expected)} />
              <MetricCard label="Optimistic Value" value={currency(totals.optimistic)} />
            </div>
=======
        <div className="rounded border border-border p-3 text-xs text-muted-foreground">
          Active selection · Tree: {activeTreeId ?? "None"} · Value model: {activeValueModelId ?? "None"}
        </div>

        <div className="rounded border border-border p-3 text-xs text-muted-foreground">
          Active selection · Tree: {activeTreeId ?? "None"} · Value model: {activeValueModelId ?? "None"}
        </div>

        <div className="grid grid-cols-3 gap-4">
          <MetricCard label="Hard Savings" value="—" />
          <MetricCard label="Strategic Value" value="—" />
          <MetricCard label="Total Annual Value" value="—" />
        </div>
>>>>>>> theirs

            <SectionCard title="Scenario Lines" subtitle={`Value case ${valueCase.case_id}`}>
              <div className="space-y-4">
                {valueCase.scenarios.map((scenario) => (
                  <div key={scenario.name} className="rounded-md border border-border p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <h3 className="text-sm font-semibold">{scenario.name}</h3>
                        <p className="text-xs text-muted-foreground">Total annual value {currency(scenario.total_value)}</p>
                      </div>
                      <span className="text-sm font-semibold">{currency(scenario.total_value)}</span>
                    </div>
                    <div className="mt-3 space-y-2">
                      {scenario.breakdown.map((item) => (
                        <div key={`${scenario.name}-${item.area}`} className="grid grid-cols-[1fr_auto_auto] items-center gap-3 text-xs">
                          <span className="font-medium">{item.area}</span>
                          <span className="text-muted-foreground">{item.percentage}%</span>
                          <span>{currency(item.value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </SectionCard>

            <SectionCard title="Linked Evidence">
              <div className="flex items-center gap-2 text-sm">
                <Link2 size={14} className="text-muted-foreground" />
                <span>{persistedModel?.evidence_links?.length ?? 0} evidence attachment(s) included in calculator context.</span>
              </div>
            </SectionCard>
          </>
        )}
      </div>
    </CalculatorShell>
  );
}
