/**
 * Value Realization Workspace Shell
 *
 * Provides a simple layout for the Value Realization page:
 *   - Account context header (name, industry, revenue)
 *   - Center canvas (flex) + Right rail slot (320px)
 */
import { useParams } from "react-router-dom";
import { Building2 } from "lucide-react";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AccountContext {
  accountName: string;
  industry: string;
  revenue: string;
}

interface RealizationShellProps {
  account: AccountContext;
  children: React.ReactNode;
  rightRail?: React.ReactNode;
}

// ── Account Context Header ────────────────────────────────────────────────────

function AccountHeader({ account }: { account: AccountContext }) {
  return (
    <div className="h-11 bg-muted/50 border-b border-border flex items-center px-6 gap-3 text-[12px] shrink-0">
      <Building2 size={14} className="text-muted-foreground shrink-0" />
      <span className="font-semibold text-foreground">{account.accountName}</span>
      <span className="text-muted-foreground">·</span>
      <span className="text-muted-foreground">{account.industry}</span>
      <span className="text-muted-foreground">·</span>
      <span className="text-muted-foreground">{account.revenue}</span>
    </div>
  );
}

// ── Shell ──────────────────────────────────────────────────────────────────────

export default function RealizationShell({
  account,
  children,
  rightRail,
}: RealizationShellProps) {
  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Account context header */}
      <AccountHeader account={account} />

      {/* Content area: center canvas + optional right rail */}
      <div className="flex flex-1 min-h-0">
        {/* Center canvas */}
        <div className="flex-1 min-w-0 overflow-y-auto p-6">
          {children}
        </div>

        {/* Right rail (320px) */}
        {rightRail && (
          <div className="w-[320px] shrink-0 border-l border-border overflow-y-auto">
            {rightRail}
          </div>
        )}
      </div>
    </div>
  );
}
