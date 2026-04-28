import { useNavigate } from "react-router-dom";
import {
  GitFork, FlaskConical, Database, ArrowRight,
  TrendingUp, Shield, Users, Clock, Plus
} from "lucide-react";

const valueModels = [
  { name: "Medtronic Sales Enablement", status: "active", progress: 72, updated: "2h ago", evidence: 24, confidence: "High" },
  { name: "Pharma Launch Acceleration", status: "active", progress: 45, updated: "1d ago", evidence: 12, confidence: "Medium" },
  { name: "Wealth Manager Productivity", status: "complete", progress: 100, updated: "3d ago", evidence: 31, confidence: "High" },
  { name: "Manufacturing Channel Enablement", status: "active", progress: 30, updated: "5d ago", evidence: 8, confidence: "Low" },
];

const templates = [
  { icon: TrendingUp, name: "Revenue Growth", desc: "Map drivers to revenue outcomes", color: "bg-emerald-100 text-emerald-600" },
  { icon: Shield, name: "Risk Reduction", desc: "Quantify risk mitigation value", color: "bg-amber-100 text-amber-600" },
  { icon: Users, name: "Productivity Gain", desc: "Model efficiency improvements", color: "bg-blue-100 text-blue-600" },
  { icon: Clock, name: "Time-to-Value", desc: "Accelerate outcome timelines", color: "bg-purple-100 text-purple-600" },
];

export default function DiscoveryHub() {
  const navigate = useNavigate();

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Discovery Hub</h2>
          <p className="text-sm text-gray-500 mt-1">Discover, model, and quantify business value before the decision.</p>
        </div>
        <button onClick={() => navigate("/hypotheses")} className="flex items-center gap-2 px-4 py-2.5 bg-[#2d8a6e] text-white rounded-lg text-sm font-medium hover:bg-[#257a5e]">
          <Plus className="w-4 h-4" />
          New Value Model
        </button>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Active Models", value: "6", sub: "2 near completion", icon: GitFork, c: "text-emerald-600", bg: "bg-emerald-50" },
          { label: "Evidence Items", value: "142", sub: "Across 4 ontologies", icon: Database, c: "text-blue-600", bg: "bg-blue-50" },
          { label: "Avg. Confidence", value: "73%", sub: "Weighted by evidence tier", icon: Shield, c: "text-amber-600", bg: "bg-amber-50" },
          { label: "Value Captured", value: "$18.4M", sub: "In active models YTD", icon: TrendingUp, c: "text-purple-600", bg: "bg-purple-50" },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg ${s.bg} flex items-center justify-center`}>
                <s.icon className={`w-5 h-5 ${s.c}`} />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{s.value}</p>
                <p className="text-xs text-gray-500">{s.label}</p>
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-3">{s.sub}</p>
          </div>
        ))}
      </div>

      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wider">Start from Template</h3>
        <div className="grid grid-cols-4 gap-4">
          {templates.map((t) => (
            <button key={t.name} onClick={() => navigate("/hypotheses")} className="bg-white rounded-xl border border-gray-200 p-5 text-left hover:border-[#2d8a6e] hover:shadow-md transition-all group">
              <div className="flex items-start justify-between mb-3">
                <div className={`w-10 h-10 rounded-lg ${t.color} flex items-center justify-center`}>
                  <t.icon className="w-5 h-5" />
                </div>
                <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-[#2d8a6e]" />
              </div>
              <h4 className="font-semibold text-gray-900 text-sm">{t.name}</h4>
              <p className="text-xs text-gray-500 mt-1">{t.desc}</p>
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">Recent Value Models</h3>
          <span className="text-xs text-[#2d8a6e] font-medium cursor-pointer hover:underline">View All</span>
        </div>
        <div className="divide-y divide-gray-100">
          {valueModels.map((m) => (
            <button key={m.name} onClick={() => navigate("/driver-tree")} className="w-full flex items-center gap-4 px-6 py-4 hover:bg-gray-50 transition-colors text-left">
              <div className={`w-2 h-2 rounded-full ${m.status === "active" ? "bg-emerald-400" : "bg-gray-300"}`} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">{m.name}</p>
                <p className="text-xs text-gray-500">{m.evidence} evidence items — {m.confidence} confidence</p>
              </div>
              <div className="w-32">
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-[#2d8a6e] rounded-full" style={{ width: `${m.progress}%` }} />
                </div>
              </div>
              <span className="text-xs text-gray-400 w-16 text-right">{m.updated}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[
          { title: "Hypothesis Canvas", icon: FlaskConical, desc: "Define use case hypotheses with expected value, success metrics, and domain owners per Data Mesh product thinking.", link: "/hypotheses" },
          { title: "Driver Tree Builder", icon: GitFork, desc: "Decompose KPIs into platform-controllable drivers with mathematical relationships per ValQ methodology.", link: "/driver-tree" },
          { title: "Evidence Library", icon: Database, desc: "Query ontology-structured evidence, apply confidence scoring, and normalize value drivers.", link: "/evidence" },
        ].map((card) => (
          <button key={card.title} onClick={() => navigate(card.link)} className="bg-white rounded-xl border border-gray-200 p-5 text-left hover:border-[#2d8a6e] hover:shadow-md transition-all group">
            <div className="flex items-center gap-2 mb-2">
              <card.icon className="w-5 h-5 text-[#2d8a6e]" />
              <h4 className="font-semibold text-gray-900 text-sm">{card.title}</h4>
            </div>
            <p className="text-xs text-gray-500">{card.desc}</p>
            <div className="flex items-center gap-1 mt-3 text-xs text-[#2d8a6e] font-medium">
              <span>Open</span>
              <ArrowRight className="w-3 h-3" />
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
