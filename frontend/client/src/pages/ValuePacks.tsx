/**
 * Screen — Value Packs
 * Design: Refined Enterprise SaaS
 * Spec: Value Packs as first-class product objects — reusable domain-specific
 * packages combining ontology, value drivers, formulas, benchmarks, and workflows.
 */
import { useState } from "react";
import { PageHeader, Btn, StatusBadge } from "@/components/WfPrimitives";
import {
  Sparkles, Package, GitBranch, FlaskConical, BarChart3, Bot,
  Users, ChevronRight, Search, Filter, CheckCircle2, Lock, Globe,
} from "lucide-react";

interface ValuePack {
  id: string;
  name: string;
  industry: string;
  description: string;
  drivers: number;
  formulas: number;
  benchmarks: number;
  workflows: number;
  status: "active" | "draft" | "archived";
  scope: "global" | "tenant";
  lastUpdated: string;
}

const PACKS: ValuePack[] = [
  {
    id: "vp-001",
    name: "Enterprise Security ROI",
    industry: "SaaS / B2B",
    description: "Quantify the financial impact of security investments — RBAC, SSO, compliance automation, and audit logging.",
    drivers: 8, formulas: 5, benchmarks: 12, workflows: 3,
    status: "active", scope: "global", lastUpdated: "2 days ago",
  },
  {
    id: "vp-002",
    name: "Cloud Cost Optimization",
    industry: "Infrastructure / DevOps",
    description: "Model savings from automated provisioning, rightsizing, and multi-cloud governance.",
    drivers: 6, formulas: 4, benchmarks: 9, workflows: 2,
    status: "active", scope: "global", lastUpdated: "1 week ago",
  },
  {
    id: "vp-003",
    name: "Customer Success Efficiency",
    industry: "SaaS / B2B",
    description: "Measure churn reduction, NRR improvement, and support deflection through intelligent automation.",
    drivers: 7, formulas: 6, benchmarks: 8, workflows: 4,
    status: "active", scope: "tenant", lastUpdated: "3 days ago",
  },
  {
    id: "vp-004",
    name: "Financial Services Compliance",
    industry: "Financial Services",
    description: "Regulatory compliance cost avoidance, audit preparation, and risk-adjusted ROI for FinServ.",
    drivers: 10, formulas: 7, benchmarks: 15, workflows: 5,
    status: "draft", scope: "tenant", lastUpdated: "Just now",
  },
  {
    id: "vp-005",
    name: "Healthcare Data Governance",
    industry: "Healthcare",
    description: "HIPAA compliance, data access controls, and interoperability value modeling.",
    drivers: 9, formulas: 5, benchmarks: 11, workflows: 3,
    status: "draft", scope: "tenant", lastUpdated: "5 days ago",
  },
];

const INDUSTRIES = ["All Industries", "SaaS / B2B", "Infrastructure / DevOps", "Financial Services", "Healthcare"];

function PackCard({ pack }: { pack: ValuePack }) {
  const statusColor = pack.status === "active" ? "completed" : pack.status === "draft" ? "processing" : "failed";

  return (
    <div className="bg-white border border-neutral-200 rounded-xl shadow-sm hover:shadow-md hover:border-neutral-300 transition-all cursor-pointer group">
      {/* Header */}
      <div className="px-5 pt-5 pb-4 border-b border-neutral-100">
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center">
              <Sparkles size={14} className="text-blue-600"/>
            </div>
            <div>
              <h3 className="text-[13px] font-bold text-neutral-900 leading-tight">{pack.name}</h3>
              <p className="text-[10px] text-neutral-400 mt-0.5">{pack.industry}</p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            {pack.scope === "global"
              ? <span title="Global pack" className="text-neutral-300"><Globe size={12}/></span>
              : <span title="Tenant pack" className="text-neutral-300"><Lock size={12}/></span>
            }
            <StatusBadge status={statusColor as any}/>
          </div>
        </div>
        <p className="text-[11px] text-neutral-500 leading-relaxed">{pack.description}</p>
      </div>

      {/* Composition stats */}
      <div className="px-5 py-3 grid grid-cols-4 gap-2">
        {[
          { icon: <GitBranch size={11}/>, label: "Drivers",    value: pack.drivers },
          { icon: <FlaskConical size={11}/>, label: "Formulas", value: pack.formulas },
          { icon: <BarChart3 size={11}/>, label: "Benchmarks", value: pack.benchmarks },
          { icon: <Bot size={11}/>, label: "Workflows",        value: pack.workflows },
        ].map(s => (
          <div key={s.label} className="text-center">
            <div className="flex items-center justify-center gap-1 text-neutral-400 mb-0.5">
              {s.icon}
            </div>
            <p className="text-[14px] font-bold text-neutral-800">{s.value}</p>
            <p className="text-[9px] text-neutral-400 uppercase tracking-wide">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-neutral-100 flex items-center justify-between">
        <span className="text-[10px] text-neutral-400">Updated {pack.lastUpdated}</span>
        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <button className="text-[11px] text-blue-600 font-medium hover:underline">Preview</button>
          <button className="text-[11px] bg-blue-600 text-white px-2.5 py-1 rounded-md font-medium hover:bg-blue-700 transition-colors flex items-center gap-1">
            Apply <ChevronRight size={10}/>
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ValuePacks() {
  const [industry, setIndustry] = useState("All Industries");
  const [search, setSearch] = useState("");

  const filtered = PACKS.filter(p =>
    (industry === "All Industries" || p.industry === industry) &&
    (search === "" || p.name.toLowerCase().includes(search.toLowerCase()) || p.description.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="p-6 max-w-5xl">
      <div className="flex items-start justify-between mb-6">
        <PageHeader
          title="Value Packs"
          subtitle="Reusable domain packages combining value drivers, formulas, benchmarks, and workflows."
        />
        <Btn variant="primary">
          <Package size={13} className="mr-1.5"/> New Pack
        </Btn>
      </div>

      {/* What is a Value Pack — info banner */}
      <div className="bg-blue-50 border border-blue-100 rounded-xl px-5 py-4 mb-6 flex items-start gap-4">
        <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shrink-0 mt-0.5">
          <Sparkles size={14} className="text-white"/>
        </div>
        <div>
          <h3 className="text-[13px] font-bold text-blue-900 mb-1">What is a Value Pack?</h3>
          <p className="text-[12px] text-blue-700 leading-relaxed max-w-2xl">
            A Value Pack is a pre-built, reusable package for a specific industry or use case. Each pack bundles
            an ontology slice, value drivers, governed formula logic, benchmark relationships, and workflow
            orchestration — so you can go from a domain to a business case in minutes, not weeks.
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-5">
        <div className="flex items-center gap-2 flex-1 max-w-xs bg-white border border-neutral-200 rounded-lg px-3 py-2">
          <Search size={12} className="text-neutral-400 shrink-0"/>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search packs…"
            className="flex-1 text-[12px] bg-transparent outline-none text-neutral-600 placeholder:text-neutral-400"
          />
        </div>
        <div className="flex items-center gap-1.5">
          <Filter size={12} className="text-neutral-400"/>
          {INDUSTRIES.map(ind => (
            <button
              key={ind}
              onClick={() => setIndustry(ind)}
              className={`text-[11px] px-2.5 py-1 rounded-full border transition-colors font-medium ${
                industry === ind
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white text-neutral-500 border-neutral-200 hover:border-neutral-300"
              }`}
            >
              {ind}
            </button>
          ))}
        </div>
      </div>

      {/* Pack grid */}
      <div className="grid grid-cols-2 gap-4">
        {filtered.map(pack => <PackCard key={pack.id} pack={pack}/>)}
        {filtered.length === 0 && (
          <div className="col-span-2 text-center py-16 text-neutral-400 text-[13px]">
            No value packs match your filters.
          </div>
        )}
      </div>
    </div>
  );
}
