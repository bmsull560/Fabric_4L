/**
 * TieredNav â€” Progressive Synthesis Navigation
 *
 * 7-Domain Left Rail (Navigation Architecture Specification):
 *   1. Accounts     â€” Entry point: select or create a prospect account
 *   2. Intelligence â€” Discovery workspace: Signals â†’ Drivers â†’ Evidence â†’ Stakeholders
 *   3. Value Studio â€” Synthesis workspace: Action Plan â†’ Value Model â†’ Narrative
 *   4. Context Engine â€” Vendor knowledge base: Value Packs, Models, Formulas, Agents
 *   5. Deliverables â€” Activation layer: packaged outputs for sharing
 *   6. Governance   â€” Trust layer: audit, provenance, compliance
 *   7. Settings     â€” Tenant configuration, integrations, user management
 *
 * Three-Layer Model:
 *   Left rail  = Global navigation (this component)
 *   Horiz tabs = Workspace navigation (rendered by workspace shells)
 *   Right rail = Contextual support (rendered by RightRail component)
 *
 * Features:
 *   - Single stable navigation spine that grows with tier
 *   - Progressive disclosure hides advanced items from lower tiers
 *   - Route-aware highlighting
 *   - Tier switcher in footer
 */

import { useState, useMemo, memo } from "react";
import { Link, useLocation } from "wouter";
import { cn } from "@/lib/utils";
import { useAccountContextStore } from "@/stores/accountContextStore";
import {
  Building2,
  Radar,
  GitBranch,
  Package,
  FileOutput,
  Shield,
  Settings,
  ChevronDown,
  ChevronRight,
  Eye,
  Lock,
  Crown,
  Wrench,
} from "lucide-react";

// â”€â”€ Types â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export type UserTier = "standard" | "advanced" | "admin";

export interface NavItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  path: string;
  tier: UserTier;
  children?: NavItem[];
  badge?: string | number;
  description?: string;
}

export interface TieredNavProps {
  currentTier: UserTier;
  onTierChange: (tier: UserTier) => void;
  userRole?: string;
  isAdvancedModeEnabled?: boolean;
  onAdvancedModeToggle?: (enabled: boolean) => void;
}

// â”€â”€ Navigation Spine â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// Single source of truth for the 7-domain left rail.
// Intelligence and Value Studio children are shown here for nav-tree expansion,
// but the actual workspace tabs are rendered by their respective workspace shells.

const NAV_SPINE: NavItem[] = [
  // â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
  // 1. ACCOUNTS â€” Entry Point
  // "Which prospect am I working on?"
  // â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
  {
    id: "accounts",
    label: "Accounts",
    icon: <Building2 size={16} />,
    path: "/accounts",
    tier: "standard",
    description: "Select or create a prospect account",
  },

  // â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
  // 2. INTELLIGENCE â€” Discovery Workspace
  // "What is happening in the prospect's business and why?"
  // â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
  {
    id: "intelligence",
    label: "Intelligence",
    icon: <Radar size={16} />,
    path: "/intelligence",
    tier: "standard",
    description: "Discover and validate prospect pain signals",
    children: [
      {
        id: "signals",
        label: "Signals",
        path: "/intelligence/signals",
        tier: "standard",
      },
      {
        id: "drivers",
        label: "Drivers",
        path: "/intelligence/drivers",
        tier: "standard",
      },
      {
        id: "evidence",
        label: "Evidence",
        path: "/intelligence/evidence",
        tier: "standard",
      },
      {
        id: "stakeholders",
        label: "Stakeholders",
        path: "/intelligence/stakeholders",
        tier: "standard",
      },
    ],
  },

  // â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
  // 3. VALUE STUDIO â€” Synthesis Workspace
  // "How does our product solve the prospect's validated problems?"
  // â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
  {
    id: "studio",
    label: "Value Studio",
    icon: <GitBranch size={16} />,
    path: "/studio",
    tier: "standard",
    description: "Build the product-anchored business case",
    children: [
      {
        id: "action-plan",
        label: "Action Plan",
        path: "/studio/action-plan",
        tier: "standard",
      },
      {
        id: "value-model",
        label: "Value Model",
        path: "/studio/value-model",
        tier: "standard",
      },
      {
        id: "narrative",
        label: "Narrative",
        path: "/studio/narrative",
        tier: "standard",
      },
    ],
  },

  // â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
  // 4. CONTEXT ENGINE â€” Vendor Knowledge Base
  // "What does the vendor know about its own products and proof points?"
  // â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
  {
    id: "context",
    label: "Context Engine",
    icon: <Package size={16} />,
    path: "/context",
    tier: "standard",
    description: "Vendor knowledge: Value Packs, models, formulas",
    children: [
      {
        id: "packs",
        label: "Value Packs",
        path: "/context/packs",
        tier: "standard",
      },
      {
        id: "models",
        label: "Models",
        path: "/context/models",
        tier: "standard",
      },
      {
        id: "value-tree-explorer",
        label: "Tree Explorer",
        path: "/context/value-trees/explorer",
        tier: "advanced",
      },
      {
        id: "formulas",
        label: "Formulas",
        path: "/context/formulas",
        tier: "advanced",
      },
      {
        id: "agents",
        label: "Agents",
        path: "/context/agents",
        tier: "advanced",
      },
      {
        id: "ontology",
        label: "Ontology",
        path: "/context/ontology",
        tier: "advanced",
        children: [
          {
            id: "ontology-editor",
            label: "Schema Editor",
            path: "/context/ontology",
            tier: "advanced",
          },
          {
            id: "entities",
            label: "Entities",
            path: "/context/ontology/entities",
            tier: "advanced",
          },
          {
            id: "graph",
            label: "Graph View",
            path: "/context/ontology/graph",
            tier: "advanced",
          },
        ],
      },
      {
        id: "ingestion",
        label: "Ingestion Jobs",
        path: "/context/ingestion/jobs",
        tier: "advanced",
      },
      {
        id: "extraction",
        label: "Extraction",
        path: "/context/extraction",
        tier: "advanced",
      },
      {
        id: "integrations",
        label: "Integrations",
        path: "/context/integrations",
        tier: "admin",
        badge: "Admin",
      },
      {
        id: "sources",
        label: "Sources",
        path: "/context/sources",
        tier: "admin",
        badge: "Admin",
      },
    ],
  },

  // â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
  // 5. DELIVERABLES â€” Activation Layer
  // "How does the business case reach the prospect?"
  // â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
  {
    id: "deliverables",
    label: "Deliverables",
    icon: <FileOutput size={16} />,
    path: "/deliverables",
    tier: "standard",
    description: "Packaged outputs for sharing with prospects",
    children: [
      {
        id: "cases",
        label: "Business Cases",
        path: "/deliverables/cases",
        tier: "standard",
      },
      {
        id: "calculators",
        label: "Calculators",
        path: "/deliverables/calculators",
        tier: "advanced",
      },
      {
        id: "views",
        label: "Stakeholder Views",
        path: "/deliverables/views",
        tier: "standard",
        children: [
          {
            id: "cfo",
            label: "CFO View",
            path: "/deliverables/views/cfo",
            tier: "standard",
          },
          {
            id: "executive",
            label: "Executive View",
            path: "/deliverables/views/executive",
            tier: "standard",
          },
          {
            id: "technical",
            label: "Technical View",
            path: "/deliverables/views/technical",
            tier: "standard",
          },
        ],
      },
      {
        id: "api",
        label: "API & Webhooks",
        path: "/deliverables/api",
        tier: "admin",
        badge: "Admin",
      },
      {
        id: "embeds",
        label: "Embeds",
        path: "/deliverables/embeds",
        tier: "admin",
        badge: "Admin",
      },
    ],
  },

  // â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
  // 6. MY SETTINGS
  // â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
  {
    id: "my-settings",
    label: "My Settings",
    icon: <Settings size={16} />,
    path: "/my-settings",
    tier: "standard",
    description: "Personal profile and preferences",
    children: [
      { id: "my-profile", label: "Profile", path: "/my-settings/profile", tier: "standard" },
      { id: "my-preferences", label: "Preferences", path: "/my-settings/preferences", tier: "standard" },
      { id: "my-notifications", label: "Notifications", path: "/my-settings/notifications", tier: "standard" },
      { id: "my-appearance", label: "Appearance", path: "/my-settings/appearance", tier: "standard" },
      { id: "my-accounts", label: "Accounts", path: "/my-settings/accounts", tier: "standard" },
    ],
  },
  {
    id: "workspace-settings",
    label: "Workspace Settings",
    icon: <Settings size={16} />,
    path: "/workspace-settings",
    tier: "admin",
    badge: "Admin",
    children: [
      { id: "workspace-integrations", label: "Integrations", path: "/workspace-settings/integrations", tier: "admin" },
      { id: "workspace-sources", label: "Sources", path: "/workspace-settings/sources", tier: "admin" },
    ],
  },
  {
    id: "organization-admin",
    label: "Organization Admin",
    icon: <Shield size={16} />,
    path: "/organization-admin",
    tier: "admin",
    badge: "Admin",
    children: [
      { id: "org-members", label: "Members", path: "/organization-admin/members", tier: "admin" },
      { id: "org-roles", label: "Roles", path: "/organization-admin/roles", tier: "admin" },
      { id: "org-billing", label: "Billing", path: "/organization-admin/billing", tier: "admin" },
      { id: "org-teams", label: "Teams", path: "/organization-admin/teams", tier: "admin" },
    ],
  },
  {
    id: "platform-configuration",
    label: "Platform Configuration",
    icon: <GitBranch size={16} />,
    path: "/platform-configuration",
    tier: "admin",
    badge: "Admin",
    children: [
      { id: "platform-integrations", label: "Integrations", path: "/platform-configuration/integrations", tier: "admin" },
      { id: "platform-api-keys", label: "API Keys", path: "/platform-configuration/api-keys", tier: "admin" },
      { id: "platform-webhooks", label: "Webhooks", path: "/platform-configuration/webhooks", tier: "admin" },
      { id: "platform-model-routing", label: "Model Routing", path: "/platform-configuration/model-routing", tier: "admin" },
      { id: "platform-feature-flags", label: "Feature Flags", path: "/platform-configuration/feature-flags", tier: "admin" },
    ],
  },
  {
    id: "governance-center",
    label: "Governance Center",
    icon: <Shield size={16} />,
    path: "/governance-center",
    tier: "admin",
    badge: "Admin",
    children: [
      { id: "gov-evidence-policy", label: "Evidence Policy", path: "/governance-center/evidence-policy", tier: "admin" },
      { id: "gov-compliance", label: "Compliance", path: "/governance-center/compliance", tier: "admin" },
      { id: "gov-audit-retention", label: "Audit Retention", path: "/governance-center/audit-retention", tier: "admin" },
      { id: "gov-residency", label: "Residency", path: "/governance-center/residency", tier: "admin" },
    ],
  },
  {
    id: "developer-console",
    label: "Developer Console",
    icon: <Wrench size={16} />,
    path: "/developer-console",
    tier: "admin",
    badge: "Admin",
    children: [
      { id: "dev-health", label: "Health", path: "/developer-console/health", tier: "admin" },
      { id: "dev-traces", label: "Traces", path: "/developer-console/traces", tier: "admin" },
      { id: "dev-queue-diagnostics", label: "Queue Diagnostics", path: "/developer-console/queue-diagnostics", tier: "admin" },
      { id: "dev-log-diagnostics", label: "Log Diagnostics", path: "/developer-console/log-diagnostics", tier: "admin" },
    ],
  },
];

// â”€â”€ Styling Constants â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const TIER_STYLES = {
  standard: {
    badge: "bg-primary/10 text-primary border-primary/20",
    icon: "text-primary",
    active: "bg-primary/10 text-primary",
    hover: "hover:bg-primary/5 hover:text-primary",
  },
  advanced: {
    badge: "bg-accent/10 text-accent border-accent/20",
    icon: "text-accent",
    active: "bg-accent/10 text-accent",
    hover: "hover:bg-accent/5 hover:text-accent",
  },
  admin: {
    badge: "bg-destructive/10 text-destructive border-destructive/20",
    icon: "text-destructive",
    active: "bg-destructive/10 text-destructive",
    hover: "hover:bg-destructive/5 hover:text-destructive",
  },
} as const;

const TIER_LABELS: Record<
  UserTier,
  { label: string; description: string; icon: React.ReactNode }
> = {
  standard: {
    label: "Standard",
    description: "Simplified flows for business users",
    icon: <Eye size={14} />,
  },
  advanced: {
    label: "Advanced",
    description: "Power-user modeling & inspection tools",
    icon: <Wrench size={14} />,
  },
  admin: {
    label: "Admin",
    description: "Governance controls & tenant configuration",
    icon: <Crown size={14} />,
  },
};

// â”€â”€ Visibility Filter â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function isItemVisible(item: NavItem, userTier: UserTier): boolean {
  if (userTier === "admin") return true;
  if (userTier === "advanced") return item.tier !== "admin";
  return item.tier === "standard";
}

// â”€â”€ Sub-components â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

interface SidebarItemProps {
  item: NavItem;
  currentTier: UserTier;
  depth?: number;
}

function resolveWorkspacePath(path: string, accountId: string | null): string {
  if (!accountId) return path;

  if (path === "/intelligence") return `/intelligence/${accountId}`;
  if (path.startsWith("/intelligence/")) {
    return path.replace("/intelligence/", `/intelligence/${accountId}/`);
  }

  if (path === "/studio") return `/studio/${accountId}`;
  if (path.startsWith("/studio/")) {
    return path.replace("/studio/", `/studio/${accountId}/`);
  }

  return path;
}

const SidebarItem = memo(function SidebarItem({
  item,
  currentTier,
  depth = 0,
}: SidebarItemProps) {
  const [location] = useLocation();
  const selectedAccountId = useAccountContextStore(
    state => state.selectedAccountId
  );
  const resolvedPath = useMemo(
    () => resolveWorkspacePath(item.path, selectedAccountId),
    [item.path, selectedAccountId]
  );
  const isActive = location.startsWith(resolvedPath);
  const [open, setOpen] = useState(isActive);

  const tierStyle = TIER_STYLES[item.tier];

  const visibleChildren = useMemo(
    () => item.children?.filter(child => isItemVisible(child, currentTier)),
    [item.children, currentTier]
  );
  const hasVisibleChildren = visibleChildren && visibleChildren.length > 0;

  const getIndentClass = (d: number): string => {
    if (d === 0) return "";
    if (d === 1) return "ml-4 mt-1 border-l-2 border-border pl-3 space-y-0.5";
    return "ml-3 pl-2 space-y-0.5";
  };
  const indentClass = getIndentClass(depth);

  return (
    <div className="group">
      <Link href={resolvedPath}>
        <div
          className={cn(
            "flex items-center gap-2.5 px-3 py-2 rounded-lg text-[12px] font-medium transition-all select-none cursor-pointer",
            isActive
              ? tierStyle.active
              : "text-muted-foreground hover:bg-muted hover:text-foreground",
            item.tier === "admin" && !isActive && "hover:bg-destructive/5",
            depth > 0 && "py-1.5 text-[11px]"
          )}
          onClick={e => {
            if (hasVisibleChildren) {
              e.preventDefault();
              setOpen(o => !o);
            }
          }}
        >
          {item.icon && (
            <span
              className={cn(
                "shrink-0",
                isActive
                  ? tierStyle.icon
                  : "text-muted-foreground group-hover:text-muted-foreground/80"
              )}
            >
              {item.icon}
            </span>
          )}
          <span className="flex-1 truncate">{item.label}</span>
          {item.badge && (
            <span
              className={cn(
                "text-[9px] px-1.5 py-0.5 rounded border font-semibold",
                tierStyle.badge
              )}
            >
              {item.badge}
            </span>
          )}
          {hasVisibleChildren && (
            <span className="text-muted-foreground transition-transform">
              {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            </span>
          )}
        </div>
      </Link>

      {hasVisibleChildren && open && (
        <div className={indentClass}>
          {visibleChildren.map(child => (
            <SidebarItem
              key={child.path}
              item={child}
              currentTier={currentTier}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
});

interface TierSwitcherProps {
  currentTier: UserTier;
  onTierChange: (tier: UserTier) => void;
  isAdvancedModeEnabled: boolean;
  onAdvancedModeToggle: (enabled: boolean) => void;
}

function TierSwitcher({
  currentTier,
  onTierChange,
  isAdvancedModeEnabled,
  onAdvancedModeToggle,
}: TierSwitcherProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="border-t border-border bg-card">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-3 py-3 flex items-center gap-3 hover:bg-muted/50 transition-colors"
      >
        <div
          className={cn(
            "w-8 h-8 rounded-lg flex items-center justify-center",
            currentTier === "standard" && "bg-primary/10 text-primary",
            currentTier === "advanced" && "bg-accent/10 text-accent",
            currentTier === "admin" && "bg-destructive/10 text-destructive"
          )}
        >
          {TIER_LABELS[currentTier].icon}
        </div>
        <div className="flex-1 text-left">
          <p className="text-[12px] font-semibold text-foreground">
            {TIER_LABELS[currentTier].label} Mode
          </p>
          <p className="text-[10px] text-muted-foreground truncate">
            {TIER_LABELS[currentTier].description}
          </p>
        </div>
        <ChevronDown
          size={14}
          className={cn(
            "text-muted-foreground transition-transform",
            isExpanded && "rotate-180"
          )}
        />
      </button>

      {isExpanded && (
        <div className="px-3 pb-3 space-y-2">
          <div className="flex items-center justify-between py-2 px-2 bg-muted/50 rounded-lg">
            <div className="flex items-center gap-2">
              <Wrench size={12} className="text-accent" />
              <span className="text-[11px] font-medium text-foreground">
                Advanced Mode
              </span>
            </div>
            <button
              onClick={() => onAdvancedModeToggle(!isAdvancedModeEnabled)}
              className={cn(
                "w-9 h-5 rounded-full transition-colors relative",
                isAdvancedModeEnabled ? "bg-accent" : "bg-muted-foreground/30"
              )}
            >
              <span
                className={cn(
                  "absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform",
                  isAdvancedModeEnabled ? "translate-x-5" : "translate-x-0.5"
                )}
              />
            </button>
          </div>

          <div className="space-y-1">
            {(Object.keys(TIER_LABELS) as UserTier[]).map(tier => (
              <button
                key={tier}
                onClick={() => {
                  onTierChange(tier);
                  setIsExpanded(false);
                }}
                disabled={tier === "admin"}
                className={cn(
                  "w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-[11px] font-medium transition-colors",
                  currentTier === tier
                    ? tier === "standard"
                      ? "bg-primary/10 text-primary"
                      : tier === "advanced"
                        ? "bg-accent/10 text-accent"
                        : "bg-destructive/10 text-destructive"
                    : "text-muted-foreground hover:bg-muted",
                  tier === "admin" && "opacity-50 cursor-not-allowed"
                )}
              >
                <span
                  className={cn(
                    "w-5 h-5 rounded flex items-center justify-center",
                    tier === "standard"
                      ? "bg-primary/10 text-primary"
                      : tier === "advanced"
                        ? "bg-accent/10 text-accent"
                        : "bg-destructive/10 text-destructive"
                  )}
                >
                  {tier === "standard" ? (
                    <Eye size={10} />
                  ) : tier === "advanced" ? (
                    <Wrench size={10} />
                  ) : (
                    <Lock size={10} />
                  )}
                </span>
                <span className="flex-1 text-left">
                  {TIER_LABELS[tier].label}
                </span>
                {tier === "admin" && (
                  <Lock size={10} className="text-muted-foreground" />
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// â”€â”€ Main Component â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export function TieredNav({
  currentTier,
  onTierChange,
  isAdvancedModeEnabled = false,
  onAdvancedModeToggle = () => {},
}: TieredNavProps) {
  const effectiveTier = useMemo<UserTier>(
    () =>
      currentTier === "standard" && isAdvancedModeEnabled
        ? "advanced"
        : currentTier,
    [currentTier, isAdvancedModeEnabled]
  );

  const visibleNavItems = useMemo(
    () => NAV_SPINE.filter(item => isItemVisible(item, effectiveTier)),
    [effectiveTier]
  );

  return (
    <aside className="w-[240px] shrink-0 bg-card border-r border-border overflow-y-auto z-20 flex flex-col h-full">
      <div className="flex-1 py-4 px-2 space-y-1">
        {visibleNavItems.map(item => (
          <SidebarItem key={item.id} item={item} currentTier={currentTier} />
        ))}
      </div>

      <TierSwitcher
        currentTier={currentTier}
        onTierChange={onTierChange}
        isAdvancedModeEnabled={isAdvancedModeEnabled}
        onAdvancedModeToggle={onAdvancedModeToggle}
      />
    </aside>
  );
}

export { NAV_SPINE };
export default TieredNav;

