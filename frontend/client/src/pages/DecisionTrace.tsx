/**
 * Screen 10 — Audit & Provenance: Decision Trace Viewer
 * Design: Refined Enterprise SaaS
 */
import GovernanceTraceView from "./GovernanceTraceView";

export default function DecisionTrace() {
  return (
    <GovernanceTraceView
      breadcrumbSection="Audit & Provenance"
      breadcrumbPage="Decision Traces"
      title="Decision Trace Viewer"
      emptyStateSubtitle="Full provenance and audit trail for all entity decisions."
    />
  );
}
