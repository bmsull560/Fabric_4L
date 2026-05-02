export function DataSources() {
  const sources = [
    { name: "Salesforce CRM", type: "CRM", status: "Connected", lastSync: "10 min ago" },
    { name: "SAP ERP", type: "ERP", status: "Connected", lastSync: "1 hour ago" },
    { name: "Google Drive", type: "Storage", status: "Disconnected", lastSync: "—" },
    { name: "Layer 1 Web Ingestion", type: "Ingestion", status: "Connected", lastSync: "5 min ago" },
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold">Connection Hub</h3>
            <p className="text-xs text-muted-foreground">Data sources and external business systems.</p>
          </div>
          <button type="button" className="inline-flex h-8 items-center rounded-md bg-primary px-3 text-xs font-medium text-primary-foreground hover:opacity-90">Add source</button>
        </div>
        <div className="mt-4 space-y-2">
          {sources.map((s) => (
            <div key={s.name} className="flex items-center justify-between rounded-md border p-3">
              <div>
                <p className="text-sm font-medium">{s.name}</p>
                <p className="text-xs text-muted-foreground">{s.type} • Last sync {s.lastSync}</p>
              </div>
              <span className={s.status === "Connected" ? "text-xs font-medium text-primary" : "text-xs font-medium text-muted-foreground"}>{s.status}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
