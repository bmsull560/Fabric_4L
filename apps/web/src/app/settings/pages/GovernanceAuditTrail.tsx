import { Link } from "react-router-dom";
import { AlertCircle, ExternalLink } from "lucide-react";
import { useOperationalAudit } from "@/hooks/useOperationalAudit";
import { CapabilityGate } from "../components/CapabilityGate";

export function GovernanceAuditTrail() {
  const { data, isLoading, error } = useOperationalAudit({ perPage: 25 });

  return (
    <CapabilityGate capability="governance">
      <div className="space-y-6">
        <section className="rounded-lg border bg-card p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-sm font-semibold">Operational Audit Events</h3>
              <p className="text-xs text-muted-foreground">
                Tenant-scoped administrative actions from Layer 4. Decision provenance
                remains available in the dedicated trace workflow.
              </p>
            </div>
            <Link
              to="/governance/traces"
              className="inline-flex h-8 items-center gap-1 rounded-md border px-3 text-xs font-medium hover:bg-accent"
            >
              Decision trace
              <ExternalLink className="h-3.5 w-3.5" />
            </Link>
          </div>

          {isLoading ? (
            <div className="mt-4 rounded-md border p-4 text-sm text-muted-foreground">
              Loading audit events...
            </div>
          ) : error ? (
            <div className="mt-4 rounded-md border border-destructive/20 bg-destructive/5 p-4">
              <div className="flex items-start gap-2 text-destructive">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <div>
                  <p className="text-sm font-medium">Failed to load audit events</p>
                  <p className="text-xs text-muted-foreground">
                    {error.message}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="mt-4 overflow-hidden rounded-md border">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Action</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Actor</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Resource</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {data?.entries.length ? data.entries.map((entry) => (
                    <tr key={entry.id}>
                      <td className="px-4 py-3 font-medium">{entry.action}</td>
                      <td className="px-4 py-3 text-muted-foreground">{entry.agent}</td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {entry.entity_type ?? "resource"}{entry.entity_id ? `:${entry.entity_id}` : ""}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {new Date(entry.timestamp).toLocaleString()}
                      </td>
                    </tr>
                  )) : (
                    <tr>
                      <td colSpan={4} className="px-4 py-6 text-center text-sm text-muted-foreground">
                        No operational audit events found for this tenant.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </CapabilityGate>
  );
}
