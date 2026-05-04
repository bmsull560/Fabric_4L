/**
 * OntologyMatchTab — Intelligence → Ontology Match
 *
 * Maps prospect pain signals to the vendor ontology.
 * Shows matched ontology nodes, confidence scores, and gap analysis.
 */
import { useState } from "react";
import { useParams } from "react-router-dom";
import { Network } from "lucide-react";
import IntelligenceShell from "@/components/workspace/IntelligenceShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
import { CenteredLoader } from "@/components/CenteredLoader";
import { SectionCard, MetricCard } from "@/components/WfPrimitives";

export default function OntologyMatchTab() {
  const params = useParams<{ accountId: string }>();
  const accountId = params.accountId ?? null;
  const { data: account, isLoading: accountLoading } = useAccount(accountId);
  const [railMode, setRailMode] = useState<RightRailMode>("agent");

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "ontology-match",
    accountName: account?.name ?? "Account",
  });

  if (!accountId) {
    return <AccountRequiredGuard accountId={accountId} />;
  }

  if (accountLoading) {
    return <CenteredLoader message="Loading account…" />;
  }

  if (!account) {
    return <div className="p-6 text-sm text-destructive">Account not found.</div>;
  }

  return (
    <IntelligenceShell
      account={{
        accountName: account?.name ?? "Account",
        industry: account?.industry ?? "Unknown",
        revenue: account?.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "N/A",
      }}
      rightRail={
        <RightRail
          mode={railMode}
          onModeChange={setRailMode}
          activeTab="ontology-match"
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
            <Network className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">Ontology Match</h2>
            <p className="text-sm text-muted-foreground">
              Map discovered signals to your vendor value ontology
            </p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <MetricCard label="Matched Pains" value="—" />
          <MetricCard label="Coverage" value="—" />
          <MetricCard label="Avg Confidence" value="—" />
        </div>

        <SectionCard title="Ontology Coverage">
          <div className="rounded-lg border border-dashed border-border p-8 text-center">
            <p className="text-sm text-muted-foreground">
              Ontology matching will be available once signals are enriched.
            </p>
            <p className="text-xs text-muted-foreground/60 mt-2">
              This tab will display matched ontology nodes, confidence scores, and coverage gaps.
            </p>
          </div>
        </SectionCard>
      </div>
    </IntelligenceShell>
  );
}
