/**
 * Screen 10 — Audit & Provenance: Decision Trace Viewer
 * Design: Refined Enterprise SaaS
 */
import { useState } from "react";
import { Shield, Download, CheckCircle2, Circle } from "lucide-react";
import { PageHeader, Btn, Toolbar, SectionCard, StatusBadge, DataTable } from "@/components/WfPrimitives";

const TRACES = [
  { id: "DT-4821", entity: "Predictive Analytics",    action: "Entity Validated",   agent: "ExtractionEngine-v2.1", ts: "09:41:14", status: "completed" as const },
  { id: "DT-4820", entity: "Churn Reduction",         action: "Relationship Mapped", agent: "SemanticMapper-v1.4",   ts: "09:41:16", status: "completed" as const },
  { id: "DT-4819", entity: "Revenue Enhancement",     action: "Value Driver Created",agent: "FabricAssembler-v3.0",  ts: "09:41:22", status: "completed" as const },
  { id: "DT-4818", entity: "Customer 360 View",       action: "Confidence Override",  agent: "Human: J. Doe",         ts: "09:38:05", status: "completed" as const },
  { id: "DT-4817", entity: "ERP Integration",         action: "Entity Flagged",      agent: "ValidationAgent-v1.2",  ts: "09:35:44", status: "failed" as const },
];

const PROVENANCE_STEPS = [
  { step: 1, label: "Domain Crawl",        detail: "4,209 pages parsed from acmecorp.com",                    done: true },
  { step: 2, label: "NER Extraction",      detail: "Node 102 identified: Capability → Predictive Analytics",  done: true },
  { step: 3, label: "Confidence Scoring",  detail: "RoBERTa model assigned confidence: 0.94",                 done: true },
  { step: 4, label: "Relationship Mapping",detail: "Linked to Use Case: Customer 360 View (Conf: 0.89)",      done: true },
  { step: 5, label: "Fabric Assembly",     detail: "Inserted into Value Tree: Revenue Enhancement",           done: true },
  { step: 6, label: "Human Validation",    detail: "Reviewed and approved by J. Doe at 09:38",                done: true },
];

export default function DecisionTrace() {
  const [selected, setSelected] = useState("DT-4821");

  return (
    <div className="p-6 max-w-5xl">
      <PageHeader
        breadcrumbs={["Audit & Provenance", "Decision Traces"]}
        title="Decision Trace Viewer"
        subtitle="Full provenance and audit trail for all entity decisions."
        actions={
          <>
            <Btn variant="ghost"><Download size={12}/> Export PROV-O</Btn>
          </>
        }
      />

      <Toolbar>
        <Btn variant="ghost">Entity: All ▾</Btn>
        <Btn variant="ghost">Date Range ▾</Btn>
        <Btn variant="ghost">Status: All ▾</Btn>
      </Toolbar>

      <div className="flex gap-5">
        {/* Trace list */}
        <div className="flex-1">
          <SectionCard title="Audit Log" noPad>
            <DataTable
              columns={["Trace ID", "Entity", "Action", "Agent", "Timestamp", "Status", "Actions"]}
              rows={TRACES.map(t => [
                <button
                  onClick={() => setSelected(t.id)}
                  className={`font-mono text-[11px] ${selected === t.id ? "text-blue-700 font-bold" : "text-neutral-600 hover:text-blue-600"}`}
                >
                  {t.id}
                </button>,
                <span className="font-semibold text-neutral-800">{t.entity}</span>,
                <span className="text-neutral-600">{t.action}</span>,
                <span className="text-neutral-500 text-[11px] font-mono">{t.agent}</span>,
                <span className="text-neutral-400 text-[11px] font-mono">{t.ts}</span>,
                <StatusBadge status={t.status}/>,
                <div className="flex gap-2">
                  <a href="#" className="text-blue-600 text-[11px] hover:underline">View</a>
                  <a href="#" className="text-neutral-400 text-[11px] hover:underline">Export</a>
                </div>,
              ])}
            />
          </SectionCard>
        </div>

        {/* Provenance panel */}
        <div className="w-[260px] shrink-0">
          <SectionCard title="Provenance Timeline">
            <div className="space-y-0">
              {PROVENANCE_STEPS.map((s, i) => (
                <div key={s.step} className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${s.done ? "bg-emerald-100" : "bg-neutral-100"}`}>
                      {s.done
                        ? <CheckCircle2 size={14} className="text-emerald-600"/>
                        : <Circle size={14} className="text-neutral-400"/>
                      }
                    </div>
                    {i < PROVENANCE_STEPS.length - 1 && (
                      <div className="w-px flex-1 bg-neutral-200 my-1 min-h-[16px]"/>
                    )}
                  </div>
                  <div className="pb-4">
                    <div className="text-[12px] font-semibold text-neutral-800">{s.label}</div>
                    <div className="text-[11px] text-neutral-500 mt-0.5 leading-relaxed">{s.detail}</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex flex-col gap-2 mt-3 pt-3 border-t border-neutral-100">
              <Btn variant="ghost" className="text-[11px] justify-center">View Complete Provenance Graph</Btn>
              <Btn variant="ghost" className="text-[11px] justify-center"><Download size={10}/> Export PROV-O</Btn>
              <Btn variant="outline" className="text-[11px] justify-center"><Shield size={10}/> Verify Hash</Btn>
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
