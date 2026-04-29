/**
 * ROITab — Calculator → ROI
 *
 * Stub: Interactive ROI calculator with adjustable inputs.
 * Will show payback period, NPV, IRR, and sensitivity analysis.
 */
import { TrendingUp } from "lucide-react";

export default function ROITab() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
          <TrendingUp className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-foreground">ROI Calculator</h2>
          <p className="text-sm text-muted-foreground">
            Calculate return on investment with adjustable assumptions
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-dashed border-border p-8 text-center">
        <p className="text-sm text-muted-foreground">
          ROI calculation requires completed driver tree and evidence.
        </p>
        <p className="text-xs text-muted-foreground/60 mt-2">
          Shows payback period, NPV, IRR, and sensitivity analysis with adjustable inputs.
        </p>
      </div>
    </div>
  );
}
