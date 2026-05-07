/**
 * ROITab — ROI Calculator
 *
 * Workspace tab for the Calculator workspace.
 */
import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Calculator, Loader2, RefreshCcw, Save } from "lucide-react";
import CalculatorShell from "@/components/workspace/CalculatorShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
import { LoadingState, ErrorState } from "@/components/states";
import { SectionCard, MetricCard } from "@/components/WfPrimitives";
import { QK } from "@/hooks/queryKeys";
import { useCanonicalCaseId, useWorkspaceTabQuery } from "@/hooks/useWorkspaceCase";
import { useModels } from "@/hooks/useModels";
import { useROIScenarioVersions, useSaveROIScenarioVersion, useUpdateROIScenarioVersion, validateScenarioAssumptions, DEFAULT_SCENARIO_ASSUMPTIONS, type ScenarioState, type ScenarioAssumptionSet, type ScenarioName } from "@/hooks/useROIScenarios";
import { useValueLevers } from "@/hooks/useCalculators";
import { useBenchmarksList, useCalculateROI, useIndustryBenchmarks, type ROICalculationRequest } from "@/hooks/useROICalculator";
import { useValuePacks } from "@/hooks/useValuePacks";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigation } from "@/hooks";
import { createNextAction } from "@/components/workspace/nextAction";


function fmtCurrency(value: number): string {
  return `$${Math.round(value).toLocaleString()}`;
}

export default function CalcROITab() {
  const params = useParams<{ accountId: string }>();
  const accountId = params.accountId ?? null;
  const { data: account, isLoading: accountLoading } = useAccount(accountId);
  const { navigateTo } = useNavigation();
  const [railMode, setRailMode] = useState<RightRailMode>("agent");
  const { data: caseId } = useCanonicalCaseId(accountId);
  const { data: valueModelTab } = useWorkspaceTabQuery<{ model_id?: string; value_model_id?: string; selected_model_id?: string }>(caseId ?? null, "value-model");
  const { data: models } = useModels({});
  const modelId = valueModelTab?.selected_model_id ?? valueModelTab?.value_model_id ?? valueModelTab?.model_id ?? models?.[0]?.id ?? null;
  const [scenario, setScenario] = useState<ScenarioAssumptionSet>(DEFAULT_SCENARIO_ASSUMPTIONS);
  const [activeScenario, setActiveScenario] = useState<ScenarioName>("expected");

  const queryClient = useQueryClient();
  const { data: leverData, isLoading: leversLoading, error: leverError } = useValueLevers({ industry: account?.industry ?? undefined });
  const { data: assumptions, isLoading: assumptionsLoading } = useIndustryBenchmarks(account?.industry ?? null);
  const { data: allAssumptions } = useBenchmarksList();
  const { data: packs } = useValuePacks({});
  const recalcMutation = useCalculateROI();

  const scenarioScope = useMemo(
    () => ({ tenantId: null, accountId, caseId: caseId ?? null, modelId }),
    [accountId, caseId, modelId]
  );

  const versionsQuery = useROIScenarioVersions(scenarioScope);
  const saveScenarioMutation = useSaveROIScenarioVersion(scenarioScope, scenario);
  const updateRemoteVersionMutation = useUpdateROIScenarioVersion(scenarioScope);

  const updateScenarioMutation = useMutation({
    mutationKey: ["calculator", "roi", "scenario", "edit"],
    mutationFn: async ({ scenarioName, next }: { scenarioName: ScenarioName; next: Partial<ScenarioState> }) => {
      const updated = { ...scenario, [scenarioName]: { ...scenario[scenarioName], ...next } };
      setScenario(updated);
      return updated;
    },
    onSuccess: async (updated) => {
      if (!accountId) return;
      const validationErrors = validateScenarioAssumptions(updated);
      if (validationErrors.length) throw new Error(validationErrors.join("; "));
      await recalcMutation.mutateAsync({ ...updated.expected, account_id: accountId } as ROICalculationRequest);
      await queryClient.invalidateQueries({ queryKey: QK.roi.list({ account_id: accountId }) });
      await queryClient.invalidateQueries({ queryKey: QK.roi.scenarioVersions(scenarioScope) });
      await queryClient.invalidateQueries({ queryKey: QK.roi.all });
      const latest = versionsQuery.data?.[0];
      if (latest?.versionId) {
        await updateRemoteVersionMutation.mutateAsync({ versionId: latest.versionId, assumptions: updated });
      }
    },
  });
  useEffect(() => {
    const latest = versionsQuery.data?.[0];
    if (latest) {
      setScenario(latest.assumptions);
    }
  }, [versionsQuery.data]);

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "roi",
    accountName: account?.name ?? "Account",
    accountId: accountId ?? undefined,
  });

  if (!accountId) return <AccountRequiredGuard accountId={accountId} />;
  if (accountLoading) return <LoadingState message="Loading account…" fullPage />;
  if (!account) return <ErrorState title="Account not found" description="Select a valid account to continue in this workspace." fullPage />;

  const calc = recalcMutation.data;
  const scenarioNames = Object.keys(calc?.scenarios ?? {});
  const hasCompletedScenarios = scenarioNames.length > 0;
  const nextAction = accountId
    ? createNextAction({
        label: "Generate Business Case",
        target: "value-case",
        params: { accountId },
        disabled: !hasCompletedScenarios,
        reason: "Run a scenario calculation first.",
      })
    : null;

  return (
    <CalculatorShell
      account={{
        accountName: account?.name ?? "Account",
        industry: account?.industry ?? "Unknown",
        revenue: account?.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "N/A",
      }}
      rightRail={<RightRail mode={railMode} onModeChange={setRailMode} activeTab="roi" messages={messages} onSendMessage={sendMessage} suggestedActions={suggestedActions} steps={steps} isStreaming={isStreaming} runMetadata={metadata} />}
    >
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <Calculator className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">ROI Calculator</h2>
            <p className="text-sm text-muted-foreground">Scenario assumptions, value levers, and traceable formula outcomes.</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <MetricCard label="Conservative" value={calc?.scenarios?.conservative ? `${Math.round(calc.scenarios.conservative.total_roi_pct)}%` : "—"} />
          <MetricCard label="Moderate" value={calc?.scenarios?.moderate ? `${Math.round(calc.scenarios.moderate.total_roi_pct)}%` : "—"} />
          <MetricCard label="Aggressive" value={calc?.scenarios?.aggressive ? `${Math.round(calc.scenarios.aggressive.total_roi_pct)}%` : "—"} />
        </div>

        <SectionCard title="Scenario assumptions">
          <div className="grid grid-cols-2 gap-3">
            {(["conservative", "expected", "optimistic"] as ScenarioName[]).map((name) => (
              <button key={name} onClick={() => setActiveScenario(name)} className={`rounded border px-2 py-1 text-xs ${activeScenario===name?"border-primary text-primary":"border-border"}`}>{name}</button>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(scenario[activeScenario]).map(([k, v]) => (
              <label key={k} className="space-y-1">
                <span className="text-xs text-muted-foreground">{k.replaceAll("_", " ")}</span>
                <input type="number" value={v} onChange={(e) => updateScenarioMutation.mutate({ scenarioName: activeScenario, next: { [k]: Number(e.target.value) } as Partial<ScenarioState> })} className="w-full rounded border border-border bg-background px-2 py-1 text-xs" />
              </label>
            ))}
          </div>
          <div className="mb-3 flex gap-2"></div>
          <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
            <button onClick={() => saveScenarioMutation.mutate(`Version ${new Date().toLocaleString()}`)} className="inline-flex items-center gap-1 rounded border border-border px-2 py-1 hover:bg-muted" disabled={saveScenarioMutation.isPending}>
              <Save className="h-3.5 w-3.5" /> Save version
            </button>
            <button onClick={() => recalcMutation.mutate({ ...scenario.expected, account_id: accountId })} className="inline-flex items-center gap-1 rounded border border-border px-2 py-1 hover:bg-muted" disabled={recalcMutation.isPending}>
              {recalcMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCcw className="h-3.5 w-3.5" />} Recalculate
            </button>
            {updateScenarioMutation.isPending && <span className="text-muted-foreground">Updating assumptions…</span>}
            {recalcMutation.isError && <span className="text-destructive">Failed to recalculate scenario.</span>}
            {updateScenarioMutation.error instanceof Error && <span className="text-destructive">{updateScenarioMutation.error.message}</span>}
            {saveScenarioMutation.isError && <span className="text-destructive">Failed to persist scenario version.</span>}
          </div>
        </SectionCard>

        <SectionCard title="Value model drivers and levers">
          {leversLoading ? <p className="text-sm text-muted-foreground">Loading value levers…</p> : leverError ? <p className="text-sm text-destructive">Failed to load value levers.</p> : (
            <div className="space-y-2">
              {(leverData?.levers ?? []).map((lever) => {
                const mappedPack = packs?.find((p) => p.name.toLowerCase().includes(lever.category.toLowerCase()));
                return (
                  <div key={lever.id} className="rounded border border-border p-2 text-xs">
                    <div className="font-medium">{lever.name}</div>
                    <div className="text-muted-foreground">Driver: {lever.category} · Formula var: <code>{lever.id}</code></div>
                    <div className="text-muted-foreground">Mapped value pack: {mappedPack?.name ?? "Unmapped"}</div>
                  </div>
                );
              })}
            </div>
          )}
        </SectionCard>

        <SectionCard title="Trace / explain">
          <div className="space-y-2 text-xs">
            <p className="text-muted-foreground">Changed assumptions are reflected in scenario outputs and benchmarks.</p>
            <p>Total NPV: <span className="font-semibold">{calc ? fmtCurrency(calc.npv) : "—"}</span></p>
            <p>Benchmark ROI ({account.industry ?? "Industry"}): <span className="font-semibold">{assumptions ? `${Math.round(assumptions.avg_roi_pct)}%` : assumptionsLoading ? "Loading…" : "N/A"}</span></p>
            <p>Loaded assumption sets: <span className="font-semibold">{allAssumptions?.benchmarks.length ?? 0}</span></p>
            <p>Calculated scenarios: <span className="font-semibold">{scenarioNames.join(", ") || "None yet"}</span></p>
          </div>
        </SectionCard>

        <SectionCard title="Saved scenario versions (reload/resume)">
          <div className="space-y-2">
            {(versionsQuery.data ?? []).map((version) => (
              <button key={version.versionId} onClick={() => setScenario(version.assumptions)} className="w-full rounded border border-border p-2 text-left text-xs hover:bg-muted">
                <div className="font-medium">{version.name}</div>
                <div className="text-muted-foreground">{version.accountId} / {version.caseId} / {version.modelId}</div>
              </button>
            ))}
            {!versionsQuery.data?.length && <p className="text-xs text-muted-foreground">No versions saved for this account/case/model.</p>}
          </div>
        </SectionCard>
        {nextAction && (
          <div className="flex items-center justify-end gap-2">
            {nextAction.disabled && <span className="text-xs text-muted-foreground">{nextAction.reason}</span>}
            <button
              className="inline-flex items-center gap-1 rounded bg-primary px-3 py-2 text-xs font-medium text-primary-foreground disabled:opacity-50"
              disabled={nextAction.disabled}
              onClick={() => navigateTo(nextAction.target, nextAction.params)}
              data-testid="primary-forward-action"
            >
              {nextAction.label}
            </button>
          </div>
        )}
      </div>
    </CalculatorShell>
  );
}
