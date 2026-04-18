/**
 * Screen 6 — Formula Studio (formerly Formula Builder)
 * Design: Refined Enterprise SaaS
 * Spec change: Reframed as a governed admin workspace with version history,
 * draft/active status, approval workflow, and dependency mapping.
 * Progressive disclosure: basic expression authoring visible by default;
 * governance controls revealed under "Governance" tab.
 */
import { useState, useMemo, useEffect, useRef } from "react";
import type { ReactNode } from "react";
import { useParams, useLocation } from "wouter";
import {
  Play, Save, X, Plus, GitBranch, CheckCircle2, Clock, AlertCircle,
  Lock, Unlock, History, ChevronRight, Users, Tag, Link2,
  Loader2, ArrowLeft,
} from "lucide-react";
import { PageHeader, Btn, SectionCard, Tabs } from "@/components/WfPrimitives";
import { useVariables, type Variable, type VariableType, type SourceType } from "@/hooks/useVariables";
import {
  useFormula,
  useCreateFormula,
  useUpdateFormula,
  useSubmitFormula,
  useApproveFormula,
  useEvaluateFormula,
  type FormulaEvaluationInput,
} from "@/hooks/useFormulas";
import {
  useFormulaVersions,
  type FormulaVersion,
} from "@/hooks/useFormulaVersions";
import {
  useFormulaDependents,
  type DependentAsset,
} from "@/hooks/useFormulaDependents";

// ============================================================================
// Type Definitions
// ============================================================================

// VariableType is imported from @/hooks/useVariables
// Local subset for formula-specific variable types
type FormulaVariableType = "rate" | "currency" | "integer";
type VariableSource = "CRM" | "Billing" | "Model" | "Manual";
type FormulaStatus = "draft" | "pending" | "approved" | "archived";
type ActivationState = "draft" | "pending" | "approved";
type DependentType = "Business Case" | "Value Tree" | "Workflow";

/** A variable bound to a formula with type and source information */
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

/** A version entry in the formula's history */
interface VersionEntry {
  version: string;
  author: string;
  date: string;
  status: FormulaStatus;
  note: string;
}

/** A dependent asset that references this formula */
interface Dependent {
  type: DependentType;
  name: string;
  pack: string;
}

/** Configuration for rendering a status badge */
interface StatusConfig {
  label: string;
  color: string;
  icon: ReactNode;
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

const VAR_TYPE_COLOR: Record<FormulaVariableType, string> = {
  rate: "bg-cyan-100 text-cyan-700",
  currency: "bg-emerald-100 text-emerald-700",
  integer: "bg-muted/30 text-muted-foreground",
};

const DEFAULT_FORMULA_EXPRESSION = `// Enter your formula expression here
// Example: ARR = MRR * 12
// Use {variable_name} to reference variables`;

// Default test inputs - will be replaced with dynamic variable sampling
const DEFAULT_TEST_INPUTS: TestInput[] = [
  { label: "Customer_Count", value: "1,000" },
  { label: "Avg_Contract_Value", value: "$50,000" },
];

const ACTIVATION_STATUS_CONFIG: Record<ActivationState, StatusConfig> = {
  draft: {
    label: "Draft",
    color: "bg-muted/30 text-muted-foreground",
    icon: <Clock size={11} />,
  },
  pending: {
    label: "Pending Approval",
    color: "bg-amber-50 text-amber-700",
    icon: <AlertCircle size={11} />,
  },
  approved: {
    label: "Active",
    color: "bg-emerald-50 text-emerald-700",
    icon: <CheckCircle2 size={11} />,
  },
};

const VERSION_STATUS_COLORS: Record<FormulaStatus, string> = {
  approved: "bg-emerald-50 text-emerald-700",
  pending: "bg-amber-50 text-amber-700",
  draft: "bg-muted/30 text-muted-foreground",
  archived: "bg-muted/20 text-muted-foreground/60",
};

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
// Sub-components
// ============================================================================

interface ActivationButtonProps {
  state: ActivationState;
  onStateChange: (state: ActivationState) => void;
}

/**
 * Renders the appropriate action button based on formula activation state.
 * - Draft: Submit for Approval
 * - Pending: Approve
 * - Approved: Revise
 */
function ActivationButton({ state, onStateChange }: ActivationButtonProps) {
  switch (state) {
    case "draft":
      return (
        <Btn variant="primary" onClick={() => onStateChange("pending")}>
          Submit for Approval
        </Btn>
      );
    case "pending":
      return (
        <Btn variant="primary" onClick={() => onStateChange("approved")}>
          <CheckCircle2 size={11} /> Approve
        </Btn>
      );
    case "approved":
      return (
        <Btn variant="ghost" onClick={() => onStateChange("draft")}>
          <Unlock size={11} /> Revise
        </Btn>
      );
  }
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

  const [activeTab, setActiveTab] = useState("Expression");
  const [tested, setTested] = useState(false);
  const [activationState, setActivationState] = useState<ActivationState>("draft");
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

  // Fetch version history and dependents
  const { data: versionHistory, isLoading: versionsLoading } = useFormulaVersions(
    !isNew && formulaId ? formulaId : null
  );
  const { data: dependents, isLoading: dependentsLoading } = useFormulaDependents(
    !isNew && formulaId ? formulaId : null
  );

  // Mutations
  const { mutate: createFormula, isPending: isCreating } = useCreateFormula();
  const { mutate: updateFormula, isPending: isUpdating } = useUpdateFormula();
  const { mutate: submitFormula, isPending: isSubmitting } = useSubmitFormula();
  const { mutate: approveFormula, isPending: isApproving } = useApproveFormula();
  const { mutate: evaluateFormula } = useEvaluateFormula();

  // Load existing formula data
  useEffect(() => {
    if (existingFormula && !isNew) {
      setFormulaName(existingFormula.name);
      setFormulaDescription(existingFormula.description || "");
      setFormulaExpression(existingFormula.expression || DEFAULT_FORMULA_EXPRESSION);
      setActivationState((existingFormula.status as ActivationState) || "draft");
    }
  }, [existingFormula, isNew]);

  // P1-21: Fetch real variables from API
  const { data: apiVariables, isLoading: variablesLoading, isError: variablesError } = useVariables({ status: 'validated' });

  // Map API variables to FormulaVariable format
  const availableVariables = useMemo(() => {
    if (!apiVariables) return [];
    return apiVariables.map(mapVariableToFormulaVariable);
  }, [apiVariables]);

  const statusConfig = ACTIVATION_STATUS_CONFIG[activationState];

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
          setSaveError(err.message);
          setIsEvaluating(false);
        },
      }
    );
  };

  // Valid activation state transitions
  const VALID_TRANSITIONS: Record<ActivationState, ActivationState[]> = {
    draft: ["pending"],
    pending: ["approved", "draft"],
    approved: ["draft"], // Requires revision workflow
  };

  const canTransition = (from: ActivationState, to: ActivationState): boolean => {
    return VALID_TRANSITIONS[from]?.includes(to) ?? false;
  };

  const handleActivationChange = (newState: ActivationState) => {
    if (!formulaId || isNew) {
      // In new formula mode, only allow valid transitions
      if (canTransition(activationState, newState)) {
        setActivationState(newState);
      }
      return;
    }

    // Validate transition before calling API
    if (!canTransition(activationState, newState)) {
      setSaveError(`Invalid state transition from ${activationState} to ${newState}`);
      return;
    }

    if (newState === "pending" && activationState === "draft") {
      submitFormula(formulaId, {
        onSuccess: () => setActivationState(newState),
        onError: (err) => setSaveError(err.message),
      });
    } else if (newState === "approved" && activationState === "pending") {
      approveFormula(
        { formulaId, action: "approve" },
        {
          onSuccess: () => setActivationState(newState),
          onError: (err) => setSaveError(err.message),
        }
      );
    } else if (newState === "draft" && activationState === "approved") {
      // Revise workflow: move from approved back to draft
      setActivationState(newState);
    } else if (newState === "draft" && activationState === "pending") {
      // Reject or request changes: move from pending back to draft
      // This could be extended to call a reject API if one exists
      setActivationState(newState);
    }
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
      {/* Back button for edit mode */}
      {!isNew && (
        <button
          onClick={() => navigate("/model/value-studio/formulas")}
          className="flex items-center gap-1 text-[12px] text-muted-foreground hover:text-foreground mb-4 transition-colors"
        >
          <ArrowLeft size={14} /> Back to formulas
        </button>
      )}

      {/* Header with governance status */}
      <div className="flex items-start justify-between mb-5">
        <PageHeader
          breadcrumbs={[{ label: "Value Models" }, { label: "Formula Studio" }, { label: isNew ? "New Formula" : formulaName }]}
          title={formulaName}
          subtitle={isNew ? "Create new formula" : `Governed formula asset — ${activationState}`}
        />
        <div className="flex items-center gap-2 shrink-0">
          <span className={`flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-1 rounded-full ${statusConfig.color}`}>
            {statusConfig.icon} {statusConfig.label}
          </span>
          <ActivationButton state={activationState} onStateChange={handleActivationChange} />
        </div>
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

      {/* Tabs: Expression | Variables | Governance | Dependencies */}
      <Tabs
        tabs={["Expression", "Variables", "Governance", "Dependencies"]}
        active={activeTab}
        onChange={setActiveTab}
      />

      <div className="flex gap-5 mt-4">
        {/* ── Left main panel ─────────────────────────────────────────────── */}
        <div className="flex-1 space-y-4">

          {/* Expression tab */}
          {activeTab === "Expression" && (
            <>
              <SectionCard title="Formula Definition">
                <div className="space-y-3">
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60 block mb-1">Name</label>
                    <input
                      value={formulaName}
                      onChange={(e) => setFormulaName(e.target.value)}
                      placeholder="Enter formula name..."
                      className="w-full border border-border rounded-md px-3 py-2 text-[13px] text-foreground bg-white outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60 block mb-1">Description</label>
                    <textarea
                      value={formulaDescription}
                      onChange={(e) => setFormulaDescription(e.target.value)}
                      placeholder="Describe what this formula calculates..."
                      rows={2}
                      className="w-full border border-border rounded-md px-3 py-2 text-[12px] text-foreground bg-white outline-none resize-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                    />
                  </div>
                </div>
              </SectionCard>

              <SectionCard title="Formula Expression">
                <textarea
                  value={formulaExpression}
                  onChange={(e) => setFormulaExpression(e.target.value)}
                  placeholder="Enter formula expression using {variable_name} syntax..."
                  className="w-full h-32 bg-[#0d1117] rounded-lg p-4 font-mono text-[12px] text-[#c9d1d9] leading-relaxed outline-none resize-none focus:ring-2 focus:ring-blue-500/20"
                  spellCheck={false}
                />
                <div className="flex gap-2 mt-3">
                  <Btn
                    variant="primary"
                    onClick={handleTest}
                    disabled={isEvaluating || !formulaExpression.trim()}
                  >
                    {isEvaluating ? (
                      <Loader2 size={11} className="animate-spin" />
                    ) : (
                      <Play size={11} />
                    )}
                    {isEvaluating ? " Testing..." : " Test with Sample Data"}
                  </Btn>
                  <Btn
                    variant="ghost"
                    onClick={handleSave}
                    disabled={isSaving || !formulaName.trim()}
                  >
                    {isSaving ? (
                      <Loader2 size={11} className="animate-spin" />
                    ) : (
                      <Save size={11} />
                    )}
                    {isSaving ? " Saving..." : " Save Draft"}
                  </Btn>
                </div>
              </SectionCard>

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
                          className="font-semibold text-foreground bg-transparent border-b border-border focus:border-blue-500 outline-none text-right w-32"
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
            </>
          )}

          {/* Variables tab */}
          {activeTab === "Variables" && (
            <SectionCard title="Variable Registry — Bound Variables">
              {variablesLoading && (
                <div className="flex items-center gap-2 p-4 text-muted-foreground">
                  <Loader2 size={16} className="animate-spin" />
                  <span className="text-[13px]">Loading variables...</span>
                </div>
              )}
              {variablesError && (
                <div className="p-4 bg-red-50 text-red-700 rounded-lg text-[13px]">
                  Failed to load variables. Please try again.
                </div>
              )}
              <div className="space-y-2">
                {availableVariables.map((variable) => (
                  <div key={variable.name} className="flex items-center gap-3 p-3 bg-muted/20 rounded-lg border border-border/50">
                    <span className="w-2 h-2 rounded-full bg-violet-400 shrink-0"/>
                    <span className="flex-1 font-mono text-[12px] text-foreground">{variable.name}</span>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${VAR_TYPE_COLOR[variable.type]}`}>{variable.type}</span>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${SOURCE_TYPE_COLOR[variable.source]}`}>{variable.source}</span>
                    <button className="text-[11px] text-muted-foreground/60 hover:text-foreground">Edit binding</button>
                  </div>
                ))}
              </div>
              <Btn variant="ghost" className="mt-3 text-[11px]">
                <Plus size={11}/> Add Variable from Registry
              </Btn>
            </SectionCard>
          )}

          {/* Governance tab */}
          {activeTab === "Governance" && (
            <div className="space-y-4">
              <SectionCard title="Version History">
                {versionsLoading && (
                  <div className="flex items-center gap-2 p-4 text-muted-foreground">
                    <Loader2 size={16} className="animate-spin" />
                    <span className="text-[13px]">Loading versions...</span>
                  </div>
                )}
                <div className="space-y-2">
                  {versionHistory?.map((version: FormulaVersion, index: number) => (
                    <div key={index} className="flex items-start gap-3 p-3 rounded-lg border border-border/50 bg-muted/20">
                      <div className="mt-0.5">
                        {version.status === "approved" && <CheckCircle2 size={14} className="text-emerald-500"/>}
                        {version.status === "active" && <CheckCircle2 size={14} className="text-emerald-600"/>}
                        {version.status === "draft"    && <Clock size={14} className="text-muted-foreground/60"/>}
                        {version.status === "under_review" && <AlertCircle size={14} className="text-amber-500"/>}
                        {version.status === "deprecated" && <History size={14} className="text-muted-foreground/60"/>}
                        {version.status === "retired" && <History size={14} className="text-muted-foreground/40"/>}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[12px] font-bold text-foreground">{version.version}</span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${VERSION_STATUS_COLORS[version.status as FormulaStatus] || VERSION_STATUS_COLORS.draft}`}>
                            {version.status}
                          </span>
                        </div>
                        <p className="text-[11px] text-muted-foreground mt-0.5">{version.change_summary}</p>
                        <p className="text-[10px] text-muted-foreground/60 mt-0.5">{version.created_by} · {new Date(version.created_at).toLocaleDateString()}</p>
                      </div>
                      {version.status !== "draft" && version.status !== "under_review" && (
                        <button className="text-[11px] text-blue-600 hover:underline shrink-0">Restore</button>
                      )}
                    </div>
                  ))}
                </div>
                {versionHistory?.length === 0 && !versionsLoading && (
                  <div className="text-center py-4 text-muted-foreground/60 text-[12px]">
                    No version history available.
                  </div>
                )}
              </SectionCard>

              <SectionCard title="Approval Workflow">
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 bg-muted/20 rounded-lg border border-border/50">
                    <Users size={14} className="text-muted-foreground/60"/>
                    <div className="flex-1">
                      <p className="text-[12px] font-semibold text-foreground">Required Approvers</p>
                      <p className="text-[11px] text-muted-foreground">Finance Team · Formula Governance Admin</p>
                    </div>
                    <button className="text-[11px] text-blue-600 hover:underline">Edit</button>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-muted/20 rounded-lg border border-border/50">
                    <Tag size={14} className="text-muted-foreground/60"/>
                    <div className="flex-1">
                      <p className="text-[12px] font-semibold text-foreground">Scope</p>
                      <p className="text-[11px] text-muted-foreground">Tenant: Acme Corp · Pack: Enterprise Security ROI</p>
                    </div>
                    <button className="text-[11px] text-blue-600 hover:underline">Edit</button>
                  </div>
                </div>
              </SectionCard>
            </div>
          )}

          {/* Dependencies tab */}
          {activeTab === "Dependencies" && (
            <SectionCard title="Used By">
              {dependentsLoading && (
                <div className="flex items-center gap-2 p-4 text-muted-foreground">
                  <Loader2 size={16} className="animate-spin" />
                  <span className="text-[13px]">Loading dependents...</span>
                </div>
              )}
              <div className="space-y-2">
                {dependents?.map((dependent: DependentAsset, index: number) => (
                  <div key={index} className="flex items-center gap-3 p-3 bg-muted/20 rounded-lg border border-border/50">
                    <Link2 size={13} className="text-muted-foreground/60 shrink-0"/>
                    <div className="flex-1">
                      <p className="text-[12px] font-semibold text-foreground">{dependent.name}</p>
                      <p className="text-[10px] text-muted-foreground/60">{dependent.type} · {dependent.pack || 'No Pack'}</p>
                    </div>
                    <ChevronRight size={13} className="text-muted-foreground/40"/>
                  </div>
                ))}
              </div>
              {dependents?.length === 0 && !dependentsLoading && (
                <div className="text-center py-4 text-muted-foreground/60 text-[12px]">
                  No dependent assets found.
                </div>
              )}
              {dependents && dependents.length > 0 && (
                <p className="text-[11px] text-muted-foreground/60 mt-3">
                  Activating or deprecating this formula will affect {dependents.length} downstream assets.
                </p>
              )}
            </SectionCard>
          )}
        </div>

        {/* ── Right panel ─────────────────────────────────────────────────── */}
        <div className="w-[220px] shrink-0 space-y-4">
          <SectionCard title="Available Variables">
            {variablesLoading && (
              <div className="flex items-center gap-2 p-2 text-muted-foreground text-[11px]">
                <Loader2 size={12} className="animate-spin" />
                <span>Loading...</span>
              </div>
            )}
            <div className="space-y-1.5">
              {availableVariables.map((variable) => (
                <div key={variable.name} className="flex items-center gap-2 p-2 bg-muted/20 rounded border border-border/50 text-[11px] font-mono text-foreground hover:bg-muted/30 cursor-pointer transition-colors">
                  <span className="w-2 h-2 rounded-full bg-violet-400 shrink-0"/>
                  <span className="truncate">{variable.name}</span>
                </div>
              ))}
            </div>
            <Btn variant="ghost" className="w-full mt-2 justify-center text-[11px]">
              <Plus size={11}/> Add Variable
            </Btn>
          </SectionCard>

          <SectionCard title="Industry Benchmarks">
            <div className="space-y-2 text-[11px] text-muted-foreground">
              {[
                { label: "SaaS Average Churn",  value: "5–7% / year" },
                { label: "Enterprise ACV",       value: "$50K – $500K" },
                { label: "Retention Lift",       value: "15–25%" },
              ].map(b => (
                <div key={b.label} className="p-2 bg-muted/20 rounded border border-border/50">
                  <div className="font-semibold text-foreground">{b.label}</div>
                  <div className="text-muted-foreground">{b.value}</div>
                </div>
              ))}
            </div>
            <Btn variant="ghost" className="w-full mt-2 justify-center text-[11px]">Apply Benchmark</Btn>
          </SectionCard>

          <SectionCard title="Formula Metadata">
            <div className="space-y-2 text-[11px]">
              <div className="flex justify-between">
                <span className="text-muted-foreground/60">Version</span>
                <span className="font-semibold text-foreground">
                  {isNew ? 'New' : existingFormula?.version || 'v1.0.0'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground/60">Status</span>
                <span className="font-semibold text-foreground capitalize">
                  {activationState.replace('_', ' ')}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground/60">Variables</span>
                <span className="font-semibold text-foreground">
                  {availableVariables.length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground/60">Used by</span>
                <span className="font-semibold text-foreground">
                  {dependentsLoading ? '...' : dependents?.length || 0} assets
                </span>
              </div>
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
