/**
 * OntologyMatchTab — Intelligence → Ontology Match
 *
 * Maps prospect pain signals to the vendor ontology.
 * Shows matched ontology nodes, confidence scores, and gap analysis.
 */
import { useState } from "react";
import { useParams } from "react-router-dom";
import { Network, CheckCircle2, AlertCircle } from "lucide-react";
import IntelligenceShell from "@/components/workspace/IntelligenceShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { useOntologyTypes } from "@/hooks/useOntology";
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
import { LoadingState, ErrorState } from "@/components/states";
import { SectionCard } from "@/components/blocks/SectionCard";
import { MetricCard } from "@/components/ui/fabric";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

export default function OntologyMatchTab() {
  const params = useParams<{ accountId: string }>();
  const accountId = params.accountId ?? null;
  const { data: account, isLoading: accountLoading } = useAccount(accountId);
  const { data: ontologyTypes, isLoading: ontologyLoading } = useOntologyTypes();
  const [railMode, setRailMode] = useState<RightRailMode>("agent");

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    accountId: accountId ?? undefined,
    activeTab: "ontology-match",
    accountName: account?.name ?? "Account",
  });

  if (!accountId) {
    return <AccountRequiredGuard accountId={accountId} />;
  }

  if (accountLoading || ontologyLoading) {
    return <LoadingState message="Loading ontology mapping…" fullPage />;
  }

  if (!account) {
    return <ErrorState title="Account not found" description="Select a valid account to continue in this workspace." fullPage />;
  }

  // Derive mock coverage from ontology types count (replace with real L3 alignment query)
  const totalTypes = ontologyTypes?.length ?? 0;
  const matchedPains = Math.min(totalTypes, 12);
  const coveragePct = totalTypes > 0 ? Math.round((matchedPains / totalTypes) * 100) : 0;
  const avgConfidence = 0.78;

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
          <MetricCard label="Matched Pains" value={String(matchedPains)} />
          <MetricCard label="Coverage" value={`${coveragePct}%`} />
          <MetricCard label="Avg Confidence" value={`${Math.round(avgConfidence * 100)}%`} />
        </div>

        <SectionCard title="Ontology Coverage">
          {totalTypes === 0 ? (
            <div className="rounded-lg border border-dashed border-border p-8 text-center">
              <p className="text-sm text-muted-foreground">
                No ontology types loaded. Ensure Layer 2 extraction is configured.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {ontologyTypes?.slice(0, 20).map((type) => {
                const isMatched = Math.random() > 0.3; // Replace with real alignment query
                return (
                  <div key={type.id} className="flex items-center justify-between p-3 rounded-lg border border-border">
                    <div className="flex items-center gap-3">
                      {isMatched ? (
                        <CheckCircle2 className="w-4 h-4 text-green-500" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-amber-500" />
                      )}
                      <div>
                        <p className="text-sm font-medium">{type.name}</p>
                        <p className="text-xs text-muted-foreground">{type.description ?? "No description"}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Progress value={isMatched ? Math.round(avgConfidence * 100) : 0} className="w-24 h-2" />
                      <Badge variant={isMatched ? "default" : "secondary"}>
                        {isMatched ? "Matched" : "Gap"}
                      </Badge>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </SectionCard>
      </div>
    </IntelligenceShell>
  );
}
