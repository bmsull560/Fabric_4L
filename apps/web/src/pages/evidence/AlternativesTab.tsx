/**
 * AlternativesTab — Evidence → Alternatives
 *
 * Competitive alternatives and do-nothing cost analysis.
 * Shows alternative solutions, their limitations, and switching costs.
 */
import { ArrowLeftRight, ShieldAlert, Building2, Wrench } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useNavigation } from "@/hooks";
import { useParams } from "react-router-dom";
import { useAccount } from "@/hooks/useAccounts";
import { useAccountBriefing } from "@/hooks/useIntelligence";
import { createNextAction } from "@/components/workspace/nextAction";
import { LoadingState, ErrorState } from "@/components/states";
import { SectionCard } from "@/components/blocks/SectionCard";

export default function AlternativesTab() {
  const { accountId } = useParams<{ accountId: string }>();
  const { navigateTo } = useNavigation();
  const { data: account, isLoading: accountLoading } = useAccount(accountId ?? null);
  const { data: briefing, isLoading: briefingLoading } = useAccountBriefing(accountId ?? null);

  const nextAction = accountId
    ? createNextAction({ label: "Attach Evidence", target: "drivers", params: { accountId }, query: { tab: "solution-cost" } })
    : null;

  if (accountLoading || briefingLoading) {
    return <LoadingState message="Loading competitive landscape…" />;
  }

  if (!account) {
    return <ErrorState title="Account not found" description="Select a valid account to view alternatives." />;
  }

  const competitors = briefing?.competitive?.competitors ?? [];
  const doNothingCost = briefing?.competitive?.do_nothing_cost ?? null;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
          <ArrowLeftRight className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-foreground">Alternatives</h2>
          <p className="text-sm text-muted-foreground">
            Competitive alternatives and cost-of-inaction analysis
          </p>
        </div>
      </div>

      {competitors.length === 0 && !doNothingCost ? (
        <div className="rounded-lg border border-dashed border-border p-8 text-center">
          <p className="text-sm text-muted-foreground">
            No competitive data available. Run account enrichment to discover competitors.
          </p>
        </div>
      ) : (
        <>
          <SectionCard title="Competitors">
            <div className="space-y-3">
              {competitors.map((comp) => (
                <div key={comp.name} className="flex items-start justify-between p-3 rounded-lg border border-border">
                  <div className="flex items-center gap-3">
                    <Building2 className="w-4 h-4 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">{comp.name}</p>
                      <p className="text-xs text-muted-foreground">{comp.weaknesses?.join("; ") ?? "No weakness data"}</p>
                    </div>
                  </div>
                  <Badge variant="outline">{comp.threat_level ?? "unknown"}</Badge>
                </div>
              ))}
              {competitors.length === 0 && (
                <p className="text-sm text-muted-foreground">No competitors detected yet.</p>
              )}
            </div>
          </SectionCard>

          <SectionCard title="Do-Nothing Cost">
            <div className="flex items-center gap-3 p-3 rounded-lg border border-border bg-amber-50/50">
              <ShieldAlert className="w-5 h-5 text-amber-600" />
              <div>
                <p className="text-sm font-medium text-amber-900">Cost of Inaction</p>
                <p className="text-xs text-amber-800/80">
                  {doNothingCost
                    ? `Estimated annual cost: $${doNothingCost.toLocaleString()}`
                    : "Run ROI calculator to estimate cost of inaction."}
                </p>
              </div>
            </div>
          </SectionCard>

          <SectionCard title="Build vs Buy">
            <div className="flex items-start gap-3 p-3 rounded-lg border border-border">
              <Wrench className="w-4 h-4 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm font-medium">Build In-House</p>
                <p className="text-xs text-muted-foreground">
                  Typical build cost: $500K–$2M over 12–18 months with ongoing maintenance.
                </p>
              </div>
            </div>
          </SectionCard>
        </>
      )}

      {nextAction && (
        <div className="flex justify-end">
          <Button onClick={() => navigateTo(nextAction.target, nextAction.params, nextAction.query)} data-testid="primary-forward-action">
            {nextAction.label}
          </Button>
        </div>
      )}
    </div>
  );
}
