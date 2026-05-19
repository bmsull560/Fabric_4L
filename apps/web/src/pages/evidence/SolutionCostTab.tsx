/**
 * SolutionCostTab — Evidence → Solution Cost
 *
 * Total cost of ownership for the proposed solution.
 * Shows implementation costs, ongoing costs, and time-to-value.
 */
import { DollarSign, Clock, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useNavigation } from "@/hooks";
import { useParams } from "react-router-dom";
import { useAccount } from "@/hooks/useAccounts";
import { createNextAction } from "@/components/workspace/nextAction";
import { LoadingState, ErrorState } from "@/components/states";
import { SectionCard } from "@/components/blocks/SectionCard";
import { MetricCard } from "@/components/ui/fabric";

export default function SolutionCostTab() {
  const { accountId } = useParams<{ accountId: string }>();
  const { navigateTo } = useNavigation();
  const { data: account, isLoading: accountLoading } = useAccount(accountId ?? null);

  const nextAction = accountId
    ? createNextAction({ label: "Model Scenarios", target: "calculator", params: { accountId } })
    : null;

  if (accountLoading) {
    return <LoadingState message="Loading cost model…" />;
  }

  if (!account) {
    return <ErrorState title="Account not found" description="Select a valid account to view solution costs." />;
  }

  // Derive costs from account metadata (replace with real scenario query)
  const implCost = account.metadata?.implementation_cost ?? 0;
  const annualBenefit = account.metadata?.annual_benefit ?? 0;
  const rampMonths = account.metadata?.ramp_months ?? 3;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
          <DollarSign className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-foreground">Solution Cost</h2>
          <p className="text-sm text-muted-foreground">
            Total cost of ownership and implementation timeline
          </p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <MetricCard
          label="Implementation"
          value={implCost > 0 ? `$${implCost.toLocaleString()}` : "—"}
        />
        <MetricCard
          label="Annual Benefit"
          value={annualBenefit > 0 ? `$${annualBenefit.toLocaleString()}` : "—"}
        />
        <MetricCard
          label="Ramp Period"
          value={rampMonths > 0 ? `${rampMonths} mo` : "—"}
        />
      </div>

      <SectionCard title="Cost Breakdown">
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-lg border border-border">
            <div className="flex items-center gap-3">
              <DollarSign className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm">Software Licensing</span>
            </div>
            <Badge variant="outline">Included</Badge>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg border border-border">
            <div className="flex items-center gap-3">
              <Clock className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm">Implementation Services</span>
            </div>
            <Badge variant="outline">
              {implCost > 0 ? `$${implCost.toLocaleString()}` : "TBD"}
            </Badge>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg border border-border">
            <div className="flex items-center gap-3">
              <TrendingUp className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm">Training & Enablement</span>
            </div>
            <Badge variant="outline">Included</Badge>
          </div>
        </div>
      </SectionCard>

      {implCost === 0 && (
        <div className="rounded-lg border border-dashed border-border p-6 text-center">
          <p className="text-sm text-muted-foreground">
            No cost model configured. Use the ROI Calculator to build scenarios.
          </p>
        </div>
      )}

      {nextAction && (
        <div className="flex justify-end">
          <Button onClick={() => navigateTo(nextAction.target, nextAction.params)} data-testid="primary-forward-action">
            {nextAction.label}
          </Button>
        </div>
      )}
    </div>
  );
}
