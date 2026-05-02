/**
 * useWorkspaceReadiness — Checks whether the workspace has enough context to render
 */
import { useWorkspaceContext } from "./useWorkspaceContext";

export function useWorkspaceReadiness() {
  const { accountId, accountName } = useWorkspaceContext();

  const isReady = Boolean(accountId);
  const hasAccountName = Boolean(accountName);

  return {
    isReady,
    hasAccountName,
    reason: !isReady ? "No account selected" : undefined,
  };
}
