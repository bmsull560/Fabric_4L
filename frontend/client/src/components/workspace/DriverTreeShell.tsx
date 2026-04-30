/**
 * DriverTreeShell — Workspace shell for Driver Tree
 *
 * Tabs: Evidence → Alternatives → Solution Cost
 */
import { Link, useLocation, useParams } from "wouter";
import { Building2 } from "lucide-react";
import { cn } from "@/lib/utils";

const TABS = [
  { key: "evidence",     label: "Evidence" },
  { key: "alternatives", label: "Alternatives" },
  { key: "solution-cost", label: "Solution Cost" },
] as const;

interface DriverTreeShellProps {
  accountName?: string;
  industry?: string;
  revenue?: string;
  children: React.ReactNode;
}

export default function DriverTreeShell({ accountName = "Account", industry = "Unknown", revenue = "N/A", children }: DriverTreeShellProps) {
  const params = useParams<{ accountId: string }>();
  const accountId = params.accountId ?? "";
  const [location] = useLocation();

  const segments = location.split("/");
  const activeTab = segments[3] || "evidence";

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Account context header */}
      <div className="h-11 bg-muted/50 border-b border-border flex items-center px-6 gap-3 text-[12px] shrink-0">
        <Building2 size={14} className="text-muted-foreground shrink-0" />
        <span className="font-semibold text-foreground">{accountName}</span>
        <span className="text-muted-foreground">·</span>
        <span className="text-muted-foreground">{industry}</span>
        <span className="text-muted-foreground">·</span>
        <span className="text-muted-foreground">{revenue}</span>
      </div>

      {/* Workspace tabs */}
      <div className="flex border-b border-border px-6" role="tablist">
        {TABS.map((tab) => (
          <Link key={tab.key} href={`/drivers/${accountId}/${tab.key}`}>
            <button
              role="tab"
              aria-selected={activeTab === tab.key}
              className={cn(
                "px-4 py-2.5 text-[12px] font-semibold border-b-2 -mb-px transition-colors",
                activeTab === tab.key
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              {tab.label}
            </button>
          </Link>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {children}
      </div>
    </div>
  );
}
