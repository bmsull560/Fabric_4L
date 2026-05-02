/**
 * WorkspaceProgressRail — Visual progress indicator for the workspace pipeline
 *
 * Shows which category the current tab belongs to:
 *   Inputs → Reasoning → Outputs
 */
import { cn } from "@/lib/utils";
import { useWorkspaceContext } from "../hooks/useWorkspaceContext";
import { getTabDef, getTabOrDefault } from "../workspaceTabRegistry";
import type { WorkspaceTabCategory } from "../types";

const CATEGORIES: { id: WorkspaceTabCategory; label: string }[] = [
  { id: "input", label: "Inputs" },
  { id: "reasoning", label: "Reasoning" },
  { id: "output", label: "Outputs" },
];

export default function WorkspaceProgressRail() {
  const { tabId } = useWorkspaceContext();
  const resolvedTab = getTabOrDefault(tabId);
  const tabDef = getTabDef(resolvedTab);
  const activeCategory = tabDef?.category ?? "input";

  return (
    <div className="flex items-center gap-1 px-6 py-1.5 border-b border-border bg-muted/30">
      {CATEGORIES.map((cat, i) => (
        <div key={cat.id} className="flex items-center gap-1">
          {i > 0 && <span className="text-muted-foreground/40 text-[10px]">→</span>}
          <span
            className={cn(
              "text-[10px] font-medium px-2 py-0.5 rounded-full transition-colors",
              activeCategory === cat.id
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground/60"
            )}
          >
            {cat.label}
          </span>
        </div>
      ))}
    </div>
  );
}
