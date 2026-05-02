export function GovernanceHealth() {
  const checks = [
    { name: "Database connectivity", status: "Healthy", latency: "12ms" },
    { name: "API response time", status: "Healthy", latency: "45ms" },
    { name: "Ingestion queue depth", status: "Warning", latency: "1,240 jobs" },
    { name: "LLM provider latency", status: "Healthy", latency: "890ms" },
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">System Health</h3>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {checks.map((c) => (
            <div key={c.name} className="rounded-md border p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">{c.name}</p>
                <span className={c.status === "Healthy" ? "text-[10px] font-medium text-primary" : "text-[10px] font-medium text-yellow-600 dark:text-yellow-400"}>{c.status}</span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{c.latency}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Recent Incidents</h3>
        <div className="mt-4">
          <p className="text-sm text-muted-foreground">No incidents in the last 30 days.</p>
        </div>
      </section>
    </div>
  );
}
