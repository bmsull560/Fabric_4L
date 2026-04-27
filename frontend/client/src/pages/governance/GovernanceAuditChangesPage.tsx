import { useGovernanceAuditChanges } from '@/hooks/useGovernanceL5';

export default function GovernanceAuditChangesPage() {
  const { data, isLoading, isError } = useGovernanceAuditChanges();

  if (isLoading) return <div>Loading audit changes…</div>;
  if (isError) return <div>Failed to load audit changes</div>;

  return (
    <section>
      <h1>Governance Audit Changes</h1>
      <ul>
        {(data ?? []).map((event) => (
          <li key={event.id}>{event.action}</li>
        ))}
      </ul>
    </section>
  );
}
