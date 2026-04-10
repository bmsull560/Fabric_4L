/**
 * Screen 10 — Audit & Provenance: Decision Trace Viewer
 * Design: Refined Enterprise SaaS
 */
import { useState } from "react";
import { useSearchParams } from "wouter";
import { Shield, Download, CheckCircle2, Circle, Loader2 } from "lucide-react";
import { PageHeader, Btn, Toolbar, SectionCard, StatusBadge, DataTable } from "@/components/WfPrimitives";
import { useProvenanceTrail, useAuditLogs, useExportProvenance, type AuditLogEntry, type AuditLogFilter } from "@/hooks/useProvenance";

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function formatDate(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleDateString();
}

export default function DecisionTrace() {
  const [searchParams] = useSearchParams();
  const entityIdFromUrl = searchParams.get("entityId");
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(entityIdFromUrl);
  const [sourceFilter, setSourceFilter] = useState<AuditLogFilter['source']>("all");

  const { data: auditLogs, isLoading: isLoadingAudit } = useAuditLogs({ source: sourceFilter });
  const { data: provenanceTrail, isLoading: isLoadingProvenance } = useProvenanceTrail(selectedEntityId);
  const exportMutation = useExportProvenance();

  const isLoading = isLoadingAudit || (selectedEntityId && isLoadingProvenance);

  const handleExportProvO = async () => {
    if (!selectedEntityId) return;
    try {
      await exportMutation.mutateAsync({ entityId: selectedEntityId, format: 'prov-o' });
    } catch (error) {
      console.error("Export failed:", error);
    }
  };

  const handleViewEntity = (entityId: string) => {
    setSelectedEntityId(entityId);
  };

  const auditEntries: AuditLogEntry[] = auditLogs?.entries || [];

  // Convert audit entries to table rows
  const auditRows = auditEntries.map((entry) => [
    <button
      key="id"
      onClick={() => entry.entity_id && handleViewEntity(entry.entity_id)}
      className={`font-mono text-[11px] ${
        selectedEntityId === entry.entity_id
          ? "text-blue-700 font-bold"
          : "text-neutral-600 hover:text-blue-600"
      }`}
    >
      {entry.id.slice(0, 12)}
    </button>,
    <span key="entity" className="font-semibold text-neutral-800">
      {entry.entity_type || "System"}
    </span>,
    <span key="action" className="text-neutral-600">{entry.action}</span>,
    <span key="agent" className="text-neutral-500 text-[11px] font-mono">
      {entry.agent}
    </span>,
    <span key="ts" className="text-neutral-400 text-[11px] font-mono">
      {formatTimestamp(entry.timestamp)}
    </span>,
    <StatusBadge key="status" status={entry.event_type === 'error' ? 'failed' : 'completed'} />,
    <div key="actions" className="flex gap-2">
      {entry.entity_id && (
        <button
          onClick={() => handleViewEntity(entry.entity_id!)}
          className="text-blue-600 text-[11px] hover:underline"
        >
          View
        </button>
      )}
    </div>,
  ]);

  // Use provenance steps from API or fallback
  const provenanceSteps = provenanceTrail?.steps || [];

  if (isLoading) {
    return (
      <div className="p-6 max-w-5xl flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-blue-600" size={32} />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl">
      <PageHeader
        breadcrumbs={["Audit & Provenance", "Decision Traces"]}
        title="Decision Trace Viewer"
        subtitle={
          selectedEntityId && provenanceTrail
            ? `Provenance for: ${provenanceTrail.entity_name} (${provenanceTrail.entity_type})`
            : "Full provenance and audit trail for all entity decisions."
        }
        actions={
          <>
            <Btn
              variant="ghost"
              onClick={handleExportProvO}
              disabled={!selectedEntityId || exportMutation.isPending}
            >
              {exportMutation.isPending ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                <Download size={12} />
              )}
              Export PROV-O
            </Btn>
          </>
        }
      />

      <Toolbar>
        <Btn
          variant="ghost"
          onClick={() => setSourceFilter(sourceFilter === 'all' ? 'provenance' : 'all')}
        >
          Source: {sourceFilter === 'all' ? 'All ▾' : 'Provenance ▾'}
        </Btn>
        <Btn variant="ghost">Date Range ▾</Btn>
        <Btn variant="ghost">Status: All ▾</Btn>
        {selectedEntityId && (
          <Btn variant="outline" onClick={() => setSelectedEntityId(null)}>
            Clear Selection
          </Btn>
        )}
      </Toolbar>

      <div className="flex gap-5">
        {/* Trace list */}
        <div className="flex-1">
          <SectionCard title={`Audit Log (${auditLogs?.total || 0} entries)`} noPad>
            <DataTable
              columns={["Trace ID", "Entity", "Action", "Agent", "Timestamp", "Status", "Actions"]}
              rows={auditRows.length > 0 ? auditRows : [
                [<td key="empty" colSpan={7} className="text-center py-8 text-neutral-500">No audit entries found</td>]
              ]}
            />
          </SectionCard>
        </div>

        {/* Provenance panel */}
        <div className="w-[260px] shrink-0">
          <SectionCard
            title={selectedEntityId ? "Provenance Timeline" : "Select an Entity"}
          >
            {selectedEntityId ? (
              <>
                {provenanceTrail && (
                  <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                    <div className="text-[12px] font-semibold text-blue-900">
                      {provenanceTrail.entity_name}
                    </div>
                    <div className="text-[11px] text-blue-700">
                      Type: {provenanceTrail.entity_type}
                    </div>
                    <div className="text-[11px] text-blue-700">
                      Source: {provenanceTrail.source}
                    </div>
                    {provenanceTrail.confidence_score && (
                      <div className="text-[11px] text-blue-700">
                        Confidence: {(provenanceTrail.confidence_score * 100).toFixed(1)}%
                      </div>
                    )}
                  </div>
                )}

                <div className="space-y-0">
                  {provenanceSteps.map((s, i) => (
                    <div key={s.step} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
                          i < provenanceSteps.length ? "bg-emerald-100" : "bg-neutral-100"
                        }`}>
                          <CheckCircle2 size={14} className="text-emerald-600" />
                        </div>
                        {i < provenanceSteps.length - 1 && (
                          <div className="w-px flex-1 bg-neutral-200 my-1 min-h-[16px]"/>
                        )}
                      </div>
                      <div className="pb-4">
                        <div className="text-[12px] font-semibold text-neutral-800">{s.label}</div>
                        <div className="text-[11px] text-neutral-500 mt-0.5 leading-relaxed">
                          {s.detail}
                        </div>
                        {s.agent && (
                          <div className="text-[10px] text-neutral-400 mt-1">
                            by {s.agent}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex flex-col gap-2 mt-3 pt-3 border-t border-neutral-100">
                  <Btn variant="ghost" className="text-[11px] justify-center">
                    View Complete Provenance Graph
                  </Btn>
                  <Btn
                    variant="ghost"
                    className="text-[11px] justify-center"
                    onClick={handleExportProvO}
                    disabled={exportMutation.isPending}
                  >
                    {exportMutation.isPending ? (
                      <Loader2 size={10} className="animate-spin" />
                    ) : (
                      <Download size={10} />
                    )}
                    Export PROV-O
                  </Btn>
                  <Btn variant="outline" className="text-[11px] justify-center">
                    <Shield size={10}/> Verify Hash
                  </Btn>
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-neutral-500">
                <p className="text-[13px] mb-2">Select an entity from the audit log</p>
                <p className="text-[11px]">to view its provenance timeline</p>
              </div>
            )}
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
