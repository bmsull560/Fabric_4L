/**
 * WorkspaceTabFrame — Renders the active tab's component with standard props
 */
import { Suspense } from "react";
import { useWorkspaceContext } from "../hooks/useWorkspaceContext";
import { getTabDef, getTabOrDefault } from "../workspaceTabRegistry";
import WorkspaceEmptyState from "./WorkspaceEmptyState";
import WorkspaceLoadingState from "./WorkspaceLoadingState";

export default function WorkspaceTabFrame() {
  const { accountId, tabId } = useWorkspaceContext();
  const resolvedTabId = getTabOrDefault(tabId);
  const tabDef = getTabDef(resolvedTabId);

  if (!tabDef || !tabDef.component) {
    return <WorkspaceEmptyState tabId={resolvedTabId} />;
  }

  const TabComponent = tabDef.component;

  return (
    <Suspense fallback={<WorkspaceLoadingState />}>
      <TabComponent accountId={accountId} />
    </Suspense>
  );
}
