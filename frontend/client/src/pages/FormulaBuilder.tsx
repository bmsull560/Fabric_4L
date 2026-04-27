/**
 * Formula Builder — Create and edit value driver formulas
 *
 * Clean, focused interface for formula authoring with:
 * - Formula definition (name, description, value driver)
 * - Expression editor with syntax highlighting
 * - Variable palette for quick insertion
 * - Live evaluation with backend POST /v1/formulas/evaluate
 * - Version history panel (useFormulaVersions)
 * - Dependency graph panel (useFormulaDependents / useFormulaDependencies)
 * - What-if scenario panel (useFormulaScenario)
 * - Governance metadata (useFormulaGovernance)
 *
 * Route: /context/formulas/new  (isNew = true)
 *        /context/formulas/:formulaId
 */
import { useState, useMemo, useEffect, useRef } from "react";
import { useParams, useLocation } from "wouter";
import {
  Save, CheckCircle2, AlertCircle, ChevronRight, Loader2,
  Target, GitBranch, Network, Beaker, Shield, Clock,
} from "lucide-react";
import { Btn, SectionCard, Tabs } from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import { useVariables, type Variable, type VariableType, type SourceType } from "@/hooks/useVariables";
import {
  useFormula,
  useCreateFormula,
  useUpdateFormula,
  useEvaluateFormula,
  type FormulaEvaluationInput,
} from "@/hooks/useFormulas";
import { useFormulaVersions, useFormulaGovernance, type FormulaVersion } from "@/hooks/useFormulaVersions";
import { useFormulaDependents, useFormulaDependencies, type DependentAsset } from "@/hooks/useFormulaDependents";
import { useFormulaScenario, type VariableAdjustment, type ScenarioResponse } from "@/hooks/useFormulaScenario";
import { formatRelativeTime } from "@/lib/formatters";

// ============================================================================
// Type Definitions
// ============================================================================
type FormulaVariableType = "rate" | "currency" | "integer";
type VariableSource = "CRM" | "Billing" | "Model" | "Manual";

interface FormulaVariable {
  name: string;
  type: FormulaVariableType;
  source: VariableSource;
}

interface TestInput {
  label: string;
  value: string;
}

// ============================================================================
// Constants
// ============================================================================
const SOURCE_TYPE_COLOR: Record<VariableSource, string> = {
  CRM: "bg-blue-50 text-blue-700",
  Billing: "bg-emerald-50 text-emerald-700",
  Model: "bg-violet-50 text-violet-700",
  Manual: "bg-amber-50 text-amber-700",
};

const DEFAULT_FORMULA_EXPRESSION = `({Customer_Count} *
{Current_Churn_Rate} -
{Projected_Retention_Lift}) *
{Average_Contract_Value} -
{Implementation_Cost}`;

const DEFAULT_TEST_INPUTS: TestInput[] = [
  { label: "Customer_Count", value: "1,000" },
  { label: "Current_Churn_Rate", value: "5%" },
  { label: "Projected_Retention_Lift", value: "2%" },
  { label: "Average_Contract_Value", value: "$50,000" },
  { label: "Implementation_Cost", value: "$100,000" },
];

const VERSION_STATUS_COLOR: Record<string, string> = {
  active: "bg-emerald-50 text-emerald-700",
  approved: "bg-blue-50 text-blue-700",
  draft: "bg-muted/30 text-muted-foreground",
  under_review: "bg-amber-50 text-amber-700",
  deprecated: "bg-red-50 text-red-600",
  retired: "bg-neutral-100 text-neutral-500",
};

/** Map API Variable to FormulaVariable format */
function mapVariableToFormulaVariable(variable: Variable): FormulaVariable {
  const typeMap: Record<string, FormulaVariableType> = {
    rate: "rate", currency: "currency", integer: "integer",
    float: "rate", boolean: "rate", string: "integer",
  };
  const sourceMap: Record<SourceType, VariableSource> = {
    CRM: "CRM", Billing: "Billing", ERP: "CRM",
    Manual: "Manual", Model: "Model", API: "CRM", Database: "Billing",
  };
  return {
    name: variable.name,
    type: typeMap[variable.type] || "integer",
    source: sourceMap[variable.source] || "Manual",
  };
}

// ============================================================================
// Sub-components
// ============================================================================

/** Version History Panel */
function VersionHistoryPanel({ formulaId }: { formulaId: string }) {
  const { data: versions, isLoading } = useFormulaVersions(formulaId);
  const { data: governance } = useFormulaGovernance(formulaId);

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => <Skeleton key={i} className="h-14 w-full" />)}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {governance && (
        <div className="p-3 bg-secondary/30 rounded-lg text-[12px] space-y-1">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Owner</span>
            <span className="font-medium">{governance.owner || "Unassigned"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Review Cycle</span>
            <span className="font-medium">{governance.review_cycle_days} days</span>
          </div>
          {governance.next_review_at && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Next Review</span>
              <span className="font-medium">{formatRelativeTime(governance.next_review_at)}</span>
            </div>
          )}
        </div>
      )}
      <div className="space-y-1.5">
        {(versions || []).map((v: FormulaVersion) => (
          <div
            key={v.version}
            className="flex items-center gap-3 p-2.5 rounded-md hover:bg-secondary/30 transition-colors"
          >
            <div className="w-1.5 h-1.5 rounded-full bg-primary/60 shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-[12px] font-mono font-semibold">v{v.version}</span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${VERSION_STATUS_COLOR[v.status] || "bg-muted/30 text-muted-foreground"}`}>
                  {v.status}
                </span>
              </div>
              <div className="text-[11px] text-muted-foreground truncate">{v.change_summary}</div>
              <div className="text-[10px] text-muted-foreground/60">
                {v.created_by} &middot; {formatRelativeTime(v.created_at)}
              </div>
            </div>
          </div>
        ))}
        {(!versions || versions.length === 0) && (
          <div className="text-[12px] text-muted-foreground text-center py-4">No version history</div>
        )}
      </div>
    </div>
  );
}

/** Dependency Graph Panel */
function DependencyPanel({ formulaId }: { formulaId: string }) {
  const { data: dependents, isLoading: loadingDeps } = useFormulaDependents(formulaId);
  const { data: dependencies, isLoading: loadingDependencies } = useFormulaDependencies(formulaId);

  if (loadingDeps || loadingDependencies) {
    return (
      <div className="space-y-2">
        {[1, 2].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
      </div>
    );
  }

  const renderList = (items: DependentAsset[] | undefined, label: string) => (
    <div>
      <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60 mb-2">{label}</div>
      {(items || []).length === 0 ? (
        <div className="text-[12px] text-muted-foreground py-2">None</div>
      ) : (
        <div className="space-y-1">
          {(items || []).map((item) => (
            <div key={item.id} className="flex items-center gap-2 p-2 bg-secondary/30 rounded-md text-[12px]">
              <span className="font-medium truncate">{item.name}</span>
              <span className="ml-auto text-[10px] text-muted-foreground">{item.type}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-4">
      {renderList(dependencies, "This formula depends on")}
      {renderList(dependents, "Used by")}
    </div>
  );
}

/** What-If Scenario Panel */
function ScenarioPanel({ formulaId }: { formulaId: string }) {
  const [baseCaseId, setBaseCaseId] = useState("");
  const [adjustments, setAdjustments] = useState<VariableAdjustment[]>([
    { name: "", value: 0, original_value: 0 },
  ]);
  const { mutate: runScenario, data: result, isPending, error } = useFormulaScenario();

  const addAdjustment = () => {
    setAdjustments([...adjustments, { name: "", value: 0, original_value: 0 }]);
  };

  const updateAdjustment = (idx: number, field: keyof VariableAdjustment, val: string | number) => {
    const updated = [...adjustments];
    if (field === "name") {
      updated[idx] = { ...updated[idx], name: val as string };
    } else {
      updated[idx] = { ...updated[idx], [field]: Number(val) };
    }
    setAdjustments(updated);
  };

  const removeAdjustment = (idx: number) => {
    if (adjustments.length > 1) {
      setAdjustments(adjustments.filter((_, i) => i !== idx));
    }
  };

  const handleRun = () => {
    if (!baseCaseId.trim()) return;
    runScenario({
      base_case_id: baseCaseId,
      adjustments: adjustments.filter((a) => a.name.trim()),
    });
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60 block mb-1">
          Base Case ID
        </label>
        <input
          value={baseCaseId}
          onChange={(e) => setBaseCaseId(e.target.value)}
          placeholder="e.g. case-abc123"
          className="w-full border border-border rounded-md px-3 py-1.5 text-[12px] bg-white outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
        />
      </div>

      <div>
        <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60 block mb-1">
          Variable Adjustments
        </label>
        <div className="space-y-2">
          {adjustments.map((adj, idx) => (
            <div key={idx} className="flex gap-1.5 items-center">
              <input
                value={adj.name}
                onChange={(e) => updateAdjustment(idx, "name", e.target.value)}
                placeholder="Variable"
                className="flex-1 border border-border rounded-md px-2 py-1 text-[11px] bg-white outline-none focus:ring-1 focus:ring-primary/20"
              />
              <input
                type="number"
                value={adj.original_value || ""}
                onChange={(e) => updateAdjustment(idx, "original_value", e.target.value)}
                placeholder="Original"
                className="w-20 border border-border rounded-md px-2 py-1 text-[11px] bg-white outline-none focus:ring-1 focus:ring-primary/20"
              />
              <input
                type="number"
                value={adj.value || ""}
                onChange={(e) => updateAdjustment(idx, "value", e.target.value)}
                placeholder="New"
                className="w-20 border border-border rounded-md px-2 py-1 text-[11px] bg-white outline-none focus:ring-1 focus:ring-primary/20"
              />
              {adjustments.length > 1 && (
                <button
                  onClick={() => removeAdjustment(idx)}
                  className="text-red-400 hover:text-red-600 text-[14px]"
                >
                  &times;
                </button>
              )}
            </div>
          ))}
        </div>
        <button
          onClick={addAdjustment}
          className="mt-2 text-[11px] text-primary hover:text-primary/80"
        >
          + Add adjustment
        </button>
      </div>

      <Btn
        variant="primary"
        onClick={handleRun}
        disabled={isPending || !baseCaseId.trim()}
        className="w-full"
      >
        {isPending ? (
          <><Loader2 size={11} className="animate-spin mr-1" /> Calculating...</>
        ) : (
          <><Beaker size={11} className="mr-1" /> Run Scenario</>
        )}
      </Btn>

      {error && (
        <div className="p-2 bg-red-50 border border-red-200 rounded text-[11px] text-red-700 flex items-center gap-1.5">
          <AlertCircle size={12} /> {error.message}
        </div>
      )}

      {result && (
        <div className="p-3 bg-secondary/30 rounded-lg space-y-2 text-[12px]">
          <div className="font-semibold text-[13px]">Scenario Results</div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <span className="text-muted-foreground">Original</span>
              <div className="font-bold">${result.original_value.toLocaleString()}</div>
            </div>
            <div>
              <span className="text-muted-foreground">Adjusted</span>
              <div className="font-bold text-primary">${result.adjusted_value.toLocaleString()}</div>
            </div>
            <div>
              <span className="text-muted-foreground">Delta</span>
              <div className={`font-bold ${result.delta_percentage >= 0 ? "text-emerald-700" : "text-red-600"}`}>
                {result.delta_percentage >= 0 ? "+" : ""}{result.delta_percentage.toFixed(1)}%
              </div>
            </div>
            <div>
              <span className="text-muted-foreground">New ROI</span>
              <div className="font-bold">{result.new_roi.toFixed(2)}x</div>
            </div>
            <div>
              <span className="text-muted-foreground">Payback</span>
              <div className="font-bold">{result.new_payback_months} mo</div>
            </div>
          </div>
          {result.warnings && result.warnings.length > 0 && (
            <div className="mt-2 text-[11px] text-amber-700 bg-amber-50 p-2 rounded">
              {result.warnings.map((w, i) => <div key={i}>{w}</div>)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================
interface FormulaBuilderProps {
  isNew?: boolean;
}

export default function FormulaBuilder({ isNew = false }: FormulaBuilderProps) {
  const params = useParams();
  const formulaId = params.formulaId;
  const [, navigate] = useLocation();
  const [tested, setTested] = useState(false);
  const [formulaExpression, setFormulaExpression] = useState(DEFAULT_FORMULA_EXPRESSION);
  const [formulaName, setFormulaName] = useState("Customer Churn Reduction ROI");
  const [formulaDescription, setFormulaDescription] = useState(
    "Calculate ROI from reducing customer churn through predictive analytics"
  );
  const [testInputs, setTestInputs] = useState(DEFAULT_TEST_INPUTS);
  const [evaluationResult, setEvaluationResult] = useState<{
    result: number;
    roi: number;
    roiPercent: number;
    confidence: number;
  } | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [rightTab, setRightTab] = useState("Variables");

  // Fetch existing formula if editing
  const { data: existingFormula, isLoading: isLoadingFormula } = useFormula(
    !isNew && formulaId ? formulaId : null
  );

  // Mutations
  const { mutate: createFormula, isPending: isCreating } = useCreateFormula();
  const { mutate: updateFormula, isPending: isUpdating } = useUpdateFormula();
  const { mutate: evaluateFormula } = useEvaluateFormula();

  // Load existing formula data
  useEffect(() => {
    if (existingFormula && !isNew) {
      setFormulaName(existingFormula.name);
      setFormulaDescription(existingFormula.description || "");
      setFormulaExpression(existingFormula.expression || DEFAULT_FORMULA_EXPRESSION);
    }
  }, [existingFormula, isNew]);

  // Fetch real variables from API
  const {
    data: apiVariables,
    isLoading: variablesLoading,
    isError: variablesError,
  } = useVariables({ status: "validated" });

  const availableVariables = useMemo(() => {
    if (!apiVariables) return [];
    return apiVariables.map(mapVariableToFormulaVariable);
  }, [apiVariables]);

  const isSaving = isCreating || isUpdating;
  const [saveSuccess, setSaveSuccess] = useState(false);
  const saveTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        window.clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

  const handleSave = () => {
    setSaveError(null);
    setSaveSuccess(false);
    if (isNew) {
      createFormula(
        {
          name: formulaName,
          description: formulaDescription,
          expression: formulaExpression,
          variables: availableVariables.map((v) => v.name),
        },
        {
          onSuccess: (data) => {
            setSaveSuccess(true);
            saveTimeoutRef.current = window.setTimeout(
              () => navigate(`/context/formulas/${data.formula_id}`),
              500
            );
          },
          onError: (err) => setSaveError(err.message),
        }
      );
    } else if (formulaId) {
      updateFormula(
        {
          formulaId,
          name: formulaName,
          description: formulaDescription,
          expression: formulaExpression,
          variables: availableVariables.map((v) => v.name),
        },
        {
          onSuccess: () => {
            setSaveSuccess(true);
            saveTimeoutRef.current = window.setTimeout(() => setSaveSuccess(false), 3000);
          },
          onError: (err) => setSaveError(err.message),
        }
      );
    }
  };

  const handleTest = async () => {
    setIsEvaluating(true);
    setSaveError(null);
    const inputs = testInputs.map((input) => {
      const parsed = parseFloat(input.value.replace(/[$,%]/g, ""));
      const value = isNaN(parsed) ? 0 : parsed;
      return {
        name: input.label,
        value,
        unit: input.value.includes("$") ? "USD" : input.value.includes("%") ? "percent" : undefined,
      };
    });
    evaluateFormula(
      {
        formulaId: isNew ? undefined : formulaId,
        expression: formulaExpression,
        inputs,
      },
      {
        onSuccess: (result) => {
          const costInput = inputs.find((i) => i.name.includes("Cost"));
          const costValue = costInput?.value ?? 0;
          setEvaluationResult({
            result: result.result,
            roi: result.result - costValue,
            roiPercent: ((result.result - costValue) / (costValue || 1)) * 100,
            confidence: result.confidence,
          });
          setTested(true);
          setIsEvaluating(false);
        },
        onError: (err) => {
          if (process.env.NODE_ENV === "development") {
            console.error("Formula evaluation error:", err);
          }
          setSaveError(err.message);
          setIsEvaluating(false);
        },
      }
    );
  };

  // Right panel tabs (edit mode only)
  const rightTabs = isNew
    ? ["Variables"]
    : ["Variables", "Versions", "Dependencies", "Scenario"];

  if (isLoadingFormula) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <Loader2 size={32} className="animate-spin text-muted-foreground/60" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-[11px] text-muted-foreground mb-2">
        <span>Value Trees</span>
        <ChevronRight size={12} />
        <span>Formulas</span>
        <ChevronRight size={12} />
        <span className="text-foreground">{isNew ? "New Formula" : "Edit Formula"}</span>
      </div>

      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-foreground mb-1">Formula Builder</h1>
        <p className="text-sm text-muted-foreground">
          Create mathematical formulas for value driver calculations.
        </p>
      </div>

      {saveError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-[13px] text-red-700 flex items-center gap-2">
          <AlertCircle size={14} /> {saveError}
        </div>
      )}
      {saveSuccess && (
        <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-[13px] text-emerald-700 flex items-center gap-2">
          <CheckCircle2 size={16} /> Formula saved successfully!
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center gap-6 border-b border-border mb-6">
        {["Tree Explorer", "Normalization", "Formulas"].map((tab) => (
          <button
            key={tab}
            onClick={() => {
              if (tab === "Tree Explorer") navigate("/context/value-trees/explorer");
              if (tab === "Normalization") navigate("/model/value-studio/normalization");
            }}
            className={`pb-3 text-sm font-medium transition-colors relative ${
              tab === "Formulas"
                ? "text-primary"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab}
            {tab === "Formulas" && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
            )}
          </button>
        ))}
      </div>

      <div className="flex gap-6">
        {/* Left main panel */}
        <div className="flex-1 space-y-4 max-w-2xl">
          {/* Formula Definition */}
          <SectionCard title="Formula Definition">
            <div className="space-y-4">
              <div>
                <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60 block mb-1.5">
                  Name
                </label>
                <input
                  value={formulaName}
                  onChange={(e) => setFormulaName(e.target.value)}
                  placeholder="Enter formula name..."
                  className="w-full border border-border rounded-md px-3 py-2 text-[13px] text-foreground bg-white outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                />
              </div>
              <div>
                <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60 block mb-1.5">
                  Description
                </label>
                <textarea
                  value={formulaDescription}
                  onChange={(e) => setFormulaDescription(e.target.value)}
                  placeholder="Describe what this formula calculates..."
                  rows={2}
                  className="w-full border border-border rounded-md px-3 py-2 text-[12px] text-foreground bg-white outline-none resize-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                />
              </div>
              <div>
                <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60 block mb-1.5">
                  Associated Value Driver
                </label>
                <div className="relative">
                  <select
                    className="w-full border border-border rounded-md px-3 py-2 text-[13px] text-foreground bg-white outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary appearance-none"
                    defaultValue=""
                  >
                    <option value="" disabled>Select a value driver...</option>
                    <option value="revenue_retention">Revenue Retention</option>
                    <option value="cost_reduction">Cost Reduction</option>
                    <option value="efficiency_gain">Efficiency Gain</option>
                    <option value="risk_mitigation">Risk Mitigation</option>
                  </select>
                  <ChevronRight
                    size={14}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground rotate-90 pointer-events-none"
                  />
                </div>
              </div>
            </div>
          </SectionCard>

          {/* Formula Expression */}
          <SectionCard title="Formula Expression">
            <div className="relative">
              <textarea
                value={formulaExpression}
                onChange={(e) => setFormulaExpression(e.target.value)}
                placeholder="Enter formula expression using {variable_name} syntax..."
                className="w-full h-40 bg-slate-900 rounded-lg p-4 font-mono text-[13px] text-slate-100 leading-relaxed outline-none resize-none focus:ring-2 focus:ring-primary/20"
                spellCheck={false}
              />
              <div className="absolute bottom-3 left-4 flex gap-2">
                <Btn
                  variant="primary"
                  onClick={handleTest}
                  disabled={isEvaluating || !formulaExpression.trim()}
                >
                  {isEvaluating ? (
                    <Loader2 size={11} className="animate-spin" />
                  ) : (
                    <Target size={11} />
                  )}
                  {isEvaluating ? " Testing..." : " Test with Sample Data"}
                </Btn>
              </div>
            </div>
          </SectionCard>

          {/* Test Results */}
          {tested && evaluationResult && (
            <SectionCard title="Test Results">
              <div className="space-y-1.5 mb-3">
                {testInputs.map((input, idx) => (
                  <div key={input.label} className="flex justify-between text-[12px]">
                    <span className="text-muted-foreground font-mono">{input.label}:</span>
                    <input
                      type="text"
                      value={input.value}
                      onChange={(e) => {
                        const newInputs = [...testInputs];
                        newInputs[idx].value = e.target.value;
                        setTestInputs(newInputs);
                      }}
                      className="font-semibold text-foreground bg-transparent border-b border-border focus:border-primary outline-none text-right w-32"
                    />
                  </div>
                ))}
              </div>
              <div className="border-t border-border/50 pt-3 flex items-center gap-6">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60">
                    Result
                  </span>
                  <div className="text-[20px] font-extrabold text-emerald-700">
                    ${evaluationResult.result.toLocaleString()}
                  </div>
                </div>
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60">
                    ROI
                  </span>
                  <div className="text-[20px] font-extrabold text-emerald-700">
                    {evaluationResult.roiPercent.toFixed(0)}%
                  </div>
                </div>
                <div className="ml-auto">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60">
                    Confidence
                  </span>
                  <div className="text-[14px] font-bold text-foreground">
                    High ({evaluationResult.confidence.toFixed(2)})
                  </div>
                </div>
              </div>
            </SectionCard>
          )}
        </div>

        {/* Right panel */}
        <div className="w-[300px] shrink-0 space-y-4">
          {/* Tab selector */}
          <Tabs tabs={rightTabs} active={rightTab} onChange={setRightTab} />

          {/* Variables tab */}
          {rightTab === "Variables" && (
            <SectionCard title="Available Variables">
              {variablesLoading && (
                <div className="flex items-center gap-2 p-3 text-muted-foreground text-[11px]">
                  <Loader2 size={12} className="animate-spin" />
                  <span>Loading variables...</span>
                </div>
              )}
              {variablesError && (
                <div className="p-3 text-[11px] text-red-600">Failed to load variables</div>
              )}
              <div className="space-y-1">
                {availableVariables.map((variable) => (
                  <div
                    key={variable.name}
                    className="flex items-center gap-2 p-2.5 bg-secondary/30 rounded-md text-[12px] font-mono text-foreground hover:bg-secondary/50 cursor-pointer transition-colors group"
                    onClick={() => {
                      setFormulaExpression(formulaExpression + `{${variable.name}}`);
                    }}
                    title="Click to insert into formula"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-primary/60 shrink-0 group-hover:bg-primary" />
                    <span className="truncate">{variable.name}</span>
                    <span className={`ml-auto text-[9px] px-1.5 py-0.5 rounded-full ${SOURCE_TYPE_COLOR[variable.source]}`}>
                      {variable.source}
                    </span>
                  </div>
                ))}
              </div>
              <button className="w-full mt-3 py-2 text-[11px] text-muted-foreground hover:text-foreground border border-dashed border-border rounded-md hover:border-muted-foreground/50 transition-colors">
                + Add Custom Variable
              </button>
            </SectionCard>
          )}

          {/* Versions tab */}
          {rightTab === "Versions" && formulaId && (
            <SectionCard title="Version History">
              <VersionHistoryPanel formulaId={formulaId} />
            </SectionCard>
          )}

          {/* Dependencies tab */}
          {rightTab === "Dependencies" && formulaId && (
            <SectionCard title="Dependencies">
              <DependencyPanel formulaId={formulaId} />
            </SectionCard>
          )}

          {/* Scenario tab */}
          {rightTab === "Scenario" && formulaId && (
            <SectionCard title="What-If Scenario">
              <ScenarioPanel formulaId={formulaId} />
            </SectionCard>
          )}

          {/* Save Button */}
          <Btn
            variant="primary"
            onClick={handleSave}
            disabled={isSaving || !formulaName.trim()}
            className="w-full"
          >
            {isSaving ? (
              <>
                <Loader2 size={11} className="animate-spin mr-2" />
                Saving...
              </>
            ) : (
              <>
                <Save size={11} className="mr-2" />
                Save Formula
              </>
            )}
          </Btn>
        </div>
      </div>
    </div>
  );
}
