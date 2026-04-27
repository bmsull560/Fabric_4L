import { useState } from "react";
import { useSearchParams } from "wouter";
import { Download, Loader2 } from "lucide-react";
import {
  PageHeader,
  Btn,
  Toolbar,
  SectionCard,
  StatusBadge,
  DataTable,
} from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useProvenanceTrail,
  useAuditLogs,
  useExportProvenance,
  type AuditLogEntry,
  type AuditLogFilter,
} from "@/hooks/useProvenance";
import { useBusinessCase } from "@/hooks/useDocuments";

interface GovernanceTraceViewProps {
  breadcrumbSection: string;
  breadcrumbPage: string;
  title: string;
  emptyStateSubtitle: string;
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function GovernanceTraceView({
  breadcrumbSection,
  breadcrumbPage,
  title,
  emptyStateSubtitle,
}: GovernanceTraceViewProps) {
  const [searchParams] = useSearchParams();
  const entityIdFromUrl = searchParams.get("entityId") || searchParams.get("caseId");
  const caseIdFromUrl = searchParams.get("caseId");
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(
    entityIdFromUrl
  );
  const [sourceFilter, setSourceFilter] = useState<AuditLogFilter["source"]>("all");

  const { data: auditLogs, isLoading: isLoadingAudit } = useAuditLogs({
    source: sourceFilter,
  });
  const { data: provenanceTrail, isLoading: isLoadingProvenance } =
    useProvenanceTrail(selectedEntityId);
  const exportMutation = useExportProvenance();
  const { data: governanceCase } = useBusinessCase(caseIdFromUrl);

  const isLoading = isLoadingAudit || (selectedEntityId && isLoadingProvenance);

  const handleExportProvO = async () => {
    if (!selectedEntityId) return;
    try {
      await exportMutation.mutateAsync({ entityId: selectedEntityId, format: "prov-o" });
    } catch (error) {
      console.error("Export failed:", error);
    }
  };

  const handleViewEntity = (entityId: string) => {
    setSelectedEntityId(entityId);
  };

  const auditEntries: AuditLogEntry[] = auditLogs?.entries || [];

  const auditRows = auditEntries.map(entry => [
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
    <span key="action" className="text-neutral-600">
      {entry.action}
    </span>,
    <span key="agent" className="text-neutral-500 text-[11px] font-mono">
      {entry.agent}
    </span>,
    <span key="ts" className="text-neutral-400 text-[11px] font-mono">
      {formatTimestamp(entry.timestamp)}
    </span>,
    <StatusBadge
      key="status"
      status={entry.event_type === "error" ? "failed" : "completed"}
    />,
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

  const provenanceSteps = provenanceTrail?.steps || [];

  if (isLoading) {
    return (
      <div className="p-6 max-w-5xl">
        <div className="mb-5">
          <Skeleton className="h-4 w-48 mb-2" />
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <Skeleton className="h-8 w-48 mb-1" />
              <Skeleton className="h-4 w-64" />
            </div>
            <Skeleton className="h-8 w-32" />
          </div>
        </div>

        <Toolbar>
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-8 w-28" />
          <Skeleton className="h-8 w-24" />
        </Toolbar>

        <div className="flex gap-5">
          <div className="flex-1">
            <SectionCard title="Audit Log" noPad>
              <div className="flex bg-neutral-50 border-b border-neutral-200 px-4 py-2.5">
                {["Trace ID", "Entity", "Action", "Agent", "Timestamp", "Status", "Actions"].map(
                  (_, i) => (
                    <Skeleton key={i} className="h-3 w-16 mr-4" />
                  )
                )}
              </div>
              <div className="divide-y divide-neutral-100">
                {[1, 2, 3, 4, 5].map(i => (
                  <div key={i} className="flex items-center px-4 py-3">
                    <Skeleton className="h-3 w-20 mr-4" />
                    <Skeleton className="h-3 w-16 mr-4" />
                    <Skeleton className="h-3 w-20 mr-4" />
                    <Skeleton className="h-3 w-24 mr-4" />
                    <Skeleton className="h-3 w-16 mr-4" />
                    <Skeleton className="h-5 w-16 mr-4 rounded-full" />
                    <Skeleton className="h-3 w-8" />
                  </div>
                ))}
              </div>
            </SectionCard>
          </div>

          <div className="w-[260px] shrink-0">
            <SectionCard title="Select an Entity">
              <div className="text-center py-8">
                <Skeleton className="h-4 w-40 mx-auto mb-2" />
                <Skeleton className="h-3 w-32 mx-auto" />
              </div>
            </SectionCard>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl">
      <PageHeader
        breadcrumbs={[{ label: breadcrumbSection }, { label: breadcrumbPage }]}
        title={title}
        subtitle={
          selectedEntityId && provenanceTrail
            ? `Provenance for: ${provenanceTrail.entity_name} (${provenanceTrail.entity_type})`
            : emptyStateSubtitle
        }
        actions={
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
        }
      />

      <Toolbar>
        <Btn
          variant="ghost"
          onClick={() =>
            setSourceFilter(sourceFilter === "all" ? "provenance" : "all")
          }
        >
          Source: {sourceFilter === "all" ? "All ▾" : "Provenance ▾"}
        </Btn>
        <Btn variant="ghost">Date Range ▾</Btn>
        <Btn variant="ghost">Status: All ▾</Btn>
        {selectedEntityId && (
          <Btn variant="outline" onClick={() => setSelectedEntityId(null)}>
            Clear Selection
          </Btn>
        )}
      </Toolbar>

      {governanceCase?.truth_references && governanceCase.truth_references.length > 0 && (
        <SectionCard title="Truth References" className="mb-5">
          <div className="space-y-2">
            {governanceCase.truth_references.map((truthRef, idx) => {
              const ref = truthRef as Record<string, unknown>;
              return (
                <div
                  key={`${String(ref.truth_object_id || idx)}`}
                  className="rounded-md border border-neutral-200 p-3 text-[12px]"
                >
                  <div className="font-semibold text-neutral-800">
                    Requirement: {String(ref.requirement || ref.claim || "Truth reference")}
                  </div>
                  <div className="text-neutral-600 mt-1">
                    ID: <span className="font-mono text-[11px]">{String(ref.truth_object_id || "n/a")}</span>
                  </div>
                  <div className="text-neutral-600">
                    Status: {String(ref.status || "unknown")} · Maturity: {String(ref.maturity_level || "n/a")}
                  </div>
                </div>
              );
            })}
          </div>
          {governanceCase.remediation_items &&
            governanceCase.remediation_items.length > 0 && (
              <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 p-3 text-[12px] text-amber-800">
                <div className="font-semibold mb-1">Remediation Required</div>
                <ul className="list-disc pl-5 space-y-1">
                  {governanceCase.remediation_items.map((item, idx) => {
                    const rem = item as Record<string, unknown>;
                    return (
                      <li key={`${idx}-${String(rem.type || "rem")}`}>
                        {String(rem.message || rem.requirement || "Action required")}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
        </SectionCard>
      )}

      <div className="flex gap-5">
        <div className="flex-1">
          <SectionCard title={`Audit Log (${auditLogs?.total || 0} entries)`} noPad>
            <DataTable
              columns={[
                "Trace ID",
                "Entity",
                "Action",
                "Agent",
                "Timestamp",
                "Status",
                "Actions",
              ]}
              rows={auditRows}
              emptyMessage="No audit entries found"
            />
          </SectionCard>
        </div>

        <div className="w-[260px] shrink-0">
          <SectionCard title={selectedEntityId ? "Provenance Timeline" : "Select an Entity"}>
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
                <div className="space-y-3">
                  {provenanceSteps.length > 0 ? (
                    provenanceSteps.map((step, idx) => (
                      <div key={idx} className="flex gap-3">
                        <div className="mt-1 w-2 h-2 rounded-full bg-blue-500 shrink-0" />
                        <div className="min-w-0 flex-1">
                          <div className="text-[12px] font-semibold text-neutral-900">
                            {step.step}
                          </div>
                          <div className="text-[11px] text-neutral-600 mt-0.5 leading-relaxed">
                            {step.detail}
                          </div>
                          <div className="text-[10px] text-neutral-400 mt-1 font-mono">
                            {new Date(step.timestamp).toLocaleString()}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-[12px] text-neutral-500">No provenance steps available</div>
                  )}
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-[12px] text-neutral-500">
                Select an entity from the audit log to view provenance timeline
              </div>
            )}
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
