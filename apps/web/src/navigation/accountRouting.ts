import { getStatePath, buildPath, type RouteState } from './navigationService';

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

  // Map path prefixes to route states
  const pathMap: Record<string, RouteState> = {
    '/intelligence': 'intelligence',
    '/studio': 'studio',
  };

  for (const [prefix, state] of Object.entries(pathMap)) {
    if (path === prefix) {
      return getStatePath(state, { accountId });
    }
    if (path.startsWith(`${prefix}/`)) {
      const suffix = path.slice(prefix.length + 1);
      return buildPath(`${getStatePath(state, { accountId })}/:suffix`, { suffix });
    }
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
  const state: RouteState = workspace === 'intelligence' ? 'intelligence' : 'studio';
  const basePath = getStatePath(state, { accountId });

  return buildPath(`${basePath}/:tab`, { tab: resolvedTab });
}
