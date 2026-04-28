import { useState } from "react";
import {
  TrendingUp, TrendingDown,
  Save, RotateCcw, BarChart3, CheckCircle2, AlertTriangle
} from "lucide-react";

interface Lever {
  id: string; name: string; baseValue: number; unit: string;
  currentMin: number; currentMax: number;
  scenarioA: number; scenarioB: number;
  annualValue: number; confidence: number;
}

const initialLevers: Lever[] = [
  { id: "l1", name: "New Rep Ramp Time (days saved)", baseValue: 45, unit: "days", currentMin: 30, currentMax: 60, scenarioA: 45, scenarioB: 55, annualValue: 2100000, confidence: 92 },
  { id: "l2", name: "Win Rate Lift (%)", baseValue: 12, unit: "%", currentMin: 8, currentMax: 15, scenarioA: 12, scenarioB: 14, annualValue: 3840000, confidence: 88 },
  { id: "l3", name: "Annual Rep Hires", baseValue: 45, unit: "reps", currentMin: 35, currentMax: 55, scenarioA: 45, scenarioB: 50, annualValue: 0, confidence: 85 },
  { id: "l4", name: "Daily ACV per Rep", baseValue: 933, unit: "$", currentMin: 700, currentMax: 1100, scenarioA: 933, scenarioB: 1000, annualValue: 0, confidence: 78 },
  { id: "l5", name: "Rep Retention Improvement (%)", baseValue: 22, unit: "%", currentMin: 15, currentMax: 30, scenarioA: 22, scenarioB: 25, annualValue: 1400000, confidence: 75 },
  { id: "l6", name: "Compliance Incident Reduction (%)", baseValue: 60, unit: "%", currentMin: 40, currentMax: 70, scenarioA: 60, scenarioB: 65, annualValue: 890000, confidence: 62 },
];

const scenarioNames = { A: "Conservative", B: "Expected", C: "Optimistic" };

export default function ValueCalculator() {
  const [levers, setLevers] = useState<Lever[]>(initialLevers);
  const [activeScenario, setActiveScenario] = useState<"A" | "B" | "C">("B");

  const updateLever = (id: string, field: "scenarioA" | "scenarioB", val: number) => {
    setLevers((prev) => prev.map((l) => l.id === id ? { ...l, [field]: val } : l));
  };

  const totalValueA = levers.reduce((s, l) => s + l.annualValue * (l.scenarioA / l.baseValue), 0);
  const totalValueB = levers.reduce((s, l) => s + l.annualValue * (l.scenarioB / l.baseValue), 0);
  const totalValueC = levers.reduce((s, l) => s + l.annualValue * 1.3, 0);
  const totals = { A: totalValueA, B: totalValueB, C: totalValueC };
  const currentTotal = totals[activeScenario];

  return (
    <div className="max-w-7xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Value Calculator</h2>
          <p className="text-sm text-gray-500 mt-0.5">Interactive scenario modeling — adjust levers and see real-time value impact per ValQ methodology.</p>
        </div>
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
            <RotateCcw className="w-4 h-4" /> Reset
          </button>
          <button className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
            <Save className="w-4 h-4" /> Save Scenario
          </button>
        </div>
      </div>

      {/* Scenario Tabs */}
      <div className="flex gap-3">
        {(["A", "B", "C"] as const).map((s) => (
          <button
            key={s}
            onClick={() => setActiveScenario(s)}
            className={`flex-1 px-5 py-4 rounded-xl border text-left transition-all ${
              activeScenario === s ? "border-[#2d8a6e] bg-[#eaf5f1] shadow-sm" : "border-gray-200 bg-white hover:border-gray-300"
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className={`text-sm font-semibold ${activeScenario === s ? "text-[#2d8a6e]" : "text-gray-700"}`}>{scenarioNames[s]}</span>
              {s === "B" && <span className="text-[10px] px-1.5 py-0.5 bg-[#2d8a6e] text-white rounded-full">Base</span>}
            </div>
            <p className="text-2xl font-bold text-gray-900">${(totals[s] / 1_000_000).toFixed(2)}M</p>
            <p className="text-xs text-gray-500">Annual value impact</p>
          </button>
        ))}
      </div>

      <div className="flex gap-4">
        {/* Lever Sliders */}
        <div className="flex-1 space-y-3">
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                Value Driver Levers — {levers.length} levers
              </h3>
              <span className="text-xs text-gray-400">Evidence anchors attached to each lever</span>
            </div>
            <div className="divide-y divide-gray-50">
              {levers.map((l) => {
                const currentVal = activeScenario === "A" ? l.scenarioA : activeScenario === "B" ? l.scenarioB : l.baseValue * 1.2;
                const leverTotal = l.annualValue * (currentVal / l.baseValue);
                const isLocked = l.confidence < 70;

                return (
                  <div key={l.id} className={`px-5 py-4 ${isLocked ? "bg-amber-50/30" : ""}`}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {l.confidence >= 80 ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> : <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />}
                        <span className="text-sm font-medium text-gray-800">{l.name}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-gray-400">Base: {l.baseValue}{l.unit}</span>
                        <span className="text-sm font-bold text-[#2d8a6e]">{currentVal.toFixed(0)}{l.unit}</span>
                        <span className="text-xs font-mono text-gray-500 w-20 text-right">${(leverTotal / 1_000_000).toFixed(2)}M</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="text-[10px] text-gray-400 w-8 text-right">{l.currentMin}</span>
                      <input
                        type="range" min={l.currentMin} max={l.currentMax}
                        value={currentVal}
                        onChange={(e) => {
                          const v = parseInt(e.target.value);
                          updateLever(l.id, activeScenario === "A" ? "scenarioA" : "scenarioB", v);
                        }}
                        className="flex-1 accent-[#2d8a6e]"
                      />
                      <span className="text-[10px] text-gray-400 w-8">{l.currentMax}</span>
                    </div>

                    {/* Evidence anchor */}
                    <div className="flex items-center gap-2 mt-2 ml-5">
                      <div className="h-px flex-1 bg-gray-100" />
                      <span className="text-[10px] text-gray-400 flex items-center gap-1">
                        Confidence: {l.confidence}% —
                        <span className="text-[#2d8a6e] cursor-pointer hover:underline">{l.confidence >= 80 ? "2 proof points" : l.confidence >= 60 ? "1 proof, 1 supporting" : "Needs evidence"}</span>
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Panel */}
        <div className="w-72 shrink-0 space-y-4">
          {/* Total Summary */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Scenario Summary</h4>
            <div className="text-center mb-4">
              <p className="text-3xl font-bold text-[#2d8a6e]">${(currentTotal / 1_000_000).toFixed(2)}M</p>
              <p className="text-xs text-gray-500">Total Annual Value Impact</p>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between"><span className="text-gray-500">vs. Conservative</span><span className={`font-medium ${currentTotal >= totalValueA ? "text-emerald-600" : "text-red-600"}`}>${((currentTotal - totalValueA) / 1_000_000).toFixed(2)}M {currentTotal >= totalValueA ? <TrendingUp className="w-3 h-3 inline" /> : <TrendingDown className="w-3 h-3 inline" />}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">vs. Optimistic</span><span className="font-medium text-gray-700">${((totalValueC - currentTotal) / 1_000_000).toFixed(2)}M gap</span></div>
            </div>
          </div>

          {/* Lever Breakdown */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Value by Lever</h4>
            <div className="space-y-2">
              {levers.map((l) => {
                const currentVal = activeScenario === "A" ? l.scenarioA : activeScenario === "B" ? l.scenarioB : l.baseValue * 1.2;
                const leverTotal = l.annualValue * (currentVal / l.baseValue);
                const pct = (leverTotal / currentTotal) * 100;
                return (
                  <div key={l.id}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] text-gray-600 truncate max-w-[120px]">{l.name.split(" (")[0]}</span>
                      <span className="text-[10px] font-semibold text-gray-700">{pct.toFixed(0)}%</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-[#2d8a6e] rounded-full" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Confidence Band */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Confidence Range</h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Low</span>
                <span className="font-mono font-semibold">${(totalValueA / 1_000_000).toFixed(2)}M</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Expected</span>
                <span className="font-mono font-semibold text-[#2d8a6e]">${(totalValueB / 1_000_000).toFixed(2)}M</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">High</span>
                <span className="font-mono font-semibold">${(totalValueC / 1_000_000).toFixed(2)}M</span>
              </div>
            </div>
            <div className="mt-3 h-2 rounded-full overflow-hidden flex">
              <div className="flex-1 bg-amber-200" />
              <div className="flex-1 bg-[#2d8a6e]" />
              <div className="flex-1 bg-emerald-200" />
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-[9px] text-amber-600">Conservative</span>
              <span className="text-[9px] text-[#2d8a6e] font-medium">Expected</span>
              <span className="text-[9px] text-emerald-600">Optimistic</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
