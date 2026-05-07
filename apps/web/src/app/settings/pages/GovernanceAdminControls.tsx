import { Link } from "react-router-dom";
import { AlertTriangle, Shield, Workflow } from "lucide-react";
import { usePlatformSettings } from "@/hooks/usePlatformSettings";
import { useAuthContext } from "@/contexts/AuthContext";
import { CapabilityGate } from "../components/CapabilityGate";

export function GovernanceAdminControls() {
  const { data: settings, isLoading, error } = usePlatformSettings();
  const { user } = useAuthContext();
  const isSuperAdmin = user?.role === "super_admin";

  return (
    <CapabilityGate capability="governance">
      <div className="space-y-6">
        <section className="rounded-lg border bg-card p-5">
          <div className="flex items-start gap-3">
            <Shield className="mt-0.5 h-4 w-4 text-primary" />
            <div>
              <h3 className="text-sm font-semibold">Tenant Security Controls</h3>
              <p className="text-xs text-muted-foreground">
                Canonical security and notification controls are now managed through
                live tenant settings rather than shell-only toggles.
              </p>
            </div>
          </div>

          {isLoading ? (
            <div className="mt-4 rounded-md border p-4 text-sm text-muted-foreground">
              Loading current controls...
            </div>
          ) : error ? (
            <div className="mt-4 rounded-md border border-destructive/20 bg-destructive/5 p-4 text-sm text-destructive">
              {error.message}
            </div>
          ) : settings ? (
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-md border p-4">
                <p className="text-xs text-muted-foreground">Tenant status</p>
                <p className="mt-1 text-sm font-medium capitalize">
                  {settings.tenant_status ?? "active"}
                </p>
              </div>
              <div className="rounded-md border p-4">
                <p className="text-xs text-muted-foreground">MFA requirement</p>
                <p className="mt-1 text-sm font-medium">
                  {settings.security.require_2fa ? "Required" : "Optional"}
                </p>
              </div>
              <div className="rounded-md border p-4">
                <p className="text-xs text-muted-foreground">Session timeout</p>
                <p className="mt-1 text-sm font-medium">
                  {settings.security.session_timeout_minutes} minutes
                </p>
              </div>
              <div className="rounded-md border p-4">
                <p className="text-xs text-muted-foreground">Audit trail feature</p>
                <p className="mt-1 text-sm font-medium">
                  {settings.features.audit_trail ? "Enabled" : "Disabled"}
                </p>
              </div>
            </div>
          ) : null}

          <div className="mt-4 flex flex-wrap gap-2">
            <Link
              to="/settings/workspace"
              className="inline-flex h-8 items-center rounded-md bg-primary px-3 text-xs font-medium text-primary-foreground hover:opacity-90"
            >
              Manage tenant settings
            </Link>
            <Link
              to="/settings/governance/health"
              className="inline-flex h-8 items-center gap-1 rounded-md border px-3 text-xs font-medium hover:bg-accent"
            >
              <Workflow className="h-3.5 w-3.5" />
              Review health
            </Link>
          </div>
        </section>

        <section className="rounded-lg border border-destructive/20 bg-destructive/5 p-5">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-4 w-4 text-destructive" />
            <div className="space-y-2">
              <div>
                <h3 className="text-sm font-semibold text-destructive">Privileged Operations</h3>
                <p className="text-xs text-muted-foreground">
                  Suspend, export, and delete flows remain super-admin operations and should
                  stay outside tenant-admin self-service screens.
                </p>
              </div>
              <p className="text-xs text-muted-foreground">
                {isSuperAdmin
                  ? "Your current role can use the super-admin tenant management surfaces for destructive platform actions."
                  : "Your current role does not include destructive tenant lifecycle permissions."}
              </p>
            </div>
          </div>
        </section>
      </div>
    </CapabilityGate>
  );
}
