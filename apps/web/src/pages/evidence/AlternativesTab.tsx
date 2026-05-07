/**
 * AlternativesTab — Evidence → Alternatives
 *
 * Stub: Competitive alternatives and do-nothing cost analysis.
 * Will show alternative solutions, their limitations, and switching costs.
 */
import { ArrowLeftRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigation } from "@/hooks";
import { useParams } from "react-router-dom";
import { createNextAction } from "@/components/workspace/nextAction";

export default function AlternativesTab() {
  const { accountId } = useParams<{ accountId: string }>();
  const { navigateTo } = useNavigation();
  const nextAction = accountId
    ? createNextAction({ label: "Attach Evidence", target: "drivers", params: { accountId }, query: { tab: "solution-cost" } })
    : null;
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

      <div className="rounded-lg border border-dashed border-border p-8 text-center">
        <p className="text-sm text-muted-foreground">
          Alternative analysis will be available once evidence is gathered.
        </p>
        <p className="text-xs text-muted-foreground/60 mt-2">
          Compares your solution against alternatives including do-nothing, build-in-house, and competitors.
        </p>
      </div>
      {nextAction && (
        <div className="flex justify-end">
          <Button onClick={() => navigateTo(`/drivers/${accountId}/solution-cost`)} data-testid="primary-forward-action">
            {nextAction.label}
          </Button>
        </div>
      )}
    </div>
  );
}
