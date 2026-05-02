/**
 * Intelligence Workspace — Route Helpers
 *
 * All workspace routes follow:
 *   /accounts/:accountId/intelligence/:tabId
 */
import type { WorkspaceTabId } from "./types";
import { getTabOrDefault } from "./workspaceTabRegistry";

export const WORKSPACE_BASE = "/accounts";

export function workspacePath(accountId: string, tabId?: WorkspaceTabId | string): string {
  const resolvedTab = getTabOrDefault(tabId);
  return `/accounts/${accountId}/intelligence/${resolvedTab}`;
}

export function workspaceBasePath(accountId: string): string {
  return `/accounts/${accountId}/intelligence`;
}

export function parseWorkspaceRoute(pathname: string): {
  accountId: string | null;
  tabId: string | null;
} {
  // Expected: /accounts/:accountId/intelligence/:tabId
  const match = pathname.match(/^\/accounts\/([^/]+)\/intelligence\/([^/]+)/);
  if (match) {
    return { accountId: match[1], tabId: match[2] };
  }
  // Also match: /accounts/:accountId/intelligence (no tab)
  const baseMatch = pathname.match(/^\/accounts\/([^/]+)\/intelligence\/?$/);
  if (baseMatch) {
    return { accountId: baseMatch[1], tabId: null };
  }
  return { accountId: null, tabId: null };
}
