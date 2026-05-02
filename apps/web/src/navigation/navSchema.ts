import type { UserTier } from "@/hooks";

export interface NavSchemaNode {
  id: string;
  label: string;
  path: string;
  tier: UserTier;
  badge?: string;
  description?: string;
  breadcrumbLabel?: string;
  children?: NavSchemaNode[];
}

export const NAV_SCHEMA: NavSchemaNode[] = [
  { id: "home", label: "Home", path: "/home", tier: "standard", description: "Dashboard & prospect prompt builder" },
  { id: "accounts", label: "Accounts", path: "/accounts", tier: "standard", description: "Select or create a prospect account" },
  {
    id: "intelligence", label: "Intelligence", path: "/intelligence", tier: "standard", description: "Discover and validate prospect pain signals",
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
    id: "studio", label: "Value Studio", path: "/studio", tier: "advanced", description: "Build the product-anchored business case",
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
];

export interface BreadcrumbItem { label: string; path?: string }

function flatten(nodes: NavSchemaNode[]): NavSchemaNode[] {
  return nodes.flatMap((node) => [node, ...(node.children ? flatten(node.children) : [])]);
}

function segmentMatches(patternSeg: string, actualSeg: string): boolean {
  if (patternSeg.startsWith(":")) return Boolean(actualSeg);
  return patternSeg === actualSeg;
}

function routeMatches(pattern: string, actual: string): boolean {
  const p = pattern.split("/").filter(Boolean);
  const a = actual.split("/").filter(Boolean);
  if (p.length !== a.length) return false;
  return p.every((seg, i) => segmentMatches(seg, a[i] || ""));
}


function isDynamicPrefixSegment(pathname: string): boolean {
  const actual = pathname.split("/").filter(Boolean);
  const nodes = flatten(NAV_SCHEMA);
  return nodes.some((node) => {
    const pattern = node.path.split("/").filter(Boolean);
    if (actual.length > pattern.length) return false;
    const targetIndex = actual.length - 1;
    if (targetIndex < 0 || !pattern[targetIndex]?.startsWith(":")) return false;
    return actual.every((_, idx) => segmentMatches(pattern[idx] || "", actual[idx] || ""));
  });
}
function labelForSegment(segment: string): string {
  return segment.split("-").map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" ");
}

export function resolveBreadcrumbs(pathname: string): BreadcrumbItem[] {
  const pathSegments = pathname.split("/").filter(Boolean);
  if (pathSegments.length === 0) return [{ label: "Value Fabric" }];

  const nodes = flatten(NAV_SCHEMA);
  const crumbs: BreadcrumbItem[] = [];

  for (let i = 0; i < pathSegments.length; i++) {
    const segmentPath = `/${pathSegments.slice(0, i + 1).join("/")}`;
    const matched = nodes.find((node) => routeMatches(node.path, segmentPath));
    if (matched) {
      crumbs.push({
        label: matched.breadcrumbLabel ?? matched.label,
        path: segmentPath,
      });
      continue;
    }

    const segment = pathSegments[i] || "";
    const isOpaqueId = /^[0-9a-f-]{8,}$/i.test(segment) || /^\d+$/.test(segment);
    const dynamicSegment = isDynamicPrefixSegment(segmentPath);
    if (isOpaqueId || dynamicSegment) continue;

    crumbs.push({ label: labelForSegment(segment), path: segmentPath });
  }

  const deduped: BreadcrumbItem[] = [];
  for (const crumb of crumbs) {
    if (!deduped.some((item) => item.path === crumb.path && item.label === crumb.label)) deduped.push(crumb);
  }
  return deduped;
}
