import { useState } from "react";
import {
  GitFork, Plus, ChevronDown, ChevronRight, Trash2, GripVertical,
  Calculator, CheckCircle2, AlertCircle, Sparkles, MessageSquare
} from "lucide-react";

interface TreeNode {
  id: string; label: string; value: string; formula: string;
  children: TreeNode[]; expanded: boolean; driverType: "kpi" | "driver" | "lever";
}

const initialTree: TreeNode = {
  id: "root", label: "Total Annual Value Impact", value: "$8.19M", formula: "SUM(children)",
  driverType: "kpi", expanded: true,
  children: [
    {
      id: "d1", label: "Sales Productivity Gain", value: "$5.88M", formula: "Reps × Ramp_days_saved × ACV",
      driverType: "driver", expanded: true,
      children: [
        { id: "l1-1", label: "Faster Rep Ramp Time", value: "$2.10M", formula: "45 reps × 45 days × $933/day", driverType: "lever", expanded: false, children: [] },
        { id: "l1-2", label: "Win Rate Improvement", value: "$3.84M", formula: "$32M pipe × 12% lift", driverType: "lever", expanded: false, children: [] },
      ],
    },
    {
      id: "d2", label: "Rep Retention Value", value: "$1.40M", formula: "Retained_reps × Replacement_cost",
      driverType: "driver", expanded: true,
      children: [
        { id: "l2-1", label: "Lower Turnover from Enablement", value: "$1.40M", formula: "14 fewer turnovers × $100K", driverType: "lever", expanded: false, children: [] },
      ],
    },
    {
      id: "d3", label: "Compliance Risk Reduction", value: "$890K", formula: "Avoided_fines + Audit_cost_savings",
      driverType: "driver", expanded: true,
      children: [
        { id: "l3-1", label: "FINRA 17a-4 Recording", value: "$620K", formula: "Avoided audit findings × fine", driverType: "lever", expanded: false, children: [] },
        { id: "l3-2", label: "AI Coaching Compliance", value: "$270K", formula: "Reduced legal review hours", driverType: "lever", expanded: false, children: [] },
      ],
    },
  ],
};

function NodeRow({ node, depth, onToggle }: { node: TreeNode; depth: number; onToggle: (id: string) => void }) {
  const hasChildren = node.children.length > 0;
  const indent = depth * 20;
  const typeColors = { kpi: "bg-[#2d8a6e] text-white", driver: "bg-[#6bc4a6] text-[#1a5c46]", lever: "bg-gray-200 text-gray-600" };

  return (
    <div>
      <div
        className={`flex items-center gap-2 py-2 px-3 rounded-lg hover:bg-gray-50 transition-colors group ${depth === 0 ? "bg-[#eaf5f1] border border-[#c5e0d5]" : ""}`}
        style={{ marginLeft: indent }}
      >
        <GripVertical className="w-4 h-4 text-gray-300 shrink-0 cursor-grab opacity-0 group-hover:opacity-100" />
        {hasChildren ? (
          <button onClick={() => onToggle(node.id)} className="shrink-0">
            {node.expanded ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
          </button>
        ) : <div className="w-4 shrink-0" />}

        <div className={`w-5 h-5 rounded flex items-center justify-center text-[10px] font-bold shrink-0 ${typeColors[node.driverType]}`}>
          {node.driverType === "kpi" ? "K" : node.driverType === "driver" ? "D" : "L"}
        </div>
        <span className="text-sm font-medium text-gray-800 flex-1 min-w-0 truncate">{node.label}</span>
        <span className="text-xs font-mono text-[#2d8a6e] font-semibold w-20 text-right shrink-0">{node.value}</span>
        <span className="text-[10px] text-gray-400 font-mono hidden lg:block w-40 truncate shrink-0">{node.formula}</span>
        <Trash2 className="w-3.5 h-3.5 text-gray-300 hover:text-red-500 shrink-0 opacity-0 group-hover:opacity-100 cursor-pointer" />
      </div>
      {hasChildren && node.expanded && (
        <div className="border-l-2 border-dashed border-gray-200 ml-5">
          {node.children.map((c) => <NodeRow key={c.id} node={c} depth={depth + 1} onToggle={onToggle} />)}
          <button className="flex items-center gap-1.5 py-1.5 px-3 ml-4 text-xs text-[#2d8a6e] hover:text-[#257a5e]">
            <Plus className="w-3 h-3" /> Add Lever
          </button>
        </div>
      )}
    </div>
  );
}

export default function DriverTree() {
  const [tree, setTree] = useState<TreeNode>(initialTree);
  const [rightPanel, setRightPanel] = useState<"formula" | "validation" | "comments">("formula");

  const toggle = (id: string) => {
    const f = (n: TreeNode): TreeNode => n.id === id ? { ...n, expanded: !n.expanded } : { ...n, children: n.children.map(f) };
    setTree(f(tree));
  };

  return (
    <div className="max-w-7xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Value Driver Tree Builder</h2>
          <p className="text-sm text-gray-500 mt-0.5">Decompose business outcomes into quantifiable drivers with mathematical formulas per ValQ methodology.</p>
        </div>
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
            <Sparkles className="w-4 h-4 text-amber-500" /> AI Suggest
          </button>
          <button className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
            <Calculator className="w-4 h-4" /> Simulate
          </button>
        </div>
      </div>

      <div className="flex items-center gap-4 bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3">
        <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
        <div className="flex-1">
          <p className="text-sm font-medium text-emerald-800">Tree Structure Valid — 3 drivers, 5 platform-controllable levers mapped</p>
          <p className="text-xs text-emerald-600">All formulas validated. Missing evidence on 1 lever (Compliance Coaching).</p>
        </div>
        <button className="text-xs text-emerald-700 font-medium hover:underline">View Report</button>
      </div>

      <div className="flex gap-4">
        <div className="flex-1 bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <GitFork className="w-4 h-4" />
              Value Driver Tree — 3 Drivers, 5 Levers
            </h3>
            <div className="flex items-center gap-3 text-xs text-gray-500">
              <span className="flex items-center gap-1"><div className="w-3 h-3 rounded-sm bg-[#2d8a6e]" /> KPI</span>
              <span className="flex items-center gap-1"><div className="w-3 h-3 rounded-sm bg-[#6bc4a6]" /> Driver</span>
              <span className="flex items-center gap-1"><div className="w-3 h-3 rounded-sm bg-gray-200" /> Lever</span>
            </div>
          </div>
          <div className="p-4">
            <NodeRow node={tree} depth={0} onToggle={toggle} />
            <button className="flex items-center gap-2 py-2.5 px-3 mt-2 text-sm text-[#2d8a6e] font-medium hover:bg-[#eaf5f1] rounded-lg w-full">
              <Plus className="w-4 h-4" /> Add Value Driver
            </button>
          </div>
        </div>

        <div className="w-80 shrink-0 space-y-4">
          <div className="flex bg-gray-100 rounded-lg p-0.5">
            {(["formula", "validation", "comments"] as const).map((tab) => (
              <button key={tab} onClick={() => setRightPanel(tab)} className={`flex-1 py-1.5 text-xs font-medium rounded-md ${rightPanel === tab ? "bg-white text-gray-900 shadow-sm" : "text-gray-500"}`}>
                {tab === "formula" ? "Formula" : tab === "validation" ? "Validate" : "Discuss"}
              </button>
            ))}
          </div>

          {rightPanel === "formula" && (
            <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
              <h4 className="text-sm font-semibold text-gray-700">Formula Inspector</h4>
              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-[10px] text-gray-500 uppercase mb-1">Selected Node</p>
                <p className="text-sm font-semibold text-gray-800">Faster Rep Ramp Time</p>
                <p className="text-xs text-gray-500 mt-1">Platform lever — Allego AI Coaching</p>
              </div>
              <div className="p-3 bg-[#eaf5f1] rounded-lg border border-[#c5e0d5]">
                <p className="text-[10px] text-[#2d8a6e] uppercase mb-1">Formula</p>
                <p className="text-sm font-mono text-gray-800">Reps × Days_Saved × Daily_ACV</p>
                <p className="text-[10px] text-gray-500 mt-1">= 45 × 45 × $933 = $2.10M</p>
              </div>
              <div className="grid grid-cols-3 gap-2">
                {["45 reps", "45 days", "$933/day"].map((v) => (
                  <div key={v} className="p-2 bg-white rounded border border-gray-200 text-center">
                    <p className="text-xs font-mono font-semibold text-gray-800">{v.split(" ")[0]}</p>
                    <p className="text-[10px] text-gray-500">{v.split(" ").slice(1).join(" ")}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {rightPanel === "validation" && (
            <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
              <h4 className="text-sm font-semibold text-gray-700">Driver Validation</h4>
              {[
                { label: "Platform-controllable", status: "pass", desc: "All 5 levers map to Allego features" },
                { label: "Formula completeness", status: "pass", desc: "All drivers have quantified formulas" },
                { label: "Evidence coverage", status: "warn", desc: "l3-2 missing evidence (4/5 covered)" },
                { label: "Mathematical consistency", status: "pass", desc: "Roll-ups match leaf sums" },
                { label: "Confidence >70%", status: "warn", desc: "2 levers below threshold" },
              ].map((c) => (
                <div key={c.label} className="flex items-start gap-2.5">
                  {c.status === "pass" ? <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" /> : <AlertCircle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />}
                  <div>
                    <p className="text-sm font-medium text-gray-800">{c.label}</p>
                    <p className="text-xs text-gray-500">{c.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {rightPanel === "comments" && (
            <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
              <h4 className="text-sm font-semibold text-gray-700">Team Notes</h4>
              {[
                { user: "James T.", text: "Should we model the manager coaching efficiency separately?", time: "30m ago" },
                { user: "Lisa M.", text: "Medtronic confirmed 45 reps annually — source attached in Evidence Library.", time: "1h ago" },
              ].map((c, i) => (
                <div key={i}>
                  <div className="flex items-center gap-2 mb-1">
                    <div className="w-6 h-6 rounded-full bg-[#eaf5f1] flex items-center justify-center text-[10px] font-bold text-[#2d8a6e]">{c.user[0]}</div>
                    <span className="text-xs font-medium text-gray-700">{c.user}</span>
                    <span className="text-[10px] text-gray-400 ml-auto">{c.time}</span>
                  </div>
                  <p className="text-xs text-gray-600 ml-8">{c.text}</p>
                </div>
              ))}
              <div className="flex items-center gap-2 pt-2">
                <MessageSquare className="w-4 h-4 text-gray-400" />
                <input placeholder="Add note..." className="flex-1 text-xs bg-gray-50 rounded-lg px-3 py-2 border border-gray-200 focus:outline-none focus:ring-1 focus:ring-[#2d8a6e]" />
              </div>
            </div>
          )}

          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Value Distribution</h4>
            {[
              { label: "Sales Productivity", value: 0.72, color: "bg-[#2d8a6e]" },
              { label: "Rep Retention", value: 0.17, color: "bg-[#6bc4a6]" },
              { label: "Compliance", value: 0.11, color: "bg-[#a8d5c7]" },
            ].map((w) => (
              <div key={w.label} className="flex items-center gap-2 mb-2">
                <span className="text-xs text-gray-600 w-24">{w.label}</span>
                <div className="flex-1 h-2.5 bg-gray-100 rounded-full overflow-hidden">
                  <div className={`h-full ${w.color} rounded-full`} style={{ width: `${w.value * 100}%` }} />
                </div>
                <span className="text-xs font-semibold text-gray-700 w-10 text-right">{(w.value * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
