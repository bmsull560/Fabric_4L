export function TeamPermissions() {
  const permissions = [
    { resource: "Accounts", owner: true, admin: true, editor: true, viewer: true },
    { resource: "Value Models", owner: true, admin: true, editor: true, viewer: false },
    { resource: "Formulas", owner: true, admin: true, editor: false, viewer: false },
    { resource: "Billing", owner: true, admin: false, editor: false, viewer: false },
    { resource: "API Keys", owner: true, admin: true, editor: false, viewer: false },
    { resource: "Governance Policies", owner: true, admin: true, editor: false, viewer: false },
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Permission Matrix</h3>
        <p className="text-xs text-muted-foreground">Fine-grained control over what each role can access.</p>
        <div className="mt-4 overflow-hidden rounded-md border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Resource</th>
                <th className="px-4 py-2 text-center text-xs font-medium text-muted-foreground">Owner</th>
                <th className="px-4 py-2 text-center text-xs font-medium text-muted-foreground">Admin</th>
                <th className="px-4 py-2 text-center text-xs font-medium text-muted-foreground">Editor</th>
                <th className="px-4 py-2 text-center text-xs font-medium text-muted-foreground">Viewer</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {permissions.map((p) => (
                <tr key={p.resource}>
                  <td className="px-4 py-3 font-medium">{p.resource}</td>
                  <td className="px-4 py-3 text-center">{p.owner ? "✓" : "—"}</td>
                  <td className="px-4 py-3 text-center">{p.admin ? "✓" : "—"}</td>
                  <td className="px-4 py-3 text-center">{p.editor ? "✓" : "—"}</td>
                  <td className="px-4 py-3 text-center">{p.viewer ? "✓" : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
