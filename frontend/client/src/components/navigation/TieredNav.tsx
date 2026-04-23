/**
 * TieredNav — Progressive Synthesis Navigation
 *
 * 7-Domain Left Rail (Navigation Architecture Specification):
 *   1. Accounts     — Entry point: select or create a prospect account
 *   2. Intelligence — Discovery workspace: Signals → Drivers → Evidence → Stakeholders
 *   3. Value Studio — Synthesis workspace: Action Plan → Value Model → Narrative
 *   4. Context Engine — Vendor knowledge base: Value Packs, Models, Formulas, Agents
 *   5. Deliverables — Activation layer: packaged outputs for sharing
 *   6. Governance   — Trust layer: audit, provenance, compliance
 *   7. Settings     — Tenant configuration, integrations, user management
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

// ── Types ─────────────────────────────────────────────────────────────────────

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

// ── Navigation Spine ─────────────────────────────────────────────────────────
// Single source of truth for the 7-domain left rail.
// Intelligence and Value Studio children are shown here for nav-tree expansion,
// but the actual workspace tabs are rendered by their respective workspace shells.

const NAV_SPINE: NavItem[] = [
  // ═══════════════════════════════════════════════════════════════════════════
  // 1. ACCOUNTS — Entry Point
  // "Which prospect am I working on?"
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: "accounts",
    label: "Accounts",
    icon: <Building2 size={16} />,
    path: "/accounts",
    tier: "standard",
    description: "Select or create a prospect account",
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // 2. INTELLIGENCE — Discovery Workspace
  // "What is happening in the prospect's business and why?"
  // ═══════════════════════════════════════════════════════════════════════════
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

  // ═══════════════════════════════════════════════════════════════════════════
  // 3. VALUE STUDIO — Synthesis Workspace
  // "How does our product solve the prospect's validated problems?"
  // ═══════════════════════════════════════════════════════════════════════════
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

  // ═══════════════════════════════════════════════════════════════════════════
  // 4. CONTEXT ENGINE — Vendor Knowledge Base
  // "What does the vendor know about its own products and proof points?"
  // ═══════════════════════════════════════════════════════════════════════════
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

  // ═══════════════════════════════════════════════════════════════════════════
  // 5. DELIVERABLES — Activation Layer
  // "How does the business case reach the prospect?"
  // ═══════════════════════════════════════════════════════════════════════════
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

  // ═══════════════════════════════════════════════════════════════════════════
  // 6. GOVERNANCE — Trust Layer
  // "Can I trust this, and can I prove it?"
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: "governance",
    label: "Governance",
    icon: <Shield size={16} />,
    path: "/governance",
    tier: "standard",
    description: "Audit, provenance, and compliance",
    children: [
      {
        id: "traces",
        label: "Decision Traces",
        path: "/governance/traces",
        tier: "standard",
      },
      {
        id: "evidence-gov",
        label: "Evidence",
        path: "/governance/evidence",
        tier: "standard",
      },
      {
        id: "provenance",
        label: "Provenance",
        path: "/governance/provenance",
        tier: "advanced",
      },
      {
        id: "integrity",
        label: "Integrity",
        path: "/governance/integrity",
        tier: "advanced",
      },
      {
        id: "compliance",
        label: "Compliance",
        path: "/governance/compliance",
        tier: "advanced",
      },
      {
        id: "benchmarks",
        label: "Benchmarks",
        path: "/governance/benchmarks",
        tier: "admin",
        badge: "Admin",
      },
      {
        id: "audit",
        label: "Audit",
        path: "/governance/audit",
        tier: "admin",
        badge: "Admin",
        children: [
          {
            id: "audit-log",
            label: "Audit Log",
            path: "/governance/audit/log",
            tier: "admin",
          },
          {
            id: "changes",
            label: "Change History",
            path: "/governance/audit/changes",
            tier: "admin",
          },
        ],
      },
      {
        id: "health",
        label: "System Health",
        path: "/governance/health",
        tier: "admin",
        badge: "Admin",
      },
    ],
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // 7. SETTINGS — Tenant Configuration
  // "How is the platform configured?"
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: "settings",
    label: "Settings",
    icon: <Settings size={16} />,
    path: "/settings",
    tier: "admin",
    description: "Platform configuration and user management",
    badge: "Admin",
    children: [
      {
        id: "content",
        label: "Content",
        path: "/settings/content",
        tier: "admin",
        children: [
          {
            id: "formula-registry",
            label: "Formula Registry",
            path: "/settings/content/formulas",
            tier: "admin",
          },
          {
            id: "versions",
            label: "Version History",
            path: "/settings/content/versions",
            tier: "admin",
          },
          {
            id: "approvals",
            label: "Approval Queue",
            path: "/settings/content/approvals",
            tier: "admin",
          },
        ],
      },
      {
        id: "data",
        label: "Data",
        path: "/settings/data",
        tier: "admin",
        children: [
          {
            id: "variables",
            label: "Variable Registry",
            path: "/settings/data/variables",
            tier: "admin",
          },
          {
            id: "bindings",
            label: "Source Bindings",
            path: "/settings/data/bindings",
            tier: "admin",
          },
          {
            id: "quality",
            label: "Quality Rules",
            path: "/settings/data/quality",
            tier: "admin",
          },
        ],
      },
      {
        id: "access",
        label: "Access",
        path: "/settings/access",
        tier: "admin",
        children: [
          {
            id: "roles",
            label: "Roles & Permissions",
            path: "/settings/access/roles",
            tier: "admin",
          },
          {
            id: "teams",
            label: "Teams",
            path: "/settings/access/teams",
            tier: "admin",
          },
          {
            id: "keys",
            label: "API Keys",
            path: "/settings/access/keys",
            tier: "admin",
          },
        ],
      },
      {
        id: "system",
        label: "System",
        path: "/settings/system",
        tier: "admin",
        children: [
          {
            id: "system-settings",
            label: "Settings",
            path: "/settings/system/settings",
            tier: "admin",
          },
          {
            id: "system-billing",
            label: "Billing",
            path: "/settings/system/billing",
            tier: "admin",
          },
          {
            id: "system-billing-usage",
            label: "Usage",
            path: "/settings/system/billing/usage",
            tier: "admin",
          },
          {
            id: "system-billing-invoices",
            label: "Invoices",
            path: "/settings/system/billing/invoices",
            tier: "admin",
          },
          {
            id: "system-billing-payments",
            label: "Payments",
            path: "/settings/system/billing/payments",
            tier: "admin",
          },
        ],
      },
    ],
  },
];

// ── Styling Constants ──────────────────────────────────────────────────────────

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

// ── Visibility Filter ─────────────────────────────────────────────────────────

function isItemVisible(item: NavItem, userTier: UserTier): boolean {
  if (userTier === "admin") return true;
  if (userTier === "advanced") return item.tier !== "admin";
  return item.tier === "standard";
}

// ── Sub-components ─────────────────────────────────────────────────────────────

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

// ── Main Component ─────────────────────────────────────────────────────────────

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

export default TieredNav;
