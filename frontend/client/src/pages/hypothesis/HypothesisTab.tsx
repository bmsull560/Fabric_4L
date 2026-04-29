/**
 * HypothesisTab — Value Hypothesis → Hypothesis
 *
 * Displays AI-generated value hypotheses for the account.
 * Shows hypothesis cards with impact estimates and confidence scores.
 */
import { Lightbulb } from "lucide-react";

export default function HypothesisTab() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
          <Lightbulb className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-foreground">Value Hypotheses</h2>
          <p className="text-sm text-muted-foreground">
            AI-generated hypotheses based on intelligence signals
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-dashed border-border p-8 text-center">
        <p className="text-sm text-muted-foreground">
          Run intelligence analysis to generate value hypotheses.
        </p>
        <p className="text-xs text-muted-foreground/60 mt-2">
          Each hypothesis includes impact estimate, confidence score, and supporting signals.
        </p>
      </div>
    </div>
  );
}
