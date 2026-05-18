/**
 * Studio ROI Tab — DIL-native
 *
 * ROI calculation surface within the Value Studio context.
 * Uses DIL ROI calculator hooks for scenario modeling.
 */
import { useState } from "react";
import { useParams } from "react-router-dom";
import {
  Calculator,
  TrendingUp,
  DollarSign,
  Clock,
  BarChart3,
} from "lucide-react";
import ValueStudioShellComponent from "@/components/workspace/ValueStudioShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { cn } from "@/lib/utils";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
import { CenteredLoader } from "@/components/CenteredLoader";
import {
  useCalculateROI,
  useROITemplates,
  useIndustryBenchmarks,
  type ROICalculationResult,
  type ROITemplate,
  type AnnualProjection,
  type ScenarioResult,
  type IndustryBenchmark,
} from "@/hooks/useROICalculator";
import { SectionCard } from "@/components/blocks/SectionCard";
import { MetricCard, Btn } from "@/components/ui/fabric";

// ── Scenario Config ────────────────────────────────────────────────────────────
const SCENARIO_COLORS: Record<string, string> = {
  conservative: "text-blue-600 bg-blue-50 border-blue-200",
  moderate: "text-green-600 bg-green-50 border-green-200",
  aggressive: "text-orange-600 bg-orange-50 border-orange-200",
};

// ── Scenario Card ──────────────────────────────────────────────────────────────
function ScenarioCard({
  name,
  scenario,
}: {
  name: string;
  scenario: ScenarioResult;
}) {
  const colorClass = SCENARIO_COLORS[name] ?? SCENARIO_COLORS.moderate;
  return (
    <div className={cn("border rounded-md p-4", colorClass)}>
      <h4 className="text-[12px] font-bold mb-3 capitalize">{name}</h4>
      <div className="space-y-2 text-[11px]">
        <div className="flex justify-between">
          <span>NPV</span>
          <span className="font-semibold">
            ${(scenario.npv / 1000).toFixed(0)}K
          </span>
        </div>
        <div className="flex justify-between">
          <span>IRR</span>
          <span className="font-semibold">
            {(scenario.irr * 100).toFixed(1)}%
          </span>
        </div>
        <div className="flex justify-between">
          <span>Payback</span>
          <span className="font-semibold">{scenario.payback_months} mo</span>
        </div>
        <div className="flex justify-between border-t pt-1 mt-1">
          <span className="font-semibold">ROI</span>
          <span className="font-bold">
            {scenario.total_roi_pct.toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function StudioROITab() {
  const { accountId } = useParams<{ accountId: string }>();
  const { data: account, isLoading: accountLoading } = useAccount(accountId ?? null);
  const { data: templatesData } = useROITemplates();
  const { data: benchmarksData } = useIndustryBenchmarks(
    account?.industry ?? null
  );
  const calculateROI = useCalculateROI();
  const [railMode, setRailMode] = useState<RightRailMode>("agent");
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);

  // Form state — maps to ROICalculationRequest fields
  const [dealSize, setDealSize] = useState("100000");
  const [implementationCost, setImplementationCost] = useState("50000");
  const [annualBenefit, setAnnualBenefit] = useState("150000");
  const [timeHorizonYears, setTimeHorizonYears] = useState("3");

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "roi",
    accountName: account?.name ?? "Account",
  });

  const templates = (templatesData as ROITemplate[]) ?? [];
  const result = calculateROI.data as ROICalculationResult | undefined;

  const handleCalculate = () => {
    if (!accountId) return;
    calculateROI.mutate({
      deal_size: parseFloat(dealSize) || 0,
      implementation_cost: parseFloat(implementationCost) || 0,
      annual_benefit: parseFloat(annualBenefit) || 0,
      time_horizon_years: parseInt(timeHorizonYears) || 3,
      account_id: accountId,
      product_id: selectedTemplate ?? undefined,
    });
  };

  if (!accountId) {
    return <AccountRequiredGuard accountId={accountId} />;
  }

  if (accountLoading) {
    return <CenteredLoader message="Loading account…" />;
  }

  if (!account) {
    return <div className="p-6 text-sm text-destructive">Account not found.</div>;
  }

  // Extract scenario entries from the Record<string, ScenarioResult>
  const scenarioEntries: [string, ScenarioResult][] = result?.scenarios
    ? Object.entries(result.scenarios)
    : [];

  // Benchmark data (singular object, not array)
  const benchmark = benchmarksData as IndustryBenchmark | undefined;

  return (
    <ValueStudioShellComponent
      account={{
        accountName: account.name,
        industry: account.industry ?? "Unknown",
        revenue: account.annual_revenue
          ? `$${account.annual_revenue.toLocaleString()}`
          : "N/A",
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
      {/* Metrics */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <MetricCard
          label="NPV"
          value={
            result ? `$${(result.npv / 1000).toFixed(0)}K` : "—"
          }
        />
        <MetricCard
          label="IRR"
          value={result ? `${(result.irr * 100).toFixed(1)}%` : "—"}
        />
        <MetricCard
          label="Payback"
          value={result ? `${result.payback_months} mo` : "—"}
        />
        <MetricCard
          label="Total ROI"
          value={result ? `${result.total_roi_pct.toFixed(1)}%` : "—"}
        />
      </div>

      {/* Input Form */}
      <SectionCard title="ROI Parameters" className="mb-4">
        <div className="grid grid-cols-4 gap-4 mb-4">
          <div>
            <label className="text-[11px] font-medium block mb-1">
              Deal Size ($)
            </label>
            <input
              type="number"
              value={dealSize}
              onChange={(e) => setDealSize(e.target.value)}
              className="w-full text-xs border border-border rounded-md px-2 py-1.5"
            />
          </div>
          <div>
            <label className="text-[11px] font-medium block mb-1">
              Implementation Cost ($)
            </label>
            <input
              type="number"
              value={implementationCost}
              onChange={(e) => setImplementationCost(e.target.value)}
              className="w-full text-xs border border-border rounded-md px-2 py-1.5"
            />
          </div>
          <div>
            <label className="text-[11px] font-medium block mb-1">
              Annual Benefit ($)
            </label>
            <input
              type="number"
              value={annualBenefit}
              onChange={(e) => setAnnualBenefit(e.target.value)}
              className="w-full text-xs border border-border rounded-md px-2 py-1.5"
            />
          </div>
          <div>
            <label className="text-[11px] font-medium block mb-1">
              Projection Years
            </label>
            <input
              type="number"
              value={timeHorizonYears}
              onChange={(e) => setTimeHorizonYears(e.target.value)}
              min="1"
              max="10"
              className="w-full text-xs border border-border rounded-md px-2 py-1.5"
            />
          </div>
        </div>

        {/* Template selector */}
        {templates.length > 0 && (
          <div className="mb-4">
            <label className="text-[11px] font-medium block mb-1">
              Template (optional)
            </label>
            <select
              value={selectedTemplate ?? ""}
              onChange={(e) =>
                setSelectedTemplate(e.target.value || null)
              }
              className="w-full text-xs border border-border rounded-md px-2 py-1.5"
            >
              <option value="">No template</option>
              {templates.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>
        )}

        <Btn
          variant="primary"
          onClick={handleCalculate}
          disabled={calculateROI.isPending}
          className="gap-1.5"
        >
          {calculateROI.isPending ? (
            "Calculating..."
          ) : (
            <>
              <BarChart3 size={12} />
              Calculate ROI
            </>
          )}
        </Btn>
      </SectionCard>

      {/* Results — Scenario Comparison */}
      {result && scenarioEntries.length > 0 && (
        <SectionCard title="Scenario Comparison" className="mb-4">
          <div className="grid grid-cols-3 gap-4">
            {scenarioEntries.map(([name, scenario]) => (
              <ScenarioCard key={name} name={name} scenario={scenario} />
            ))}
          </div>
        </SectionCard>
      )}

      {/* Annual Projections */}
      {result && result.annual_projections && result.annual_projections.length > 0 && (
        <SectionCard title="Year-over-Year Projections">
          <div className="overflow-x-auto">
            <table className="w-full text-[11px]">
              <thead>
                <tr className="border-b text-left">
                  <th className="py-2 font-semibold">Year</th>
                  <th className="py-2 font-semibold text-right">Benefit</th>
                  <th className="py-2 font-semibold text-right">Cost</th>
                  <th className="py-2 font-semibold text-right">Cumulative Net</th>
                  <th className="py-2 font-semibold text-right">Discounted Benefit</th>
                </tr>
              </thead>
              <tbody>
                {result.annual_projections.map((yr: AnnualProjection, i: number) => (
                  <tr key={i} className="border-b border-border/50">
                    <td className="py-1.5">Year {yr.year}</td>
                    <td className="py-1.5 text-right text-green-600">
                      ${(yr.benefit / 1000).toFixed(0)}K
                    </td>
                    <td className="py-1.5 text-right text-red-600">
                      ${(yr.cost / 1000).toFixed(0)}K
                    </td>
                    <td
                      className={cn(
                        "py-1.5 text-right font-medium",
                        yr.cumulative_net >= 0
                          ? "text-green-600"
                          : "text-red-600"
                      )}
                    >
                      ${(yr.cumulative_net / 1000).toFixed(0)}K
                    </td>
                    <td className="py-1.5 text-right">
                      ${(yr.discounted_benefit / 1000).toFixed(0)}K
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>
      )}

      {/* Industry Benchmarks */}
      {benchmark && (
        <SectionCard title="Industry Benchmarks" className="mt-4">
          <div className="text-[11px] text-muted-foreground mb-2">
            Benchmarks for {benchmark.industry} (sample size: {benchmark.sample_size})
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="border border-border rounded-md p-3">
              <div className="text-[10px] text-muted-foreground">Avg ROI</div>
              <div className="text-[14px] font-bold mt-1">
                {benchmark.avg_roi_pct.toFixed(1)}%
              </div>
            </div>
            <div className="border border-border rounded-md p-3">
              <div className="text-[10px] text-muted-foreground">Avg Payback</div>
              <div className="text-[14px] font-bold mt-1">
                {benchmark.avg_payback_months} mo
              </div>
            </div>
            <div className="border border-border rounded-md p-3">
              <div className="text-[10px] text-muted-foreground">Avg NPV</div>
              <div className="text-[14px] font-bold mt-1">
                ${(benchmark.avg_npv / 1000).toFixed(0)}K
              </div>
            </div>
          </div>
        </SectionCard>
      )}
    </ValueStudioShellComponent>
  );
}
