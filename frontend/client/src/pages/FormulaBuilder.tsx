/**
 * Screen 6 — Formula Studio (formerly Formula Builder)
 * Design: Refined Enterprise SaaS
 * Spec change: Reframed as a governed admin workspace with version history,
 * draft/active status, approval workflow, and dependency mapping.
 * Progressive disclosure: basic expression authoring visible by default;
 * governance controls revealed under "Governance" tab.
 */
import { useState } from "react";
import {
  Play, Save, X, Plus, GitBranch, CheckCircle2, Clock, AlertCircle,
  Lock, Unlock, History, ChevronRight, Users, Tag, Link2,
} from "lucide-react";
import { PageHeader, Btn, SectionCard, Tabs } from "@/components/WfPrimitives";

const VARIABLES = [
  { name: "Current_Churn_Rate",       type: "rate",     source: "CRM" },
  { name: "Average_Contract_Value",   type: "currency",  source: "Billing" },
  { name: "Projected_Retention_Lift", type: "rate",     source: "Model" },
  { name: "Implementation_Cost",      type: "currency",  source: "Manual" },
  { name: "Customer_Count",           type: "integer",  source: "CRM" },
];

const FORMULA = `({Customer_Count} *
 {Current_Churn_Rate} *
 {Projected_Retention_Lift} *
 {Average_Contract_Value})
— {Implementation_Cost}`;

const TEST_INPUTS = [
  { label: "Customer_Count",       value: "1,000" },
  { label: "Current_Churn_Rate",   value: "5%" },
  { label: "Retention_Lift",       value: "20%" },
  { label: "Avg_Contract_Value",   value: "$50,000" },
  { label: "Implementation_Cost",  value: "$100,000" },
];

const VERSION_HISTORY = [
  { version: "v3 (current draft)", author: "J. Rivera", date: "Today 09:41", status: "draft",    note: "Added Implementation_Cost variable" },
  { version: "v2 (active)",        author: "M. Chen",   date: "Apr 7",       status: "approved", note: "Approved by Finance team" },
  { version: "v1",                 author: "J. Rivera", date: "Apr 2",       status: "archived", note: "Initial version" },
];

const DEPENDENTS = [
  { type: "Business Case", name: "Globex.io — Q2 Expansion",     pack: "Enterprise Security ROI" },
  { type: "Value Tree",    name: "Revenue Retention Driver",      pack: "SaaS / B2B" },
  { type: "Workflow",      name: "Churn Reduction Agent",         pack: "Customer Success" },
];

const SOURCE_TYPE_COLOR: Record<string, string> = {
  CRM:     "bg-blue-50 text-blue-700",
  Billing: "bg-emerald-50 text-emerald-700",
  Model:   "bg-violet-50 text-violet-700",
  Manual:  "bg-amber-50 text-amber-700",
};

const VAR_TYPE_COLOR: Record<string, string> = {
  rate:     "bg-cyan-100 text-cyan-700",
  currency: "bg-emerald-100 text-emerald-700",
  integer:  "bg-neutral-100 text-neutral-600",
};

export default function FormulaBuilder() {
  const [activeTab, setActiveTab] = useState("Expression");
  const [tested, setTested] = useState(false);
  const [activationState, setActivationState] = useState<"draft" | "pending" | "approved">("draft");

  const statusLabel = {
    draft:    { label: "Draft",           color: "bg-neutral-100 text-neutral-600", icon: <Clock size={11}/> },
    pending:  { label: "Pending Approval",color: "bg-amber-50 text-amber-700",      icon: <AlertCircle size={11}/> },
    approved: { label: "Active",          color: "bg-emerald-50 text-emerald-700",  icon: <CheckCircle2 size={11}/> },
  }[activationState];

  return (
    <div className="p-6">
      {/* Header with governance status */}
      <div className="flex items-start justify-between mb-5">
        <PageHeader
          breadcrumbs={["Value Models", "Formula Studio", "Customer Churn Reduction ROI"]}
          title="Customer Churn Reduction ROI"
          subtitle="Governed formula asset — version 3 (draft)"
        />
        <div className="flex items-center gap-2 shrink-0">
          <span className={`flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-1 rounded-full ${statusLabel.color}`}>
            {statusLabel.icon} {statusLabel.label}
          </span>
          {activationState === "draft" && (
            <Btn variant="primary" onClick={() => setActivationState("pending")}>
              Submit for Approval
            </Btn>
          )}
          {activationState === "pending" && (
            <Btn variant="primary" onClick={() => setActivationState("approved")}>
              <CheckCircle2 size={11}/> Approve
            </Btn>
          )}
          {activationState === "approved" && (
            <Btn variant="ghost" onClick={() => setActivationState("draft")}>
              <Unlock size={11}/> Revise
            </Btn>
          )}
        </div>
      </div>

      {/* Tabs: Expression | Variables | Governance | Dependencies */}
      <Tabs
        tabs={["Expression", "Variables", "Governance", "Dependencies"]}
        active={activeTab}
        onChange={setActiveTab}
      />

      <div className="flex gap-5 mt-4">
        {/* ── Left main panel ─────────────────────────────────────────────── */}
        <div className="flex-1 space-y-4">

          {/* Expression tab */}
          {activeTab === "Expression" && (
            <>
              <SectionCard title="Formula Definition">
                <div className="space-y-3">
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 block mb-1">Name</label>
                    <input
                      readOnly
                      value="Customer Churn Reduction ROI"
                      className="w-full border border-neutral-200 rounded-md px-3 py-2 text-[13px] text-neutral-800 bg-neutral-50 outline-none"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 block mb-1">Description</label>
                    <textarea
                      readOnly
                      value="Calculate ROI from reducing customer churn through predictive analytics"
                      rows={2}
                      className="w-full border border-neutral-200 rounded-md px-3 py-2 text-[12px] text-neutral-700 bg-neutral-50 outline-none resize-none"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 block mb-1">Value Driver</label>
                      <div className="border border-neutral-200 rounded-md px-3 py-2 text-[12px] text-neutral-700 bg-neutral-50 flex justify-between">
                        Revenue Retention <span className="text-neutral-400">▾</span>
                      </div>
                    </div>
                    <div>
                      <label className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 block mb-1">Value Pack</label>
                      <div className="border border-neutral-200 rounded-md px-3 py-2 text-[12px] text-neutral-700 bg-neutral-50 flex justify-between">
                        Enterprise Security ROI <span className="text-neutral-400">▾</span>
                      </div>
                    </div>
                  </div>
                </div>
              </SectionCard>

              <SectionCard title="Formula Expression">
                <div className="bg-[#0d1117] rounded-lg p-4 font-mono text-[12px] text-[#c9d1d9] leading-relaxed whitespace-pre">
                  {FORMULA}
                </div>
                <div className="flex gap-2 mt-3">
                  <Btn variant="primary" onClick={() => setTested(true)}>
                    <Play size={11}/> Test with Sample Data
                  </Btn>
                  <Btn variant="ghost"><Save size={11}/> Save Draft</Btn>
                </div>
              </SectionCard>

              {tested && (
                <SectionCard title="Test Results">
                  <div className="space-y-1.5 mb-3">
                    {TEST_INPUTS.map(t => (
                      <div key={t.label} className="flex justify-between text-[12px]">
                        <span className="text-neutral-500 font-mono">{t.label}:</span>
                        <span className="font-semibold text-neutral-800">{t.value}</span>
                      </div>
                    ))}
                  </div>
                  <div className="border-t border-neutral-100 pt-3 flex items-center gap-6">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">Result</span>
                      <div className="text-[20px] font-extrabold text-emerald-700">$900,000.00</div>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">ROI</span>
                      <div className="text-[20px] font-extrabold text-emerald-700">900%</div>
                    </div>
                    <div className="ml-auto">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">Confidence</span>
                      <div className="text-[14px] font-bold text-neutral-700">High (0.91)</div>
                    </div>
                  </div>
                </SectionCard>
              )}
            </>
          )}

          {/* Variables tab */}
          {activeTab === "Variables" && (
            <SectionCard title="Variable Registry — Bound Variables">
              <div className="space-y-2">
                {VARIABLES.map(v => (
                  <div key={v.name} className="flex items-center gap-3 p-3 bg-neutral-50 rounded-lg border border-neutral-100">
                    <span className="w-2 h-2 rounded-full bg-violet-400 shrink-0"/>
                    <span className="flex-1 font-mono text-[12px] text-neutral-800">{v.name}</span>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${VAR_TYPE_COLOR[v.type]}`}>{v.type}</span>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${SOURCE_TYPE_COLOR[v.source]}`}>{v.source}</span>
                    <button className="text-[11px] text-neutral-400 hover:text-neutral-700">Edit binding</button>
                  </div>
                ))}
              </div>
              <Btn variant="ghost" className="mt-3 text-[11px]">
                <Plus size={11}/> Add Variable from Registry
              </Btn>
            </SectionCard>
          )}

          {/* Governance tab */}
          {activeTab === "Governance" && (
            <div className="space-y-4">
              <SectionCard title="Version History">
                <div className="space-y-2">
                  {VERSION_HISTORY.map((v, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 rounded-lg border border-neutral-100 bg-neutral-50">
                      <div className="mt-0.5">
                        {v.status === "approved" && <CheckCircle2 size={14} className="text-emerald-500"/>}
                        {v.status === "draft"    && <Clock size={14} className="text-neutral-400"/>}
                        {v.status === "archived" && <History size={14} className="text-neutral-300"/>}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[12px] font-bold text-neutral-800">{v.version}</span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                            v.status === "approved" ? "bg-emerald-50 text-emerald-700" :
                            v.status === "draft"    ? "bg-neutral-100 text-neutral-600" :
                            "bg-neutral-50 text-neutral-400"
                          }`}>{v.status}</span>
                        </div>
                        <p className="text-[11px] text-neutral-500 mt-0.5">{v.note}</p>
                        <p className="text-[10px] text-neutral-400 mt-0.5">{v.author} · {v.date}</p>
                      </div>
                      {v.status !== "draft" && (
                        <button className="text-[11px] text-blue-600 hover:underline shrink-0">Restore</button>
                      )}
                    </div>
                  ))}
                </div>
              </SectionCard>

              <SectionCard title="Approval Workflow">
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 bg-neutral-50 rounded-lg border border-neutral-100">
                    <Users size={14} className="text-neutral-400"/>
                    <div className="flex-1">
                      <p className="text-[12px] font-semibold text-neutral-800">Required Approvers</p>
                      <p className="text-[11px] text-neutral-500">Finance Team · Formula Governance Admin</p>
                    </div>
                    <button className="text-[11px] text-blue-600 hover:underline">Edit</button>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-neutral-50 rounded-lg border border-neutral-100">
                    <Tag size={14} className="text-neutral-400"/>
                    <div className="flex-1">
                      <p className="text-[12px] font-semibold text-neutral-800">Scope</p>
                      <p className="text-[11px] text-neutral-500">Tenant: Acme Corp · Pack: Enterprise Security ROI</p>
                    </div>
                    <button className="text-[11px] text-blue-600 hover:underline">Edit</button>
                  </div>
                </div>
              </SectionCard>
            </div>
          )}

          {/* Dependencies tab */}
          {activeTab === "Dependencies" && (
            <SectionCard title="Used By">
              <div className="space-y-2">
                {DEPENDENTS.map((d, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 bg-neutral-50 rounded-lg border border-neutral-100">
                    <Link2 size={13} className="text-neutral-400 shrink-0"/>
                    <div className="flex-1">
                      <p className="text-[12px] font-semibold text-neutral-800">{d.name}</p>
                      <p className="text-[10px] text-neutral-400">{d.type} · {d.pack}</p>
                    </div>
                    <ChevronRight size={13} className="text-neutral-300"/>
                  </div>
                ))}
              </div>
              <p className="text-[11px] text-neutral-400 mt-3">
                Activating or deprecating this formula will affect {DEPENDENTS.length} downstream assets.
              </p>
            </SectionCard>
          )}
        </div>

        {/* ── Right panel ─────────────────────────────────────────────────── */}
        <div className="w-[220px] shrink-0 space-y-4">
          <SectionCard title="Available Variables">
            <div className="space-y-1.5">
              {VARIABLES.map(v => (
                <div key={v.name} className="flex items-center gap-2 p-2 bg-neutral-50 rounded border border-neutral-100 text-[11px] font-mono text-neutral-700 hover:bg-neutral-100 cursor-pointer transition-colors">
                  <span className="w-2 h-2 rounded-full bg-violet-400 shrink-0"/>
                  <span className="truncate">{v.name}</span>
                </div>
              ))}
            </div>
            <Btn variant="ghost" className="w-full mt-2 justify-center text-[11px]">
              <Plus size={11}/> Add Variable
            </Btn>
          </SectionCard>

          <SectionCard title="Industry Benchmarks">
            <div className="space-y-2 text-[11px] text-neutral-600">
              {[
                { label: "SaaS Average Churn",  value: "5–7% / year" },
                { label: "Enterprise ACV",       value: "$50K – $500K" },
                { label: "Retention Lift",       value: "15–25%" },
              ].map(b => (
                <div key={b.label} className="p-2 bg-neutral-50 rounded border border-neutral-100">
                  <div className="font-semibold text-neutral-700">{b.label}</div>
                  <div className="text-neutral-500">{b.value}</div>
                </div>
              ))}
            </div>
            <Btn variant="ghost" className="w-full mt-2 justify-center text-[11px]">Apply Benchmark</Btn>
          </SectionCard>

          <SectionCard title="Formula Metadata">
            <div className="space-y-2 text-[11px]">
              <div className="flex justify-between">
                <span className="text-neutral-400">Version</span>
                <span className="font-semibold text-neutral-700">v3 (draft)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-400">Created by</span>
                <span className="font-semibold text-neutral-700">J. Rivera</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-400">Last modified</span>
                <span className="font-semibold text-neutral-700">Today</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-400">Used in</span>
                <span className="font-semibold text-neutral-700">3 assets</span>
              </div>
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
