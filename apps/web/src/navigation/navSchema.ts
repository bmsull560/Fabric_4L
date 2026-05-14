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
      { id: "intel-stakeholders", label: "Stakeholders", path: "/intelligence/:accountId/stakeholders", tier: "standard" },
      { id: "intel-enrichment", label: "Enrichment", path: "/intelligence/:accountId/enrichment", tier: "advanced" },
      { id: "intel-ontology-match", label: "Value Ontology", path: "/intelligence/:accountId/ontology-match", tier: "advanced" },
    ],
  },
  {
    id: "hypothesis", label: "Hypothesis", path: "/hypothesis", tier: "standard", description: "AI-generated value hypotheses",
    children: [
      { id: "hypo-main", label: "Opportunities / Value Paths", path: "/hypothesis/:accountId/hypothesis", tier: "standard" },
      { id: "hypo-discovery", label: "Discovery Questions", path: "/hypothesis/:accountId/discovery-questions", tier: "standard" },
      { id: "hypo-persona", label: "Persona Fit", path: "/hypothesis/:accountId/persona-fit", tier: "standard" },
      { id: "hypo-assumptions", label: "Assumptions", path: "/hypothesis/:accountId/assumptions", tier: "standard" },
    ],
  },
  {
    id: "drivers", label: "Driver Tree", path: "/drivers", tier: "standard", description: "Value driver tree and evidence mapping",
    children: [
      { id: "driver-tree", label: "Driver Tree", path: "/drivers/:accountId", tier: "standard" },
      { id: "driver-tab", label: "Driver Tab", path: "/drivers/:accountId/:tab", tier: "standard" },
    ],
  },
  {
    id: "calculator", label: "Calculator", path: "/calculator", tier: "standard", description: "ROI and value modeling",
    children: [
      { id: "calc-roi", label: "Scenarios", path: "/calculator/:accountId/roi", tier: "standard" },
      { id: "calc-value-model", label: "Value Model", path: "/calculator/:accountId/value-model", tier: "standard" },
    ],
  },
  {
    id: "value-case", label: "Value Case", path: "/value-case", tier: "standard", description: "Business case generation",
    children: [
      { id: "vc-main", label: "Business Case", path: "/value-case/:accountId", tier: "standard" },
    ],
  },
  {
    id: "realization", label: "Realization", path: "/realization", tier: "standard", description: "Value realization plan",
    children: [
      { id: "real-main", label: "Realization", path: "/realization/:accountId", tier: "standard" },
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

const ROUTE_ALIASES: Record<string, string> = {
  "/hypothesis/:accountId": "/hypothesis/:accountId/hypothesis",
  "/drivers/:accountId/evidence": "/drivers/:accountId/evidence",
  "/calculator/:accountId": "/calculator/:accountId/roi",
};

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

function resolveAliasPath(pathname: string): string {
  const aliasEntry = Object.entries(ROUTE_ALIASES).find(([alias]) => routeMatches(alias, pathname));
  if (!aliasEntry) return pathname;

  const [alias, canonical] = aliasEntry;
  const aliasParts = alias.split("/").filter(Boolean);
  const pathParts = pathname.split("/").filter(Boolean);
  const replacements = new Map<string, string>();

  aliasParts.forEach((seg, idx) => {
    if (seg.startsWith(":")) replacements.set(seg, pathParts[idx] || "");
  });

  return canonical
    .split("/")
    .filter(Boolean)
    .map((seg) => (seg.startsWith(":") ? replacements.get(seg) || seg : seg))
    .join("/")
    .replace(/^/, "/");
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
  pathname = resolveAliasPath(pathname);
  const pathSegments = pathname.split("/").filter(Boolean);
  if (pathSegments.length === 0) return [{ label: "Value Fabric" }];

  const nodes = flatten(NAV_SCHEMA);
  const crumbs: BreadcrumbItem[] = [];

  for (let i = 0; i < pathSegments.length; i++) {
    const segmentPath = ['', ...pathSegments.slice(0, i + 1)].join('/');
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
