/**
 * DiscoveryQuestionsTab — Value Hypothesis → Discovery Questions
 *
 * Stub: AI-generated discovery questions to validate hypotheses.
 * Will show persona-specific questions grouped by hypothesis.
 */
import { MessageCircleQuestion } from "lucide-react";

export default function DiscoveryQuestionsTab() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
          <MessageCircleQuestion className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-foreground">Discovery Questions</h2>
          <p className="text-sm text-muted-foreground">
            Persona-specific questions to validate hypotheses in sales conversations
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-dashed border-border p-8 text-center">
        <p className="text-sm text-muted-foreground">
          Discovery questions will be generated once hypotheses are created.
        </p>
        <p className="text-xs text-muted-foreground/60 mt-2">
          Questions are tailored to each stakeholder persona and linked to specific hypotheses.
        </p>
      </div>
    </div>
  );
}
