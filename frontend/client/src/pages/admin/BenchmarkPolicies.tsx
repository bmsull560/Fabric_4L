/**
 * BenchmarkPolicies — Admin Tier 3 Page
 * 
 * Industry benchmark management:
 * - Benchmark Library (view and manage benchmarks)
 * - Policy Configuration (set thresholds, refresh cadence, fallback policies)
 * 
 * Features:
 * - Confidence scoring and source tracking
 * - Industry/vertical filtering
 * - Policy rule management
 */

import { useState } from "react";
import {
  BarChart3, Plus, Search, Filter, ArrowUpDown, Edit3, Trash2, Eye,
  Clock, Globe, Database, CheckCircle2, AlertTriangle, TrendingUp,
  Download, Settings2, Info, ChevronDown, ChevronRight
} from "lucide-react";
import { PageHeader, Btn } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";

// ── Types ───────────────────────────────────────────────────────────────────────

type ConfidenceLevel = "High" | "Medium" | "Low";
type BenchmarkStatus = "active" | "draft" | "deprecated";
type PolicyType = "threshold" | "cadence" | "fallback" | "override";

interface Benchmark {
  id: string;
  name: string;
  industry: string;
  vertical?: string;
  valueRange: string;
  confidence: ConfidenceLevel;
  source: string;
  sourceUrl?: string;
  year: number;
  status: BenchmarkStatus;
  tags: string[];
  lastVerified?: string;
  usageCount: number;
}

interface Policy {
  id: string;
  type: PolicyType;
  name: string;
  description: string;
  value: string;
  isEnabled: boolean;
  scope: "tenant" | "pack" | "formula";
}

// ── Mock Data ───────────────────────────────────────────────────────────────────

const BENCHMARKS: Benchmark[] = [
  { 
    id: "b-001", 
    name: "SaaS Average Churn Rate",     
    industry: "SaaS", 
    vertical: "B2B",
    valueRange: "5–7% / year",    
    confidence: "High",   
    source: "Gartner", 
    year: 2024,
    status: "active",
    tags: ["retention", "subscription"],
    lastVerified: "2024-03-15",
    usageCount: 23,
  },
  { 
    id: "b-002", 
    name: "Enterprise ACV Range",         
    industry: "SaaS", 
    vertical: "B2B",
    valueRange: "$50K – $500K",   
    confidence: "High",   
    source: "Internal", 
    year: 2024,
    status: "active",
    tags: ["pricing", "enterprise"],
    usageCount: 45,
  },
  { 
    id: "b-003", 
    name: "Retention Lift (Analytics)",   
    industry: "SaaS", 
    vertical: "B2B",
    valueRange: "15–25%",         
    confidence: "Medium", 
    source: "Forrester", 
    year: 2023,
    status: "active",
    tags: ["analytics", "retention"],
    lastVerified: "2024-01-20",
    usageCount: 12,
  },
  { 
    id: "b-004", 
    name: "Cloud Cost Reduction (IaC)",   
    industry: "Infrastructure", 
    valueRange: "20–35%",         
    confidence: "High",   
    source: "IDC", 
    year: 2024,
    status: "active",
    tags: ["cloud", "cost-optimization"],
    usageCount: 18,
  },
  { 
    id: "b-005", 
    name: "Compliance Fine Avoidance",    
    industry: "Financial Services", 
    valueRange: "$500K – $5M",    
    confidence: "Low",    
    source: "Manual", 
    year: 2024,
    status: "draft",
    tags: ["compliance", "risk"],
    usageCount: 3,
  },
  { 
    id: "b-006", 
    name: "Manufacturing OEE Benchmark",   
    industry: "Manufacturing", 
    valueRange: "60–85%",         
    confidence: "High",   
    source: "Industry Association", 
    year: 2024,
    status: "active",
    tags: ["oee", "efficiency"],
    usageCount: 8,
  },
];

const POLICIES: Policy[] = [
  {
    id: "p-001",
    type: "threshold",
    name: "Default Confidence Threshold",
    description: "Minimum confidence level required for benchmark usage in formulas",
    value: "Medium",
    isEnabled: true,
    scope: "tenant",
  },
  {
    id: "p-002",
    type: "cadence",
    name: "Benchmark Refresh Cadence",
    description: "How frequently benchmark values are reviewed and updated",
    value: "Quarterly",
    isEnabled: true,
    scope: "tenant",
  },
  {
    id: "p-003",
    type: "fallback",
    name: "Low Confidence Fallback",
    description: "Action when benchmark confidence falls below threshold",
    value: "Use internal estimates",
    isEnabled: true,
    scope: "tenant",
  },
  {
    id: "p-004",
    type: "override",
    name: "Allow Admin Override",
    description: "Permit administrators to override confidence thresholds",
    value: "Enabled",
    isEnabled: false,
    scope: "tenant",
  },
];

// ── Styling Constants ───────────────────────────────────────────────────────────

const CONFIDENCE_STYLES: Record<ConfidenceLevel, { color: string; bg: string; icon: React.ReactNode }> = {
  High:   { color: "text-emerald-600", bg: "bg-emerald-50", icon: <CheckCircle2 size={12}/> },
  Medium: { color: "text-amber-600", bg: "bg-amber-50", icon: <Info size={12}/> },
  Low:    { color: "text-red-600", bg: "bg-red-50", icon: <AlertTriangle size={12}/> },
};

const STATUS_STYLES: Record<BenchmarkStatus, string> = {
  active: "bg-emerald-50 text-emerald-700 border-emerald-200",
  draft: "bg-neutral-100 text-neutral-600 border-neutral-200",
  deprecated: "bg-red-50 text-red-500 border-red-200",
};

const POLICY_TYPE_ICONS: Record<PolicyType, React.ReactNode> = {
  threshold: <BarChart3 size={14}/>,
  cadence: <Clock size={14}/>,
  fallback: <Database size={14}/>,
  override: <Settings2 size={14}/>,
};

// ── Sub-components ─────────────────────────────────────────────────────────────

function ConfidenceBadge({ level }: { level: ConfidenceLevel }) {
  const style = CONFIDENCE_STYLES[level];
  return (
    <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full ${style.bg} ${style.color}`}>
      {style.icon} {level}
    </span>
  );
}

function StatusBadge({ status }: { status: BenchmarkStatus }) {
  return (
    <span className={`inline-flex items-center text-[10px] font-semibold px-2 py-0.5 rounded-full border ${STATUS_STYLES[status]}`}>
      {status}
    </span>
  );
}

function PolicyCard({ policy, onToggle }: { policy: Policy; onToggle: (id: string) => void }) {
  return (
    <div className="bg-white border border-neutral-200 rounded-xl p-4 flex items-start gap-4">
      <div className="w-10 h-10 rounded-lg bg-neutral-100 flex items-center justify-center text-neutral-600 shrink-0">
        {POLICY_TYPE_ICONS[policy.type]}
      </div>
      <div className="flex-1">
        <div className="flex items-start justify-between mb-1">
          <h4 className="text-[13px] font-semibold text-neutral-800">{policy.name}</h4>
          <button
            onClick={() => onToggle(policy.id)}
            className={cn(
              "w-10 h-5 rounded-full transition-colors relative",
              policy.isEnabled ? "bg-blue-600" : "bg-neutral-300"
            )}
          >
            <span className={cn(
              "absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform",
              policy.isEnabled ? "translate-x-5" : "translate-x-0.5"
            )} />
          </button>
        </div>
        <p className="text-[11px] text-neutral-500 mb-2">{policy.description}</p>
        <div className="flex items-center gap-3">
          <span className="text-[11px] font-medium text-neutral-700 bg-neutral-100 px-2 py-0.5 rounded">
            {policy.value}
          </span>
          <span className="text-[10px] text-neutral-400 uppercase tracking-wider">
            Scope: {policy.scope}
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────

type TabType = "library" | "policies";

export default function BenchmarkPolicies() {
  const [activeTab, setActiveTab] = useState<TabType>("library");
  const [search, setSearch] = useState("");
  const [confidenceFilter, setConfidenceFilter] = useState<"all" | ConfidenceLevel>("all");
  const [industryFilter, setIndustryFilter] = useState<"all" | string>("all");
  const [policies, setPolicies] = useState(POLICIES);

  const industries = Array.from(new Set(BENCHMARKS.map(b => b.industry)));

  const filteredBenchmarks = BENCHMARKS.filter(b =>
    (confidenceFilter === "all" || b.confidence === confidenceFilter) &&
    (industryFilter === "all" || b.industry === industryFilter) &&
    (search === "" || b.name.toLowerCase().includes(search.toLowerCase()))
  );

  const stats = {
    total: BENCHMARKS.length,
    highConfidence: BENCHMARKS.filter(b => b.confidence === "High").length,
    active: BENCHMARKS.filter(b => b.status === "active").length,
    totalUsage: BENCHMARKS.reduce((s, b) => s + b.usageCount, 0),
  };

  const togglePolicy = (id: string) => {
    setPolicies(policies.map(p => 
      p.id === id ? { ...p, isEnabled: !p.isEnabled } : p
    ));
  };

  return (
    <div className="p-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <PageHeader
          title="Benchmark Policies"
          subtitle="Define and manage industry benchmarks used in formula evaluation and business case generation."
        />
        <Btn variant="primary"><Plus size={13} className="mr-1"/> Add Benchmark</Btn>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: "Total Benchmarks", value: stats.total, icon: <BarChart3 size={14}/> },
          { label: "High Confidence", value: stats.highConfidence, icon: <CheckCircle2 size={14}/>, color: "text-emerald-600" },
          { label: "Active", value: stats.active, icon: <TrendingUp size={14}/>, color: "text-blue-600" },
          { label: "Total Usage", value: stats.totalUsage, icon: <Database size={14}/>, color: "text-violet-600" },
        ].map(s => (
          <div key={s.label} className="bg-white border border-neutral-200 rounded-xl px-4 py-3">
            <div className="flex items-center gap-2 mb-1">
              <span className={s.color || "text-neutral-500"}>{s.icon}</span>
              <span className="text-[10px] uppercase tracking-wider text-neutral-400 font-semibold">{s.label}</span>
            </div>
            <p className={`text-[22px] font-extrabold ${s.color || "text-neutral-800"}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-neutral-200 mb-4">
        {[
          { id: "library" as const, label: "Benchmark Library", count: BENCHMARKS.length },
          { id: "policies" as const, label: "Policy Configuration" },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "px-4 py-2.5 text-[12px] font-medium transition-colors relative",
              activeTab === tab.id
                ? "text-blue-700"
                : "text-neutral-500 hover:text-neutral-700"
            )}
          >
            <span className="flex items-center gap-2">
              {tab.label}
              {tab.count !== undefined && (
                <span className={cn(
                  "px-1.5 py-0.5 rounded text-[10px]",
                  activeTab === tab.id ? "bg-blue-100 text-blue-700" : "bg-neutral-100 text-neutral-600"
                )}>
                  {tab.count}
                </span>
              )}
            </span>
            {activeTab === tab.id && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-t-full" />
            )}
          </button>
        ))}
      </div>

      {activeTab === "library" ? (
        <>
          {/* Filters */}
          <div className="flex items-center gap-3 mb-4">
            <div className="flex items-center gap-2 bg-white border border-neutral-200 rounded-lg px-3 py-2 max-w-sm flex-1">
              <Search size={12} className="text-neutral-400 shrink-0"/>
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search benchmarks..."
                className="flex-1 text-[12px] bg-transparent outline-none text-neutral-600 placeholder:text-neutral-400"
              />
            </div>
            <select
              value={confidenceFilter}
              onChange={e => setConfidenceFilter(e.target.value as any)}
              className="px-3 py-2 text-[11px] border border-neutral-200 rounded-lg bg-white text-neutral-600 outline-none focus:border-blue-300"
            >
              <option value="all">All Confidence</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
            <select
              value={industryFilter}
              onChange={e => setIndustryFilter(e.target.value)}
              className="px-3 py-2 text-[11px] border border-neutral-200 rounded-lg bg-white text-neutral-600 outline-none focus:border-blue-300"
            >
              <option value="all">All Industries</option>
              {industries.map(ind => (
                <option key={ind} value={ind}>{ind}</option>
              ))}
            </select>
            <div className="ml-auto flex items-center gap-2">
              <button className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium text-neutral-600 hover:bg-neutral-100 rounded-lg transition-colors">
                <Download size={12}/> Export
              </button>
            </div>
          </div>

          {/* Benchmark Table */}
          <div className="bg-white border border-neutral-200 rounded-xl shadow-sm overflow-hidden">
            <table className="w-full text-[12px]">
              <thead>
                <tr className="border-b border-neutral-100 bg-neutral-50">
                  {["Benchmark", "Industry", "Value Range", "Confidence", "Source", "Status", "Usage", ""].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-[10px] uppercase tracking-wider text-neutral-400 font-semibold">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {filteredBenchmarks.map(b => (
                  <tr key={b.id} className="hover:bg-neutral-50 transition-colors group">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <BarChart3 size={14} className="text-blue-500 shrink-0"/>
                        <div>
                          <span className="font-medium text-neutral-800 block">{b.name}</span>
                          {b.tags.length > 0 && (
                            <div className="flex items-center gap-1 mt-1">
                              {b.tags.map(tag => (
                                <span key={tag} className="text-[9px] px-1.5 py-0.5 bg-neutral-100 text-neutral-500 rounded">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-neutral-500">
                      {b.industry}
                      {b.vertical && <span className="text-neutral-400"> / {b.vertical}</span>}
                    </td>
                    <td className="px-4 py-3 font-mono text-[11px] text-neutral-700">{b.valueRange}</td>
                    <td className="px-4 py-3"><ConfidenceBadge level={b.confidence}/></td>
                    <td className="px-4 py-3 text-neutral-500">
                      <div className="flex items-center gap-1">
                        <Globe size={10}/>
                        {b.source} {b.year}
                      </div>
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={b.status}/></td>
                    <td className="px-4 py-3 text-neutral-600">{b.usageCount} formulas</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button className="p-1.5 rounded hover:bg-neutral-100 text-neutral-400 hover:text-neutral-700" title="View">
                          <Eye size={13}/>
                        </button>
                        <button className="p-1.5 rounded hover:bg-neutral-100 text-neutral-400 hover:text-neutral-700" title="Edit">
                          <Edit3 size={13}/>
                        </button>
                        <button className="p-1.5 rounded hover:bg-red-50 text-neutral-400 hover:text-red-500" title="Delete">
                          <Trash2 size={13}/>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filteredBenchmarks.length === 0 && (
              <div className="text-center py-12 text-neutral-400 text-[12px]">
                <BarChart3 size={32} className="mx-auto mb-3 text-neutral-300"/>
                No benchmarks match your filters.
              </div>
            )}
          </div>
        </>
      ) : (
        <>
          {/* Policy Configuration */}
          <div className="mb-6">
            <h3 className="text-[14px] font-semibold text-neutral-800 mb-4">Policy Rules</h3>
            <div className="grid grid-cols-2 gap-4">
              {policies.map(policy => (
                <PolicyCard 
                  key={policy.id} 
                  policy={policy} 
                  onToggle={togglePolicy}
                />
              ))}
            </div>
          </div>

          {/* Policy Audit Log */}
          <div className="bg-white border border-neutral-200 rounded-xl p-4">
            <h3 className="text-[14px] font-semibold text-neutral-800 mb-4">Recent Policy Changes</h3>
            <div className="space-y-3">
              {[
                { action: "Updated", target: "Default Confidence Threshold", from: "Low", to: "Medium", user: "Admin", time: "2 hours ago" },
                { action: "Enabled", target: "Low Confidence Fallback", from: "—", to: "Active", user: "Admin", time: "1 day ago" },
                { action: "Created", target: "Quarterly Review Cadence", from: "—", to: "Active", user: "System", time: "3 days ago" },
              ].map((log, i) => (
                <div key={i} className="flex items-center gap-3 text-[12px]">
                  <span className="text-neutral-400">{log.time}</span>
                  <span className="font-medium text-neutral-700">{log.action}</span>
                  <span className="text-neutral-600">{log.target}</span>
                  {log.from !== "—" && (
                    <>
                      <span className="text-neutral-400">from</span>
                      <span className="bg-neutral-100 px-1.5 py-0.5 rounded text-neutral-600">{log.from}</span>
                    </>
                  )}
                  <span className="text-neutral-400">to</span>
                  <span className="bg-blue-50 px-1.5 py-0.5 rounded text-blue-700">{log.to}</span>
                  <span className="text-neutral-400 ml-auto">by {log.user}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
