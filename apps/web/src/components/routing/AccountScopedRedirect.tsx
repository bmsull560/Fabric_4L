/**
 * AccountScopedRedirect
 *
 * Redirects a parent route (e.g. /intelligence) to its account-scoped child
 * (e.g. /intelligence/:accountId/signals) using the selectedAccountId from
 * the account context store. Falls back to /accounts if no account is selected.
 */
import { Navigate } from "react-router-dom";
import { useAccountContextStore } from "@/stores/accountContextStore";
import { getStatePath, buildPath, type RouteState } from "@/navigation/navigationService";

const BASE_PATH_STATE_MAP: Record<string, RouteState> = {
  '/intelligence': 'intelligence',
  '/hypothesis': 'hypothesis',
  '/drivers': 'drivers',
  '/calculator': 'calculator',
  '/value-case': 'value-case',
  '/realization': 'realization',
};

interface AccountScopedRedirectProps {
  basePath: string;
  defaultTab?: string;
}

export function AccountScopedRedirect({
  basePath,
  defaultTab,
}: AccountScopedRedirectProps) {
  const selectedAccountId = useAccountContextStore(
    (state) => state.selectedAccountId
  );

  if (!selectedAccountId) {
    return <Navigate to="/accounts" replace />;
  }

  const state = BASE_PATH_STATE_MAP[basePath];
  if (!state) {
    // Fallback for unknown base paths — construct safely without raw concatenation
    const safeBase = basePath.replace(/\/$/, '');
    if (!safeBase) {
      // Edge case: basePath is empty or just slashes - redirect to accounts
      return <Navigate to="/accounts" replace />;
    }
    const safeSuffix = defaultTab
      ? `/${selectedAccountId}/${defaultTab}`
      : `/${selectedAccountId}`;
    return <Navigate to={`${safeBase}${safeSuffix}`} replace />;
  }

  const baseStatePath = getStatePath(state, { accountId: selectedAccountId });
  const targetPath = defaultTab
    ? buildPath(`${baseStatePath}/:tab`, { tab: defaultTab })
    : baseStatePath;

  return <Navigate to={targetPath} replace />;
}
