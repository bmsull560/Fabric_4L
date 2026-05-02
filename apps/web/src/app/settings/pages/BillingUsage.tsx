export function BillingUsage() {
  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Usage Dashboard</h3>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {[
            { label: "API calls", used: "42,301", total: "100,000" },
            { label: "LLM tokens", used: "1.2M", total: "2M" },
            { label: "Ingestion jobs", used: "312", total: "500" },
          ].map((u) => (
            <div key={u.label} className="rounded-md border p-4">
              <p className="text-xs text-muted-foreground">{u.label}</p>
              <p className="mt-1 text-lg font-semibold">{u.used}</p>
              <p className="text-xs text-muted-foreground">of {u.total}</p>
              <div className="mt-2 h-1.5 w-full rounded-full bg-muted">
                <div
                  className="h-1.5 rounded-full bg-primary"
                  style={{ width: `${(parseInt(u.used.replace(/[^0-9]/g, "")) / parseInt(u.total.replace(/[^0-9]/g, ""))) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
