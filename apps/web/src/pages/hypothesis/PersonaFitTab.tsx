/**
 * PersonaFitTab — Buyer persona fit analysis
 *
 * Will show how the value hypothesis maps to specific buyer personas
 * and their priorities.
 */
import { useState } from "react";
import { useParams } from "react-router-dom";
import { Users } from "lucide-react";
import HypothesisShell from "@/components/workspace/HypothesisShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
import { LoadingState, ErrorState } from "@/components/states";
import { SectionCard, MetricCard } from "@/components/WfPrimitives";

export default function PersonaFitTab() {
  const params = useParams<{ accountId: string }>();
  const accountId = params.accountId ?? null;
  const { data: account, isLoading: accountLoading } = useAccount(accountId);
  const [railMode, setRailMode] = useState<RightRailMode>("agent");

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "persona-fit",
    accountName: account?.name ?? "Account",
    accountId: accountId ?? undefined,
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
    <HypothesisShell
      account={{
        accountName: account?.name ?? "Account",
        industry: account?.industry ?? "Unknown",
        revenue: account?.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "N/A",
      }}
      rightRail={
        <RightRail
          mode={railMode}
          onModeChange={setRailMode}
          activeTab="persona-fit"
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
            <Users className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">Persona Fit</h2>
            <p className="text-sm text-muted-foreground">
              Map value hypotheses to buyer personas and their priorities
            </p>
          </div>
        </div>

        <SectionCard title="Persona Fit Analysis">
          <div className="rounded-lg border border-dashed border-border p-8 text-center">
            <p className="text-sm text-muted-foreground">
              Persona fit analysis will be available once value hypotheses are generated.
            </p>
            <p className="text-xs text-muted-foreground/60 mt-2">
              Shows which personas care most about each hypothesis and suggested messaging.
            </p>
          </div>
        </SectionCard>
      </div>
    </HypothesisShell>
  );
}
