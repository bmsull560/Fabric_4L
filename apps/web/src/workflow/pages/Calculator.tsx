/**
 * Calculator Page - Production Implementation
 * 
 * Uses real API data from Layer 3 Calculator service for value lever configuration.
 */
import { useState, useCallback, useMemo, useEffect } from "react";
import { useNavigation } from "@/hooks/useNavigation";
import { useValueLevers, useCreateValueCase } from "@/hooks/useCalculators";
import { Save, RotateCcw, CheckCircle2, AlertTriangle, ArrowRight } from "lucide-react";
import { ProgressBar } from "@/components/blocks";
import { SectionCard } from "@/components/blocks/SectionCard";
import { WorkflowLayout } from "../components/WorkflowLayout";
import { useWorkflowStore } from "../store/workflowStore";
import { STEPS } from "../constants";
import { createFeatureLogger } from "@/lib/telemetry";
import { toast } from "sonner";

const log = createFeatureLogger('Calculator');

export default function Calculator() {
  const { navigateTo } = useNavigation();
  const { setCurrentStep, setGeneratedCaseId, prospect } = useWorkflowStore();
  const { data: leverConfig, isLoading, error } = useValueLevers({
    industry: prospect?.industry,
    company_size: prospect?.employees ? (prospect.employees > 5000 ? "Enterprise" : "SMB") : undefined,
  });
  const createCase = useCreateValueCase();

  const [leverValues, setLeverValues] = useState<Record<string, { valA: number; valB: number }>>({});

  // Initialize lever values when config loads
  useEffect(() => {
    if (leverConfig && Object.keys(leverValues).length === 0) {
      setLeverValues(
        leverConfig.levers.reduce((acc, l) => ({
          ...acc,
          [l.id]: { valA: l.min_value, valB: l.base_value }
        }), {})
      );
    }
  }, [leverConfig, leverValues]);

  const handleSave = async () => {
    if (!prospect?.companyId || !leverConfig) return;

    const leversData = Object.entries(leverValues).map(([id, values]) => ({
      lever_id: id,
      scenario_a: values.valA,
      scenario_b: values.valB,
    }));

    // Calculate scenarios (simplified for MVP)
    const scenarios = [
      {
        name: "Conservative" as const,
        total_value: leverConfig.levers.reduce((sum, l) => {
          const lever = leverValues[l.id];
          if (!lever || l.base_value === 0) return sum;
          return sum + (l.annual_impact * (lever.valA / l.base_value));
        }, 0),
        breakdown: [],
      },
      {
        name: "Expected" as const,
        total_value: leverConfig.levers.reduce((sum, l) => {
          const lever = leverValues[l.id];
          if (!lever || l.base_value === 0) return sum;
          return sum + (l.annual_impact * (lever.valB / l.base_value));
        }, 0),
        breakdown: [],
      },
    ];

    try {
      const result = await createCase.mutateAsync({
        account_id: prospect.companyId,
        levers: leversData,
        scenarios,
        metadata: {
          generated_by: "workflow-calculator",
          confidence_score: 85,
        },
      });
      setGeneratedCaseId(result.case_id);
      setCurrentStep(STEPS.VALUE_CASE);
      navigateTo('workflow-value-case');
    } catch (err) {
      log.error('Failed to save value case', { error: err instanceof Error ? err.message : String(err) });
      toast.error('Failed to save value case. Please try again.');
    }
  };

  const handleReset = () => {
    if (!leverConfig) return;
    setLeverValues(leverConfig.levers.reduce((acc, l) => ({ ...acc, [l.id]: { valA: l.min_value, valB: l.base_value } }), {}));
  };

  const totals = useMemo(() => {
    if (!leverConfig) return { A: 0, B: 0, C: 0 };
    return {
      A: leverConfig.levers.reduce((s, l) => l.base_value === 0 ? s : s + l.annual_impact * ((leverValues[l.id]?.valA || l.min_value) / l.base_value), 0),
      B: leverConfig.levers.reduce((s, l) => l.base_value === 0 ? s : s + l.annual_impact * ((leverValues[l.id]?.valB || l.base_value) / l.base_value), 0),
      C: leverConfig.levers.reduce((s, l) => s + l.annual_impact * 1.25, 0),
    };
  }, [leverValues, leverConfig]);

  const current = totals.B;

  const handleContinue = useCallback(() => {
    setGeneratedCaseId(`case_${Date.now()}`);
    setCurrentStep(STEPS.VALUE_CASE);
    navigateTo('workflow-value-case');
  }, [setGeneratedCaseId, setCurrentStep, navigateTo]);

  return (
    <WorkflowLayout>
      <main className="w-full space-y-4" aria-label="Value Calculator">
        <header className="flex items-center justify-between">
          <div><h1 className="text-xl font-bold text-foreground">Value Calculator</h1><p className="text-sm text-muted-foreground mt-0.5">Prospect-specific scenario modeling. AI pre-filled from Meridian profile.</p></div>
          <div className="flex items-center gap-2">
            <button onClick={handleReset} className="flex items-center gap-2 px-3 py-2 bg-card border border-border rounded-lg text-sm text-muted-foreground hover:bg-muted"><RotateCcw className="w-4 h-4" /> Reset</button>
            <button onClick={handleSave} className="flex items-center gap-2 px-3 py-2 bg-card border border-border rounded-lg text-sm text-muted-foreground hover:bg-muted"><Save className="w-4 h-4" /> Save</button>
            <button onClick={handleContinue} className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold hover:bg-primary/90 shadow-lg shadow-primary/25">
              <ArrowRight className="w-4 h-4" /> Generate Value Case
            </button>
          </div>
        </header>

        {/* Scenario Cards */}
        <section className="flex gap-3">
          {(["A", "B", "C"] as const).map((s) => (
            <div key={s} className={`flex-1 px-5 py-4 rounded-xl border text-left ${s === "B" ? "border-primary bg-primary/5 shadow-sm" : "border-border bg-card"}`}>
              <span className={`text-sm font-semibold ${s === "B" ? "text-primary" : "text-foreground"}`}>{s === "A" ? "Conservative" : s === "B" ? "Expected" : "Optimistic"}</span>
              {s === "B" && <span className="text-[10px] px-1.5 py-0.5 bg-primary text-primary-foreground rounded-full ml-2">Base</span>}
              <p className="text-2xl font-bold text-card-foreground mt-1">${(totals[s] / 1_000_000).toFixed(2)}M</p>
              <p className="text-xs text-muted-foreground">Annual value</p>
            </div>
          ))}
        </section>

        <div className="flex gap-4">
          <SectionCard title="Value Levers — AI Pre-filled" description="Drag to adjust" className="flex-1"
            action={<span className="text-xs text-muted-foreground/60">Confidence indicators</span>}
          >
            {isLoading ? (
              <div className="p-8 text-center text-muted-foreground">Loading lever configuration...</div>
            ) : error ? (
              <div className="p-8 text-center text-destructive">Failed to load lever configuration. Please try again.</div>
            ) : leverConfig ? (
              <div className="space-y-4">
                {leverConfig.levers.map((lever) => (
                  <div key={lever.id} className="flex items-center gap-4 p-4 bg-muted/20 rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-semibold text-foreground">{lever.name}</span>
                        <span className="text-xs text-muted-foreground">${(lever.annual_impact / 1000000).toFixed(2)}M annual impact</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="flex-1">
                          <label className="text-[10px] text-muted-foreground">Conservative</label>
                          <input
                            type="range"
                            min={lever.min_value}
                            max={lever.max_value}
                            value={leverValues[lever.id]?.valA ?? lever.min_value}
                            onChange={(e) => setLeverValues(prev => ({ ...prev, [lever.id]: { valA: Number(e.target.value), valB: prev[lever.id]?.valB ?? lever.base_value } }))}
                            className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer"
                          />
                          <div className="text-[10px] text-center text-muted-foreground mt-0.5">{leverValues[lever.id]?.valA ?? lever.min_value} {lever.unit}</div>
                        </div>
                        <div className="flex-1">
                          <label className="text-[10px] text-muted-foreground">Expected</label>
                          <input
                            type="range"
                            min={lever.min_value}
                            max={lever.max_value}
                            value={leverValues[lever.id]?.valB ?? lever.base_value}
                            onChange={(e) => setLeverValues(prev => ({ ...prev, [lever.id]: { valA: prev[lever.id]?.valA ?? lever.min_value, valB: Number(e.target.value) } }))}
                            className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer"
                          />
                          <div className="text-[10px] text-center text-muted-foreground mt-0.5">{leverValues[lever.id]?.valB ?? lever.base_value} {lever.unit}</div>
                        </div>
                      </div>
                    </div>
                    <div className="w-16 text-right">
                      <ProgressBar value={lever.confidence} max={100} size="sm" />
                      <p className="text-[10px] text-muted-foreground mt-0.5 text-center">{lever.confidence}%</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-muted-foreground">No value levers configured for this account.</div>
            )}
          </SectionCard>

          <aside className="w-72 shrink-0 space-y-4">
            <div className="bg-card rounded-xl border border-border p-4 text-center">
              <p className="text-3xl font-bold text-primary">${(current / 1_000_000).toFixed(2)}M</p>
              <p className="text-xs text-muted-foreground">Total Annual Value</p>
              <div className="space-y-1 text-xs mt-3 pt-3 border-t border-border/60">
                <div className="flex justify-between"><span className="text-muted-foreground">vs. Conservative</span><span className="font-medium text-emerald-500">+${((current - totals.A) / 1_000_000).toFixed(2)}M</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">vs. Optimistic</span><span className="font-medium text-muted-foreground">-${((totals.C - current) / 1_000_000).toFixed(2)}M gap</span></div>
              </div>
            </div>

            <SectionCard title="By Lever">
              <div className="p-4 space-y-3">
                {leverConfig?.levers.map((l) => {
                  const lever = leverValues[l.id];
                  const val = lever ? lever.valB : l.base_value;
                  const pct = current > 0 && l.base_value !== 0 ? (l.annual_impact * (val / l.base_value) / current) * 100 : 0;
                  return (
                    <div key={l.id}>
                      <div className="flex justify-between mb-1"><span className="text-xs text-muted-foreground">{l.name.split(" (")[0]}</span><span className="text-xs font-semibold">{pct.toFixed(0)}%</span></div>
                      <ProgressBar value={pct} max={100} size="sm" />
                    </div>
                  );
                }) || <div className="text-xs text-muted-foreground text-center">No levers loaded</div>}
              </div>
            </SectionCard>

            <div className="bg-card rounded-xl border border-border p-4">
              <h4 className="text-sm font-semibold text-foreground mb-2">Confidence Range</h4>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between"><span className="text-muted-foreground">Low</span><span className="font-mono font-semibold text-foreground">${(totals.A / 1_000_000).toFixed(2)}M</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Expected</span><span className="font-mono font-semibold text-primary">${(totals.B / 1_000_000).toFixed(2)}M</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">High</span><span className="font-mono font-semibold text-foreground">${(totals.C / 1_000_000).toFixed(2)}M</span></div>
              </div>
              <div className="mt-2 h-2 rounded-full overflow-hidden flex"><div className="flex-1 bg-amber-500/30" /><div className="flex-1 bg-primary" /><div className="flex-1 bg-emerald-500/30" /></div>
            </div>
          </aside>
        </div>
      </main>
    </WorkflowLayout>
  );
}
