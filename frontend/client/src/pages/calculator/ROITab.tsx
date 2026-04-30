/**
 * ROITab — ROI Calculator
 *
 * Workspace tab for the Calculator workspace.
 */
import { useState } from "react";
import { useParams } from "react-router-dom";
import { Calculator } from "lucide-react";
import CalculatorShell from "@/components/workspace/CalculatorShell";
import RightRail, { type RightRailMode } from "@/components/workspace/RightRail";
import { useAgentEvents } from "@/agui";
import { useAccount } from "@/hooks/useAccounts";
import { SectionCard, MetricCard } from "@/components/WfPrimitives";

export default function CalcROITab() {
  const params = useParams<{ accountId: string }>();
  const accountId = params.accountId ?? null;
  const { data: account, isLoading: accountLoading } = useAccount(accountId);
  const [railMode, setRailMode] = useState<RightRailMode>("agent");

  const { messages, sendMessage, suggestedActions, steps, isStreaming, metadata } = useAgentEvents({
    activeTab: "roi",
    accountName: account?.name ?? "Account",
  });

  if (accountLoading) {
    return <div className="p-6 text-sm text-muted-foreground">Loading account…</div>;
  }

  return (
    <CalculatorShell
      account={{
        accountName: account?.name ?? "Account",
        industry: account?.industry ?? "Unknown",
        revenue: account?.annual_revenue ? `$${account.annual_revenue.toLocaleString()}` : "N/A",
      }}
      rightRail={
        <RightRail
          mode={railMode}
          onModeChange={setRailMode}
          activeTab="roi"
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
            <Calculator className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">ROI Calculator</h2>
            <p className="text-sm text-muted-foreground">
              Scenario-based ROI modeling with conservative, expected, and optimistic projections
            </p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <MetricCard label="Conservative" value="—" />
          <MetricCard label="Expected" value="—" />
          <MetricCard label="Optimistic" value="—" />
        </div>

        <SectionCard title="ROI Analysis">
          <div className="rounded-lg border border-dashed border-border p-8 text-center">
            <p className="text-sm text-muted-foreground">
              ROI calculations will be available once value drivers and evidence are established.
            </p>
            <p className="text-xs text-muted-foreground/60 mt-2">
              Scenario modeling with NPV, IRR, payback period, and risk-adjusted projections.
            </p>
          </div>
        </SectionCard>
      </div>
    </CalculatorShell>
  );
}
