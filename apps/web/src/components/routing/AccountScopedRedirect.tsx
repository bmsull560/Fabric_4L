/**
 * AccountScopedRedirect
 *
 * Redirects a parent route (e.g. /intelligence) to its account-scoped child
 * (e.g. /intelligence/:accountId/signals) using the selectedAccountId from
 * the account context store. Falls back to /accounts if no account is selected.
 */
import { Navigate } from "react-router-dom";
import { useAccountContextStore } from "@/stores/accountContextStore";

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

  const suffix = defaultTab
    ? `/${selectedAccountId}/${defaultTab}`
    : `/${selectedAccountId}`;

  return <Navigate to={`${basePath}${suffix}`} replace />;
}
