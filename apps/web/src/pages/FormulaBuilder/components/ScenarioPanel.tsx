/**
 * What-If Scenario Panel - Allows testing formula with variable adjustments
 */
import { useState } from "react";
import { AlertCircle, Beaker, Loader2 } from "lucide-react";
import { useFormulaScenario, type VariableAdjustment, type ScenarioResponse } from "@/hooks/useFormulaScenario";
import { Btn } from "@/components/ui/fabric";

interface ScenarioPanelProps {
  formulaId: string;
}

// UI-specific type with stable id for React keys
export type UIVariableAdjustment = VariableAdjustment & {
  id: string;
};

// Generate stable ID with fallback for older browsers
const generateId = () => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
};

// Convert UI state to API DTO (strips id)
export const toVariableAdjustmentDto = (adj: UIVariableAdjustment): VariableAdjustment => ({
  name: adj.name,
  value: adj.value,
  original_value: adj.original_value,
});

// Create new UI adjustment with stable id
export const createUiAdjustment = (base: Partial<VariableAdjustment> = {}): UIVariableAdjustment => ({
  ...base,
  id: generateId(),
  name: base.name || "",
  value: base.value ?? 0,
  original_value: base.original_value ?? 0,
});

export function ScenarioPanel({ formulaId }: ScenarioPanelProps) {
  const [baseCaseId, setBaseCaseId] = useState("");
  const [adjustments, setAdjustments] = useState<UIVariableAdjustment[]>([
    createUiAdjustment({ name: "", value: 0, original_value: 0 }),
  ]);
  const { mutate: runScenario, data: result, isPending, error } = useFormulaScenario();

  const addAdjustment = () => {
    setAdjustments([...adjustments, createUiAdjustment({ name: "", value: 0, original_value: 0 })]);
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
      adjustments: adjustments
        .filter((a) => a.name.trim())
        .map(toVariableAdjustmentDto),
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
            <div key={adj.id} className="flex gap-1.5 items-center">
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
                  type="button"
                  onClick={() => removeAdjustment(idx)}
                  className="text-red-400 hover:text-red-600 text-[14px] w-6 h-6 flex items-center justify-center rounded hover:bg-red-50"
                  aria-label="Remove adjustment"
                >
                  &times;
                </button>
              )}
            </div>
          ))}
        </div>
        <button
          type="button"
          onClick={addAdjustment}
          className="mt-2 text-[11px] text-primary hover:text-primary/80 border border-dashed border-primary/30 rounded-md px-2 py-1"
          aria-label="Add variable adjustment"
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
              {result.warnings.map((w, i) => <div key={`warning-${i}`}>{w}</div>)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
