import { Route } from "wouter";
import type { ComponentType } from "react";
import type { RouteComposerContext } from "./types";

interface GovernancePages {
  DecisionTrace: ComponentType;
  GovernanceEvidence: ComponentType;
  GovernanceCompliance: ComponentType;
  GovernanceAuditLog: ComponentType;
  GovernanceChangeHistory: ComponentType;
  BenchmarkPolicies: ComponentType;
  HealthMonitor: ComponentType;
}

function AliasRedirect({ from, to, Navigate }: { from: string; to: string; Navigate: ComponentType<{ to: string }> }) {
  return <Route path={from}><Navigate to={to} /></Route>;
}

export function GovernanceRoutes(context: RouteComposerContext, p: GovernancePages) {
  const { tierProps, AuthenticatedRoute, Navigate } = context;
  return <>
    <Route path="/governance"><Navigate to="/governance/traces" /></Route>
    <Route path="/governance/traces"><AuthenticatedRoute {...tierProps}><p.DecisionTrace /></AuthenticatedRoute></Route>
    <Route path="/governance/evidence"><AuthenticatedRoute {...tierProps}><p.GovernanceEvidence /></AuthenticatedRoute></Route>
    <Route path="/governance/provenance"><AuthenticatedRoute {...tierProps} requiredTier="advanced"><p.DecisionTrace /></AuthenticatedRoute></Route>
    <Route path="/governance/integrity"><AuthenticatedRoute {...tierProps} requiredTier="advanced"><p.DecisionTrace /></AuthenticatedRoute></Route>
    <Route path="/governance/compliance"><AuthenticatedRoute {...tierProps} requiredTier="advanced"><p.GovernanceCompliance /></AuthenticatedRoute></Route>
    <Route path="/governance/benchmarks"><AuthenticatedRoute {...tierProps} requiredTier="admin"><p.BenchmarkPolicies /></AuthenticatedRoute></Route>
    <Route path="/governance/audit"><Navigate to="/governance/audit/log" /></Route>
    <Route path="/governance/audit/log"><AuthenticatedRoute {...tierProps} requiredTier="admin"><p.GovernanceAuditLog /></AuthenticatedRoute></Route>
    <Route path="/governance/audit/changes"><AuthenticatedRoute {...tierProps} requiredTier="admin"><p.GovernanceChangeHistory /></AuthenticatedRoute></Route>
    <Route path="/governance/health"><AuthenticatedRoute {...tierProps} requiredTier="admin"><p.HealthMonitor /></AuthenticatedRoute></Route>

    <AliasRedirect from="/trust" to="/governance/traces" Navigate={Navigate} />
    <AliasRedirect from="/trust/traces" to="/governance/traces" Navigate={Navigate} />
    <AliasRedirect from="/trust/evidence" to="/governance/evidence" Navigate={Navigate} />
    <AliasRedirect from="/trust/provenance" to="/governance/provenance" Navigate={Navigate} />
    <AliasRedirect from="/trust/integrity" to="/governance/integrity" Navigate={Navigate} />
    <AliasRedirect from="/trust/compliance" to="/governance/compliance" Navigate={Navigate} />
    <AliasRedirect from="/trust/benchmarks" to="/governance/benchmarks" Navigate={Navigate} />
    <AliasRedirect from="/trust/audit" to="/governance/audit/log" Navigate={Navigate} />
    <AliasRedirect from="/trust/audit/log" to="/governance/audit/log" Navigate={Navigate} />
    <AliasRedirect from="/trust/audit/changes" to="/governance/audit/changes" Navigate={Navigate} />
    <AliasRedirect from="/trust/health" to="/governance/health" Navigate={Navigate} />

    <AliasRedirect from="/evidence" to="/governance/traces" Navigate={Navigate} />
    <AliasRedirect from="/evidence/traces" to="/governance/traces" Navigate={Navigate} />
    <AliasRedirect from="/evidence/export" to="/governance/evidence" Navigate={Navigate} />
    <AliasRedirect from="/evidence/lineage" to="/governance/provenance" Navigate={Navigate} />
    <AliasRedirect from="/evidence/compliance" to="/governance/compliance" Navigate={Navigate} />
    <AliasRedirect from="/evidence/changelog" to="/governance/audit/changes" Navigate={Navigate} />
  </>;
}
