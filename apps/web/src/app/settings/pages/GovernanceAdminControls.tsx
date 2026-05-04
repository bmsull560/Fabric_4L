export function GovernanceAdminControls() {
  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Tenant Administration</h3>
        <p className="text-xs text-muted-foreground">High-sensitivity controls restricted to tenant owners.</p>
        <div className="mt-4 space-y-3">
          <div className="flex items-center justify-between rounded-md border p-3">
            <div>
              <p className="text-sm font-medium">Maintenance mode</p>
              <p className="text-xs text-muted-foreground">Temporarily disable non-essential features.</p>
            </div>
            <label className="relative inline-flex cursor-pointer items-center">
              <input type="checkbox" className="peer sr-only" />
              <div className="h-5 w-9 rounded-full bg-muted-foreground/30 transition-colors peer-checked:bg-primary" />
              <div className="absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white transition-transform peer-checked:translate-x-4" />
            </label>
          </div>

          <div className="flex items-center justify-between rounded-md border p-3">
            <div>
              <p className="text-sm font-medium">Require MFA for all users</p>
              <p className="text-xs text-muted-foreground">Enforce two-factor authentication tenant-wide.</p>
            </div>
            <label className="relative inline-flex cursor-pointer items-center">
              <input type="checkbox" className="peer sr-only" defaultChecked />
              <div className="h-5 w-9 rounded-full bg-muted-foreground/30 transition-colors peer-checked:bg-primary" />
              <div className="absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white transition-transform peer-checked:translate-x-4" />
            </label>
          </div>

          <div className="flex items-center justify-between rounded-md border p-3">
            <div>
              <p className="text-sm font-medium">Audit log retention</p>
              <p className="text-xs text-muted-foreground">Keep audit logs for 7 years (compliance requirement).</p>
            </div>
            <label className="relative inline-flex cursor-pointer items-center">
              <input type="checkbox" className="peer sr-only" defaultChecked />
              <div className="h-5 w-9 rounded-full bg-muted-foreground/30 transition-colors peer-checked:bg-primary" />
              <div className="absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white transition-transform peer-checked:translate-x-4" />
            </label>
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-destructive/20 bg-destructive/5 p-5">
        <h3 className="text-sm font-semibold text-destructive">Danger Zone</h3>
        <p className="text-xs text-muted-foreground">Destructive actions that cannot be undone.</p>
        <div className="mt-4 space-y-2">
          <div className="flex items-center justify-between rounded-md border p-3">
            <div>
              <p className="text-sm font-medium">Export all tenant data</p>
              <p className="text-xs text-muted-foreground">Download a full archive of your workspace data.</p>
            </div>
            <button type="button" className="inline-flex h-8 items-center rounded-md border px-3 text-xs font-medium hover:bg-accent">Export</button>
          </div>
          <div className="flex items-center justify-between rounded-md border p-3">
            <div>
              <p className="text-sm font-medium">Delete tenant</p>
              <p className="text-xs text-muted-foreground">Permanently delete this tenant and all associated data.</p>
            </div>
            <button type="button" className="inline-flex h-8 items-center rounded-md bg-destructive px-3 text-xs font-medium text-destructive-foreground hover:opacity-90">Delete</button>
          </div>
        </div>
      </section>
    </div>
  );
}
