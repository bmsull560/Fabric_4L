/**
 * ValueCasePage — Value Case workspace entry point
 *
 * Route: /value-case/:accountId
 */
import { useState } from "react";
import { useParams } from "react-router-dom";
import { FileText } from "lucide-react";
import ValueCaseShell from "@/components/workspace/ValueCaseShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
import { LoadingState, ErrorState } from "@/components/states";
import { SectionCard, MetricCard } from "@/components/WfPrimitives";

export default function ValueCasePage() {
  const params = useParams<{ accountId: string }>();
  const accountId = params.accountId ?? null;
  const { data: account, isLoading: accountLoading } = useAccount(accountId);
  const [railMode, setRailMode] = useState<RightRailMode>("agent");

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "value-case",
    accountName: account?.name ?? "Account",
  });

  if (!accountId) {
    return <AccountRequiredGuard accountId={accountId} />;
  }

  if (accountLoading) {
    return <LoadingState message="Loading account…" fullPage />;
  }

  if (!account) {
    return <ErrorState title="Account not found" description="Select a valid account to continue in this workspace." fullPage />;
  }

  return (
    <ValueCaseShell
      account={{
        accountName: account?.name ?? "Account",
        industry: account?.industry ?? "Unknown",
        revenue: account?.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "N/A",
      }}
      rightRail={
        <RightRail
          mode={railMode}
          onModeChange={setRailMode}
          activeTab="value-case"
          messages={messages}
          onSendMessage={sendMessage}
          suggestedActions={suggestedActions}
          steps={steps}
          isStreaming={isStreaming}
          runMetadata={metadata}
        />
      }
    >
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <FileText className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">Value Case</h2>
            <p className="text-sm text-muted-foreground">
              Generated value narrative and business case for the prospect
            </p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <MetricCard label="3-Year Value" value="—" />
          <MetricCard label="ROI" value="—" />
          <MetricCard label="Payback" value="—" />
        </div>

        <SectionCard title="Value Case">
          <div className="rounded-lg border border-dashed border-border p-8 text-center">
            <p className="text-sm text-muted-foreground">
              Value case will be generated once calculator and evidence are complete.
            </p>
            <p className="text-xs text-muted-foreground/60 mt-2">
              Auto-generated narrative with stakeholder-specific messaging and financial projections.
            </p>
          </div>
        </SectionCard>
      </div>
    </ValueCaseShell>
  );
}
