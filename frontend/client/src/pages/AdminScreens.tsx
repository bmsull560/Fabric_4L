/**
 * Admin Screens — Formula Governance, Benchmark Policies, Variable Registry
 * Design: Refined Enterprise SaaS
 * Spec: Tenant-admin governance surfaces separated from standard user workflows.
 * These screens are only visible in Admin mode.
 */
import { useState } from "react";
import {
  FlaskConical, CheckCircle2, Clock, AlertCircle, History, ChevronRight,
  BarChart3, ListChecks, Plus, Search, Filter, Tag, Users, Globe, Lock,
  ArrowUpDown, Edit3, Trash2, Eye, GitBranch, Link2, Database,
} from "lucide-react";
import { PageHeader, Btn, SectionCard, DataTable, StatusBadge } from "@/components/WfPrimitives";

// ── Shared types ──────────────────────────────────────────────────────────────

type ApprovalStatus = "active" | "draft" | "pending" | "deprecated";

// ── Formula Governance ────────────────────────────────────────────────────────

const FORMULAS = [
  { id: "f-001", name: "Customer Churn Reduction ROI",  pack: "Enterprise Security ROI",  version: "v3", status: "draft" as ApprovalStatus,   owner: "J. Rivera",  updated: "Today",     usedIn: 3 },
  { id: "f-002", name: "Cloud Cost Avoidance",          pack: "Cloud Cost Optimization",  version: "v2", status: "active" as ApprovalStatus,  owner: "M. Chen",    updated: "Apr 7",     usedIn: 7 },
  { id: "f-003", name: "Compliance Cost Reduction",     pack: "Enterprise Security ROI",  version: "v1", status: "active" as ApprovalStatus,  owner: "S. Park",    updated: "Apr 3",     usedIn: 5 },
  { id: "f-004", name: "Support Deflection Savings",    pack: "Customer Success",          version: "v2", status: "pending" as ApprovalStatus, owner: "J. Rivera",  updated: "Apr 8",     usedIn: 2 },
  { id: "f-005", name: "NRR Improvement Model",         pack: "Customer Success",          version: "v1", status: "deprecated" as ApprovalStatus, owner: "M. Chen", updated: "Mar 20",    usedIn: 0 },
];

const FORMULA_STATUS_MAP: Record<ApprovalStatus, { label: string; color: string; icon: React.ReactNode }> = {
  active:     { label: "Active",      color: "bg-emerald-50 text-emerald-700 border-emerald-200", icon: <CheckCircle2 size={11}/> },
  draft:      { label: "Draft",       color: "bg-neutral-100 text-neutral-600 border-neutral-200", icon: <Clock size={11}/> },
  pending:    { label: "Pending",     color: "bg-amber-50 text-amber-700 border-amber-200",        icon: <AlertCircle size={11}/> },
  deprecated: { label: "Deprecated", color: "bg-red-50 text-red-500 border-red-200",              icon: <History size={11}/> },
};

function FormulaStatusChip({ status }: { status: ApprovalStatus }) {
  const s = FORMULA_STATUS_MAP[status];
  return (
    <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border ${s.color}`}>
      {s.icon} {s.label}
    </span>
  );
}

export function FormulaGovernance() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | ApprovalStatus>("all");

  const filtered = FORMULAS.filter(f =>
    (filter === "all" || f.status === filter) &&
    (search === "" || f.name.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="p-6 max-w-5xl">
      <div className="flex items-start justify-between mb-6">
        <PageHeader
          title="Formula Governance"
          subtitle="Manage the lifecycle of all governed formula assets — draft, review, approve, and deprecate."
        />
        <Btn variant="primary"><Plus size={13} className="mr-1"/> New Formula</Btn>
      </div>

      {/* Approval queue callout */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl px-5 py-3.5 mb-5 flex items-center gap-4">
        <AlertCircle size={16} className="text-amber-600 shrink-0"/>
        <div className="flex-1">
          <p className="text-[12px] font-semibold text-amber-800">1 formula pending your approval</p>
          <p className="text-[11px] text-amber-600">Support Deflection Savings (v2) — submitted by J. Rivera</p>
        </div>
        <Btn variant="primary">Review Now</Btn>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex items-center gap-2 bg-white border border-neutral-200 rounded-lg px-3 py-2 max-w-xs flex-1">
          <Search size={12} className="text-neutral-400 shrink-0"/>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search formulas…"
            className="flex-1 text-[12px] bg-transparent outline-none text-neutral-600 placeholder:text-neutral-400"
          />
        </div>
        <div className="flex items-center gap-1.5">
          {(["all", "active", "draft", "pending", "deprecated"] as const).map(s => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`text-[11px] px-2.5 py-1 rounded-full border capitalize transition-colors font-medium ${
                filter === s
                  ? "bg-neutral-800 text-white border-neutral-800"
                  : "bg-white text-neutral-500 border-neutral-200 hover:border-neutral-300"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Formula table */}
      <div className="bg-white border border-neutral-200 rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-[12px]">
          <thead>
            <tr className="border-b border-neutral-100 bg-neutral-50">
              {["Formula Name", "Value Pack", "Version", "Status", "Owner", "Used In", "Updated", ""].map(h => (
                <th key={h} className="text-left px-4 py-3 text-[10px] uppercase tracking-widest text-neutral-400 font-semibold">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {filtered.map(f => (
              <tr key={f.id} className="hover:bg-neutral-50 transition-colors group">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <FlaskConical size={13} className="text-neutral-400 shrink-0"/>
                    <span className="font-medium text-neutral-800">{f.name}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-neutral-500">{f.pack}</td>
                <td className="px-4 py-3 font-mono text-neutral-600">{f.version}</td>
                <td className="px-4 py-3"><FormulaStatusChip status={f.status}/></td>
                <td className="px-4 py-3 text-neutral-500">{f.owner}</td>
                <td className="px-4 py-3 text-neutral-600">{f.usedIn} assets</td>
                <td className="px-4 py-3 text-neutral-400">{f.updated}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-1 rounded hover:bg-neutral-100 text-neutral-400 hover:text-neutral-700"><Eye size={13}/></button>
                    <button className="p-1 rounded hover:bg-neutral-100 text-neutral-400 hover:text-neutral-700"><Edit3 size={13}/></button>
                    <button className="p-1 rounded hover:bg-red-50 text-neutral-400 hover:text-red-500"><Trash2 size={13}/></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="text-center py-12 text-neutral-400 text-[12px]">No formulas match your filters.</div>
        )}
      </div>
    </div>
  );
}

// ── Benchmark Policies ────────────────────────────────────────────────────────

const BENCHMARKS = [
  { id: "b-001", name: "SaaS Average Churn Rate",     industry: "SaaS / B2B",           value: "5–7% / year",    confidence: "High",   source: "Gartner 2024",   status: "active" as const },
  { id: "b-002", name: "Enterprise ACV Range",         industry: "SaaS / B2B",           value: "$50K – $500K",   confidence: "High",   source: "Internal",       status: "active" as const },
  { id: "b-003", name: "Retention Lift (Analytics)",   industry: "SaaS / B2B",           value: "15–25%",         confidence: "Medium", source: "Forrester 2023", status: "active" as const },
  { id: "b-004", name: "Cloud Cost Reduction (IaC)",   industry: "Infrastructure",       value: "20–35%",         confidence: "High",   source: "IDC 2024",       status: "active" as const },
  { id: "b-005", name: "Compliance Fine Avoidance",    industry: "Financial Services",   value: "$500K – $5M",    confidence: "Low",    source: "Manual",         status: "draft" as const },
];

const CONFIDENCE_COLOR: Record<string, string> = {
  High:   "bg-emerald-50 text-emerald-700",
  Medium: "bg-amber-50 text-amber-700",
  Low:    "bg-red-50 text-red-500",
};

export function BenchmarkPolicies() {
  return (
    <div className="p-6 max-w-5xl">
      <div className="flex items-start justify-between mb-6">
        <PageHeader
          title="Benchmark Policies"
          subtitle="Define and manage industry benchmarks used in formula evaluation and business case generation."
        />
        <Btn variant="primary"><Plus size={13} className="mr-1"/> Add Benchmark</Btn>
      </div>

      {/* Policy config panel */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {[
          { label: "Default Confidence Threshold", value: "Medium", icon: <BarChart3 size={14}/> },
          { label: "Benchmark Refresh Cadence",     value: "Quarterly",  icon: <Clock size={14}/> },
          { label: "Fallback Policy",               value: "Use internal estimates", icon: <Database size={14}/> },
        ].map(p => (
          <div key={p.label} className="bg-white border border-neutral-200 rounded-xl px-4 py-4 flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-neutral-100 flex items-center justify-center text-neutral-500 shrink-0">
              {p.icon}
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest text-neutral-400 font-semibold mb-0.5">{p.label}</p>
              <p className="text-[13px] font-bold text-neutral-800">{p.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Benchmark library */}
      <div className="bg-white border border-neutral-200 rounded-xl shadow-sm overflow-hidden">
        <div className="px-4 pt-4 pb-3 border-b border-neutral-100 flex items-center justify-between">
          <h2 className="text-[14px] font-bold text-neutral-800">Benchmark Library</h2>
          <div className="flex items-center gap-2 text-[11px] text-neutral-400">
            <ArrowUpDown size={12}/> Sort by confidence
          </div>
        </div>
        <table className="w-full text-[12px]">
          <thead>
            <tr className="border-b border-neutral-100 bg-neutral-50">
              {["Benchmark", "Industry", "Value Range", "Confidence", "Source", "Status", ""].map(h => (
                <th key={h} className="text-left px-4 py-3 text-[10px] uppercase tracking-widest text-neutral-400 font-semibold">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {BENCHMARKS.map(b => (
              <tr key={b.id} className="hover:bg-neutral-50 transition-colors group">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <BarChart3 size={13} className="text-neutral-400 shrink-0"/>
                    <span className="font-medium text-neutral-800">{b.name}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-neutral-500">{b.industry}</td>
                <td className="px-4 py-3 font-mono text-neutral-700">{b.value}</td>
                <td className="px-4 py-3">
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${CONFIDENCE_COLOR[b.confidence]}`}>
                    {b.confidence}
                  </span>
                </td>
                <td className="px-4 py-3 text-neutral-500">{b.source}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={b.status === "active" ? "completed" : "processing"}/>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-1 rounded hover:bg-neutral-100 text-neutral-400 hover:text-neutral-700"><Edit3 size={13}/></button>
                    <button className="p-1 rounded hover:bg-red-50 text-neutral-400 hover:text-red-500"><Trash2 size={13}/></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Variable Registry ─────────────────────────────────────────────────────────

const VARIABLES = [
  { id: "v-001", name: "Current_Churn_Rate",       type: "rate",     unit: "%",   source: "CRM",     binding: "salesforce.churn_rate",    usedIn: 4, validated: true },
  { id: "v-002", name: "Average_Contract_Value",   type: "currency", unit: "USD", source: "Billing", binding: "stripe.avg_contract_value", usedIn: 7, validated: true },
  { id: "v-003", name: "Customer_Count",           type: "integer",  unit: "—",   source: "CRM",     binding: "salesforce.account_count",  usedIn: 6, validated: true },
  { id: "v-004", name: "Implementation_Cost",      type: "currency", unit: "USD", source: "Manual",  binding: "manual.impl_cost",          usedIn: 3, validated: false },
  { id: "v-005", name: "Projected_Retention_Lift", type: "rate",     unit: "%",   source: "Model",   binding: "ml_model.retention_lift",   usedIn: 5, validated: true },
  { id: "v-006", name: "Support_Ticket_Volume",    type: "integer",  unit: "—",   source: "CRM",     binding: "zendesk.ticket_count",      usedIn: 2, validated: false },
];

const TYPE_COLOR: Record<string, string> = {
  rate:     "bg-cyan-50 text-cyan-700",
  currency: "bg-emerald-50 text-emerald-700",
  integer:  "bg-neutral-100 text-neutral-600",
};

const SOURCE_COLOR: Record<string, string> = {
  CRM:     "bg-blue-50 text-blue-700",
  Billing: "bg-violet-50 text-violet-700",
  Model:   "bg-amber-50 text-amber-700",
  Manual:  "bg-neutral-100 text-neutral-600",
};

export function VariableRegistry() {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  const filtered = VARIABLES.filter(v =>
    (typeFilter === "all" || v.type === typeFilter) &&
    (search === "" || v.name.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="p-6 max-w-5xl">
      <div className="flex items-start justify-between mb-6">
        <PageHeader
          title="Variable Registry"
          subtitle="Catalog of all formula variables — definitions, source bindings, type system, and validation rules."
        />
        <Btn variant="primary"><Plus size={13} className="mr-1"/> Register Variable</Btn>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: "Total Variables", value: VARIABLES.length.toString() },
          { label: "Validated",       value: VARIABLES.filter(v => v.validated).length.toString() },
          { label: "Manual Sources",  value: VARIABLES.filter(v => v.source === "Manual").length.toString() },
          { label: "Avg Usage",       value: (VARIABLES.reduce((s, v) => s + v.usedIn, 0) / VARIABLES.length).toFixed(1) },
        ].map(s => (
          <div key={s.label} className="bg-white border border-neutral-200 rounded-xl px-4 py-3">
            <p className="text-[10px] uppercase tracking-widest text-neutral-400 font-semibold mb-0.5">{s.label}</p>
            <p className="text-[20px] font-extrabold text-neutral-800">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex items-center gap-2 bg-white border border-neutral-200 rounded-lg px-3 py-2 max-w-xs flex-1">
          <Search size={12} className="text-neutral-400 shrink-0"/>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search variables…"
            className="flex-1 text-[12px] bg-transparent outline-none text-neutral-600 placeholder:text-neutral-400"
          />
        </div>
        <div className="flex items-center gap-1.5">
          {["all", "rate", "currency", "integer"].map(t => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={`text-[11px] px-2.5 py-1 rounded-full border capitalize transition-colors font-medium ${
                typeFilter === t
                  ? "bg-neutral-800 text-white border-neutral-800"
                  : "bg-white text-neutral-500 border-neutral-200 hover:border-neutral-300"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Variable table */}
      <div className="bg-white border border-neutral-200 rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-[12px]">
          <thead>
            <tr className="border-b border-neutral-100 bg-neutral-50">
              {["Variable Name", "Type", "Unit", "Source", "Binding", "Used In", "Validated", ""].map(h => (
                <th key={h} className="text-left px-4 py-3 text-[10px] uppercase tracking-widest text-neutral-400 font-semibold">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {filtered.map(v => (
              <tr key={v.id} className="hover:bg-neutral-50 transition-colors group">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <ListChecks size={13} className="text-neutral-400 shrink-0"/>
                    <span className="font-mono font-medium text-neutral-800">{v.name}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${TYPE_COLOR[v.type]}`}>{v.type}</span>
                </td>
                <td className="px-4 py-3 text-neutral-500">{v.unit}</td>
                <td className="px-4 py-3">
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${SOURCE_COLOR[v.source]}`}>{v.source}</span>
                </td>
                <td className="px-4 py-3 font-mono text-[11px] text-neutral-500">{v.binding}</td>
                <td className="px-4 py-3 text-neutral-600">{v.usedIn} formulas</td>
                <td className="px-4 py-3">
                  {v.validated
                    ? <CheckCircle2 size={14} className="text-emerald-500"/>
                    : <AlertCircle size={14} className="text-amber-500"/>
                  }
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-1 rounded hover:bg-neutral-100 text-neutral-400 hover:text-neutral-700"><Edit3 size={13}/></button>
                    <button className="p-1 rounded hover:bg-neutral-100 text-neutral-400 hover:text-neutral-700"><Link2 size={13}/></button>
                    <button className="p-1 rounded hover:bg-red-50 text-neutral-400 hover:text-red-500"><Trash2 size={13}/></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="text-center py-12 text-neutral-400 text-[12px]">No variables match your filters.</div>
        )}
      </div>
    </div>
  );
}
