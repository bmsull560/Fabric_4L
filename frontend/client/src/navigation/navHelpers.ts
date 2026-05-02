import type { ReactNode } from "react";
import { resolveWorkspacePath } from "./navigationService";

export type UserTier = "standard" | "advanced" | "admin";

export interface NavItem {
  id: string;
  label: string;
  icon?: ReactNode;
  path: string;
  tier: UserTier;
  children?: NavItem[];
  badge?: string | number;
  description?: string;
}

// Re-export from navigationService for backward compatibility during migration
export { resolveWorkspacePath };

export function isItemVisible(item: NavItem, userTier: UserTier): boolean {
  if (userTier === "admin") return true;
  if (userTier === "advanced") return item.tier !== "admin";
  return item.tier === "standard";
}

export function isRouteActive(location: string, resolvedPath: string): boolean {
  return location === resolvedPath || location.startsWith(resolvedPath + "/");
}
