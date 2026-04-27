import GovernanceTraceView from "./GovernanceTraceView";

export default function GovernanceAuditLog() {
  return (
    <GovernanceTraceView
      breadcrumbSection="Governance Audit"
      breadcrumbPage="Audit Log"
      title="Audit Log"
      emptyStateSubtitle="Inspect governance audit events and entity-level trace data."
    />
  );
}
