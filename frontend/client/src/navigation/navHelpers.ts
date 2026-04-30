import type { ReactNode } from "react";

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

export function resolveWorkspacePath(path: string, accountId: string | null): string {
  if (!accountId) return path;

  const ACCOUNT_PREFIXES = ["/intelligence", "/hypothesis", "/drivers", "/calculator", "/value-case", "/realization"];
  for (const prefix of ACCOUNT_PREFIXES) {
    if (path === prefix) return `${prefix}/${accountId}`;
    if (path.startsWith(prefix + "/")) return path.replace(prefix + "/", `${prefix}/${accountId}/`);
  }

  if (path === "/studio") return `/studio/${accountId}`;
  if (path.startsWith("/studio/")) {
    return path.replace("/studio/", `/studio/${accountId}/`);
  }

  return path;
}

export function isItemVisible(item: NavItem, userTier: UserTier): boolean {
  if (userTier === "admin") return true;
  if (userTier === "advanced") return item.tier !== "admin";
  return item.tier === "standard";
}

export function isRouteActive(location: string, resolvedPath: string): boolean {
  return location === resolvedPath || location.startsWith(resolvedPath + "/");
}
