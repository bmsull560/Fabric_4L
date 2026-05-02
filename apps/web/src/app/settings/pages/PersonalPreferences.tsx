export function PersonalPreferences() {
  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Appearance</h3>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div>
            <label className="text-xs font-medium">Theme</label>
            <select className="mt-1 h-9 w-full rounded-md border bg-background px-3 text-sm">
              <option>System</option>
              <option>Light</option>
              <option>Dark</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-medium">Density</label>
            <select className="mt-1 h-9 w-full rounded-md border bg-background px-3 text-sm">
              <option>Comfortable</option>
              <option>Compact</option>
            </select>
          </div>
        </div>
      </section>

      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Localization</h3>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div>
            <label className="text-xs font-medium">Language</label>
            <select className="mt-1 h-9 w-full rounded-md border bg-background px-3 text-sm">
              <option>English (US)</option>
              <option>English (UK)</option>
              <option>Spanish</option>
              <option>German</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-medium">Time zone</label>
            <select className="mt-1 h-9 w-full rounded-md border bg-background px-3 text-sm">
              <option>UTC</option>
              <option>America/New_York</option>
              <option>Europe/London</option>
              <option>Asia/Tokyo</option>
            </select>
          </div>
        </div>
      </section>

      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Default Views</h3>
        <p className="text-xs text-muted-foreground">Choose your landing page after sign-in.</p>
        <div className="mt-4 max-w-sm">
          <select className="h-9 w-full rounded-md border bg-background px-3 text-sm">
            <option>Home Dashboard</option>
            <option>Accounts</option>
            <option>Command Center</option>
          </select>
        </div>
      </section>
    </div>
  );
}
