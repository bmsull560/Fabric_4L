import { useMemo } from "react";
import { Loader2 } from "lucide-react";
import {
  PageHeader,
  MetricCard,
  SectionCard,
  DataTable,
} from "@/components/WfPrimitives";
import {
  useMaturityLadder,
  useStaleTruths,
  useTruthFreshnessSummary,
  useTruths,
} from "@/hooks/useGroundTruthGovernance";

export default function GovernanceCompliance() {
  const { data: freshnessSummary, isLoading: isLoadingFreshness } =
    useTruthFreshnessSummary();
  const { data: staleTruths, isLoading: isLoadingStale } = useStaleTruths({
    limit: 50,
  });
  const { data: maturityLadder, isLoading: isLoadingLadder } =
    useMaturityLadder();
  const { data: truths, isLoading: isLoadingTruths } = useTruths({
    limit: 200,
  });

  const maturityCounts = useMemo(() => {
    const counts: Record<number, number> = {};
    for (const truth of truths?.items ?? []) {
      counts[truth.maturity_level] = (counts[truth.maturity_level] ?? 0) + 1;
    }
    return counts;
  }, [truths?.items]);

  const isLoading =
    isLoadingFreshness || isLoadingStale || isLoadingLadder || isLoadingTruths;

  return (
    <div className="p-6 max-w-6xl">
      <PageHeader
        breadcrumbs={[{ label: "Governance" }, { label: "Compliance" }]}
        title="Compliance"
        subtitle="Maturity, freshness, and stale-truth summaries from Layer 5 governance endpoints."
      />

      {isLoading ? (
        <div className="flex items-center gap-2 text-[12px] text-neutral-500 mb-5">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading compliance
          summaries…
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-4 mb-5">
          <MetricCard
            label="Fresh truths"
            value={String(freshnessSummary?.fresh_count ?? 0)}
          />
          <MetricCard
            label="Stale truths"
            value={String(
              freshnessSummary?.stale_count ?? staleTruths?.items.length ?? 0
            )}
          />
          <MetricCard
            label="Expiring soon"
            value={String(freshnessSummary?.expiring_soon_count ?? 0)}
          />
          <MetricCard
            label="Total truths"
            value={String(truths?.total ?? freshnessSummary?.total_count ?? 0)}
          />
        </div>
      )}

      <div className="grid gap-5 lg:grid-cols-2">
        <SectionCard title="Maturity Ladder Coverage" noPad>
          <DataTable
            columns={["Level", "Name", "Required Status", "Count"]}
            rows={(maturityLadder?.levels ?? []).map(level => [
              <span key="level" className="font-semibold">
                L{level.level}
              </span>,
              <span key="name">{level.name}</span>,
              <span key="status">{level.required_status}</span>,
              <span key="count">{maturityCounts[level.level] ?? 0}</span>,
            ])}
            emptyMessage="No maturity ladder definition returned"
          />
        </SectionCard>

        <SectionCard
          title={`Stale Truth Objects (${staleTruths?.items.length ?? 0})`}
          noPad
        >
          <DataTable
            columns={["Truth ID", "Claim", "Status", "Maturity", "Freshness"]}
            rows={(staleTruths?.items ?? []).map(truth => [
              <span key="id" className="font-mono text-[11px]">
                {(truth.id ?? '').slice(0, 12)}
              </span>,
              <span key="claim" className="line-clamp-2">
                {truth.claim}
              </span>,
              <span key="status">{truth.status}</span>,
              <span key="maturity">L{truth.maturity_level}</span>,
              <span key="freshness" className="text-[11px] text-neutral-500">
                {truth.freshness ? new Date(truth.freshness).toLocaleDateString() : (truth.is_stale ? 'Stale' : 'Fresh')}
              </span>,
            ])}
            emptyMessage="No stale truths currently detected"
          />
        </SectionCard>
      </div>
    </div>
  );
}
