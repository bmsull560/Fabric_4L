/**
 * PersonaFitTab — Value Hypothesis → Persona Fit
 *
 * Stub: Shows how each hypothesis maps to stakeholder personas.
 * Will display a matrix of hypothesis × persona relevance.
 */
import { Users } from "lucide-react";

export default function PersonaFitTab() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
          <Users className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-foreground">Persona Fit</h2>
          <p className="text-sm text-muted-foreground">
            Map hypotheses to stakeholder personas and buying roles
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-dashed border-border p-8 text-center">
        <p className="text-sm text-muted-foreground">
          Persona fit analysis will be available once hypotheses and stakeholders are defined.
        </p>
        <p className="text-xs text-muted-foreground/60 mt-2">
          Shows relevance scores, messaging angles, and objection handling per persona.
        </p>
      </div>
    </div>
  );
}
