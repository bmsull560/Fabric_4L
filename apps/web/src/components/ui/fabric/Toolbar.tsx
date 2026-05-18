/**
 * Toolbar — Simple flex row for action buttons.
 * Migrated from WfPrimitives shim.
 */
import type { ReactNode } from "react";

export function Toolbar({ children }: { children: ReactNode }) {
  return <div className="flex items-center gap-2 flex-wrap mb-4">{children}</div>;
}
