import { useGovernanceAuditLog } from '@/hooks/useGovernanceL5';

export default function GovernanceAuditLogPage() {
  const { data, isLoading, isError } = useGovernanceAuditLog();

  if (isLoading) return <div>Loading audit log…</div>;
  if (isError) return <div>Failed to load audit log</div>;

  return (
    <section>
      <h1>Governance Audit Log</h1>
      <ul>
        {(data ?? []).map((event) => (
          <li key={event.id}>{event.action}</li>
        ))}
      </ul>
    </section>
  );
}
