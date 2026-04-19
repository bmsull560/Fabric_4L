/**
 * Formula Builder — Create and edit value driver formulas
 * 
 * Clean, focused interface for formula authoring with:
 * - Formula definition (name, description, value driver)
 * - Expression editor with syntax highlighting
 * - Variable palette for quick insertion
 * - Industry benchmarks for reference
 */
import { useState, useMemo, useEffect, useRef } from "react";
import { useParams, useLocation } from "wouter";
import {
  Save, CheckCircle2, AlertCircle,
  ChevronRight, Loader2, Target,
} from "lucide-react";
import { Btn, SectionCard } from "@/components/WfPrimitives";
import { useVariables, type Variable, type VariableType, type SourceType } from "@/hooks/useVariables";
import {
  useFormula,
  useCreateFormula,
  useUpdateFormula,
  useEvaluateFormula,
  type FormulaEvaluationInput,
} from "@/hooks/useFormulas";

// ============================================================================
// Type Definitions
// ============================================================================

// VariableType is imported from @/hooks/useVariables
// Local subset for formula-specific variable types
type FormulaVariableType = "rate" | "currency" | "integer";
type VariableSource = "CRM" | "Billing" | "Model" | "Manual";

/** A formula variable with type and source info */
interface FormulaVariable {
  name: string;
  type: FormulaVariableType;
  source: VariableSource;
}

/** A test input for formula evaluation */
interface TestInput {
  label: string;
  value: string;
}


// ============================================================================
// Constants & Mock Data
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

// Default test inputs - will be replaced with dynamic variable sampling
const DEFAULT_TEST_INPUTS: TestInput[] = [
  { label: "Customer_Count", value: "1,000" },
  { label: "Current_Churn_Rate", value: "5%" },
  { label: "Projected_Retention_Lift", value: "2%" },
  { label: "Average_Contract_Value", value: "$50,000" },
  { label: "Implementation_Cost", value: "$100,000" },
];

/** Map API Variable to FormulaVariable format */
function mapVariableToFormulaVariable(variable: Variable): FormulaVariable {
  // Map VariableType to FormulaVariable type (only 'rate' | 'currency' | 'integer')
  const typeMap: Record<string, FormulaVariableType> = {
    rate: 'rate',
    currency: 'currency',
    integer: 'integer',
    float: 'rate', // Map float to rate for formula purposes
    boolean: 'rate', // Map boolean to rate (0/1)
    string: 'integer', // Default fallback
  };

  // Map source to VariableSource
  const sourceMap: Record<SourceType, VariableSource> = {
    'CRM': 'CRM',
    'Billing': 'Billing',
    'ERP': 'CRM', // Map ERP to CRM category
    'Manual': 'Manual',
    'Model': 'Model',
    'API': 'CRM', // Map API to CRM category
    'Database': 'Billing', // Map Database to Billing category
  };

  return {
    name: variable.name,
    type: typeMap[variable.type] || 'integer',
    source: sourceMap[variable.source] || 'Manual',
  };
}


// ============================================================================
// Helper Functions
// ============================================================================

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
  const [formulaDescription, setFormulaDescription] = useState("Calculate ROI from reducing customer churn through predictive analytics");
  const [testInputs, setTestInputs] = useState(DEFAULT_TEST_INPUTS);
  const [evaluationResult, setEvaluationResult] = useState<{
    result: number;
    roi: number;
    roiPercent: number;
    confidence: number;
  } | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

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

  // P1-21: Fetch real variables from API
  const { data: apiVariables, isLoading: variablesLoading, isError: variablesError } = useVariables({ status: 'validated' });

  // Map API variables to FormulaVariable format
  const availableVariables = useMemo(() => {
    if (!apiVariables) return [];
    return apiVariables.map(mapVariableToFormulaVariable);
  }, [apiVariables]);

  const isSaving = isCreating || isUpdating;

  const [saveSuccess, setSaveSuccess] = useState(false);
  const saveTimeoutRef = useRef<number | null>(null);

  // Cleanup timeout on unmount to prevent state updates on unmounted component
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
            saveTimeoutRef.current = window.setTimeout(() => navigate(`/model/value-studio/formulas/${data.formula_id}`), 500);
          },
          onError: (err) => {
            setSaveError(err.message);
          },
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
          onError: (err) => {
            setSaveError(err.message);
          },
        }
      );
    }
  };

  const handleTest = async () => {
    setIsEvaluating(true);
    setSaveError(null);

    // Parse test inputs into evaluation format
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
          if (process.env.NODE_ENV === 'development') {
            console.error('Formula evaluation error:', err);
          }
          setSaveError(err.message);
          setIsEvaluating(false);
        },
      }
    );
  };


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
        <p className="text-sm text-muted-foreground">Create mathematical formulas for value driver calculations.</p>
      </div>

      {saveError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-[13px] text-red-700">
          {saveError}
        </div>
      )}

      {saveSuccess && (
        <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-[13px] text-emerald-700 flex items-center gap-2">
          <CheckCircle2 size={16} />
          Formula saved successfully!
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center gap-6 border-b border-border mb-6">
        {["Tree Explorer", "Normalization", "Formulas"].map((tab) => (
          <button
            key={tab}
            onClick={() => {
              if (tab === "Tree Explorer") navigate("/model/value-studio/explorer");
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
        {/* ── Left main panel ─────────────────────────────────────────────── */}
        <div className="flex-1 space-y-4 max-w-2xl">
          {/* Formula Definition */}
          <SectionCard title="Formula Definition">
            <div className="space-y-4">
              <div>
                <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60 block mb-1.5">Name</label>
                <input
                  value={formulaName}
                  onChange={(e) => setFormulaName(e.target.value)}
                  placeholder="Enter formula name..."
                  className="w-full border border-border rounded-md px-3 py-2 text-[13px] text-foreground bg-white outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                />
              </div>
              <div>
                <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60 block mb-1.5">Description</label>
                <textarea
                  value={formulaDescription}
                  onChange={(e) => setFormulaDescription(e.target.value)}
                  placeholder="Describe what this formula calculates..."
                  rows={2}
                  className="w-full border border-border rounded-md px-3 py-2 text-[12px] text-foreground bg-white outline-none resize-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                />
              </div>
              <div>
                <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60 block mb-1.5">Associated Value Driver</label>
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
                  <ChevronRight size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground rotate-90 pointer-events-none" />
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
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60">Result</span>
                  <div className="text-[20px] font-extrabold text-emerald-700">
                    ${evaluationResult.result.toLocaleString()}
                  </div>
                </div>
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60">ROI</span>
                  <div className="text-[20px] font-extrabold text-emerald-700">
                    {evaluationResult.roiPercent.toFixed(0)}%
                  </div>
                </div>
                <div className="ml-auto">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60">Confidence</span>
                  <div className="text-[14px] font-bold text-foreground">
                    High ({evaluationResult.confidence.toFixed(2)})
                  </div>
                </div>
              </div>
            </SectionCard>
          )}
        </div>

        {/* ── Right panel ─────────────────────────────────────────────────── */}
        <div className="w-[280px] shrink-0 space-y-4">
          {/* Available Variables */}
          <SectionCard title="Available Variables">
            {variablesLoading && (
              <div className="flex items-center gap-2 p-3 text-muted-foreground text-[11px]">
                <Loader2 size={12} className="animate-spin" />
                <span>Loading variables...</span>
              </div>
            )}
            {variablesError && (
              <div className="p-3 text-[11px] text-red-600">
                Failed to load variables
              </div>
            )}
            <div className="space-y-1">
              {availableVariables.map((variable) => (
                <div 
                  key={variable.name} 
                  className="flex items-center gap-2 p-2.5 bg-secondary/30 rounded-md text-[12px] font-mono text-foreground hover:bg-secondary/50 cursor-pointer transition-colors group"
                  onClick={() => {
                    // Insert variable into formula at cursor position
                    const newExpr = formulaExpression + `{${variable.name}}`;
                    setFormulaExpression(newExpr);
                  }}
                  title="Click to insert into formula"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-primary/60 shrink-0 group-hover:bg-primary" />
                  <span className="truncate">{variable.name}</span>
                </div>
              ))}
            </div>
            <button className="w-full mt-3 py-2 text-[11px] text-muted-foreground hover:text-foreground border border-dashed border-border rounded-md hover:border-muted-foreground/50 transition-colors">
              + Add Custom Variable
            </button>
          </SectionCard>

          {/* Industry Benchmarks */}
          <SectionCard title="Industry Benchmarks">
            <div className="space-y-3">
              {[
                { label: "SaaS Average Churn", value: "5–7% / year" },
                { label: "Enterprise ACV", value: "$50K – $500K" },
                { label: "Retention Lift", value: "15–25%" },
              ].map((b) => (
                <div key={b.label} className="p-3 bg-secondary/30 rounded-md">
                  <div className="text-[12px] font-medium text-foreground">{b.label}</div>
                  <div className="text-[11px] text-muted-foreground mt-0.5">{b.value}</div>
                </div>
              ))}
            </div>
          </SectionCard>

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
