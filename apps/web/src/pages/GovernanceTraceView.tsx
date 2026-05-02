import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Download, Loader2 } from "lucide-react";
import {
  PageHeader,
  Btn,
  Toolbar,
  SectionCard,
  DataTable,
} from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useL5MaturityLadder,
  useL5TruthAudit,
  useL5Truths,
} from "@/hooks/useL5Governance";

interface GovernanceTraceViewProps {
  breadcrumbSection: string;
  breadcrumbPage: string;
  title: string;
  emptyStateSubtitle: string;
}

function formatTimestamp(timestamp?: string): string {
  if (!timestamp) return "—";
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
  const truthIdFromUrl = searchParams.get("truthId") || searchParams.get("caseId");
  const statusFromUrl = searchParams.get("status") || undefined;
  const [selectedTruthId, setSelectedTruthId] = useState<string | null>(truthIdFromUrl);
  const [isStaleOnly, setIsStaleOnly] = useState<boolean>(false);

  const { data: truths, isLoading: isLoadingTruths, error: truthsError } = useL5Truths({
    status: statusFromUrl,
    is_stale: isStaleOnly ? true : undefined,
  });
  const { data: maturityLadder } = useL5MaturityLadder();
  const { data: auditEntries, isLoading: isLoadingAudit, error: auditError } = useL5TruthAudit(selectedTruthId);

  const selectedTruth = useMemo(
    () => truths?.items.find(item => item.truth_id === selectedTruthId),
    [truths?.items, selectedTruthId]
  );

  const maturityByLevel = useMemo(() => {
    return new Map((maturityLadder || []).map(level => [level.level, level.name]));
  }, [maturityLadder]);

  const truthRows = (truths?.items || []).map(item => [
    <button
      key="truth-id"
      onClick={() => setSelectedTruthId(item.truth_id)}
      className={`font-mono text-[11px] ${
        selectedTruthId === item.truth_id
          ? "text-blue-700 font-bold"
          : "text-neutral-600 hover:text-blue-600"
      }`}
    >
      {item.truth_id.slice(0, 12)}
    </button>,
    <span key="claim" className="text-neutral-700">
      {item.claim_type || "unknown"}
    </span>,
    <span key="status" className="text-neutral-700">
      {item.status}
    </span>,
    <span key="maturity" className="text-neutral-700">
      {typeof item.maturity_level === "number"
        ? `${item.maturity_level} · ${maturityByLevel.get(item.maturity_level) || "Level"}`
        : "—"}
    </span>,
    <span key="freshness" className="text-neutral-700">
      {item.freshness || (item.is_stale ? "stale" : "fresh")}
    </span>,
    <span key="updated" className="text-neutral-500 text-[11px] font-mono">
      {formatTimestamp(item.updated_at)}
    </span>,
    <div key="actions" className="flex gap-2">
      <button
        onClick={() => setSelectedTruthId(item.truth_id)}
        className="text-blue-600 text-[11px] hover:underline"
      >
        View
      </button>
    </div>,
  ]);

  const auditRows = (auditEntries || []).map(entry => [
    <span key="audit-id" className="font-mono text-[11px] text-neutral-600">
      {entry.id.slice(0, 12)}
    </span>,
    <span key="action" className="text-neutral-700">{entry.action}</span>,
    <span key="actor" className="text-neutral-500">{entry.actor || "system"}</span>,
    <span key="timestamp" className="text-neutral-500 text-[11px] font-mono">
      {formatTimestamp(entry.timestamp)}
    </span>,
  ]);

  const isLoading = isLoadingTruths || (selectedTruthId && isLoadingAudit);

  if (isLoading) {
    return (
      <div className="p-6 max-w-5xl">
        <div className="mb-5">
          <Skeleton className="h-4 w-48 mb-2" />
          <Skeleton className="h-8 w-48 mb-1" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Toolbar>
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-8 w-28" />
        </Toolbar>
        <div className="flex gap-5">
          <div className="flex-1">
            <SectionCard title="Truth Objects" noPad>
              <div className="p-4">
                <Skeleton className="h-3 w-full" />
              </div>
            </SectionCard>
          </div>
          <div className="w-[260px] shrink-0">
            <SectionCard title="Truth Audit">
              <Skeleton className="h-3 w-32" />
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
        subtitle={selectedTruth ? `Truth: ${selectedTruth.truth_id}` : emptyStateSubtitle}
        actions={
          <Btn variant="ghost" disabled>
            <Download size={12} />
            Export PROV-O
          </Btn>
        }
      />

      <Toolbar>
        <Btn variant="ghost" onClick={() => setIsStaleOnly(current => !current)}>
          {isStaleOnly ? "Filter: Stale Only" : "Filter: All Truths"}
        </Btn>
        <Btn variant="ghost" disabled>
          {selectedTruthId ? <Loader2 size={12} className="opacity-0" /> : null}
          Status: {statusFromUrl || "all"}
        </Btn>
        {selectedTruthId && (
          <Btn variant="outline" onClick={() => setSelectedTruthId(null)}>
            Clear Selection
          </Btn>
        )}
      </Toolbar>

      <div className="flex gap-5">
        <div className="flex-1">
          <SectionCard title={`Truth Objects (${truths?.total || 0})`} noPad>
            {truthsError ? (
              <div className="p-4 text-sm text-red-600">Failed to load truth objects.</div>
            ) : (
              <DataTable
                columns={["Truth ID", "Claim Type", "Status", "Maturity", "Freshness", "Updated", "Actions"]}
                rows={truthRows}
                emptyMessage="No truth objects found"
              />
            )}
          </SectionCard>
        </div>

        <div className="w-[260px] shrink-0">
          <SectionCard title="Truth Audit" noPad>
            {!selectedTruthId ? (
              <div className="text-center py-8 px-4 text-[12px] text-neutral-500">
                Select a truth object to view audit events
              </div>
            ) : auditError ? (
              <div className="p-4 text-sm text-red-600">Failed to load truth audit.</div>
            ) : (
              <DataTable
                columns={["Event ID", "Action", "Actor", "Timestamp"]}
                rows={auditRows}
                emptyMessage="No audit entries found"
              />
            )}
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
