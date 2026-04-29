/**
 * SolutionCostTab — Evidence → Solution Cost
 *
 * Stub: Total cost of ownership for the proposed solution.
 * Will show implementation costs, ongoing costs, and time-to-value.
 */
import { DollarSign } from "lucide-react";

export default function SolutionCostTab() {
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

      <div className="rounded-lg border border-dashed border-border p-8 text-center">
        <p className="text-sm text-muted-foreground">
          Solution cost breakdown will be available once evidence is validated.
        </p>
        <p className="text-xs text-muted-foreground/60 mt-2">
          Includes implementation, licensing, training, and ongoing operational costs.
        </p>
      </div>
    </div>
  );
}
