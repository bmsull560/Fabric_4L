export function BillingSubscription() {
  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Current Plan</h3>
        <div className="mt-4 flex items-center justify-between rounded-md border p-4">
          <div>
            <p className="text-base font-semibold">Professional</p>
            <p className="text-xs text-muted-foreground">Billed monthly • Renews on Oct 12, 2025</p>
          </div>
          <button type="button" className="inline-flex h-8 items-center rounded-md border px-3 text-xs font-medium hover:bg-accent">Change plan</button>
        </div>
      </section>

      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Plan Features</h3>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {[
            { label: "Accounts", value: "Unlimited" },
            { label: "Team members", value: "25" },
            { label: "API calls", value: "100K / month" },
            { label: "Ingestion jobs", value: "500 / month" },
            { label: "Support", value: "Priority" },
            { label: "Custom packs", value: "Enabled" },
          ].map((f) => (
            <div key={f.label} className="rounded-md border p-3">
              <p className="text-xs text-muted-foreground">{f.label}</p>
              <p className="text-sm font-medium">{f.value}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
