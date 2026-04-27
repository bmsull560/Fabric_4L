import { useGovernanceTruths } from '@/hooks/useGovernanceL5';

export default function GovernanceEvidencePage() {
  const { data, isLoading, isError } = useGovernanceTruths({ limit: 25 });

  if (isLoading) return <div>Loading governance evidence…</div>;
  if (isError) return <div>Failed to load governance evidence</div>;

  return (
    <section>
      <h1>Governance Evidence</h1>
      {data?.items.length ? (
        <ul>
          {data.items.map((truth) => (
            <li key={truth.id}>{truth.claim}</li>
          ))}
        </ul>
      ) : (
        <p>No evidence records found.</p>
      )}
    </section>
  );
}
