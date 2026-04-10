/**
 * Screen 1 — Ingestion Command Center
 * Design: Refined Enterprise SaaS
 * Spec change: simple-by-default with progressive disclosure for advanced config
 */
import { useState } from "react";
import { Globe, ChevronDown, ChevronUp, Settings2, Zap, Clock, CheckCircle2, AlertCircle, Loader2, ArrowRight } from "lucide-react";
import { MetricCard, PageHeader, DataTable, StatusBadge, Btn } from "@/components/WfPrimitives";

const recentMaps = [
  { domain: "acmecorp.com",        entities: "1,402", status: "completed" as const, updated: "2 mins ago" },
  { domain: "globex.io",           entities: "845",   status: "completed" as const, updated: "1 hour ago" },
  { domain: "initech.com",         entities: "120",   status: "processing" as const, updated: "Just now" },
  { domain: "massive-dynamic.com", entities: "3,105", status: "completed" as const, updated: "Yesterday" },
  { domain: "soylent.co",          entities: "—",     status: "failed" as const,    updated: "2 days ago" },
];

const recentActivity = [
  { icon: <CheckCircle2 size={13} className="text-emerald-500"/>, text: "acmecorp.com synthesis complete — 1,402 entities extracted", time: "2m ago" },
  { icon: <Loader2 size={13} className="text-blue-500 animate-spin"/>, text: "initech.com NER extraction in progress (68%)", time: "Just now" },
  { icon: <AlertCircle size={13} className="text-red-400"/>, text: "soylent.co crawl failed — domain unreachable", time: "2d ago" },
  { icon: <Zap size={13} className="text-violet-500"/>, text: "Business case generated for globex.io", time: "1h ago" },
];

const EXTRACTION_PROFILES = ["Default", "Deep Crawl", "Financial Focus", "Technical Focus"];
const ONTOLOGY_TARGETS = ["General", "SaaS / B2B", "Financial Services", "Healthcare"];

export default function CommandCenter() {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [profile, setProfile] = useState("Default");
  const [ontology, setOntology] = useState("SaaS / B2B");
  const [depth, setDepth] = useState("3");

  return (
    <div className="p-6 max-w-5xl">
      <PageHeader
        title="Command Center"
        subtitle="Start a new synthesis or review recent extraction maps."
      />

      {/* ── Simple synthesis input ─────────────────────────────────────────── */}
      <div className="bg-white border border-neutral-200 rounded-xl shadow-sm mb-4 overflow-hidden">
        {/* Main input row */}
        <div className="flex items-center gap-3 px-4 py-3.5">
          <Globe size={16} className="text-neutral-400 shrink-0"/>
          <input
            readOnly
            placeholder="Enter company domain to synthesize (e.g., https://example.com)…"
            className="flex-1 text-[13px] text-neutral-500 bg-transparent outline-none placeholder:text-neutral-400"
          />
          <Btn variant="primary">
            Synthesize <ArrowRight size={13} className="inline ml-1"/>
          </Btn>
        </div>

        {/* Advanced config toggle */}
        <button
          onClick={() => setShowAdvanced(v => !v)}
          className="w-full flex items-center gap-2 px-4 py-2 border-t border-neutral-100 text-[11px] text-neutral-400 hover:text-neutral-600 hover:bg-neutral-50 transition-colors"
        >
          <Settings2 size={11}/>
          <span>Advanced configuration</span>
          {showAdvanced ? <ChevronUp size={11} className="ml-auto"/> : <ChevronDown size={11} className="ml-auto"/>}
        </button>

        {/* Advanced config panel — hidden by default */}
        {showAdvanced && (
          <div className="px-4 py-4 bg-neutral-50 border-t border-neutral-100 grid grid-cols-3 gap-4">
            <div>
              <label className="block text-[10px] uppercase tracking-widest text-neutral-400 font-semibold mb-1.5">
                Extraction Profile
              </label>
              <select
                value={profile}
                onChange={e => setProfile(e.target.value)}
                className="w-full text-[12px] border border-neutral-200 rounded-md px-2.5 py-1.5 bg-white text-neutral-700 outline-none"
              >
                {EXTRACTION_PROFILES.map(p => <option key={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-[10px] uppercase tracking-widest text-neutral-400 font-semibold mb-1.5">
                Ontology Target
              </label>
              <select
                value={ontology}
                onChange={e => setOntology(e.target.value)}
                className="w-full text-[12px] border border-neutral-200 rounded-md px-2.5 py-1.5 bg-white text-neutral-700 outline-none"
              >
                {ONTOLOGY_TARGETS.map(o => <option key={o}>{o}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-[10px] uppercase tracking-widest text-neutral-400 font-semibold mb-1.5">
                Crawl Depth
              </label>
              <select
                value={depth}
                onChange={e => setDepth(e.target.value)}
                className="w-full text-[12px] border border-neutral-200 rounded-md px-2.5 py-1.5 bg-white text-neutral-700 outline-none"
              >
                {["1","2","3","4","5"].map(d => <option key={d}>{d}</option>)}
              </select>
            </div>
            <div className="col-span-3 pt-1">
              <p className="text-[11px] text-neutral-400">
                Value Pack context: <span className="font-medium text-neutral-600">SaaS / B2B — Enterprise Security</span>
                <button className="ml-2 text-blue-600 underline underline-offset-2">Change</button>
              </p>
            </div>
          </div>
        )}
      </div>

      {/* ── KPI row ────────────────────────────────────────────────────────── */}
      <div className="flex gap-4 mb-6">
        <MetricCard label="Total Processed Nodes"   value="14,208" trend="+12%" trendUp />
        <MetricCard label="Verified Relationships"  value="8,451"  trend="+5%"  trendUp />
        <MetricCard label="Total Accounts"          value="124"    trend="Active" />
      </div>

      {/* ── Two-column lower section ───────────────────────────────────────── */}
      <div className="grid grid-cols-3 gap-4">
        {/* Recent maps table — spans 2 cols */}
        <div className="col-span-2 bg-white border border-neutral-200 rounded-lg shadow-sm">
          <div className="px-4 pt-4 pb-3 border-b border-neutral-100 flex items-center justify-between">
            <h2 className="text-[14px] font-bold text-neutral-800">Recent Maps</h2>
            <button className="text-[11px] text-blue-600 hover:underline">View all</button>
          </div>
          <DataTable
            columns={["Domain", "Entities", "Status", "Updated"]}
            rows={recentMaps.map(r => [
              <span className="flex items-center gap-2">
                <span className="text-neutral-300 text-[14px]">🏢</span>
                <span className="font-medium text-neutral-800">{r.domain}</span>
              </span>,
              <span className="text-neutral-600">{r.entities}</span>,
              <StatusBadge status={r.status}/>,
              <span className="text-neutral-400 text-[11px]">{r.updated}</span>,
            ])}
          />
        </div>

        {/* Activity feed — 1 col */}
        <div className="bg-white border border-neutral-200 rounded-lg shadow-sm">
          <div className="px-4 pt-4 pb-3 border-b border-neutral-100 flex items-center gap-2">
            <Clock size={13} className="text-neutral-400"/>
            <h2 className="text-[13px] font-bold text-neutral-800">Recent Activity</h2>
          </div>
          <div className="divide-y divide-neutral-100">
            {recentActivity.map((a, i) => (
              <div key={i} className="px-4 py-3 flex items-start gap-2.5">
                <span className="mt-0.5 shrink-0">{a.icon}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] text-neutral-700 leading-snug">{a.text}</p>
                  <p className="text-[10px] text-neutral-400 mt-0.5">{a.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
