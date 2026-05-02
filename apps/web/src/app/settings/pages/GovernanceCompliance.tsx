export function GovernanceCompliance() {
  const frameworks = [
    { name: "SOC 2 Type II", status: "Compliant", expiry: "Mar 15, 2026" },
    { name: "GDPR", status: "Compliant", expiry: "—" },
    { name: "HIPAA", status: "In progress", expiry: "—" },
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Compliance Frameworks</h3>
        <div className="mt-4 space-y-2">
          {frameworks.map((f) => (
            <div key={f.name} className="flex items-center justify-between rounded-md border p-3">
              <div>
                <p className="text-sm font-medium">{f.name}</p>
                <p className="text-xs text-muted-foreground">Expiry {f.expiry}</p>
              </div>
              <span className={f.status === "Compliant" ? "inline-flex rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary" : "inline-flex rounded-full bg-yellow-100 px-2 py-0.5 text-[10px] font-medium text-yellow-700 dark:bg-yellow-950 dark:text-yellow-300"}>
                {f.status}
              </span>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Data Residency</h3>
        <p className="text-xs text-muted-foreground">Control where tenant data is stored and processed.</p>
        <div className="mt-4 max-w-sm">
          <select className="h-9 w-full rounded-md border bg-background px-3 text-sm">
            <option>US-East (Virginia)</option>
            <option>EU-West (Ireland)</option>
            <option>APAC (Singapore)</option>
          </select>
        </div>
      </section>
    </div>
  );
}
