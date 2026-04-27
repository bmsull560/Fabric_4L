/**
 * Screen 10 — Audit & Provenance: Decision Trace Viewer
 * Design: Refined Enterprise SaaS
 */
import { useEffect, useMemo, useState } from "react";
import { useLocation, useSearchParams } from "wouter";
import { Shield, Download, CheckCircle2, Loader2 } from "lucide-react";
import { PageHeader, Btn, Toolbar, SectionCard, StatusBadge, DataTable } from "@/components/WfPrimitives";
import { useProvenanceTrail, useAuditLogs, useExportProvenance, type AuditLogEntry, type AuditLogFilter } from "@/hooks/useProvenance";
import {
  useGroundTruths,
  useGroundTruthAuditTrail,
  useGroundTruthFreshnessSummary,
  useGroundTruthStaleTruths,
  useGroundTruthMaturityLadder,
} from "@/hooks/useGroundTruthGovernance";
import { useBusinessCase } from "@/hooks/useDocuments";

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export default function DecisionTrace() {
  const [location, setLocation] = useLocation();
  const [searchParams] = useSearchParams();
  const entityIdFromUrl = searchParams.get("entityId") || searchParams.get("caseId");
  const caseIdFromUrl = searchParams.get("caseId");
  const truthIdFromUrl = searchParams.get("truthId");
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(entityIdFromUrl);
  const [selectedTruthId, setSelectedTruthId] = useState<string | null>(null);
  const [sourceFilter, setSourceFilter] = useState<AuditLogFilter['source']>("all");
  const [truthStatusFilter, setTruthStatusFilter] = useState<string>('');
  const [staleOnly, setStaleOnly] = useState<boolean | undefined>(undefined);

  const isEvidencePage = location.startsWith('/governance/evidence');
  const isAuditPage = location.startsWith('/governance/audit');
  const isCompliancePage = location.startsWith('/governance/compliance');
  const isProvenancePage = !(isEvidencePage || isAuditPage || isCompliancePage);

  const truthFilters = useMemo(
    () => ({ status: truthStatusFilter || undefined, is_stale: staleOnly, limit: 50, offset: 0 }),
    [truthStatusFilter, staleOnly]
  );

  const { data: auditLogs, isLoading: isLoadingAudit } = useAuditLogs({ source: sourceFilter }, isProvenancePage);
  const { data: provenanceTrail, isLoading: isLoadingProvenance } = useProvenanceTrail(selectedEntityId, isProvenancePage);
  const exportMutation = useExportProvenance();
  const { data: governanceCase } = useBusinessCase(caseIdFromUrl);

  const { data: truths } = useGroundTruths(
    truthFilters,
    isEvidencePage || isAuditPage || isCompliancePage
  );
  const { data: truthAuditTrail } = useGroundTruthAuditTrail(selectedTruthId, isAuditPage);
  const { data: freshnessSummary, isLoading: isLoadingFreshness } = useGroundTruthFreshnessSummary(isCompliancePage);
  const { data: staleTruths } = useGroundTruthStaleTruths(25, 0, isCompliancePage);
  const { data: maturityLadder, isLoading: isLoadingMaturity } = useGroundTruthMaturityLadder(isCompliancePage);

  useEffect(() => {
    setSelectedEntityId(entityIdFromUrl);
  }, [entityIdFromUrl]);

  useEffect(() => {
    if (isAuditPage) {
      setSelectedTruthId(truthIdFromUrl);
    }
  }, [truthIdFromUrl, isAuditPage]);

  const handleExportProvO = async () => {
    if (!selectedEntityId) return;
    try {
      await exportMutation.mutateAsync({ entityId: selectedEntityId, format: 'prov-o' });
    } catch (error) {
      console.error("Export failed:", error);
    }
  };

  if (isEvidencePage) {
    const truthRows = (truths?.items || []).map((truth) => [
      <button
        key="id"
        onClick={() => setLocation(`/governance/audit/changes?truthId=${encodeURIComponent(truth.id)}`)}
        className="font-mono text-[11px] text-blue-700 hover:underline"
      >
        {truth.id.slice(0, 12)}
      </button>,
      <span key="claim" className="text-neutral-800">{truth.claim}</span>,
      <span key="type" className="text-neutral-600">{truth.claim_type}</span>,
      <span key="status" className="text-neutral-600">{truth.status}</span>,
      <span key="maturity" className="text-neutral-600">L{truth.maturity_level}</span>,
      <StatusBadge key="stale" status={truth.is_stale ? 'failed' : 'completed'} />, 
    ]);

    return (
      <div className="p-6 max-w-6xl">
        <PageHeader
          breadcrumbs={[{ label: "Governance" }, { label: "Evidence" }]}
          title="Truth Object Evidence"
          subtitle="Ground truth object listing and governance-focused filtering."
        />
        <Toolbar>
          <Btn variant="ghost" onClick={() => setStaleOnly(staleOnly == null ? true : undefined)}>
            {staleOnly ? 'Stale Only' : 'All Freshness'} ▾
          </Btn>
          <Btn variant="ghost" onClick={() => setTruthStatusFilter(truthStatusFilter ? '' : 'approved')}>
            {truthStatusFilter || 'All Status'} ▾
          </Btn>
        </Toolbar>
        <SectionCard title={`Truth Objects (${truths?.total || 0})`} noPad>
          <DataTable
            columns={["Truth ID", "Claim", "Type", "Status", "Maturity", "Freshness"]}
            rows={truthRows}
            emptyMessage="No truth objects found"
          />
        </SectionCard>
      </div>
    );
  }

  if (isAuditPage) {
    const truthRows = (truths?.items || []).map((truth) => [
      <button
        key="id"
        onClick={() => setSelectedTruthId(truth.id)}
        className={`font-mono text-[11px] ${selectedTruthId === truth.id ? 'text-blue-700 font-bold' : 'text-neutral-600 hover:text-blue-600'}`}
      >
        {truth.id.slice(0, 12)}
      </button>,
      <span key="claim" className="text-neutral-700">{truth.claim}</span>,
      <span key="status" className="text-neutral-600">{truth.status}</span>,
      <span key="maturity" className="text-neutral-600">L{truth.maturity_level}</span>,
    ]);

    const auditRows = (truthAuditTrail || []).map((event, idx) => [
      <span key="idx" className="font-mono text-[11px]">{idx + 1}</span>,
      <span key="action" className="text-neutral-700">{`${event.from_status ?? "—"} → ${event.to_status}`}</span>,
      <span key="from" className="text-neutral-600">{event.from_status || '—'}</span>,
      <span key="to" className="text-neutral-600">{event.to_status || '—'}</span>,
      <span key="actor" className="text-neutral-600">{event.actor || 'system'}</span>,
      <span key="ts" className="text-neutral-500 text-[11px]">{event.created_at ? formatTimestamp(event.created_at) : '—'}</span>,
    ]);

    return (
      <div className="p-6 max-w-6xl">
        <PageHeader
          breadcrumbs={[{ label: "Governance" }, { label: "Audit" }, { label: "Changes" }]}
          title="Truth Audit Log"
          subtitle="State transitions and validation events for TruthObjects."
        />
        <div className="grid grid-cols-2 gap-5">
          <SectionCard title="Truth Objects" noPad>
            <DataTable
              columns={["Truth ID", "Claim", "Status", "Maturity"]}
              rows={truthRows}
                emptyMessage="No truth objects found"
            />
          </SectionCard>
          <SectionCard title={`State Transitions (${truthAuditTrail?.length || 0})`} noPad>
            <DataTable
              columns={["#", "Action", "From", "To", "Actor", "Timestamp"]}
              rows={auditRows}
              emptyMessage={selectedTruthId ? 'No audit events found' : 'Select a truth object to view audit trail'}
            />
          </SectionCard>
        </div>
      </div>
    );
  }

  if (isCompliancePage) {
    const staleRows = (staleTruths?.items || []).map((truth) => [
      <span key="id" className="font-mono text-[11px]">{truth.id.slice(0, 12)}</span>,
      <span key="claim" className="text-neutral-700">{truth.claim}</span>,
      <span key="status" className="text-neutral-600">{truth.status}</span>,
      <span key="freshness" className="text-neutral-600">{truth.freshness ? String(truth.freshness) : '—'}</span>,
    ]);

    return (
      <div className="p-6 max-w-6xl">
        <PageHeader
          breadcrumbs={[{ label: "Governance" }, { label: "Compliance" }]}
          title="Compliance & Maturity Overview"
          subtitle="Freshness, staleness, and maturity ladder summaries for governance review."
        />

        <div className="grid grid-cols-3 gap-4 mb-5">
          <SectionCard title="Fresh">
            <div className="text-2xl font-semibold">{isLoadingFreshness ? '…' : (freshnessSummary?.fresh_count ?? 0)}</div>
          </SectionCard>
          <SectionCard title="Expiring Soon">
            <div className="text-2xl font-semibold">{isLoadingFreshness ? '…' : (freshnessSummary?.expiring_soon_count ?? 0)}</div>
          </SectionCard>
          <SectionCard title="Stale">
            <div className="text-2xl font-semibold text-amber-700">{isLoadingFreshness ? '…' : (freshnessSummary?.stale_count ?? 0)}</div>
          </SectionCard>
        </div>

        <div className="grid grid-cols-2 gap-5">
          <SectionCard title="Stale Truth Objects" noPad>
            <DataTable
              columns={["Truth ID", "Claim", "Status", "Freshness"]}
              rows={staleRows}
              emptyMessage="No stale truth objects"
            />
          </SectionCard>

          <SectionCard title="Maturity Ladder (0-5)">
            {isLoadingMaturity ? (
              <div className="text-sm text-neutral-500">Loading maturity ladder…</div>
            ) : (
              <div className="space-y-2">
                {(maturityLadder?.levels || []).map((level) => (
                  <div key={level.level} className="rounded-md border border-neutral-200 p-2">
                    <div className="text-sm font-semibold">Level {level.level}: {level.name}</div>
                    <div className="text-xs text-neutral-600">{level.description}</div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </div>
      </div>
    );
  }

  const isLoading = isLoadingAudit || Boolean(selectedEntityId && isLoadingProvenance);
  const auditEntries: AuditLogEntry[] = auditLogs?.entries || [];
  const auditRows = auditEntries.map((entry) => [
    <button
      key="id"
      onClick={() => entry.entity_id && setSelectedEntityId(entry.entity_id)}
      className={`font-mono text-[11px] ${selectedEntityId === entry.entity_id ? "text-blue-700 font-bold" : "text-neutral-600 hover:text-blue-600"}`}
    >
      {entry.id.slice(0, 12)}
    </button>,
    <span key="entity" className="font-semibold text-neutral-800">{entry.entity_type || "System"}</span>,
    <span key="action" className="text-neutral-600">{entry.action}</span>,
    <span key="agent" className="text-neutral-500 text-[11px] font-mono">{entry.agent}</span>,
    <span key="ts" className="text-neutral-400 text-[11px] font-mono">{formatTimestamp(entry.timestamp)}</span>,
    <StatusBadge key="status" status={entry.event_type === 'error' ? 'failed' : 'completed'} />,
    <div key="actions" className="flex gap-2">
      {entry.entity_id && (
        <button
          onClick={() => setSelectedEntityId(entry.entity_id)}
          className="text-blue-600 text-[11px] hover:underline"
        >
          View
        </button>
      )}
    </div>,
  ]);

  return (
    <div className="p-6 max-w-5xl">
      <PageHeader
        breadcrumbs={[{ label: "Audit & Provenance" }, { label: "Decision Traces" }]}
        title="Decision Trace Viewer"
        subtitle={
          selectedEntityId && provenanceTrail
            ? `Provenance for: ${provenanceTrail.entity_name} (${provenanceTrail.entity_type})`
            : "Full provenance and audit trail for entity decisions."
        }
        actions={
          <Btn variant="ghost" onClick={handleExportProvO} disabled={!selectedEntityId || exportMutation.isPending}>
            {exportMutation.isPending ? <Loader2 size={12} className="animate-spin" /> : <Download size={12} />}
            Export PROV-O
          </Btn>
        }
      />

      <Toolbar>
        <Btn variant="ghost" onClick={() => setSourceFilter(sourceFilter === 'all' ? 'provenance' : 'all')}>
          Source: {sourceFilter === 'all' ? 'All ▾' : 'Provenance ▾'}
        </Btn>
        {selectedEntityId && <Btn variant="outline" onClick={() => setSelectedEntityId(null)}>Clear Selection</Btn>}
      </Toolbar>

      {isLoading && (
        <div className="mb-3 text-xs text-neutral-500">Loading audit/provenance data…</div>
      )}

      {governanceCase?.truth_references && governanceCase.truth_references.length > 0 && (
        <SectionCard title="Truth References" className="mb-5">
          <div className="space-y-2">
            {governanceCase.truth_references.map((truthRef, idx) => {
              const ref = truthRef as Record<string, unknown>;
              return (
                <div key={`${String(ref.truth_object_id || idx)}`} className="rounded-md border border-neutral-200 p-3 text-[12px]">
                  <div className="font-semibold text-neutral-800">Requirement: {String(ref.requirement || ref.claim || "Truth reference")}</div>
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
          {governanceCase.remediation_items && governanceCase.remediation_items.length > 0 && (
            <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 p-3 text-[12px] text-amber-800">
              <div className="font-semibold mb-1">Remediation Required</div>
              <ul className="list-disc pl-5 space-y-1">
                {governanceCase.remediation_items.map((item, idx) => {
                  const rem = item as Record<string, unknown>;
                  return <li key={`${idx}-${String(rem.type || "rem")}`}>{String(rem.message || rem.requirement || "Action required")}</li>;
                })}
              </ul>
            </div>
          )}
        </SectionCard>
      )}

      <div className="flex gap-5">
        <div className="flex-1">
          <SectionCard title="Audit Log" noPad>
            <DataTable
              columns={["Trace ID", "Entity", "Action", "Agent", "Timestamp", "Status", "Actions"]}
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
                    <div className="text-[12px] font-semibold text-blue-900">{provenanceTrail.entity_name}</div>
                    <div className="text-[11px] text-blue-700">Type: {provenanceTrail.entity_type}</div>
                    <div className="text-[11px] text-blue-700">Source: {provenanceTrail.source}</div>
                  </div>
                )}
                <div className="space-y-0">
                  {(provenanceTrail?.steps || []).map((s, i, arr) => (
                    <div key={s.step} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <div className="w-6 h-6 rounded-full flex items-center justify-center shrink-0 bg-emerald-100">
                          <CheckCircle2 size={14} className="text-emerald-600" />
                        </div>
                        {i < arr.length - 1 && <div className="w-px flex-1 bg-neutral-200 my-1 min-h-[16px]" />}
                      </div>
                      <div className="pb-4">
                        <div className="text-[12px] font-semibold text-neutral-800">{s.label}</div>
                        <div className="text-[11px] text-neutral-500 mt-0.5 leading-relaxed">{s.detail}</div>
                      </div>
                    </div>
                  ))}
                </div>
                <Btn variant="outline" className="text-[11px] justify-center w-full mt-2">
                  <Shield size={10}/> Verify Hash
                </Btn>
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
