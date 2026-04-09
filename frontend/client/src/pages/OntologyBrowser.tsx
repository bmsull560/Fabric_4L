/**
 * Screen 3 — Ontology Entity Browser
 * Design: Refined Enterprise SaaS
 */
import { useState } from "react";
import { Plus } from "lucide-react";
import {
  PageHeader, EntityBadge, DataTable, Toolbar, SearchInput, Btn, SectionCard, Tabs
} from "@/components/WfPrimitives";
import type { EntityType } from "@/components/WfPrimitives";

const ENTITIES = [
  { name: "Predictive Analytics",    type: "capability" as EntityType,  domain: "acmecorp.com",        conf: 94, status: "Validated" },
  { name: "Customer 360 View",       type: "usecase" as EntityType,     domain: "acmecorp.com",        conf: 89, status: "Validated" },
  { name: "Sales Director",          type: "persona" as EntityType,     domain: "globex.io",           conf: 97, status: "Validated" },
  { name: "Revenue Retention",       type: "valuedriver" as EntityType, domain: "massive-dynamic.com", conf: 91, status: "Validated" },
  { name: "Single Sign-On",          type: "capability" as EntityType,  domain: "initech.com",         conf: 94, status: "Pending" },
  { name: "Churn Reduction",         type: "usecase" as EntityType,     domain: "acmecorp.com",        conf: 88, status: "Validated" },
  { name: "RBAC",                    type: "capability" as EntityType,  domain: "initech.com",         conf: 97, status: "Validated" },
  { name: "Audit Logging",           type: "capability" as EntityType,  domain: "initech.com",         conf: 91, status: "Validated" },
  { name: "Compliance Automation",   type: "usecase" as EntityType,     domain: "initech.com",         conf: 85, status: "Pending" },
  { name: "Cost Savings",            type: "valuedriver" as EntityType, domain: "massive-dynamic.com", conf: 92, status: "Validated" },
];

const CONF_COLORS = (c: number) =>
  c >= 90 ? "text-emerald-700 font-semibold" : c >= 80 ? "text-amber-700" : "text-red-600";

export default function OntologyBrowser() {
  const [activeTab, setActiveTab] = useState("Entity Browser");

  return (
    <div className="p-6 max-w-5xl">
      <PageHeader
        breadcrumbs={["Ontology", "Entity Browser"]}
        title="Entity Browser"
        subtitle="Browse and manage extracted ontology entities across all domains."
        actions={<Btn variant="primary"><Plus size={12}/> New Entity</Btn>}
      />

      <Tabs
        tabs={["Entity Browser", "Extraction Jobs", "Reference Models", "Validation"]}
        active={activeTab}
        onChange={setActiveTab}
      />

      {/* Filter toolbar */}
      <Toolbar>
        <SearchInput placeholder="Search entities…"/>
        <Btn variant="ghost">Type: All ▾</Btn>
        <Btn variant="ghost">Domain: All ▾</Btn>
        <Btn variant="ghost">Confidence ▾</Btn>
      </Toolbar>

      {/* Type legend chips */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {(["capability","usecase","persona","valuedriver"] as EntityType[]).map(t => (
          <EntityBadge key={t} type={t}/>
        ))}
      </div>

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
              <a href="#" className="text-blue-600 text-[11px] hover:underline">View</a>
              <a href="#" className="text-neutral-400 text-[11px] hover:underline">Edit</a>
            </div>,
          ])}
        />
      </SectionCard>
    </div>
  );
}
