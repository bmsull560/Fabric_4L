/**
 * DiscoveryQuestionsTab — Prospect discovery questions
 *
 * Will contain AI-generated discovery questions based on
 * the selected value hypothesis and account context.
 */
import { useState } from "react";
import { useParams } from "react-router-dom";
import { MessageCircleQuestion } from "lucide-react";
import HypothesisShell from "@/components/workspace/HypothesisShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { AccountRequiredGuard } from "@/components/AccountRequiredGuard";
import { CenteredLoader } from "@/components/CenteredLoader";
import { SectionCard, MetricCard } from "@/components/WfPrimitives";

export default function DiscoveryQuestionsTab() {
  const params = useParams<{ accountId: string }>();
  const accountId = params.accountId ?? null;
  const { data: account, isLoading: accountLoading } = useAccount(accountId);
  const [railMode, setRailMode] = useState<RightRailMode>("agent");

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "discovery-questions",
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
          activeTab="discovery-questions"
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
            <MessageCircleQuestion className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">Discovery Questions</h2>
            <p className="text-sm text-muted-foreground">
              AI-generated questions to validate value hypotheses with prospects
            </p>
          </div>
        </div>

        <SectionCard title="Discovery Questions">
          <div className="rounded-lg border border-dashed border-border p-8 text-center">
            <p className="text-sm text-muted-foreground">
              Discovery questions will be generated once a value hypothesis is selected.
            </p>
            <p className="text-xs text-muted-foreground/60 mt-2">
              These questions help sales teams validate pain points and quantify value during discovery calls.
            </p>
          </div>
        </SectionCard>
      </div>
    </HypothesisShell>
  );
}
