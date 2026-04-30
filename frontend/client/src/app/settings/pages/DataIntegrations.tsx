export function DataIntegrations() {
  const integrations = [
    { name: "Slack", description: "Send alerts and summaries to Slack channels.", status: "Connected" },
    { name: "Microsoft Teams", description: "Share value cases and notifications.", status: "Not connected" },
    { name: "Jira", description: "Create issues from value findings.", status: "Not connected" },
    { name: "HubSpot", description: "Sync account and contact data.", status: "Connected" },
  ];

  return (
    <div className="space-y-6">
      <section className="rounded-lg border bg-card p-5">
        <h3 className="text-sm font-semibold">Integrations</h3>
        <p className="text-xs text-muted-foreground">Connect external tools to automate workflows.</p>
        <div className="mt-4 space-y-2">
          {integrations.map((i) => (
            <div key={i.name} className="flex items-center justify-between rounded-md border p-3">
              <div>
                <p className="text-sm font-medium">{i.name}</p>
                <p className="text-xs text-muted-foreground">{i.description}</p>
              </div>
              <button
                type="button"
                className={i.status === "Connected"
                  ? "inline-flex h-7 items-center rounded-md border px-2 text-xs font-medium hover:bg-accent"
                  : "inline-flex h-7 items-center rounded-md bg-primary px-2 text-xs font-medium text-primary-foreground hover:opacity-90"
                }
              >
                {i.status === "Connected" ? "Manage" : "Connect"}
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
