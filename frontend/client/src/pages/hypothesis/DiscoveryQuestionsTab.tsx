/**
 * DiscoveryQuestionsTab — Prospect discovery questions
 *
 * Stub: Will contain AI-generated discovery questions based on
 * the selected value hypothesis and account context.
 */
import { MessageCircleQuestion } from "lucide-react";

export default function DiscoveryQuestionsTab() {
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
          <MessageCircleQuestion className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-foreground">Discovery Questions</h2>
          <p className="text-sm text-muted-foreground">
            AI-generated questions to validate value hypotheses with prospects
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-dashed border-border p-8 text-center">
        <p className="text-sm text-muted-foreground">
          Discovery questions will be generated once a value hypothesis is selected.
        </p>
        <p className="text-xs text-muted-foreground/60 mt-2">
          These questions help sales teams validate pain points and quantify value during discovery calls.
        </p>
      </div>
    </div>
  );
}
