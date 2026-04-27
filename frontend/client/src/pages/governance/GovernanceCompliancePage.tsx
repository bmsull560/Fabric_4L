import { useGovernanceFreshnessSummary, useGovernanceMaturityLadder } from '@/hooks/useGovernanceL5';

export default function GovernanceCompliancePage() {
  const ladder = useGovernanceMaturityLadder();
  const freshness = useGovernanceFreshnessSummary();

  if (ladder.isLoading || freshness.isLoading) return <div>Loading compliance…</div>;
  if (ladder.isError || freshness.isError) return <div>Failed to load compliance data</div>;

  return (
    <section>
      <h1>Governance Compliance</h1>
      <h2>Maturity Ladder</h2>
      <ul>
        {(ladder.data ?? []).map((level) => (
          <li key={level.level}>{level.level}</li>
        ))}
      </ul>
      <h2>Freshness Summary</h2>
      <pre>{JSON.stringify(freshness.data ?? {}, null, 2)}</pre>
    </section>
  );
}
