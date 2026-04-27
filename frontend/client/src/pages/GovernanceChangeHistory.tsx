import GovernanceTraceView from "./GovernanceTraceView";

export default function GovernanceChangeHistory() {
  return (
    <GovernanceTraceView
      breadcrumbSection="Governance Audit"
      breadcrumbPage="Change History"
      title="Change History"
      emptyStateSubtitle="Track governance changes over time with full provenance context."
    />
  );
}
