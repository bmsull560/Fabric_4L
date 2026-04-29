/**
 * AssumptionsTab — Value Hypothesis → Assumptions
 *
 * Stub: Lists and manages assumptions underlying each hypothesis.
 * Will show assumption cards with validation status and risk level.
 */
import { AlertTriangle } from "lucide-react";

export default function AssumptionsTab() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
          <AlertTriangle className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-foreground">Assumptions</h2>
          <p className="text-sm text-muted-foreground">
            Track and validate assumptions underlying each value hypothesis
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-dashed border-border p-8 text-center">
        <p className="text-sm text-muted-foreground">
          Assumptions will be extracted once hypotheses are generated.
        </p>
        <p className="text-xs text-muted-foreground/60 mt-2">
          Each assumption shows validation status (unverified, confirmed, rejected) and risk level.
        </p>
      </div>
    </div>
  );
}
