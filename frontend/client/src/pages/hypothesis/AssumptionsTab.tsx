/**
 * AssumptionsTab — Key assumptions and risk analysis
 *
 * Stub: Will list critical assumptions underlying each value hypothesis
 * and their validation status.
 */
import { ShieldAlert } from "lucide-react";

export default function AssumptionsTab() {
  return (
    <div className="space-y-6 p-6">
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

      <div className="rounded-lg border border-dashed border-border p-8 text-center">
        <p className="text-sm text-muted-foreground">
          Assumption analysis will be available once value hypotheses are generated.
        </p>
        <p className="text-xs text-muted-foreground/60 mt-2">
          Tracks validation status of key assumptions and surfaces risks to the business case.
        </p>
      </div>
    </div>
  );
}
