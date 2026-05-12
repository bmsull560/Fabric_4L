import { Shield, ShieldCheck, ShieldAlert, Lock } from "lucide-react";
import { useAccountGates } from "@/hooks/useGates";
import { Skeleton } from "@/components/ui/skeleton";

interface GateStatusBannerProps {
  accountId: string;
}

export function GateStatusBanner({ accountId }: GateStatusBannerProps) {
  const { data: gateSummary, isLoading, error } = useAccountGates(accountId);

  if (isLoading) {
    return (
      <div className="rounded-lg border border-border bg-card p-4 mb-4">
        <Skeleton className="h-5 w-48 mb-2" />
        <div className="flex gap-3">
          <Skeleton className="h-6 w-20" />
          <Skeleton className="h-6 w-20" />
          <Skeleton className="h-6 w-20" />
        </div>
      </div>
    );
  }

  if (error || !gateSummary) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 mb-4 text-red-700 text-sm">
        Unable to load gate status. Export and sharing may be unavailable.
      </div>
    );
  }

  const { all_passed, gates } = gateSummary;

  if (all_passed) {
    return (
      <div className="rounded-lg border border-green-200 bg-green-50 p-4 mb-4 flex items-center gap-3">
        <ShieldCheck className="h-5 w-5 text-green-600 shrink-0" />
        <div>
          <p className="text-sm font-medium text-green-800">All gates closed</p>
          <p className="text-xs text-green-600">This account is ready for export and CRM push.</p>
        </div>
      </div>
    );
  }

  const openGates = gates.filter((g) => g.status === "open");

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 mb-4">
      <div className="flex items-center gap-2 mb-2">
        <ShieldAlert className="h-5 w-5 text-amber-600 shrink-0" />
        <p className="text-sm font-medium text-amber-800">
          {openGates.length} gate{openGates.length > 1 ? "s" : ""} open — export blocked
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        {gates.map((gate) => {
          const isClosed = gate.status !== "open";
          return (
            <span
              key={gate.type}
              className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${
                isClosed
                  ? "bg-green-100 text-green-700"
                  : "bg-amber-100 text-amber-700"
              }`}
              title={gate.reason || undefined}
            >
              {isClosed ? (
                <ShieldCheck className="h-3 w-3" />
              ) : (
                <Lock className="h-3 w-3" />
              )}
              {gate.type}
            </span>
          );
        })}
      </div>
    </div>
  );
}
