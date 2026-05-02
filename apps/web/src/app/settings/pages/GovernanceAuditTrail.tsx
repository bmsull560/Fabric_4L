export function GovernanceAuditTrail() {
  const events = [
    { action: "Policy updated", actor: "sarah.chen@axiomrobotics.com", target: "Data Retention", timestamp: "Sep 12, 2025 14:32" },
    { action: "User invited", actor: "sarah.chen@axiomrobotics.com", target: "alex.m@partner.com", timestamp: "Sep 11, 2025 09:15" },
    { action: "API key created", actor: "james.w@axiomrobotics.com", target: "Staging key", timestamp: "Sep 10, 2025 16:45" },
    { action: "Formula approved", actor: "sarah.chen@axiomrobotics.com", target: "OEE Formula v3", timestamp: "Sep 9, 2025 11:20" },
    { action: "Workspace updated", actor: "sarah.chen@axiomrobotics.com", target: "Tenant settings", timestamp: "Sep 8, 2025 10:05" },
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Audit Trail</h3>
        <p className="text-xs text-muted-foreground">Immutable log of administrative actions across the tenant.</p>
        <div className="mt-4 overflow-hidden rounded-md border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Action</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Actor</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Target</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {events.map((e, i) => (
                <tr key={i}>
                  <td className="px-4 py-3 font-medium">{e.action}</td>
                  <td className="px-4 py-3 text-muted-foreground">{e.actor}</td>
                  <td className="px-4 py-3 text-muted-foreground">{e.target}</td>
                  <td className="px-4 py-3 text-muted-foreground">{e.timestamp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
