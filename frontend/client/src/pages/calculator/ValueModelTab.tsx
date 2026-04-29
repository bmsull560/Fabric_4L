/**
 * ValueModelTab — Calculator → Value Model
 *
 * Stub: Visual value model showing how drivers roll up to total value.
 * Will display a tree/waterfall of value components.
 */
import { GitBranch } from "lucide-react";

export default function ValueModelTab() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
          <GitBranch className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-foreground">Value Model</h2>
          <p className="text-sm text-muted-foreground">
            Visual breakdown of how value drivers compose the total business case
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-dashed border-border p-8 text-center">
        <p className="text-sm text-muted-foreground">
          Value model will be generated from the driver tree and calculator inputs.
        </p>
        <p className="text-xs text-muted-foreground/60 mt-2">
          Displays a waterfall chart showing how individual drivers roll up to total value.
        </p>
      </div>
    </div>
  );
}
