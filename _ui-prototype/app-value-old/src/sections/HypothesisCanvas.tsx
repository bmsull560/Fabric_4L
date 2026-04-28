import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  FlaskConical, Plus, Trash2, CheckCircle2, AlertCircle, ArrowRight,
  Target, Users, Zap, Sparkles, GitFork, Database
} from "lucide-react";

interface Hypothesis {
  id: string;
  useCase: string;
  hypothesis: string;
  expectedValue: string;
  successMetrics: string[];
  domainOwner: string;
  priority: "high" | "medium" | "low";
  status: "draft" | "validated" | "modeling";
}

const initialHypotheses: Hypothesis[] = [
  {
    id: "h1", useCase: "Reduce New Rep Ramp Time",
    hypothesis: "IF we deploy Allego AI Coaching + Content Mgmt THEN new hire quota attainment improves 30% faster",
    expectedValue: "$2.1M annual from 45-day faster ramp x 45 new reps",
    successMetrics: ["Time to first sale", "Quota attainment at 6mo", "Certification completion rate"],
    domainOwner: "Sales Enablement", priority: "high", status: "validated",
  },
  {
    id: "h2", useCase: "Improve Win Rate via Digital Rooms",
    hypothesis: "IF reps use Allego Digital Sales Rooms THEN win rate improves by 12% through better buyer engagement",
    expectedValue: "$3.8M from 12% win rate lift on $32M pipeline",
    successMetrics: ["Win rate %", "Buyer engagement score", "Sales cycle length"],
    domainOwner: "Sales Operations", priority: "high", status: "modeling",
  },
  {
    id: "h3", useCase: "Reduce Compliance Risk",
    hypothesis: "IF we deploy Allego FINRA 17a-4 Recording THEN compliance incidents drop 60% and legal exposure decreases",
    expectedValue: "$890K from avoided regulatory fines + legal costs",
    successMetrics: ["Compliance incidents", "Audit findings", "Rep certification rate"],
    domainOwner: "Legal / Compliance", priority: "medium", status: "draft",
  },
  {
    id: "h4", useCase: "Manager Efficiency via AI Coaching",
    hypothesis: "IF managers use AI-powered coaching scorecards THEN coaching frequency quadruples with same time investment",
    expectedValue: "$1.4M from reclaimed manager hours + improved rep performance",
    successMetrics: ["Coaching sessions per week", "Rep performance score", "Manager time saved"],
    domainOwner: "L&D", priority: "medium", status: "draft",
  },
];

export default function HypothesisCanvas() {
  const navigate = useNavigate();
  const [hypotheses] = useState<Hypothesis[]>(initialHypotheses);
  const [activeTab, setActiveTab] = useState<"all" | "high" | "validated">("all");
  const [showNewForm, setShowNewForm] = useState(false);

  const filtered = activeTab === "all" ? hypotheses :
    activeTab === "high" ? hypotheses.filter((h) => h.priority === "high") :
    hypotheses.filter((h) => h.status === "validated" || h.status === "modeling");

  return (
    <div className="max-w-7xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Hypothesis Canvas</h2>
          <p className="text-sm text-gray-500 mt-0.5">Define value hypotheses per Data Mesh product thinking: IF capability THEN outcome WITH expected value.</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowNewForm(!showNewForm)} className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
            <Sparkles className="w-4 h-4 text-amber-500" />
            AI Suggest
          </button>
          <button onClick={() => setShowNewForm(!showNewForm)} className="flex items-center gap-2 px-3 py-2 bg-[#2d8a6e] text-white rounded-lg text-sm font-medium hover:bg-[#257a5e]">
            <Plus className="w-4 h-4" />
            Add Hypothesis
          </button>
        </div>
      </div>

      {/* New Hypothesis Form */}
      {showNewForm && (
        <div className="bg-white rounded-xl border-2 border-[#2d8a6e] p-5 space-y-4">
          <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <FlaskConical className="w-4 h-4 text-[#2d8a6e]" />
            New Hypothesis Template
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-gray-600 mb-1 block">Use Case Name</label>
              <input placeholder="e.g. Reduce New Rep Ramp Time" className="w-full px-3 py-2 bg-gray-50 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-1 focus:ring-[#2d8a6e]" />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-600 mb-1 block">Domain Owner</label>
              <input placeholder="e.g. Sales Enablement" className="w-full px-3 py-2 bg-gray-50 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-1 focus:ring-[#2d8a6e]" />
            </div>
          </div>
          <div>
            <label className="text-xs font-medium text-gray-600 mb-1 block">Hypothesis Statement (IF... THEN...)</label>
            <input placeholder="IF we deploy [capability] THEN [outcome] improves by [X%]" className="w-full px-3 py-2 bg-gray-50 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-1 focus:ring-[#2d8a6e]" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-gray-600 mb-1 block">Expected Value</label>
              <input placeholder="e.g. $2.1M annual from 45-day faster ramp" className="w-full px-3 py-2 bg-gray-50 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-1 focus:ring-[#2d8a6e]" />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-600 mb-1 block">Success Metrics (comma-separated)</label>
              <input placeholder="Time to first sale, Quota attainment, Certification rate" className="w-full px-3 py-2 bg-gray-50 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-1 focus:ring-[#2d8a6e]" />
            </div>
          </div>
          <div className="flex items-center gap-3 pt-2">
            <button onClick={() => setShowNewForm(false)} className="px-4 py-2 bg-[#2d8a6e] text-white rounded-lg text-sm font-medium">Save Hypothesis</button>
            <button onClick={() => setShowNewForm(false)} className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700">Cancel</button>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex items-center gap-2">
        {(["all", "high", "validated"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab ? "bg-[#2d8a6e] text-white" : "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
            }`}
          >
            {tab === "all" ? "All Hypotheses" : tab === "high" ? "High Priority" : "In Modeling"}
          </button>
        ))}
        <span className="text-xs text-gray-400 ml-auto">{filtered.length} hypotheses</span>
      </div>

      {/* Hypothesis Cards */}
      <div className="grid grid-cols-2 gap-4">
        {filtered.map((h) => (
          <div key={h.id} className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold uppercase ${
                  h.priority === "high" ? "bg-red-50 text-red-600" : h.priority === "medium" ? "bg-amber-50 text-amber-600" : "bg-gray-100 text-gray-500"
                }`}>{h.priority}</span>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold uppercase ${
                  h.status === "validated" ? "bg-emerald-50 text-emerald-600" : h.status === "modeling" ? "bg-blue-50 text-blue-600" : "bg-gray-100 text-gray-500"
                }`}>{h.status}</span>
              </div>
              <button className="text-gray-300 hover:text-red-500">
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>

            <h4 className="font-semibold text-gray-900 text-sm mb-1">{h.useCase}</h4>
            <p className="text-xs text-gray-600 mb-3 italic">"{h.hypothesis}"</p>

            <div className="space-y-2 mb-4">
              <div className="flex items-center gap-2">
                <Target className="w-3.5 h-3.5 text-[#2d8a6e] shrink-0" />
                <span className="text-xs text-gray-700 font-medium">{h.expectedValue}</span>
              </div>
              <div className="flex items-center gap-2">
                <Users className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                <span className="text-xs text-gray-500">{h.domainOwner}</span>
              </div>
            </div>

            <div className="flex items-center gap-1.5 flex-wrap mb-4">
              {h.successMetrics.map((m) => (
                <span key={m} className="text-[10px] px-2 py-0.5 bg-[#eaf5f1] text-[#2d8a6e] rounded-full">{m}</span>
              ))}
            </div>

            <div className="flex items-center gap-2 pt-3 border-t border-gray-100">
              <button onClick={() => navigate("/driver-tree")} className="flex items-center gap-1.5 px-3 py-1.5 bg-[#eaf5f1] text-[#2d8a6e] rounded-lg text-xs font-medium hover:bg-[#d4ebe3]">
                <GitFork className="w-3.5 h-3.5" />
                Build Driver Tree
              </button>
              <button onClick={() => navigate("/evidence")} className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 text-gray-600 rounded-lg text-xs font-medium hover:bg-gray-100">
                <Database className="w-3.5 h-3.5" />
                Find Evidence
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Lean Value Tree Preview */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-700">Lean Value Tree Preview — Medtronic</h3>
          <span className="text-xs text-gray-400">Auto-generated from hypotheses</span>
        </div>
        <div className="flex items-start gap-6">
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2 px-3 py-2 bg-[#eaf5f1] rounded-lg border border-[#c5e0d5]">
              <Target className="w-4 h-4 text-[#2d8a6e]" />
              <span className="text-sm font-semibold text-gray-900">Medical Device Revenue Growth</span>
              <span className="text-xs text-[#2d8a6e] font-bold ml-auto">$8.2M potential</span>
            </div>
            <div className="ml-6 space-y-2">
              {[
                { label: "Sales Productivity", value: "$5.9M", sub: "Ramp Time + Win Rate + Deal Velocity", pct: 72 },
                { label: "Rep Retention", value: "$1.4M", sub: "Enablement Satisfaction", pct: 17 },
                { label: "Compliance Confidence", value: "$890K", sub: "Reduced Legal Risk", pct: 11 },
              ].map((branch) => (
                <div key={branch.label} className="flex items-center gap-3">
                  <div className="flex-1 px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Zap className="w-3.5 h-3.5 text-amber-500" />
                        <span className="text-sm font-medium text-gray-800">{branch.label}</span>
                      </div>
                      <span className="text-xs font-bold text-[#2d8a6e]">{branch.value}</span>
                    </div>
                    <p className="text-[10px] text-gray-500 mt-1">{branch.sub}</p>
                  </div>
                  <div className="w-16">
                    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-[#2d8a6e] rounded-full" style={{ width: `${branch.pct}%` }} />
                    </div>
                    <p className="text-[10px] text-gray-400 mt-1 text-center">{branch.pct}%</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="w-48 shrink-0 space-y-2">
            <h4 className="text-xs font-semibold text-gray-600">LVT Status</h4>
            {[
              { label: "Goals mapped", val: "3 of 5", ok: true },
              { label: "Drivers linked", val: "7 of 12", ok: false },
              { label: "Hypotheses validated", val: "2 of 4", ok: false },
              { label: "Evidence attached", val: "18 items", ok: true },
            ].map((s) => (
              <div key={s.label} className="flex items-center justify-between text-xs">
                <span className="text-gray-500">{s.label}</span>
                <div className="flex items-center gap-1">
                  <span className="font-medium text-gray-700">{s.val}</span>
                  {s.ok ? <CheckCircle2 className="w-3 h-3 text-emerald-500" /> : <AlertCircle className="w-3 h-3 text-amber-500" />}
                </div>
              </div>
            ))}
            <button onClick={() => navigate("/driver-tree")} className="w-full mt-2 flex items-center justify-center gap-1.5 px-3 py-2 bg-[#2d8a6e] text-white rounded-lg text-xs font-medium hover:bg-[#257a5e]">
              <ArrowRight className="w-3.5 h-3.5" />
              Expand Tree
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
