import { useAuthContext } from "@/contexts/AuthContext";
import { useUsage } from "@/hooks/useUsage";
import { CapabilityGate } from "../components/CapabilityGate";

export function BillingUsage() {
  const { user } = useAuthContext();
  const customerId = user?.tenantId ?? "";
  const { metrics, isLoading, error } = useUsage(customerId);

  return (
    <CapabilityGate capability="billing">
      <div className="space-y-6">
        <section className="rounded-lg border bg-card p-5">
          <h3 className="text-sm font-semibold">Usage Dashboard</h3>
          <p className="text-xs text-muted-foreground">Metered usage and plan limits from the billing backend.</p>
          {isLoading ? (
            <div className="mt-4 rounded-md border p-4 text-sm text-muted-foreground">Loading usage...</div>
          ) : error ? (
            <div className="mt-4 rounded-md border border-destructive/20 bg-destructive/5 p-4 text-sm text-destructive">
              {String(error)}
            </div>
          ) : (
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {metrics.length ? metrics.map((metric) => (
                <div key={metric.metric} className="rounded-md border p-4">
                  <p className="text-xs text-muted-foreground">{metric.metric}</p>
                  <p className="mt-1 text-lg font-semibold">{metric.total_quantity.toLocaleString()}</p>
                  <p className="text-xs text-muted-foreground">
                    of {metric.limit.toLocaleString()} {metric.unit}
                  </p>
                  <div className="mt-2 h-1.5 w-full rounded-full bg-muted">
                    <div
                      className="h-1.5 rounded-full bg-primary"
                      style={{ width: `${Math.min(metric.percentage, 100)}%` }}
                    />
                  </div>
                </div>
              )) : (
                <div className="rounded-md border p-4 text-sm text-muted-foreground">
                  No usage metrics are available for this tenant.
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </CapabilityGate>
  );
}
