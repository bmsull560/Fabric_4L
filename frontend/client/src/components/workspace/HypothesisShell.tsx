/**
 * Hypothesis Workspace Shell
 *
 * Provides the shared layout for all Hypothesis workspace tabs:
 *   Hypotheses → Discovery Questions → Persona Fit → Assumptions
 *
 * Layout:
 *   - Account context header (name, industry, revenue)
 *   - Horizontal workspace tabs (route-driven)
 *   - Center canvas (flex) + Right rail slot (320px)
 */
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { Building2, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { Btn } from "@/components/WfPrimitives";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AccountContext {
  accountName: string;
  industry: string;
  revenue: string;
}

interface HypothesisShellProps {
  account: AccountContext;
  children: React.ReactNode;
  rightRail?: React.ReactNode;
}

// ── Tab Definitions ───────────────────────────────────────────────────────────

const TABS = [
  { key: "hypothesis",         label: "Hypotheses" },
  { key: "discovery-questions", label: "Discovery Questions" },
  { key: "persona-fit",        label: "Persona Fit" },
  { key: "assumptions",        label: "Assumptions" },
] as const;

// ── Account Context Header ────────────────────────────────────────────────────

function AccountHeader({ account, accountId }: { account: AccountContext; accountId: string }) {
  const navigate = useNavigate();

  return (
    <div className="h-11 bg-muted/50 border-b border-border flex items-center px-6 gap-3 text-[12px] shrink-0">
      <Building2 size={14} className="text-muted-foreground shrink-0" />
      <span className="font-semibold text-foreground">{account.accountName}</span>
      <span className="text-muted-foreground">·</span>
      <span className="text-muted-foreground">{account.industry}</span>
      <span className="text-muted-foreground">·</span>
      <span className="text-muted-foreground">{account.revenue}</span>
      <div className="flex-1" />
      <Btn
        variant="primary"
        onClick={() => navigate(`/drivers/${accountId}`)}
        className="gap-1.5"
      >
        <Sparkles size={13} />
        Generate Driver Tree
      </Btn>
    </div>
  );
}

// ── Workspace Tabs ────────────────────────────────────────────────────────────

function WorkspaceTabs({ accountId, activeTab }: { accountId: string; activeTab: string }) {
  return (
    <div className="flex border-b border-border px-6" role="tablist">
      {TABS.map((tab) => (
        <Link key={tab.key} to={`/hypothesis/${accountId}/${tab.key}`}>
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
  );
}

// ── Shell ──────────────────────────────────────────────────────────────────────

export default function HypothesisShell({
  account,
  children,
  rightRail,
}: HypothesisShellProps) {
  const params = useParams<{ accountId: string }>();
  const accountId = params.accountId ?? "";
  const location = useLocation().pathname;

  // Derive active tab from URL
  const segments = location.split("/");
  const activeTab = segments[3] || "hypothesis";

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Account context header */}
      <AccountHeader account={account} accountId={accountId} />

      {/* Workspace tabs */}
      <WorkspaceTabs accountId={accountId} activeTab={activeTab} />

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
