import type * as React from "react";
import {
  Building2, Radar, GitBranch, Package, FileOutput, Shield, Settings, Frame,
} from "lucide-react";
import type { UserTier } from "@/hooks";

export interface NavRoute {
  id: string;
  label: string;
  icon?: React.ElementType;
  path: string;
  tier: UserTier;
  breadcrumbLabel?: string;
  badge?: string;
  description?: string;
  children?: NavRoute[];
}

export const NAV_DOMAINS: NavRoute[] = [
  { id: "home", label: "Home", icon: Frame, path: "/home", tier: "standard", description: "Dashboard & prospect prompt builder" },
  { id: "accounts", label: "Accounts", icon: Building2, path: "/accounts", tier: "standard", description: "Select or create a prospect account" },
  {
    id: "intelligence", label: "Intelligence", icon: Radar, path: "/intelligence/:accountId", tier: "standard", description: "Discover and validate prospect pain signals",
    children: [
      { id: "intel-signals", label: "Signals", path: "/intelligence/:accountId/signals", tier: "standard" },
      { id: "intel-drivers", label: "Drivers", path: "/intelligence/:accountId/drivers", tier: "standard" },
      { id: "intel-evidence", label: "Evidence", path: "/intelligence/:accountId/evidence", tier: "standard" },
      { id: "intel-stakeholders", label: "Stakeholders", path: "/intelligence/:accountId/stakeholders", tier: "standard" },
      { id: "intel-enrichment", label: "Enrichment", path: "/intelligence/:accountId/enrichment", tier: "advanced" },
      { id: "intel-hypotheses", label: "Hypotheses", path: "/intelligence/:accountId/hypotheses", tier: "advanced" },
      { id: "intel-competitive", label: "Competitive", path: "/intelligence/:accountId/competitive", tier: "advanced" },
      { id: "intel-roi", label: "ROI", path: "/intelligence/:accountId/roi", tier: "advanced" },
      { id: "intel-evidence-library", label: "Evidence Library", path: "/intelligence/:accountId/evidence-library", tier: "advanced" },
    ],
  },
  {
    id: "studio", label: "Value Studio", icon: GitBranch, path: "/studio/:accountId", tier: "advanced", description: "Build the product-anchored business case",
    children: [
      { id: "studio-action-plan", label: "Action Plan", path: "/studio/:accountId/action-plan", tier: "standard" },
      { id: "studio-value-model", label: "Value Model", path: "/studio/:accountId/value-model", tier: "standard" },
      { id: "studio-narrative", label: "Narrative", path: "/studio/:accountId/narrative", tier: "standard" },
      { id: "studio-enrichment", label: "Enrichment", path: "/studio/:accountId/enrichment", tier: "advanced" },
      { id: "studio-competitive", label: "Competitive", path: "/studio/:accountId/competitive", tier: "advanced" },
      { id: "studio-roi", label: "ROI", path: "/studio/:accountId/roi", tier: "advanced" },
      { id: "studio-evidence", label: "Evidence", path: "/studio/:accountId/evidence", tier: "advanced" },
    ],
  },
  { id: "context", label: "Context Engine", icon: Package, path: "/context", tier: "advanced", description: "Vendor knowledge: Value Packs, models, formulas", children: [
    { id: "packs", label: "Value Packs", path: "/context/packs", tier: "standard" }, { id: "models", label: "Models", path: "/context/models", tier: "standard" }, { id: "value-trees", label: "Tree Explorer", path: "/context/value-trees/explorer", tier: "advanced" }, { id: "formulas", label: "Formulas", path: "/context/formulas", tier: "advanced" }, { id: "agents", label: "Agents", path: "/context/agents", tier: "advanced" }, { id: "ontology", label: "Ontology", path: "/context/ontology", tier: "advanced" }, { id: "ingestion", label: "Ingestion", path: "/context/ingestion/jobs", tier: "advanced" }, { id: "extraction", label: "Extraction", path: "/context/extraction", tier: "advanced" }, { id: "integrations", label: "Integrations", path: "/context/integrations", tier: "admin", badge: "Admin" }, { id: "sources", label: "Sources", path: "/context/sources", tier: "admin", badge: "Admin" },
  ] },
  { id: "deliverables", label: "Deliverables", icon: FileOutput, path: "/deliverables", tier: "standard", description: "Packaged outputs for sharing with prospects", children: [
    { id: "cases", label: "Business Cases", path: "/deliverables/cases", tier: "standard" }, { id: "calculators", label: "Calculators", path: "/deliverables/calculators", tier: "advanced" }, { id: "cfo", label: "CFO View", path: "/deliverables/views/cfo", tier: "standard" }, { id: "executive", label: "Executive View", path: "/deliverables/views/executive", tier: "standard" }, { id: "technical", label: "Technical View", path: "/deliverables/views/technical", tier: "standard" },
  ] },
  { id: "governance", label: "Governance", icon: Shield, path: "/governance", tier: "admin", children: [
    { id: "traces", label: "Decision Traces", path: "/governance/traces", tier: "standard" }, { id: "evidence-gov", label: "Evidence", path: "/governance/evidence", tier: "standard" }, { id: "provenance", label: "Provenance", path: "/governance/provenance", tier: "advanced" }, { id: "integrity", label: "Integrity", path: "/governance/integrity", tier: "advanced" }, { id: "compliance", label: "Compliance", path: "/governance/compliance", tier: "advanced" }, { id: "benchmarks", label: "Benchmarks", path: "/governance/benchmarks", tier: "admin", badge: "Admin" }, { id: "audit-log", label: "Audit Log", path: "/governance/audit/log", tier: "admin", badge: "Admin" }, { id: "health", label: "System Health", path: "/governance/health", tier: "admin", badge: "Admin" },
  ] },
];

export const SUPPORT_ITEMS: NavRoute[] = [{ id: "settings", label: "Settings", icon: Settings, path: "/settings", tier: "admin", children: [
  { id: "content-formulas", label: "Formulas", path: "/settings/content/formulas", tier: "admin" }, { id: "data-variables", label: "Variables", path: "/settings/data/variables", tier: "admin" }, { id: "access-roles", label: "Roles", path: "/settings/access/roles", tier: "admin" }, { id: "system-settings", label: "System", path: "/settings/system/settings", tier: "admin" }, { id: "system-billing", label: "Billing", path: "/settings/system/billing", tier: "admin" },
] }];

const isOpaqueId = (segment: string) => /^[0-9a-f]{8,}$/i.test(segment) || /^\d+$/.test(segment);

const flatten = (routes: NavRoute[], out: NavRoute[] = []): NavRoute[] => {
  for (const r of routes) {
    out.push(r);
    if (r.children) flatten(r.children, out);
  }
  return out;
};

const matchesPattern = (pattern: string, path: string): boolean => {
  const p1 = pattern.split("/").filter(Boolean);
  const p2 = path.split("/").filter(Boolean);

  if (p2.length > p1.length) return false;
  if (!p2.every((seg, i) => p1[i]?.startsWith(":") || p1[i] === seg)) return false;

  return p1.slice(p2.length).every(seg => seg.startsWith(":"));
};

export function resolveWorkspacePath(path: string, accountId: string | null): string {
  if (path.includes(":accountId")) {
    return accountId ? path.replace(":accountId", accountId) : path.replace("/:accountId", "");
  }
  return path;
}

export function resolveBreadcrumbs(pathname: string): { label: string; path?: string }[] {
  const all = flatten([...NAV_DOMAINS, ...SUPPORT_ITEMS]);
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length === 0) return [{ label: "Value Fabric" }];

  const crumbs: { label: string; path?: string }[] = [];
  for (let i = 1; i <= segments.length; i++) {
    const partial = `/${segments.slice(0, i).join("/")}`;
    const match = all.find(r => matchesPattern(r.path, partial));
    const current = segments[i - 1];
    if (!match && isOpaqueId(current)) continue;
    crumbs.push({
      label: match?.breadcrumbLabel ?? match?.label ?? current.split("-").map(w => w[0]?.toUpperCase() + w.slice(1)).join(" "),
      path: match ? partial : undefined,
    });
  }
  return crumbs;
}
