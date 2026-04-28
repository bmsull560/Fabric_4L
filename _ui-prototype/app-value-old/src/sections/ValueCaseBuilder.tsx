import {
  FileText, Download, Share2, Trophy, TrendingUp, Shield,
  CheckCircle2, AlertTriangle, BarChart3, GitFork, Database,
  ArrowRight, Star, Zap, Clock, Printer
} from "lucide-react";

const results = [
  {
    rank: 1, area: "Sales Productivity", value: "$5.88M", pct: 72,
    breakdown: [
      { label: "Faster Rep Ramp", amount: "$2.10M", evidence: "Case Study — Fortune 500 Pharma", conf: 92 },
      { label: "Win Rate Improvement", amount: "$3.84M", evidence: "Salesloft Pipeline Study 2024", conf: 88 },
    ],
  },
  {
    rank: 2, area: "Rep Retention", value: "$1.40M", pct: 17,
    breakdown: [
      { label: "Lower Turnover", amount: "$1.40M", evidence: "Gartner SE MQ 2024", conf: 75 },
    ],
  },
  {
    rank: 3, area: "Compliance Risk", value: "$890K", pct: 11,
    breakdown: [
      { label: "FINRA Recording", amount: "$620K", evidence: "Compliance Analysis", conf: 62 },
      { label: "AI Coaching", amount: "$270K", evidence: "Industry Estimate", conf: 55 },
    ],
  },
];

const executiveSummary = [
  { icon: Trophy, label: "Total 3-Year Value", value: "$24.6M", sub: "Conservative: $18.2M | Optimistic: $31.4M" },
  { icon: TrendingUp, label: "ROI", value: "412%", sub: "$24.6M value vs. $6.0M investment" },
  { icon: Clock, label: "Payback Period", value: "8 months", sub: "Expected scenario" },
  { icon: Shield, label: "Confidence", value: "73%", sub: "Weighted by evidence tiers" },
];

export default function ValueCaseBuilder() {
  return (
    <div className="max-w-7xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Value Case Builder</h2>
          <p className="text-sm text-gray-500 mt-0.5">Auto-generated business case with evidence anchors per hypothesis.</p>
        </div>
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
            <Printer className="w-4 h-4" /> Print
          </button>
          <button className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
            <Download className="w-4 h-4" /> PDF
          </button>
          <button className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
            <Download className="w-4 h-4" /> PPT
          </button>
          <button className="flex items-center gap-2 px-3 py-2 bg-[#2d8a6e] text-white rounded-lg text-sm font-medium hover:bg-[#257a5e]">
            <Share2 className="w-4 h-4" /> Share
          </button>
        </div>
      </div>

      {/* Executive Summary Banner */}
      <div className="grid grid-cols-4 gap-4">
        {executiveSummary.map((item) => (
          <div key={item.label} className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-lg bg-[#eaf5f1] flex items-center justify-center">
                <item.icon className="w-4 h-4 text-[#2d8a6e]" />
              </div>
              <span className="text-[10px] text-gray-500 uppercase font-medium">{item.label}</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{item.value}</p>
            <p className="text-[10px] text-gray-500 mt-1">{item.sub}</p>
          </div>
        ))}
      </div>

      <div className="flex gap-4">
        {/* Main Case */}
        <div className="flex-1 space-y-4">
          {/* Value Driver Breakdown */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
              <GitFork className="w-4 h-4" />
              Value Driver Breakdown — Annual
            </h3>
            <div className="space-y-4">
              {results.map((r) => (
                <div key={r.area}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        r.rank === 1 ? "bg-[#2d8a6e] text-white" : r.rank === 2 ? "bg-[#6bc4a6] text-[#1a5c46]" : "bg-gray-200 text-gray-600"
                      }`}>{r.rank}</span>
                      <span className="text-sm font-semibold text-gray-800">{r.area}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-bold text-[#2d8a6e]">{r.value}</span>
                      <span className="text-xs text-gray-400">{r.pct}%</span>
                    </div>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden mb-3">
                    <div className="h-full bg-[#2d8a6e] rounded-full" style={{ width: `${r.pct}%` }} />
                  </div>
                  <div className="ml-8 space-y-1.5">
                    {r.breakdown.map((b) => (
                      <div key={b.label} className="flex items-center justify-between py-1.5 px-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-2">
                          <Zap className="w-3 h-3 text-amber-500" />
                          <span className="text-xs text-gray-700">{b.label}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-xs font-mono text-gray-600">{b.amount}</span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${b.conf >= 80 ? "bg-emerald-50 text-emerald-600" : "bg-amber-50 text-amber-600"}`}>
                            {b.conf}% conf
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Hypothesis Table */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-100">
              <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Hypothesis Evidence Summary
              </h3>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Hypothesis</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Expected Value</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Key Evidence</th>
                  <th className="text-center px-4 py-3 font-semibold text-gray-600">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {[
                  { hyp: "IF AI Coaching THEN 45-day faster ramp", val: "$2.10M", evidence: "Fortune 500 Pharma case study", conf: 92 },
                  { hyp: "IF Digital Rooms THEN 12% win rate lift", val: "$3.84M", evidence: "Salesloft Pipeline Study 2024", conf: 88 },
                  { hyp: "IF Enablement THEN 22% lower turnover", val: "$1.40M", evidence: "Gartner SE MQ 2024", conf: 75 },
                  { hyp: "IF FINRA Recording THEN 60% fewer incidents", val: "$890K", evidence: "Compliance Industry Analysis", conf: 62 },
                ].map((h, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-xs text-gray-800">{h.hyp}</td>
                    <td className="px-4 py-3 text-xs font-mono font-semibold text-[#2d8a6e]">{h.val}</td>
                    <td className="px-4 py-3 text-xs text-gray-600">{h.evidence}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${h.conf >= 80 ? "bg-emerald-50 text-emerald-600" : "bg-amber-50 text-amber-600"}`}>
                        {h.conf}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 3-Year Projection */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              3-Year Value Projection
            </h3>
            <div className="flex items-end gap-6 h-40 px-4">
              {[
                { year: "Year 1", conservative: 5.2, expected: 8.2, optimistic: 11.0 },
                { year: "Year 2", conservative: 6.8, expected: 9.5, optimistic: 12.5 },
                { year: "Year 3", conservative: 7.5, expected: 10.2, optimistic: 13.2 },
              ].map((y) => (
                <div key={y.year} className="flex-1 flex flex-col items-center gap-2">
                  <div className="flex items-end gap-1 w-full justify-center" style={{ height: 120 }}>
                    <div className="w-6 bg-amber-200 rounded-t" style={{ height: `${(y.conservative / 15) * 100}px` }} />
                    <div className="w-6 bg-[#2d8a6e] rounded-t" style={{ height: `${(y.expected / 15) * 100}px` }} />
                    <div className="w-6 bg-emerald-200 rounded-t" style={{ height: `${(y.optimistic / 15) * 100}px` }} />
                  </div>
                  <span className="text-xs font-medium text-gray-700">{y.year}</span>
                  <span className="text-[10px] text-[#2d8a6e] font-semibold">${y.expected}M</span>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-center gap-4 mt-3 text-xs text-gray-500">
              <span className="flex items-center gap-1"><div className="w-3 h-3 bg-amber-200 rounded" /> Conservative</span>
              <span className="flex items-center gap-1"><div className="w-3 h-3 bg-[#2d8a6e] rounded" /> Expected</span>
              <span className="flex items-center gap-1"><div className="w-3 h-3 bg-emerald-200 rounded" /> Optimistic</span>
            </div>
          </div>
        </div>

        {/* Right Panel */}
        <div className="w-72 shrink-0 space-y-4">
          {/* Value Model Quality */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Model Quality Score</h4>
            <div className="flex items-center justify-center mb-3">
              <div className="relative w-20 h-20">
                <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
                  <circle cx="40" cy="40" r="34" fill="none" stroke="#f3f4f6" strokeWidth="8" />
                  <circle cx="40" cy="40" r="34" fill="none" stroke="#2d8a6e" strokeWidth="8" strokeDasharray="156 213" strokeLinecap="round" />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-xl font-bold text-gray-900">73</span>
                  <span className="text-[8px] text-gray-500">of 100</span>
                </div>
              </div>
            </div>
            <div className="space-y-2">
              {[
                { label: "Evidence depth", score: 82 },
                { label: "Formula rigor", score: 90 },
                { label: "Customer relevance", score: 68 },
                { label: "Confidence coverage", score: 55 },
              ].map((s) => (
                <div key={s.label} className="flex items-center gap-2">
                  <span className="text-[10px] text-gray-500 flex-1">{s.label}</span>
                  <div className="w-12 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-[#2d8a6e] rounded-full" style={{ width: `${s.score}%` }} />
                  </div>
                  <span className="text-[10px] text-gray-600 w-5 text-right">{s.score}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Evidence Summary */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Evidence Summary</h4>
            <div className="space-y-2">
              {[
                { icon: CheckCircle2, label: "Proof Points", count: 3, color: "text-emerald-500" },
                { icon: Star, label: "Supporting", count: 3, color: "text-blue-500" },
                { icon: AlertTriangle, label: "Anecdotal", count: 2, color: "text-amber-500" },
              ].map((e) => (
                <div key={e.label} className="flex items-center gap-2">
                  <e.icon className={`w-4 h-4 ${e.color}`} />
                  <span className="text-xs text-gray-600 flex-1">{e.label}</span>
                  <span className="text-xs font-semibold text-gray-800">{e.count}</span>
                </div>
              ))}
            </div>
            <div className="mt-3 pt-3 border-t border-gray-100">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-[#2d8a6e]" />
                <span className="text-xs text-gray-600">8 evidence items across 4 ontologies</span>
              </div>
            </div>
          </div>

          {/* Recommended Actions */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Recommended Next Steps</h4>
            <div className="space-y-2.5">
              {[
                { label: "Get Medtronic-specific data", priority: "high", action: "Request" },
                { label: "Validate compliance estimate", priority: "high", action: "Schedule call" },
                { label: "Add customer testimonial", priority: "med", action: "Draft" },
                { label: "Peer review model", priority: "med", action: "Invite reviewer" },
              ].map((a) => (
                <div key={a.label} className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${a.priority === "high" ? "bg-red-400" : "bg-amber-400"}`} />
                  <span className="text-xs text-gray-700 flex-1">{a.label}</span>
                  <button className="text-[10px] px-2 py-0.5 bg-[#eaf5f1] text-[#2d8a6e] rounded font-medium">{a.action}</button>
                </div>
              ))}
            </div>
          </div>

          {/* Decision Handoff */}
          <div className="bg-[#eaf5f1] rounded-xl border border-[#c5e0d5] p-4">
            <div className="flex items-center gap-2 mb-2">
              <ArrowRight className="w-4 h-4 text-[#2d8a6e]" />
              <h4 className="text-sm font-semibold text-[#1a5c46]">Ready for Decision</h4>
            </div>
            <p className="text-xs text-[#2d8a6e] mb-3">This value model is ready for decision evaluation. Hand off to Decision Studio.</p>
            <button className="w-full flex items-center justify-center gap-1.5 px-3 py-2 bg-[#2d8a6e] text-white rounded-lg text-xs font-medium hover:bg-[#257a5e]">
              <Trophy className="w-3.5 h-3.5" />
              Open in Decision Studio
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
