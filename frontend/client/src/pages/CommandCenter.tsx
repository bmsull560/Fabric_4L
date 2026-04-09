/**
 * Screen 1 — Ingestion Command Center
 * Design: Refined Enterprise SaaS
 */
import { Globe } from "lucide-react";
import { MetricCard, PageHeader, DataTable, StatusBadge, Btn } from "@/components/WfPrimitives";

const recentMaps = [
  { domain: "acmecorp.com",        entities: "1,402", status: "completed" as const, updated: "2 mins ago" },
  { domain: "globex.io",           entities: "845",   status: "completed" as const, updated: "1 hour ago" },
  { domain: "initech.com",         entities: "120",   status: "processing" as const, updated: "Just now" },
  { domain: "massive-dynamic.com", entities: "3,105", status: "completed" as const, updated: "Yesterday" },
  { domain: "soylent.co",          entities: "—",     status: "failed" as const,    updated: "2 days ago" },
];

export default function CommandCenter() {
  return (
    <div className="p-6 max-w-5xl">
      <PageHeader
        title="Ingestion Command Center"
        subtitle="Enter a new domain to synthesize or review historical extraction maps."
      />

      {/* Domain input */}
      <div className="flex items-center gap-3 bg-white border border-neutral-200 rounded-lg px-4 py-3 mb-6 shadow-sm">
        <Globe size={16} className="text-neutral-400 shrink-0"/>
        <input
          readOnly
          value=""
          placeholder="Enter domain to map (e.g., https://example.com)…"
          className="flex-1 text-[13px] text-neutral-500 bg-transparent outline-none placeholder:text-neutral-400"
        />
        <Btn variant="primary">Synthesize →</Btn>
      </div>

      {/* KPI row */}
      <div className="flex gap-4 mb-6">
        <MetricCard label="Total Processed Nodes"   value="14,208" trend="+12%" trendUp />
        <MetricCard label="Verified Relationships"  value="8,451"  trend="+5%"  trendUp />
        <MetricCard label="Total Accounts"          value="124"    trend="Active" />
      </div>

      {/* Recent maps table */}
      <div className="bg-white border border-neutral-200 rounded-lg shadow-sm">
        <div className="px-4 pt-4 pb-3 border-b border-neutral-100">
          <h2 className="text-[14px] font-bold text-neutral-800">Recent Maps</h2>
        </div>
        <DataTable
          columns={["Domain", "Entities Extracted", "Status", "Last Updated"]}
          rows={recentMaps.map(r => [
            <span className="flex items-center gap-2">
              <span className="text-neutral-300 text-[14px]">🏢</span>
              <span className="font-medium text-neutral-800">{r.domain}</span>
            </span>,
            <span className="text-neutral-600">{r.entities}</span>,
            <StatusBadge status={r.status}/>,
            <span className="text-neutral-400 text-[11px]">{r.updated}</span>,
          ])}
        />
      </div>
    </div>
  );
}
