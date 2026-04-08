/**
 * Screen 6 — Value Trees: Formula Builder
 * Design: Refined Enterprise SaaS
 */
import { useState } from "react";
import { Play, Save, X, Plus } from "lucide-react";
import { PageHeader, Btn, SectionCard, Tabs } from "@/components/WfPrimitives";

const VARIABLES = [
  "Current_Churn_Rate",
  "Average_Contract_Value",
  "Projected_Retention_Lift",
  "Implementation_Cost",
  "Customer_Count",
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

export default function FormulaBuilder() {
  const [activeTab, setActiveTab] = useState("Formulas");
  const [tested, setTested] = useState(false);

  return (
    <div className="p-6">
      <PageHeader
        breadcrumbs={["Value Trees", "Formulas", "New Formula"]}
        title="Formula Builder"
        subtitle="Create mathematical formulas for value driver calculations."
      />

      <Tabs
        tabs={["Tree Explorer", "Normalization", "Formulas"]}
        active={activeTab}
        onChange={setActiveTab}
      />

      <div className="flex gap-5 mt-2">
        {/* Left: formula definition */}
        <div className="flex-1 space-y-4">
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
              <div>
                <label className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 block mb-1">Associated Value Driver</label>
                <div className="border border-neutral-200 rounded-md px-3 py-2 text-[12px] text-neutral-700 bg-neutral-50 flex justify-between">
                  Revenue Retention <span className="text-neutral-400">▾</span>
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
              <div className="border-t border-neutral-100 pt-3 flex items-center gap-4">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">Result</span>
                  <div className="text-[20px] font-extrabold text-emerald-700">$900,000.00</div>
                </div>
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">ROI</span>
                  <div className="text-[20px] font-extrabold text-emerald-700">900%</div>
                </div>
              </div>
            </SectionCard>
          )}

          <div className="flex gap-2">
            <Btn variant="primary"><Save size={11}/> Save Formula</Btn>
            <Btn variant="ghost"><X size={11}/> Cancel</Btn>
          </div>
        </div>

        {/* Right: variables panel */}
        <div className="w-[220px] shrink-0 space-y-4">
          <SectionCard title="Available Variables">
            <div className="space-y-1.5">
              {VARIABLES.map(v => (
                <div key={v} className="flex items-center gap-2 p-2 bg-neutral-50 rounded border border-neutral-100 text-[11px] font-mono text-neutral-700 hover:bg-neutral-100 cursor-pointer transition-colors">
                  <span className="w-2 h-2 rounded-full bg-violet-400 shrink-0"/>
                  {v}
                </div>
              ))}
            </div>
            <Btn variant="ghost" className="w-full mt-2 justify-center text-[11px]">
              <Plus size={11}/> Add Custom Variable
            </Btn>
          </SectionCard>

          <SectionCard title="Industry Benchmarks">
            <div className="space-y-2 text-[11px] text-neutral-600">
              <div className="p-2 bg-neutral-50 rounded border border-neutral-100">
                <div className="font-semibold text-neutral-700">SaaS Average Churn</div>
                <div className="text-neutral-500">5–7% / year</div>
              </div>
              <div className="p-2 bg-neutral-50 rounded border border-neutral-100">
                <div className="font-semibold text-neutral-700">Enterprise ACV</div>
                <div className="text-neutral-500">$50K – $500K</div>
              </div>
              <div className="p-2 bg-neutral-50 rounded border border-neutral-100">
                <div className="font-semibold text-neutral-700">Retention Lift</div>
                <div className="text-neutral-500">15–25%</div>
              </div>
            </div>
            <Btn variant="ghost" className="w-full mt-2 justify-center text-[11px]">Apply Benchmark</Btn>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
