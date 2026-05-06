import { useState } from "react";
import { Loader2, AlertCircle, Beaker } from "lucide-react";
import { Btn } from "@/components/WfPrimitives";
import {
  useFormulaScenario,
  type VariableAdjustment,
  type ScenarioResponse,
} from "@/hooks/useFormulaScenario";

export function ScenarioPanel({ formulaId }: { formulaId: string }) {
  const [baseCaseId, setBaseCaseId] = useState("");
  const [adjustments, setAdjustments] = useState<VariableAdjustment[]>([
    { name: "", value: 0, original_value: 0 },
  ]);
  const {
    mutate: runScenario,
    data: result,
    isPending,
    error,
  } = useFormulaScenario();

  const addAdjustment = () => {
    setAdjustments([
      ...adjustments,
      { name: "", value: 0, original_value: 0 },
    ]);
  };

  const updateAdjustment = (
    idx: number,
    field: keyof VariableAdjustment,
    val: string | number
  ) => {
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
        <label
          htmlFor="base-case-id"
          className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/60 block mb-1"
        >
          Base Case ID
        </label>
        <input
          id="base-case-id"
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
                id={`adj-name-${idx}`}
                value={adj.name}
                onChange={(e) =>
                  updateAdjustment(idx, "name", e.target.value)
                }
                placeholder="Variable"
                className="flex-1 border border-border rounded-md px-2 py-1 text-[11px] bg-white outline-none focus:ring-1 focus:ring-primary/20"
                aria-label={`Variable name ${idx + 1}`}
              />
              <input
                id={`adj-original-${idx}`}
                type="number"
                value={adj.original_value || ""}
                onChange={(e) =>
                  updateAdjustment(idx, "original_value", e.target.value)
                }
                placeholder="Original"
                className="w-20 border border-border rounded-md px-2 py-1 text-[11px] bg-white outline-none focus:ring-1 focus:ring-primary/20"
                aria-label={`Original value ${idx + 1}`}
              />
              <input
                id={`adj-new-${idx}`}
                type="number"
                value={adj.value || ""}
                onChange={(e) =>
                  updateAdjustment(idx, "value", e.target.value)
                }
                placeholder="New"
                className="w-20 border border-border rounded-md px-2 py-1 text-[11px] bg-white outline-none focus:ring-1 focus:ring-primary/20"
                aria-label={`New value ${idx + 1}`}
              />
              {adjustments.length > 1 && (
                <button
                  onClick={() => removeAdjustment(idx)}
                  className="text-red-400 hover:text-red-600 text-[14px]"
                  aria-label={`Remove adjustment ${idx + 1}`}
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
          aria-label="Add adjustment"
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
          <>
            <Loader2 size={11} className="animate-spin mr-1" /> Calculating...
          </>
        ) : (
          <>
            <Beaker size={11} className="mr-1" /> Run Scenario
          </>
        )}
      </Btn>

      {error && (
        <div className="p-2 bg-red-50 border border-red-200 rounded text-[11px] text-red-700 flex items-center gap-1.5">
          <AlertCircle size={12} /> {error.message}
        </div>
      )}

      {result && <ScenarioResults result={result} />}
    </div>
  );
}

function ScenarioResults({ result }: { result: ScenarioResponse }) {
  return (
    <div className="p-3 bg-secondary/30 rounded-lg space-y-2 text-[12px]">
      <div className="font-semibold text-[13px]">Scenario Results</div>
      <div className="grid grid-cols-2 gap-2">
        <div>
          <span className="text-muted-foreground">Original</span>
          <div className="font-bold">
            ${result.original_value.toLocaleString()}
          </div>
        </div>
        <div>
          <span className="text-muted-foreground">Adjusted</span>
          <div className="font-bold text-primary">
            ${result.adjusted_value.toLocaleString()}
          </div>
        </div>
        <div>
          <span className="text-muted-foreground">Delta</span>
          <div
            className={`font-bold ${
              result.delta_percentage >= 0
                ? "text-emerald-700"
                : "text-red-600"
            }`}
          >
            {result.delta_percentage >= 0 ? "+" : ""}
            {result.delta_percentage.toFixed(1)}%
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
          {result.warnings.map((w, i) => (
            <div key={i}>{w}</div>
          ))}
        </div>
      )}
    </div>
  );
}
