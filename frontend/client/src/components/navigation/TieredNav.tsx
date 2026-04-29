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
  getSidebarTreeModel,
  isTierVisible,
  resolveWorkspacePath,
  TIER_LABELS as NAV_TIER_LABELS,
  type NavNode,
} from "@/navigation/schema";
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

export interface NavItem extends NavNode {
  icon?: React.ReactNode;
}

export interface TieredNavProps {
  currentTier: UserTier;
  onTierChange: (tier: UserTier) => void;
  userRole?: string;
  isAdvancedModeEnabled?: boolean;
  onAdvancedModeToggle?: (enabled: boolean) => void;
}

const NAV_ICONS: Record<string, React.ReactNode> = {
  accounts: <Building2 size={16} />, intelligence: <Radar size={16} />, studio: <GitBranch size={16} />,
  context: <Package size={16} />, deliverables: <FileOutput size={16} />, governance: <Shield size={16} />, settings: <Settings size={16} />,
};

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

const TIER_LABELS: Record<UserTier, { label: string; description: string; icon: React.ReactNode }> = {
  standard: { label: NAV_TIER_LABELS.standard.label, description: NAV_TIER_LABELS.standard.description, icon: <Eye size={14} /> },
  advanced: { label: NAV_TIER_LABELS.advanced.label, description: NAV_TIER_LABELS.advanced.description, icon: <Wrench size={14} /> },
  admin: { label: NAV_TIER_LABELS.admin.label, description: NAV_TIER_LABELS.admin.description, icon: <Crown size={14} /> },
};

// ── Visibility Filter ─────────────────────────────────────────────────────────

// ── Sub-components ─────────────────────────────────────────────────────────────

interface SidebarItemProps {
  item: NavItem;
  currentTier: UserTier;
  depth?: number;
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

  const tierStyle = TIER_STYLES[(item.tier === "unknown" ? "standard" : item.tier) as "standard" | "advanced" | "admin"];

  const visibleChildren = useMemo(
    () => item.children?.filter(child => isTierVisible(child.tier, currentTier)),
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
    () => getSidebarTreeModel(effectiveTier).filter(item => item.id !== "home").map(item => ({ ...item, icon: NAV_ICONS[item.id] } as NavItem)),
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
