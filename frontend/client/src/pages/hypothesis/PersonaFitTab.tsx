/**
 * PersonaFitTab — Buyer persona fit analysis
 *
 * Stub: Will show how the value hypothesis maps to specific buyer personas
 * and their priorities.
 */
import { Users } from "lucide-react";

export default function PersonaFitTab() {
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
          <Users className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-foreground">Persona Fit</h2>
          <p className="text-sm text-muted-foreground">
            Map value hypotheses to buyer personas and their priorities
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-dashed border-border p-8 text-center">
        <p className="text-sm text-muted-foreground">
          Persona fit analysis will be available once value hypotheses are generated.
        </p>
        <p className="text-xs text-muted-foreground/60 mt-2">
          Shows which personas care most about each hypothesis and suggested messaging.
        </p>
      </div>
    </div>
  );
}
