export function TeamApiKeys() {
  const keys = [
    { name: "Production", prefix: "vf_live_••••8f3a", created: "Sep 1, 2025", lastUsed: "2 hours ago" },
    { name: "Staging", prefix: "vf_test_••••2b91", created: "Aug 15, 2025", lastUsed: "1 day ago" },
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold">Developer API Keys</h3>
            <p className="text-xs text-muted-foreground">Generate, rotate, and revoke programmatic access.</p>
          </div>
          <button type="button" className="inline-flex h-8 items-center rounded-md bg-primary px-3 text-xs font-medium text-primary-foreground hover:opacity-90">Create API key</button>
        </div>
        <div className="mt-4 space-y-2">
          {keys.map((k) => (
            <div key={k.name} className="flex items-center justify-between rounded-md border p-3">
              <div>
                <p className="text-sm font-medium">{k.name}</p>
                <p className="text-xs text-muted-foreground">{k.prefix} • Created {k.created} • Last used {k.lastUsed}</p>
              </div>
              <button type="button" className="text-xs font-medium text-destructive hover:underline">Revoke</button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
