/**
 * ROITab — account-scoped ROI calculator.
 */
import { useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { ArrowRight, Calculator, FileText, Save } from "lucide-react";
import CalculatorShell from "@/components/workspace/CalculatorShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { useHypothesis } from "@/hooks/useHypotheses";
import { useCreateValueCase, useValueLevers, type ValueCaseRequest, type ValueLever } from "@/hooks/useCalculators";
import { useCalculateROI } from "@/hooks/useROICalculator";
import { useCanonicalCaseId, usePersistWorkspaceTab, useWorkspaceTabQuery } from "@/hooks/useWorkspaceCase";
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
import { LoadingState, ErrorState, EmptyState } from "@/components/states";
import { SectionCard, MetricCard, Btn } from "@/components/WfPrimitives";
import { useNavigation } from "@/hooks";

type LeverValues = Record<string, { conservative: number; expected: number; optimistic: number }>;

const SCENARIOS = ["conservative", "expected", "optimistic"] as const;
const SCENARIO_LABELS = {
  conservative: "Conservative",
  expected: "Expected",
  optimistic: "Optimistic",
} as const;

function currency(value: number): string {
  return `$${Math.round(value).toLocaleString()}`;
}

function buildInitialValues(levers: ValueLever[]): LeverValues {
  return Object.fromEntries(
    levers.map((lever) => [
      lever.id,
      {
        conservative: lever.min_value,
        expected: lever.base_value,
        optimistic: lever.max_value,
      },
    ]),
  );
}

function scenarioTotal(levers: ValueLever[], values: LeverValues, scenario: keyof typeof SCENARIO_LABELS): number {
  return levers.reduce((sum, lever) => {
    const selected = values[lever.id]?.[scenario] ?? lever.base_value;
    const ratio = lever.base_value === 0 ? 1 : selected / lever.base_value;
    return sum + lever.annual_impact * ratio;
  }, 0);
}

function buildValueCaseRequest(accountId: string, levers: ValueLever[], values: LeverValues, hypothesisId: string | null): ValueCaseRequest {
  const totals = Object.fromEntries(SCENARIOS.map((scenario) => [scenario, scenarioTotal(levers, values, scenario)])) as Record<keyof typeof SCENARIO_LABELS, number>;
  const expectedTotal = totals.expected || 1;

  return {
    account_id: accountId,
    levers: levers.map((lever) => ({
      lever_id: lever.id,
      scenario_a: values[lever.id]?.conservative ?? lever.min_value,
      scenario_b: values[lever.id]?.expected ?? lever.base_value,
      scenario_c: values[lever.id]?.optimistic ?? lever.max_value,
    })),
    scenarios: SCENARIOS.map((scenario) => ({
      name: SCENARIO_LABELS[scenario],
      total_value: totals[scenario],
      breakdown: levers.map((lever) => {
        const value = scenarioTotal([lever], values, scenario);
        return {
          area: lever.name,
          value,
          percentage: expectedTotal > 0 ? Math.round((value / expectedTotal) * 100) : 0,
        };
      }),
    })),
    metadata: {
      generated_by: "calculator-roi",
      confidence_score: Math.round(
        levers.reduce((sum, lever) => sum + lever.confidence, 0) / Math.max(levers.length, 1),
      ),
      hypothesis_id: hypothesisId ?? undefined,
    } as ValueCaseRequest["metadata"] & { hypothesis_id?: string },
  };
}

export default function CalcROITab() {
  const params = useParams<{ accountId: string }>();
  const accountId = params.accountId ?? null;
  const { data: account, isLoading: accountLoading } = useAccount(accountId);
  const [searchParams] = useSearchParams();
  const hypothesisId = searchParams.get("hypothesisId");
  const { navigateTo } = useNavigation();
  const [railMode, setRailMode] = useState<RightRailMode>("agent");
  const [leverValues, setLeverValues] = useState<LeverValues>({});

  const { data: hypothesis } = useHypothesis(hypothesisId);
  const { data: caseId } = useCanonicalCaseId(accountId);
  const { data: linkData } = useWorkspaceTabQuery<{ evidence_links?: Array<{ evidence_id: string; driver_id: string }> }>(caseId ?? null, "evidence-links");
  const persistValueModel = usePersistWorkspaceTab("value-model");
  const createValueCase = useCreateValueCase();
  const calculateROI = useCalculateROI();
  const { data: leverConfig, isLoading: leversLoading, error: leversError } = useValueLevers({
    industry: account?.industry || undefined,
  });

  const levers = leverConfig?.levers ?? [];

  useEffect(() => {
    if (levers.length > 0 && Object.keys(leverValues).length === 0) {
      setLeverValues(buildInitialValues(levers));
    }
  }, [levers, leverValues]);

  const totals = useMemo(() => ({
    conservative: scenarioTotal(levers, leverValues, "conservative"),
    expected: scenarioTotal(levers, leverValues, "expected"),
    optimistic: scenarioTotal(levers, leverValues, "optimistic"),
  }), [levers, leverValues]);

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "roi",
    accountName: account?.name ?? "Account",
    accountId: accountId ?? undefined,
    selectedHypothesisId: hypothesisId ?? undefined,
    workspaceCaseId: caseId ?? undefined,
    entityContext: { hypothesisId, valueTotals: totals, evidenceLinks: linkData?.evidence_links ?? [] },
  });

  const updateLever = (leverId: string, scenario: keyof typeof SCENARIO_LABELS, value: number) => {
    setLeverValues((prev) => ({
      ...prev,
      [leverId]: {
        conservative: prev[leverId]?.conservative ?? 0,
        expected: prev[leverId]?.expected ?? 0,
        optimistic: prev[leverId]?.optimistic ?? 0,
        [scenario]: value,
      },
    }));
  };

  const handleSaveValueCase = async () => {
    if (!accountId || levers.length === 0) return;
    const request = buildValueCaseRequest(accountId, levers, leverValues, hypothesisId);
    const saved = await createValueCase.mutateAsync(request);
    await calculateROI.mutateAsync({
      deal_size: account?.annual_revenue ?? totals.expected,
      implementation_cost: Math.max(totals.expected * 0.2, 1),
      annual_benefit: totals.expected,
      time_horizon_years: 3,
      account_id: accountId,
      product_id: hypothesis?.product_id,
    });
    if (caseId) {
      await persistValueModel.mutateAsync({
        caseId,
        payload: {
          latest_value_case_id: saved.case_id,
          value_case: saved,
          evidence_links: linkData?.evidence_links ?? [],
        },
      });
    }
    navigateTo("value-case", { accountId });
  };

  if (!accountId) return <AccountRequiredGuard accountId={accountId} />;
  if (accountLoading) return <LoadingState message="Loading account..." fullPage />;
  if (!account) return <ErrorState title="Account not found" description="Select a valid account to continue in this workspace." fullPage />;

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
          activeTab="roi"
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
              <Calculator className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">ROI Calculator</h2>
              <p className="text-sm text-muted-foreground">Scenario-based ROI modeling from value levers.</p>
            </div>
          </div>
          <Btn
            variant="primary"
            disabled={createValueCase.isPending || calculateROI.isPending || levers.length === 0}
            onClick={handleSaveValueCase}
          >
            <Save size={12} />
            {createValueCase.isPending || calculateROI.isPending ? "Saving..." : "Save Value Case"}
            <ArrowRight size={12} />
          </Btn>
        </div>

        {hypothesis && (
          <SectionCard title="Linked Hypothesis">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium">{hypothesis.hypothesis_text}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Value Path: {hypothesis.value_path_category ?? "Unclassified"} - Confidence: {Math.round((hypothesis.confidence_score ?? hypothesis.confidence ?? 0.5) * 100)}% - Impact: {currency(hypothesis.estimated_impact_usd ?? 0)}
                </p>
              </div>
              <FileText size={16} className="text-muted-foreground" />
            </div>
          </SectionCard>
        )}

        <div className="grid grid-cols-3 gap-4">
          <MetricCard label="Conservative" value={currency(totals.conservative)} />
          <MetricCard label="Expected" value={currency(totals.expected)} />
          <MetricCard label="Optimistic" value={currency(totals.optimistic)} />
        </div>

        <SectionCard title="Value Levers">
          {leversLoading ? (
            <LoadingState message="Loading value levers..." />
          ) : leversError ? (
            <ErrorState title="Value levers could not be loaded" description="Retry after the calculator API is available." />
          ) : levers.length === 0 ? (
            <EmptyState title="No value levers" description="Validate hypotheses to promote driver tree levers for this account." icon={Calculator} />
          ) : (
            <div className="space-y-3">
              {levers.map((lever) => (
                <div key={lever.id} className="grid grid-cols-[1.2fr_1fr_1fr_1fr_auto] gap-3 items-center rounded-md border border-border px-3 py-3">
                  <div>
                    <div className="text-xs font-semibold">{lever.name}</div>
                    <div className="text-[10px] text-muted-foreground">{lever.category} - {currency(lever.annual_impact)} annual impact</div>
                  </div>
                  {SCENARIOS.map((scenario) => (
                    <label key={scenario} className="space-y-1">
                      <span className="text-[10px] text-muted-foreground">{SCENARIO_LABELS[scenario]}</span>
                      <input
                        type="number"
                        min={lever.min_value}
                        max={lever.max_value}
                        value={leverValues[lever.id]?.[scenario] ?? lever.base_value}
                        onChange={(event) => updateLever(lever.id, scenario, Number(event.target.value))}
                        className="w-full h-8 rounded-md border border-border bg-background px-2 text-xs"
                      />
                    </label>
                  ))}
                  <span className="text-[10px] text-muted-foreground">{lever.confidence}%</span>
                </div>
              ))}
            </div>
          )}
        </SectionCard>
      </div>
    </CalculatorShell>
  );
}
