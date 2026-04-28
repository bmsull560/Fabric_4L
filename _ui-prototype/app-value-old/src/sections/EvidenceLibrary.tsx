import { useState } from "react";
import {
  Database, Search, Filter, CheckCircle2, ArrowUpDown,
  Shield, FileText, Zap, Star, GitFork
} from "lucide-react";

interface EvidenceItem {
  id: string; statement: string; source: string; type: string;
  tier: "proof" | "supporting" | "anecdotal"; confidence: number;
  ontology: string; impactArea: string; status: "verified" | "pending" | "rejected";
}

const evidence: EvidenceItem[] = [
  { id: "e1", statement: "45-day faster ramp: Allego customer (Fortune 500 pharma) achieved 45-day reduction in time-to-first-sale with AI coaching.", source: "Case Study — Fortune 500 Pharma", type: "Case Study", tier: "proof", confidence: 92, ontology: "Proof", impactArea: "Sales Productivity", status: "verified" },
  { id: "e2", statement: "12% win rate lift: Digital Sales Rooms correlated with 12% win rate improvement across 120 deals tracked.", source: "Salesloft Pipeline Study 2024", type: "Analytical Study", tier: "proof", confidence: 88, ontology: "Proof", impactArea: "Win Rate", status: "verified" },
  { id: "e3", statement: "Rep turnover drops 22% when enablement satisfaction exceeds 7/10 per Gartner research.", source: "Gartner Sales Enablement MQ 2024", type: "Research", tier: "supporting", confidence: 75, ontology: "Products", impactArea: "Rep Retention", status: "verified" },
  { id: "e4", statement: "Allego AI coaching 4x more sessions than manual coaching for same manager time investment.", source: "Allego Internal Benchmark", type: "Platform Data", tier: "proof", confidence: 85, ontology: "Trust", impactArea: "Sales Productivity", status: "verified" },
  { id: "e5", statement: "FINRA 17a-4 compliant recording reduces audit findings by estimated 40-60%.", source: "Compliance Industry Analysis", type: "Estimate", tier: "supporting", confidence: 62, ontology: "Commercial", impactArea: "Compliance", status: "pending" },
  { id: "e6", statement: "Sales teams with dedicated enablement see 15% higher quota attainment on average.", source: "CSO Insights 2024", type: "Research", tier: "supporting", confidence: 78, ontology: "Proof", impactArea: "Sales Productivity", status: "verified" },
  { id: "e7", statement: "Medtronic VP Sales confirmed Allego reduced onboarding complexity in pilot program.", source: "Customer Interview — Medtronic", type: "Testimonial", tier: "anecdotal", confidence: 55, ontology: "Trust", impactArea: "Sales Productivity", status: "pending" },
  { id: "e8", statement: "AI-generated coaching scorecards show 91% accuracy vs. expert human assessment.", source: "Allego NLP Benchmark", type: "Platform Data", tier: "proof", confidence: 90, ontology: "Trust", impactArea: "Coaching Quality", status: "verified" },
];

const ontologyColors: Record<string, string> = {
  Proof: "bg-emerald-50 text-emerald-700 border-emerald-200",
  Products: "bg-blue-50 text-blue-700 border-blue-200",
  Trust: "bg-purple-50 text-purple-700 border-purple-200",
  Commercial: "bg-amber-50 text-amber-700 border-amber-200",
};

export default function EvidenceLibrary() {
  const [filterTier, setFilterTier] = useState<string>("all");
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>("e1");

  const filtered = evidence.filter((e) => {
    if (filterTier !== "all" && e.tier !== filterTier) return false;
    if (search && !e.statement.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const selected = evidence.find((e) => e.id === selectedId);

  return (
    <div className="max-w-7xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Evidence Library</h2>
          <p className="text-sm text-gray-500 mt-0.5">Query ontology-structured evidence, score confidence, and map to value drivers.</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span>{filtered.length} of {evidence.length} items</span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Total Evidence", value: evidence.length, icon: Database, c: "text-gray-600", bg: "bg-gray-50" },
          { label: "Proof Points", value: evidence.filter((e) => e.tier === "proof").length, icon: Shield, c: "text-emerald-600", bg: "bg-emerald-50" },
          { label: "Avg. Confidence", value: `${Math.round(evidence.reduce((s, e) => s + e.confidence, 0) / evidence.length)}%`, icon: Star, c: "text-amber-600", bg: "bg-amber-50" },
          { label: "Verified", value: evidence.filter((e) => e.status === "verified").length, icon: CheckCircle2, c: "text-blue-600", bg: "bg-blue-50" },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-3">
            <div className={`w-9 h-9 rounded-lg ${s.bg} flex items-center justify-center`}>
              <s.icon className={`w-4 h-4 ${s.c}`} />
            </div>
            <div>
              <p className="text-lg font-bold text-gray-900">{s.value}</p>
              <p className="text-[10px] text-gray-500">{s.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Search + Filters */}
      <div className="flex items-center gap-3">
        <div className="flex-1 flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg">
          <Search className="w-4 h-4 text-gray-400" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search evidence statements..." className="flex-1 text-sm bg-transparent focus:outline-none" />
        </div>
        <div className="flex bg-gray-100 rounded-lg p-0.5">
          {["all", "proof", "supporting", "anecdotal"].map((tier) => (
            <button key={tier} onClick={() => setFilterTier(tier)} className={`px-3 py-1.5 text-xs font-medium rounded-md ${filterTier === tier ? "bg-white text-gray-900 shadow-sm" : "text-gray-500"}`}>
              {tier === "all" ? "All" : tier.charAt(0).toUpperCase() + tier.slice(1)}
            </button>
          ))}
        </div>
        <button className="flex items-center gap-1.5 px-3 py-2 bg-white border border-gray-200 rounded-lg text-xs text-gray-500 hover:bg-gray-50">
          <Filter className="w-3.5 h-3.5" /> More Filters
        </button>
      </div>

      <div className="flex gap-4">
        {/* Evidence List */}
        <div className="flex-1 bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-4 py-2.5 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-600">Statement</span>
            <div className="flex items-center gap-6">
              <span className="text-xs font-semibold text-gray-600 w-16 text-center">Tier</span>
              <span className="text-xs font-semibold text-gray-600 w-16 text-center">Confidence</span>
              <span className="text-xs font-semibold text-gray-600 w-16 text-center">Status</span>
            </div>
          </div>
          <div className="divide-y divide-gray-100 max-h-[500px] overflow-y-auto">
            {filtered.map((e) => (
              <button
                key={e.id}
                onClick={() => setSelectedId(e.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${selectedId === e.id ? "bg-[#eaf5f1] border-l-2 border-l-[#2d8a6e]" : "hover:bg-gray-50"}`}
              >
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-800 line-clamp-2">{e.statement}</p>
                  <p className="text-[10px] text-gray-400 mt-1">{e.source}</p>
                </div>
                <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium shrink-0 w-16 text-center ${
                  e.tier === "proof" ? "bg-emerald-50 text-emerald-700 border-emerald-200" :
                  e.tier === "supporting" ? "bg-blue-50 text-blue-700 border-blue-200" :
                  "bg-gray-100 text-gray-600 border-gray-200"
                }`}>{e.tier}</span>
                <div className="w-16 text-center shrink-0">
                  <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden mx-auto w-10">
                    <div className="h-full rounded-full" style={{ width: `${e.confidence}%`, backgroundColor: e.confidence >= 80 ? "#2d8a6e" : e.confidence >= 60 ? "#f59e0b" : "#ef4444" }} />
                  </div>
                  <span className="text-[10px] text-gray-600 font-medium">{e.confidence}%</span>
                </div>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium shrink-0 w-16 text-center ${
                  e.status === "verified" ? "bg-emerald-50 text-emerald-600" : e.status === "pending" ? "bg-amber-50 text-amber-600" : "bg-red-50 text-red-600"
                }`}>{e.status}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Detail Panel */}
        <div className="w-80 shrink-0 space-y-4">
          {selected ? (
            <>
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-center gap-2 mb-3">
                  <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${ontologyColors[selected.ontology]}`}>{selected.ontology}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">{selected.type}</span>
                </div>
                <p className="text-sm text-gray-800 mb-3">{selected.statement}</p>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <FileText className="w-3.5 h-3.5" />
                  <span>{selected.source}</span>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">Confidence Score</h4>
                <div className="flex items-center justify-center mb-3">
                  <div className="relative w-20 h-20">
                    <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
                      <circle cx="40" cy="40" r="34" fill="none" stroke="#f3f4f6" strokeWidth="8" />
                      <circle cx="40" cy="40" r="34" fill="none" stroke={selected.confidence >= 80 ? "#2d8a6e" : selected.confidence >= 60 ? "#f59e0b" : "#ef4444"} strokeWidth="8" strokeDasharray={`${selected.confidence * 2.14} 213`} strokeLinecap="round" />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-lg font-bold text-gray-900">{selected.confidence}</span>
                    </div>
                  </div>
                </div>
                <div className="space-y-1.5">
                  {[
                    { label: "Source credibility", score: selected.confidence > 80 ? 95 : 70 },
                    { label: "Data recency", score: 85 },
                    { label: "Customer relevance", score: selected.confidence > 70 ? 88 : 55 },
                    { label: "Peer-reviewed", score: selected.tier === "proof" ? 90 : 40 },
                  ].map((cs) => (
                    <div key={cs.label} className="flex items-center gap-2">
                      <span className="text-[10px] text-gray-500 flex-1">{cs.label}</span>
                      <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div className="h-full bg-[#2d8a6e] rounded-full" style={{ width: `${cs.score}%` }} />
                      </div>
                      <span className="text-[10px] text-gray-600 w-6 text-right">{cs.score}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Impact Mapping</h4>
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-3.5 h-3.5 text-amber-500" />
                  <span className="text-xs text-gray-700">{selected.impactArea}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <GitFork className="w-3.5 h-3.5" />
                  <span>Driver Tree: Sales Productivity</span>
                </div>
                <div className="mt-3 pt-3 border-t border-gray-100 flex gap-2">
                  <button className="flex-1 py-1.5 bg-emerald-50 text-emerald-700 rounded-lg text-[10px] font-medium flex items-center justify-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Verify
                  </button>
                  <button className="flex-1 py-1.5 bg-gray-50 text-gray-600 rounded-lg text-[10px] font-medium flex items-center justify-center gap-1">
                    <ArrowUpDown className="w-3 h-3" /> Re-score
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 p-6 text-center">
              <Database className="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-500">Select an evidence item to inspect</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
