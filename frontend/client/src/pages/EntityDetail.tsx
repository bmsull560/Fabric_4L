/**
 * Screen 4 — Entity Detail (Right Drawer)
 * Design: Refined Enterprise SaaS
 */
import { useState } from "react";
import { X, Zap } from "lucide-react";
import { EntityBadge, DataTable, Toolbar, SearchInput, Btn, SectionCard, Tabs } from "@/components/WfPrimitives";
import type { EntityType } from "@/components/WfPrimitives";

const ENTITIES = [
  { name: "Predictive Analytics",  type: "capability" as EntityType,  domain: "acmecorp.com",        conf: 94, status: "Validated" },
  { name: "Customer 360 View",     type: "usecase" as EntityType,     domain: "acmecorp.com",        conf: 89, status: "Validated" },
  { name: "Sales Director",        type: "persona" as EntityType,     domain: "globex.io",           conf: 97, status: "Validated" },
  { name: "Revenue Retention",     type: "valuedriver" as EntityType, domain: "massive-dynamic.com", conf: 91, status: "Validated" },
  { name: "Single Sign-On",        type: "capability" as EntityType,  domain: "initech.com",         conf: 94, status: "Pending" },
  { name: "Churn Reduction",       type: "usecase" as EntityType,     domain: "acmecorp.com",        conf: 88, status: "Validated" },
];

const CONF_COLORS = (c: number) =>
  c >= 90 ? "text-emerald-700 font-semibold" : c >= 80 ? "text-amber-700" : "text-red-600";

export default function EntityDetail() {
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [drawerTab, setDrawerTab] = useState("Details");

  return (
    <div className="p-6 max-w-5xl relative">
      <div className="mb-4 text-[11px] text-neutral-400 flex items-center gap-1">
        <span>Ontology</span><span>›</span><span>Entity Browser</span>
      </div>
      <h1 className="text-[20px] font-extrabold text-neutral-900 mb-4">Entity Browser</h1>

      <Toolbar>
        <SearchInput placeholder="Search entities…"/>
        <Btn variant="ghost">Type: All ▾</Btn>
        <Btn variant="ghost">Domain: All ▾</Btn>
      </Toolbar>

      {/* Dimmed table */}
      <div className={`transition-opacity ${drawerOpen ? "opacity-40 pointer-events-none" : ""}`}>
        <SectionCard noPad>
          <DataTable
            columns={["Entity Name", "Type", "Domain", "Confidence", "Status", "Actions"]}
            rows={ENTITIES.map(e => [
              <span className="font-semibold text-neutral-800">{e.name}</span>,
              <EntityBadge type={e.type}/>,
              <span className="text-neutral-500 text-[11px] font-mono">{e.domain}</span>,
              <span className={`text-[12px] ${CONF_COLORS(e.conf)}`}>{e.conf}%</span>,
              <span className={`text-[11px] font-semibold ${e.status === "Validated" ? "text-emerald-700" : "text-amber-600"}`}>
                {e.status === "Validated" ? "● Validated" : "○ Pending"}
              </span>,
              <div className="flex gap-2">
                <button onClick={() => setDrawerOpen(true)} className="text-blue-600 text-[11px] hover:underline">View</button>
                <a href="#" className="text-neutral-400 text-[11px] hover:underline">Edit</a>
              </div>,
            ])}
          />
        </SectionCard>
      </div>

      {/* Right Drawer */}
      {drawerOpen && (
        <div className="absolute top-0 right-0 w-[360px] h-full bg-white border-l border-neutral-200 shadow-xl z-20 flex flex-col overflow-y-auto">
          {/* Drawer header */}
          <div className="flex items-start justify-between p-4 border-b border-neutral-100">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-violet-100 flex items-center justify-center">
                <Zap size={14} className="text-violet-600"/>
              </div>
              <div>
                <div className="text-[14px] font-bold text-neutral-900">Predictive Analytics</div>
                <EntityBadge type="capability"/>
              </div>
            </div>
            <button onClick={() => setDrawerOpen(false)} className="text-neutral-400 hover:text-neutral-700 transition-colors mt-0.5">
              <X size={16}/>
            </button>
          </div>

          {/* Status bar */}
          <div className="flex items-center gap-4 px-4 py-2 bg-neutral-50 border-b border-neutral-100 text-[11px]">
            <span className="text-neutral-500">Status: <span className="text-emerald-700 font-semibold">● Validated</span></span>
            <span className="text-neutral-500">Confidence: <span className="font-semibold text-neutral-800">94%</span></span>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-neutral-200 px-4">
            {["Details", "Relationships", "Source", "History"].map(tab => (
              <button
                key={tab}
                onClick={() => setDrawerTab(tab)}
                className={`px-3 py-2.5 text-[11px] font-semibold border-b-2 -mb-px transition-colors ${
                  drawerTab === tab ? "border-blue-600 text-blue-700" : "border-transparent text-neutral-500 hover:text-neutral-800"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Drawer content */}
          <div className="flex-1 p-4 space-y-4">
            {drawerTab === "Details" && (
              <>
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 mb-1">Description</div>
                  <p className="text-[12px] text-neutral-700 leading-relaxed">
                    AI-powered predictive analytics engine that forecasts equipment failures and optimizes maintenance schedules.
                  </p>
                </div>
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 mb-1">Category</div>
                  <div className="text-[12px] text-neutral-700">Analytics</div>
                </div>
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 mb-2">Technical Specs</div>
                  <ul className="space-y-1">
                    {[
                      "ML Models: Random Forest, LSTM",
                      "Data Sources: IoT sensors, ERP",
                      "Latency: <100ms prediction",
                    ].map(s => (
                      <li key={s} className="flex items-start gap-1.5 text-[12px] text-neutral-700">
                        <span className="text-neutral-300 mt-0.5">•</span>{s}
                      </li>
                    ))}
                  </ul>
                </div>
              </>
            )}
            {drawerTab === "Relationships" && (
              <div className="space-y-2">
                {[
                  { rel: "ENABLES →",    target: "Asset Lifecycle Mgmt",  color: "text-violet-600" },
                  { rel: "ENABLES →",    target: "Demand Forecasting",     color: "text-violet-600" },
                  { rel: "DEPENDS_ON →", target: "Real-Time Ingestion",    color: "text-cyan-600" },
                ].map(r => (
                  <div key={r.target} className="flex items-center gap-2 p-2.5 bg-neutral-50 rounded-md border border-neutral-100">
                    <span className="text-[10px] font-bold text-neutral-400 w-[80px] shrink-0">{r.rel}</span>
                    <span className={`text-[12px] font-semibold ${r.color}`}>{r.target}</span>
                  </div>
                ))}
              </div>
            )}
            {(drawerTab === "Source" || drawerTab === "History") && (
              <div className="text-[12px] text-neutral-500 italic">
                {drawerTab === "Source" ? "Source: acmecorp.com/product/analytics — crawled 09:41:14" : "Last modified: 2 mins ago by Extraction Engine v2.1"}
              </div>
            )}
          </div>

          {/* Drawer actions */}
          <div className="flex gap-2 p-4 border-t border-neutral-100">
            <Btn variant="ghost" className="text-[11px]">View Provenance</Btn>
            <Btn variant="primary" className="text-[11px]">Edit Entity</Btn>
            <Btn variant="danger" className="text-[11px]">Delete</Btn>
          </div>
        </div>
      )}

      {!drawerOpen && (
        <div className="mt-4">
          <Btn variant="outline" onClick={() => setDrawerOpen(true)}>Open Entity Detail Panel →</Btn>
        </div>
      )}
    </div>
  );
}
