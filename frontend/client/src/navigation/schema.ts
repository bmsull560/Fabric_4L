import type { UserTier } from "@/stores/userTierStore";

export type NavTag = "workspace" | "settings" | "configuration" | "governance";

export interface NavigationRoute {
  id: string;
  label: string;
  path: string;
  tier: Exclude<UserTier, "unknown">;
  badge?: string;
  tags?: NavTag[];
  children?: NavigationRoute[];
}

export const TIER_LABELS: Record<Exclude<UserTier, "unknown">, { label: string; description: string }> = {
  standard: { label: "Standard", description: "Simplified flows for business users" },
  advanced: { label: "Advanced", description: "Power-user modeling & inspection tools" },
  admin: { label: "Admin", description: "Governance controls & tenant configuration" },
};

export const NAVIGATION_SCHEMA: NavigationRoute[] = [
  { id: "home", label: "Home", path: "/home", tier: "standard", tags: ["workspace"] },
  { id: "accounts", label: "Accounts", path: "/accounts", tier: "standard", tags: ["workspace"] },
  { id: "intelligence", label: "Intelligence", path: "/intelligence", tier: "standard", tags: ["workspace"], children: [
    { id: "signals", label: "Signals", path: "/intelligence/signals", tier: "standard" },
    { id: "drivers", label: "Drivers", path: "/intelligence/drivers", tier: "standard" },
    { id: "evidence", label: "Evidence", path: "/intelligence/evidence", tier: "standard" },
    { id: "stakeholders", label: "Stakeholders", path: "/intelligence/stakeholders", tier: "standard" },
  ]},
  { id: "studio", label: "Value Studio", path: "/studio", tier: "standard", tags: ["workspace"], children: [
    { id: "action-plan", label: "Action Plan", path: "/studio/action-plan", tier: "standard" },
    { id: "value-model", label: "Value Model", path: "/studio/value-model", tier: "standard" },
    { id: "narrative", label: "Narrative", path: "/studio/narrative", tier: "standard" },
  ]},
  { id: "context", label: "Context Engine", path: "/context", tier: "standard", tags: ["workspace", "configuration"], children: [
    { id: "packs", label: "Value Packs", path: "/context/packs", tier: "standard" },
    { id: "models", label: "Models", path: "/context/models", tier: "standard" },
    { id: "formulas", label: "Formulas", path: "/context/formulas", tier: "advanced" },
    { id: "ontology", label: "Ontology", path: "/context/ontology", tier: "advanced" },
    { id: "integrations", label: "Integrations", path: "/context/integrations", tier: "admin", badge: "Admin" },
  ]},
  { id: "deliverables", label: "Deliverables", path: "/deliverables", tier: "standard", tags: ["workspace"], children: [
    { id: "cases", label: "Business Cases", path: "/deliverables/cases", tier: "standard" },
    { id: "calculators", label: "Calculators", path: "/deliverables/calculators", tier: "advanced" },
    { id: "cfo", label: "CFO View", path: "/deliverables/views/cfo", tier: "standard" },
  ]},
  { id: "governance", label: "Governance", path: "/governance", tier: "admin", tags: ["governance"], children: [
    { id: "traces", label: "Decision Traces", path: "/governance/traces", tier: "standard" },
    { id: "compliance", label: "Compliance", path: "/governance/compliance", tier: "advanced" },
    { id: "audit-log", label: "Audit Log", path: "/governance/audit/log", tier: "admin", badge: "Admin" },
  ]},
  { id: "settings", label: "Settings", path: "/settings", tier: "admin", tags: ["settings", "configuration"], children: [
    { id: "content-formulas", label: "Formulas", path: "/settings/content/formulas", tier: "admin" },
    { id: "access-roles", label: "Roles", path: "/settings/access/roles", tier: "admin" },
    { id: "system-settings", label: "System", path: "/settings/system/settings", tier: "admin" },
  ]},
];

export function isTierVisible(itemTier: Exclude<UserTier, "unknown">, userTier: Exclude<UserTier, "unknown">): boolean {
  if (userTier === "admin") return true;
  if (userTier === "advanced") return itemTier !== "admin";
  return itemTier === "standard";
}

export function getSidebarTreeModel(userTier: Exclude<UserTier, "unknown">, source: NavigationRoute[] = NAVIGATION_SCHEMA): NavigationRoute[] {
  return source
    .filter(item => isTierVisible(item.tier, userTier))
    .map(item => ({ ...item, children: item.children ? getSidebarTreeModel(userTier, item.children) : undefined }));
}

export function getBreadcrumbLabels(pathname: string): { label: string; path?: string }[] {
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length === 0) return [{ label: "Value Fabric" }];

  const flat = flattenRoutes(NAVIGATION_SCHEMA);
  const crumbs: { label: string; path?: string }[] = [];
  const domainPath = `/${segments[0]}`;
  const domain = flat.find(route => route.path === domainPath);
  crumbs.push({ label: domain?.label ?? titleCase(segments[0]), path: domainPath });

  for (let i = 1; i < segments.length; i++) {
    const seg = segments[i];
    if (/^[0-9a-f-]{8,}$/i.test(seg) || /^\d+$/.test(seg)) continue;
    const currentPath = `/${segments.slice(0, i + 1).join("/")}`;
    const route = flat.find(entry => entry.path === currentPath);
    crumbs.push({ label: route?.label ?? titleCase(seg), path: currentPath });
  }

  return crumbs;
}

export function getTaggedSlice(tag: NavTag): NavigationRoute[] {
  return NAVIGATION_SCHEMA.filter(route => route.tags?.includes(tag));
}

export const getSettingsSlice = () => getTaggedSlice("settings");
export const getConfigurationSlice = () => getTaggedSlice("configuration");
export const getGovernanceSlice = () => getTaggedSlice("governance");

function flattenRoutes(routes: NavigationRoute[]): NavigationRoute[] {
  return routes.flatMap(route => [route, ...(route.children ? flattenRoutes(route.children) : [])]);
}

function titleCase(value: string): string {
  return value.split("-").map(part => part.charAt(0).toUpperCase() + part.slice(1)).join(" ");
}
