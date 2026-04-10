/**
 * VariableRegistry — Admin Tier 3 Page
 * 
 * Variable catalog and binding management:
 * - Variable Catalog (view all variable definitions)
 * - Source Bindings (manage data source connections)
 * 
 * Features:
 * - Type system management
 * - Source binding configuration
 * - Validation rules
 * - Usage tracking
 */

import { useState } from "react";
import {
  ListChecks, Plus, Search, Filter, Edit3, Trash2, Eye, Link2,
  CheckCircle2, AlertCircle, Database, Code2, Hash, DollarSign,
  Percent, Type, Settings, ChevronRight, ChevronDown, Download,
  Upload, RefreshCw, ExternalLink, Check, X
} from "lucide-react";
import { PageHeader, Btn } from "@/components/WfPrimitives";
import { cn } from "@/lib/utils";

// ── Types ───────────────────────────────────────────────────────────────────────

type VariableType = "rate" | "currency" | "integer" | "float" | "boolean" | "string";
type SourceType = "CRM" | "Billing" | "ERP" | "Manual" | "Model" | "API" | "Database";
type ValidationStatus = "validated" | "pending" | "failed" | "deprecated";

interface Variable {
  id: string;
  name: string;
  displayName: string;
  description: string;
  type: VariableType;
  unit: string;
  source: SourceType;
  binding: string;
  bindingPath?: string;
  defaultValue?: string;
  validRange?: { min: number; max: number };
  usedIn: number;
  validationStatus: ValidationStatus;
  validationMessage?: string;
  tags: string[];
  createdAt: string;
  updatedAt: string;
  version: string;
}

interface Binding {
  id: string;
  name: string;
  sourceType: SourceType;
  connectionString: string;
  status: "connected" | "disconnected" | "error";
  lastSync?: string;
  variablesBound: number;
  errorMessage?: string;
}

// ── Mock Data ───────────────────────────────────────────────────────────────────

const VARIABLES: Variable[] = [
  { 
    id: "v-001", 
    name: "Current_Churn_Rate",       
    displayName: "Current Churn Rate",
    description: "Monthly customer churn rate percentage",
    type: "rate",     
    unit: "%",   
    source: "CRM",     
    binding: "salesforce.churn_rate",
    bindingPath: "Account.metrics.churn_rate",
    defaultValue: "5.0",
    validRange: { min: 0, max: 100 },
    usedIn: 4, 
    validationStatus: "validated",
    tags: ["retention", "customer-success"],
    createdAt: "2024-01-15",
    updatedAt: "2024-03-20",
    version: "v1.2",
  },
  { 
    id: "v-002", 
    name: "Average_Contract_Value",   
    displayName: "Average Contract Value",
    description: "Average annual contract value in USD",
    type: "currency", 
    unit: "USD", 
    source: "Billing", 
    binding: "stripe.avg_contract_value",
    bindingPath: "Subscription.avg_value",
    defaultValue: "50000",
    validRange: { min: 0, max: 10000000 },
    usedIn: 7, 
    validationStatus: "validated",
    tags: ["revenue", "pricing"],
    createdAt: "2024-01-10",
    updatedAt: "2024-04-01",
    version: "v2.0",
  },
  { 
    id: "v-003", 
    name: "Customer_Count",           
    displayName: "Total Customer Count",
    description: "Total number of active customers",
    type: "integer",  
    unit: "—",   
    source: "CRM",     
    binding: "salesforce.account_count",
    usedIn: 6, 
    validationStatus: "validated",
    tags: ["account", "count"],
    createdAt: "2024-01-20",
    updatedAt: "2024-02-15",
    version: "v1.0",
  },
  { 
    id: "v-004", 
    name: "Implementation_Cost",      
    displayName: "Implementation Cost",
    description: "One-time implementation cost estimate",
    type: "currency", 
    unit: "USD", 
    source: "Manual",  
    binding: "manual.impl_cost",
    defaultValue: "25000",
    validRange: { min: 0, max: 1000000 },
    usedIn: 3, 
    validationStatus: "pending",
    validationMessage: "Awaiting manual verification",
    tags: ["cost", "services"],
    createdAt: "2024-03-01",
    updatedAt: "2024-03-01",
    version: "v1.0",
  },
  { 
    id: "v-005", 
    name: "Projected_Retention_Lift", 
    displayName: "Projected Retention Lift",
    description: "ML-predicted retention improvement percentage",
    type: "rate",     
    unit: "%",   
    source: "Model",   
    binding: "ml_model.retention_lift",
    usedIn: 5, 
    validationStatus: "validated",
    tags: ["ml", "prediction", "retention"],
    createdAt: "2024-02-10",
    updatedAt: "2024-03-15",
    version: "v1.5",
  },
  { 
    id: "v-006", 
    name: "Support_Ticket_Volume",    
    displayName: "Support Ticket Volume",
    description: "Monthly support ticket count",
    type: "integer",  
    unit: "—",   
    source: "CRM",     
    binding: "zendesk.ticket_count",
    usedIn: 2, 
    validationStatus: "failed",
    validationMessage: "Connection timeout - check API credentials",
    tags: ["support", "operations"],
    createdAt: "2024-01-05",
    updatedAt: "2024-04-05",
    version: "v1.1",
  },
  { 
    id: "v-007", 
    name: "Manufacturing_OEE",    
    displayName: "Manufacturing OEE",
    description: "Overall Equipment Effectiveness percentage",
    type: "rate",  
    unit: "%",   
    source: "ERP",     
    binding: "sap.oee_value",
    defaultValue: "75.0",
    validRange: { min: 0, max: 100 },
    usedIn: 3, 
    validationStatus: "validated",
    tags: ["manufacturing", "efficiency", "oee"],
    createdAt: "2024-03-10",
    updatedAt: "2024-03-10",
    version: "v1.0",
  },
];

const BINDINGS: Binding[] = [
  {
    id: "b-001",
    name: "Salesforce CRM",
    sourceType: "CRM",
    connectionString: "salesforce://prod.instance",
    status: "connected",
    lastSync: "2024-04-10T08:30:00Z",
    variablesBound: 3,
  },
  {
    id: "b-002",
    name: "Stripe Billing",
    sourceType: "Billing",
    connectionString: "stripe://api.stripe.com",
    status: "connected",
    lastSync: "2024-04-10T09:15:00Z",
    variablesBound: 1,
  },
  {
    id: "b-003",
    name: "Zendesk Support",
    sourceType: "CRM",
    connectionString: "zendesk://support.api",
    status: "error",
    lastSync: "2024-04-09T14:20:00Z",
    variablesBound: 1,
    errorMessage: "API rate limit exceeded",
  },
  {
    id: "b-004",
    name: "ML Prediction Service",
    sourceType: "Model",
    connectionString: "internal://ml-service",
    status: "connected",
    lastSync: "2024-04-10T07:45:00Z",
    variablesBound: 1,
  },
];

// ── Styling Constants ───────────────────────────────────────────────────────────

const TYPE_CONFIG: Record<VariableType, { label: string; color: string; icon: React.ReactNode }> = {
  rate:     { label: "Rate",     color: "bg-cyan-50 text-cyan-700",     icon: <Percent size={10}/> },
  currency: { label: "Currency", color: "bg-emerald-50 text-emerald-700", icon: <DollarSign size={10}/> },
  integer:  { label: "Integer",  color: "bg-blue-50 text-blue-700",     icon: <Hash size={10}/> },
  float:    { label: "Float",    color: "bg-violet-50 text-violet-700",  icon: <Code2 size={10}/> },
  boolean:  { label: "Boolean",  color: "bg-amber-50 text-amber-700",    icon: <Check size={10}/> },
  string:   { label: "String",   color: "bg-neutral-100 text-neutral-600", icon: <Type size={10}/> },
};

const SOURCE_CONFIG: Record<SourceType, { color: string; icon: React.ReactNode }> = {
  CRM:      { color: "bg-blue-50 text-blue-700", icon: <Database size={10}/> },
  Billing:  { color: "bg-violet-50 text-violet-700", icon: <DollarSign size={10}/> },
  ERP:      { color: "bg-indigo-50 text-indigo-700", icon: <Database size={10}/> },
  Manual:   { color: "bg-neutral-100 text-neutral-600", icon: <Type size={10}/> },
  Model:    { color: "bg-amber-50 text-amber-700", icon: <Code2 size={10}/> },
  API:      { color: "bg-cyan-50 text-cyan-700", icon: <ExternalLink size={10}/> },
  Database: { color: "bg-emerald-50 text-emerald-700", icon: <Database size={10}/> },
};

const VALIDATION_CONFIG: Record<ValidationStatus, { color: string; icon: React.ReactNode; label: string }> = {
  validated:  { color: "text-emerald-500", icon: <CheckCircle2 size={14}/>, label: "Validated" },
  pending:    { color: "text-amber-500", icon: <AlertCircle size={14}/>, label: "Pending" },
  failed:     { color: "text-red-500", icon: <X size={14}/>, label: "Failed" },
  deprecated: { color: "text-neutral-400", icon: <AlertCircle size={14}/>, label: "Deprecated" },
};

// ── Sub-components ─────────────────────────────────────────────────────────────

function TypeBadge({ type }: { type: VariableType }) {
  const config = TYPE_CONFIG[type];
  return (
    <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full ${config.color}`}>
      {config.icon} {config.label}
    </span>
  );
}

function SourceBadge({ source }: { source: SourceType }) {
  const config = SOURCE_CONFIG[source];
  return (
    <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full ${config.color}`}>
      {config.icon} {source}
    </span>
  );
}

function ValidationIcon({ status }: { status: ValidationStatus }) {
  const config = VALIDATION_CONFIG[status];
  return <span className={config.color} title={config.label}>{config.icon}</span>;
}

function BindingCard({ binding, onTest }: { binding: Binding; onTest: (id: string) => void }) {
  const statusColors = {
    connected: "bg-emerald-50 text-emerald-700 border-emerald-200",
    disconnected: "bg-neutral-100 text-neutral-600 border-neutral-200",
    error: "bg-red-50 text-red-600 border-red-200",
  };

  return (
    <div className="bg-white border border-neutral-200 rounded-xl p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-neutral-100 flex items-center justify-center text-neutral-600">
            <Database size={18}/>
          </div>
          <div>
            <h4 className="text-[13px] font-semibold text-neutral-800">{binding.name}</h4>
            <p className="text-[11px] text-neutral-500 font-mono">{binding.connectionString}</p>
          </div>
        </div>
        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${statusColors[binding.status]}`}>
          {binding.status}
        </span>
      </div>
      
      <div className="flex items-center justify-between text-[11px]">
        <div className="flex items-center gap-4">
          <span className="text-neutral-500">
            <span className="font-semibold text-neutral-700">{binding.variablesBound}</span> variables bound
          </span>
          {binding.lastSync && (
            <span className="text-neutral-400">
              Last sync: {new Date(binding.lastSync).toLocaleString()}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={() => onTest(binding.id)}
            className="flex items-center gap-1 px-2.5 py-1 text-[10px] font-medium text-neutral-600 hover:bg-neutral-100 rounded transition-colors"
          >
            <RefreshCw size={10}/> Test
          </button>
          <button className="p-1.5 hover:bg-neutral-100 rounded text-neutral-400 hover:text-neutral-700 transition-colors">
            <Settings size={12}/>
          </button>
        </div>
      </div>
      
      {binding.errorMessage && (
        <div className="mt-3 p-2 bg-red-50 border border-red-100 rounded-lg text-[11px] text-red-600">
          {binding.errorMessage}
        </div>
      )}
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────

type TabType = "catalog" | "bindings";

export default function VariableRegistry() {
  const [activeTab, setActiveTab] = useState<TabType>("catalog");
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<"all" | VariableType>("all");
  const [sourceFilter, setSourceFilter] = useState<"all" | SourceType>("all");
  const [expandedVariable, setExpandedVariable] = useState<string | null>(null);

  const filteredVariables = VARIABLES.filter(v =>
    (typeFilter === "all" || v.type === typeFilter) &&
    (sourceFilter === "all" || v.source === sourceFilter) &&
    (search === "" || 
     v.name.toLowerCase().includes(search.toLowerCase()) ||
     v.displayName.toLowerCase().includes(search.toLowerCase()))
  );

  const stats = {
    total: VARIABLES.length,
    validated: VARIABLES.filter(v => v.validationStatus === "validated").length,
    pending: VARIABLES.filter(v => v.validationStatus === "pending").length,
    failed: VARIABLES.filter(v => v.validationStatus === "failed").length,
    totalUsage: VARIABLES.reduce((s, v) => s + v.usedIn, 0),
  };

  const handleTestBinding = (id: string) => {
    console.log(`Testing binding ${id}`);
    // In real implementation, call API to test connection
  };

  return (
    <div className="p-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <PageHeader
          title="Variable Registry"
          subtitle="Catalog of all formula variables — definitions, source bindings, type system, and validation rules."
        />
        <div className="flex items-center gap-2">
          <Btn variant="outline"><Upload size={13} className="mr-1"/> Import</Btn>
          <Btn variant="primary"><Plus size={13} className="mr-1"/> Register Variable</Btn>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-5 gap-4 mb-6">
        {[
          { label: "Total Variables", value: stats.total, icon: <ListChecks size={14}/> },
          { label: "Validated", value: stats.validated, icon: <CheckCircle2 size={14}/>, color: "text-emerald-600" },
          { label: "Pending", value: stats.pending, icon: <AlertCircle size={14}/>, color: "text-amber-600" },
          { label: "Failed", value: stats.failed, icon: <X size={14}/>, color: "text-red-600" },
          { label: "Total Usage", value: stats.totalUsage, icon: <Link2 size={14}/>, color: "text-blue-600" },
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
          { id: "catalog" as const, label: "Variable Catalog", count: VARIABLES.length },
          { id: "bindings" as const, label: "Source Bindings", count: BINDINGS.length },
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

      {activeTab === "catalog" ? (
        <>
          {/* Filters */}
          <div className="flex items-center gap-3 mb-4">
            <div className="flex items-center gap-2 bg-white border border-neutral-200 rounded-lg px-3 py-2 max-w-sm flex-1">
              <Search size={12} className="text-neutral-400 shrink-0"/>
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search variables..."
                className="flex-1 text-[12px] bg-transparent outline-none text-neutral-600 placeholder:text-neutral-400"
              />
            </div>
            <select
              value={typeFilter}
              onChange={e => setTypeFilter(e.target.value as any)}
              className="px-3 py-2 text-[11px] border border-neutral-200 rounded-lg bg-white text-neutral-600 outline-none focus:border-blue-300"
            >
              <option value="all">All Types</option>
              {Object.keys(TYPE_CONFIG).map(t => (
                <option key={t} value={t}>{TYPE_CONFIG[t as VariableType].label}</option>
              ))}
            </select>
            <select
              value={sourceFilter}
              onChange={e => setSourceFilter(e.target.value as any)}
              className="px-3 py-2 text-[11px] border border-neutral-200 rounded-lg bg-white text-neutral-600 outline-none focus:border-blue-300"
            >
              <option value="all">All Sources</option>
              {Object.keys(SOURCE_CONFIG).map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <div className="ml-auto flex items-center gap-2">
              <button className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium text-neutral-600 hover:bg-neutral-100 rounded-lg transition-colors">
                <Download size={12}/> Export
              </button>
            </div>
          </div>

          {/* Variable Table */}
          <div className="bg-white border border-neutral-200 rounded-xl shadow-sm overflow-hidden">
            <table className="w-full text-[12px]">
              <thead>
                <tr className="border-b border-neutral-100 bg-neutral-50">
                  <th className="w-8 px-3 py-3"></th>
                  {["Variable Name", "Type", "Unit", "Source", "Binding", "Used In", "Status", ""].map(h => (
                    <th key={h} className="text-left px-3 py-3 text-[10px] uppercase tracking-wider text-neutral-400 font-semibold">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {filteredVariables.map(v => (
                  <>
                    <tr 
                      key={v.id} 
                      className="hover:bg-neutral-50 transition-colors group cursor-pointer"
                      onClick={() => setExpandedVariable(expandedVariable === v.id ? null : v.id)}
                    >
                      <td className="px-3 py-3">
                        {expandedVariable === v.id ? 
                          <ChevronDown size={14} className="text-neutral-400"/> : 
                          <ChevronRight size={14} className="text-neutral-400"/>
                        }
                      </td>
                      <td className="px-3 py-3">
                        <div className="flex items-center gap-2">
                          <ListChecks size={14} className="text-violet-500 shrink-0"/>
                          <div>
                            <span className="font-mono font-medium text-neutral-800 block">{v.name}</span>
                            <span className="text-[10px] text-neutral-500">{v.displayName}</span>
                          </div>
                        </div>
                      </td>
                      <td className="px-3 py-3"><TypeBadge type={v.type}/></td>
                      <td className="px-3 py-3 text-neutral-500">{v.unit}</td>
                      <td className="px-3 py-3"><SourceBadge source={v.source}/></td>
                      <td className="px-3 py-3 font-mono text-[11px] text-neutral-500">{v.binding}</td>
                      <td className="px-3 py-3 text-neutral-600">{v.usedIn} formulas</td>
                      <td className="px-3 py-3"><ValidationIcon status={v.validationStatus}/></td>
                      <td className="px-3 py-3">
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
                    {expandedVariable === v.id && (
                      <tr className="bg-neutral-50/50">
                        <td colSpan={9} className="px-3 py-4">
                          <div className="grid grid-cols-3 gap-4">
                            <div>
                              <p className="text-[10px] uppercase tracking-wider text-neutral-400 font-semibold mb-1">Description</p>
                              <p className="text-[12px] text-neutral-700">{v.description}</p>
                            </div>
                            <div>
                              <p className="text-[10px] uppercase tracking-wider text-neutral-400 font-semibold mb-1">Binding Details</p>
                              <p className="text-[11px] font-mono text-neutral-600">{v.bindingPath || v.binding}</p>
                              {v.defaultValue && (
                                <p className="text-[11px] text-neutral-500 mt-1">Default: {v.defaultValue}</p>
                              )}
                            </div>
                            <div>
                              <p className="text-[10px] uppercase tracking-wider text-neutral-400 font-semibold mb-1">Metadata</p>
                              <div className="space-y-1 text-[11px] text-neutral-600">
                                <p>Version: {v.version}</p>
                                <p>Created: {new Date(v.createdAt).toLocaleDateString()}</p>
                                <p>Updated: {new Date(v.updatedAt).toLocaleDateString()}</p>
                                {v.validRange && (
                                  <p>Range: {v.validRange.min} - {v.validRange.max}</p>
                                )}
                              </div>
                            </div>
                          </div>
                          {v.validationMessage && (
                            <div className={`mt-3 p-2 rounded-lg text-[11px] ${
                              v.validationStatus === "failed" ? "bg-red-50 text-red-600" : "bg-amber-50 text-amber-700"
                            }`}>
                              {v.validationMessage}
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
            {filteredVariables.length === 0 && (
              <div className="text-center py-12 text-neutral-400 text-[12px]">
                <ListChecks size={32} className="mx-auto mb-3 text-neutral-300"/>
                No variables match your filters.
              </div>
            )}
          </div>
        </>
      ) : (
        <>
          {/* Source Bindings */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[14px] font-semibold text-neutral-800">Connected Data Sources</h3>
              <Btn variant="outline"><Plus size={12} className="mr-1"/> Add Connection</Btn>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {BINDINGS.map(binding => (
                <BindingCard 
                  key={binding.id} 
                  binding={binding} 
                  onTest={handleTestBinding}
                />
              ))}
            </div>
          </div>

          {/* Binding Health Summary */}
          <div className="bg-white border border-neutral-200 rounded-xl p-4">
            <h3 className="text-[14px] font-semibold text-neutral-800 mb-4">Connection Health</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="flex items-center gap-3 p-3 bg-emerald-50 rounded-lg">
                <CheckCircle2 size={20} className="text-emerald-600"/>
                <div>
                  <p className="text-[18px] font-bold text-emerald-700">{BINDINGS.filter(b => b.status === "connected").length}</p>
                  <p className="text-[11px] text-emerald-600">Connected</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-red-50 rounded-lg">
                <X size={20} className="text-red-600"/>
                <div>
                  <p className="text-[18px] font-bold text-red-700">{BINDINGS.filter(b => b.status === "error").length}</p>
                  <p className="text-[11px] text-red-600">Errors</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-neutral-50 rounded-lg">
                <RefreshCw size={20} className="text-neutral-600"/>
                <div>
                  <p className="text-[18px] font-bold text-neutral-700">
                    {BINDINGS.filter(b => b.lastSync).length}
                  </p>
                  <p className="text-[11px] text-neutral-600">Synced Today</p>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
