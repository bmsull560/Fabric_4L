/**
 * IntelligenceWorkspacePage — Route entry point
 *
 * Route: /accounts/:accountId/intelligence/:tabId?
 *
 * This page component handles account context sync and renders
 * the IntelligenceWorkspace feature.
 */
import IntelligenceWorkspace from "@/features/intelligence-workspace/IntelligenceWorkspace";

export default function IntelligenceWorkspacePage() {
  return <IntelligenceWorkspace />;
}
