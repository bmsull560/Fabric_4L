/**
 * IntelligenceWorkspace — Main workspace shell
 *
 * Composes: Header → Progress Rail → Tabs → Tab Frame
 *
 * Route: /accounts/:accountId/intelligence/:tabId
 */
import WorkspaceHeader from "./components/WorkspaceHeader";
import WorkspaceProgressRail from "./components/WorkspaceProgressRail";
import IntelligenceWorkspaceTabs from "./IntelligenceWorkspaceTabs";
import WorkspaceTabFrame from "./components/WorkspaceTabFrame";

export default function IntelligenceWorkspace() {
  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Account context header */}
      <WorkspaceHeader />
      {/* Pipeline progress indicator */}
      <WorkspaceProgressRail />
      {/* Workspace tabs */}
      <IntelligenceWorkspaceTabs />
      {/* Active tab content */}
      <div className="flex-1 min-h-0 overflow-y-auto p-6">
        <WorkspaceTabFrame />
      </div>
    </div>
  );
}
