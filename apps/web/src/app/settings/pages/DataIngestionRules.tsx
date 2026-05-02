export function DataIngestionRules() {
  const rules = [
    { name: "Weekly CRM sync", source: "Salesforce", schedule: "Every Monday 09:00", status: "Active" },
    { name: "ERP cost pull", source: "SAP", schedule: "Daily 06:00", status: "Active" },
    { name: "Document crawler", source: "Google Drive", schedule: "On demand", status: "Paused" },
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Ingestion Rules</h3>
        <p className="text-xs text-muted-foreground">Automated and scheduled data ingestion pipelines.</p>
        <div className="mt-4 overflow-hidden rounded-md border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Rule</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Source</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Schedule</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Status</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {rules.map((r) => (
                <tr key={r.name}>
                  <td className="px-4 py-3 font-medium">{r.name}</td>
                  <td className="px-4 py-3 text-muted-foreground">{r.source}</td>
                  <td className="px-4 py-3 text-muted-foreground">{r.schedule}</td>
                  <td className="px-4 py-3">
                    <span className={r.status === "Active" ? "text-xs font-medium text-primary" : "text-xs font-medium text-muted-foreground"}>{r.status}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button type="button" className="text-xs font-medium text-primary hover:underline">Edit</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
