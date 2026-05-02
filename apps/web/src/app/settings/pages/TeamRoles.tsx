export function TeamRoles() {
  const roles = [
    { name: "Owner", description: "Full tenant control including billing and deletion." },
    { name: "Admin", description: "Manage members, roles, data sources, and governance." },
    { name: "Editor", description: "Create and edit accounts, value models, and narratives." },
    { name: "Viewer", description: "Read-only access to workspaces and deliverables." },
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Role-Based Access Control</h3>
        <p className="text-xs text-muted-foreground">Map roles to capabilities and route access.</p>
        <div className="mt-4 space-y-2">
          {roles.map((r) => (
            <div key={r.name} className="flex items-start justify-between rounded-md border p-3">
              <div>
                <p className="text-sm font-medium">{r.name}</p>
                <p className="text-xs text-muted-foreground">{r.description}</p>
              </div>
              <button type="button" className="text-xs font-medium text-primary hover:underline">Edit permissions</button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
