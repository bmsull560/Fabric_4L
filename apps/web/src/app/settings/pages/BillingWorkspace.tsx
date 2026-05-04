export function BillingWorkspace() {
  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Workspace Management</h3>
        <p className="text-xs text-muted-foreground">Name, domain, account picker behavior, and workspace switching.</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div>
            <label className="text-xs font-medium">Workspace name</label>
            <input className="mt-1 h-9 w-full rounded-md border bg-background px-3 text-sm" placeholder="My Workspace" />
          </div>
          <div>
            <label className="text-xs font-medium">Verified domain</label>
            <input className="mt-1 h-9 w-full rounded-md border bg-background px-3 text-sm" placeholder="company.com" />
          </div>
          <div>
            <label className="text-xs font-medium">Default industry pack</label>
            <select className="mt-1 h-9 w-full rounded-md border bg-background px-3 text-sm">
              <option>Manufacturing</option>
              <option>Financial Services</option>
              <option>AI / Data Platform</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-medium">Tenant ID</label>
            <input readOnly className="mt-1 h-9 w-full rounded-md border bg-muted px-3 text-sm text-muted-foreground" value="ten_2v8x9a1k" />
          </div>
        </div>
      </section>
    </div>
  );
}
