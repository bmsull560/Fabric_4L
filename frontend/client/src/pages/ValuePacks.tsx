/**
 * Screen — Value Packs
 * Design: Refined Enterprise SaaS
 * Spec: Value Packs as first-class product objects — reusable domain-specific
 * packages combining ontology, value drivers, formulas, benchmarks, and workflows.
 */
import { useState, useEffect } from "react";
import { PageHeader, Btn, StatusBadge } from "@/components/WfPrimitives";
import {
  Sparkles, Package, GitBranch, FlaskConical, BarChart3, Bot,
  Users, ChevronRight, Search, Filter, CheckCircle2, Lock, Globe,
} from "lucide-react";

interface ValuePack {
  id: string;
  pack_id: string;
  name: string;
  industry: string;
  description: string;
  driver_count: number;
  formula_count: number;
  benchmark_count: number;
  workflow_count: number;
  status: "active" | "draft" | "archived" | "published";
  scope: "global" | "tenant";
  lastUpdated: string;
  updated_at?: string;
}

// API base URL - adjust for your environment
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8001";

// Fallback mock data when API is unavailable
const MOCK_PACKS: ValuePack[] = [
  {
    id: "vp-001",
    pack_id: "vp-001",
    name: "Enterprise Security ROI",
    industry: "SaaS / B2B",
    description: "Quantify the financial impact of security investments — RBAC, SSO, compliance automation, and audit logging.",
    driver_count: 8, formula_count: 5, benchmark_count: 12, workflow_count: 3,
    status: "active", scope: "global", lastUpdated: "2 days ago",
  },
  {
    id: "vp-002",
    pack_id: "vp-002",
    name: "Cloud Cost Optimization",
    industry: "Infrastructure / DevOps",
    description: "Model savings from automated provisioning, rightsizing, and multi-cloud governance.",
    driver_count: 6, formula_count: 4, benchmark_count: 9, workflow_count: 2,
    status: "active", scope: "global", lastUpdated: "1 week ago",
  },
  {
    id: "vp-003",
    pack_id: "vp-003",
    name: "Customer Success Efficiency",
    industry: "SaaS / B2B",
    description: "Measure churn reduction, NRR improvement, and support deflection through intelligent automation.",
    driver_count: 7, formula_count: 6, benchmark_count: 8, workflow_count: 4,
    status: "active", scope: "tenant", lastUpdated: "3 days ago",
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
          { icon: <GitBranch size={11}/>, label: "Drivers",    value: pack.driver_count },
          { icon: <FlaskConical size={11}/>, label: "Formulas", value: pack.formula_count },
          { icon: <BarChart3 size={11}/>, label: "Benchmarks", value: pack.benchmark_count },
          { icon: <Bot size={11}/>, label: "Workflows",        value: pack.workflow_count },
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
  const [packs, setPacks] = useState<ValuePack[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch packs from API
  useEffect(() => {
    const fetchPacks = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await fetch(`${API_BASE}/v1/packs`);
        
        if (!response.ok) {
          // If API fails, fall back to mock data
          console.warn("API unavailable, using mock data");
          setPacks(MOCK_PACKS);
          return;
        }
        
        const data = await response.json();
        
        // Transform API response to match our interface
        const transformed: ValuePack[] = data.map((p: any) => ({
          id: p.pack_id,
          pack_id: p.pack_id,
          name: p.name,
          industry: p.industry,
          description: p.description || "",
          driver_count: p.driver_count ?? 0,
          formula_count: p.formula_count ?? 0,
          benchmark_count: p.benchmark_count ?? 0,
          workflow_count: p.workflow_count ?? 0,
          status: p.status === "published" ? "active" : (p.status || "draft"),
          scope: p.scope || "global",
          lastUpdated: p.updated_at ? new Date(p.updated_at).toLocaleDateString() : "Unknown",
          updated_at: p.updated_at,
        }));
        
        setPacks(transformed);
      } catch (err) {
        console.error("Failed to fetch packs:", err);
        setError("Failed to load value packs. Using fallback data.");
        setPacks(MOCK_PACKS);
      } finally {
        setLoading(false);
      }
    };
    
    fetchPacks();
  }, []);

  const filtered = packs.filter(p =>
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

      {/* Loading state */}
      {loading && (
        <div className="text-center py-16 text-neutral-400 text-[13px]">
          <div className="animate-pulse">Loading value packs...</div>
        </div>
      )}
      
      {/* Error state */}
      {error && !loading && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 mb-4">
          <p className="text-[12px] text-amber-700">{error}</p>
        </div>
      )}
      
      {/* Pack grid */}
      {!loading && (
        <div className="grid grid-cols-2 gap-4">
          {filtered.map(pack => <PackCard key={pack.id} pack={pack}/>)}
          {filtered.length === 0 && (
            <div className="col-span-2 text-center py-16 text-neutral-400 text-[13px]">
              No value packs match your filters.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
