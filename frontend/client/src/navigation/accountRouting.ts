export type AccountWorkspace = "intelligence" | "studio";

const WORKSPACE_TABS = {
  intelligence: [
    "signals",
    "enrichment",
    "stakeholders",
    "ontology-match",
    "hypotheses",
    "drivers",
    "evidence",
    "alternatives",
    "solution-cost",
    "calculator",
    "value-model",
    "value-case",
    "value-realization",
  ],
  studio: [
    "action-plan",
    "value-model",
    "narrative",
    "enrichment",
    "competitive",
    "roi",
    "evidence",
  ],
} as const;

const DEFAULT_WORKSPACE_TAB: Record<AccountWorkspace, string> = {
  intelligence: "signals",
  studio: "action-plan",
};

export function isValidWorkspaceTab(workspace: AccountWorkspace, tab: string | undefined): tab is string {
  return Boolean(tab) && WORKSPACE_TABS[workspace].includes(tab as never);
}

export function getWorkspaceTabOrDefault(
  workspace: AccountWorkspace,
  tab: string | undefined
): string {
  return isValidWorkspaceTab(workspace, tab) ? tab : DEFAULT_WORKSPACE_TAB[workspace];
}

export function resolveWorkspaceRoutePath(path: string, accountId: string | null): string {
  if (!accountId) return path;
  if (path === "/intelligence") return `/intelligence/${accountId}`;
  if (path.startsWith("/intelligence/")) {
    return path.replace("/intelligence/", `/intelligence/${accountId}/`);
  }
  if (path === "/studio") return `/studio/${accountId}`;
  if (path.startsWith("/studio/")) {
    return path.replace("/studio/", `/studio/${accountId}/`);
  }
  return path;
}

export function resolveAccountScopedWorkspacePath(options: {
  workspace: AccountWorkspace;
  accountId: string | null;
  tab?: string;
}): string {
  const { workspace, accountId, tab } = options;
  if (!accountId) return "/accounts";
  const resolvedTab = getWorkspaceTabOrDefault(workspace, tab);
  if (workspace === "intelligence") {
    return `/intelligence/${accountId}/${resolvedTab}`;
  }
  return `/${workspace}/${accountId}/${resolvedTab}`;
}
