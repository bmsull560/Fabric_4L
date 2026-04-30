/**
 * AssumptionsTab — Key assumptions and risk analysis
 *
 * Will list critical assumptions underlying each value hypothesis
 * and their validation status.
 */
import { useState } from "react";
import { useParams } from "react-router-dom";
import { ShieldAlert } from "lucide-react";
import HypothesisShell from "@/components/workspace/HypothesisShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { SectionCard, MetricCard } from "@/components/WfPrimitives";

export default function AssumptionsTab() {
  const params = useParams<{ accountId: string }>();
  const accountId = params.accountId ?? null;
  const { data: account, isLoading: accountLoading } = useAccount(accountId);
  const [railMode, setRailMode] = useState<RightRailMode>("agent");

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "assumptions",
    accountName: account?.name ?? "Account",
  });

  if (accountLoading) {
    return <div className="p-6 text-sm text-muted-foreground">Loading account…</div>;
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
          activeTab="assumptions"
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
            <ShieldAlert className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">Assumptions</h2>
            <p className="text-sm text-muted-foreground">
              Critical assumptions and risks for each value hypothesis
            </p>
          </div>
        </div>

        <SectionCard title="Assumption Analysis">
          <div className="rounded-lg border border-dashed border-border p-8 text-center">
            <p className="text-sm text-muted-foreground">
              Assumption analysis will be available once value hypotheses are generated.
            </p>
            <p className="text-xs text-muted-foreground/60 mt-2">
              Tracks validation status of key assumptions and surfaces risks to the business case.
            </p>
          </div>
        </SectionCard>
      </div>
    </HypothesisShell>
  );
}
