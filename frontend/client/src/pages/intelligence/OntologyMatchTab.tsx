/**
 * OntologyMatchTab — Intelligence → Ontology Match
 *
 * Stub: Maps prospect pain signals to the vendor ontology.
 * Will show matched ontology nodes, confidence scores, and gap analysis.
 */
import { Network } from "lucide-react";

export default function OntologyMatchTab() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
          <Network className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-foreground">Ontology Match</h2>
          <p className="text-sm text-muted-foreground">
            Map discovered signals to your vendor value ontology
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-dashed border-border p-8 text-center">
        <p className="text-sm text-muted-foreground">
          Ontology matching will be available once signals are enriched.
        </p>
        <p className="text-xs text-muted-foreground/60 mt-2">
          This tab will display matched ontology nodes, confidence scores, and coverage gaps.
        </p>
      </div>
    </div>
  );
}
