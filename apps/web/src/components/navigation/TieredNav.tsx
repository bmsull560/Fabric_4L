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

import { useState, useMemo, memo, useEffect } from "react";
import {
  resolveWorkspacePath,
  isItemVisible,
  isRouteActive,
  type NavItem,
  type UserTier,
} from "@/navigation/navigationService";
export type { UserTier } from "@/navigation/navigationService";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useAccountContextStore } from "@/stores/accountContextStore";
import { useWorkflowSessionStore } from "@/stores/workflowSessionStore";
import {
  Building2,
  Radar,
  GitBranch,
  Settings,
  ChevronDown,
  ChevronRight,
  Eye,
  Lock,
  Crown,
  Wrench,
  Lightbulb,
  Calculator,
  FileText,
  TrendingUp,
  RotateCcw,
} from "lucide-react";

// â”€â”€ Types â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



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
  // ─── 1. HOME ──────────────────────────────────────────────────────────────────
  {
    id: "home",
    label: "Home",
    icon: <Building2 size={16} />,
    path: "/home",
    tier: "standard",
    description: "Dashboard overview",
  },
  // ─── 2. ACCOUNTS ──────────────────────────────────────────────────────────────
  {
    id: "accounts",
    label: "Accounts",
    icon: <Building2 size={16} />,
    path: "/accounts",
    tier: "standard",
    description: "Manage prospect accounts",
  },
  // ─── 3. INTELLIGENCE ──────────────────────────────────────────────────────────
  // Tabs (rendered by IntelligenceShell): Signals, Stakeholder Map, Ontology Match, Enrichment
  {
    id: "intelligence",
    label: "Intelligence",
    icon: <Radar size={16} />,
    path: "/intelligence",
    tier: "standard",
    description: "AI-enriched prospect profile: signals, stakeholders, ontology",
  },
  // ─── 4. HYPOTHESIS ────────────────────────────────────────────────────────────
  {
    id: "hypothesis",
    label: "Hypothesis",
    icon: <Lightbulb size={16} />,
    path: "/hypothesis",
    tier: "standard",
    description: "AI-generated value hypotheses for the account",
  },
  // ─── 5. DRIVER TREE ───────────────────────────────────────────────────────────
  // Tabs (rendered by DriverTreeShell): Evidence, Alternatives, Solution Cost
  {
    id: "drivers",
    label: "Driver Tree",
    icon: <GitBranch size={16} />,
    path: "/drivers",
    tier: "standard",
    description: "Map signals to business value drivers with evidence",
  },
  // ─── 6. CALCULATOR ────────────────────────────────────────────────────────────
  {
    id: "calculator",
    label: "Calculator",
    icon: <Calculator size={16} />,
    path: "/calculator",
    tier: "standard",
    description: "ROI calculator and value model",
  },
  // ─── 7. VALUE CASE ────────────────────────────────────────────────────────────
  {
    id: "value-case",
    label: "Value Case",
    icon: <FileText size={16} />,
    path: "/value-case",
    tier: "standard",
    description: "Generated narrative and executive value case",
  },
  // ─── 8. VALUE REALIZATION ─────────────────────────────────────────────────────
  {
    id: "realization",
    label: "Value Realization",
    icon: <TrendingUp size={16} />,
    path: "/realization",
    tier: "standard",
    description: "Track realized value post-sale",
  },
  // ─── SETUP ────────────────────────────────────────────────────────────────────
  {
    id: "setup",
    label: "Setup",
    icon: <Wrench size={16} />,
    path: "/workflow/prospect",
    tier: "standard",
    description: "Prospect setup and configuration",
  },
  {
    id: "resume-workflow",
    label: "Resume Last Workflow",
    icon: <RotateCcw size={16} />,
    path: "/intelligence",
    tier: "standard",
    description: "Jump back to the most recent workflow location",
  },
  // ─── SETTINGS (Admin) ─────────────────────────────────────────────────────────
  {
    id: "settings",
    label: "Settings",
    icon: <Settings size={16} />,
    path: "/settings",
    tier: "admin",
    badge: "Admin",
    description: "Tenant configuration and administration",
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



// â”€â”€ Sub-components â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
  const location = useLocation().pathname;
  const selectedAccountId = useAccountContextStore(
    state => state.selectedAccountId
  );
  const resumePath = useWorkflowSessionStore((state) => state.context.lastPath);
  const resolvedPath = useMemo(
    () => item.id === "resume-workflow"
      ? (resumePath ?? resolveWorkspacePath(item.path, selectedAccountId))
      : resolveWorkspacePath(item.path, selectedAccountId),
    [item.id, item.path, resumePath, selectedAccountId]
  );
  const isActive = isRouteActive(location, resolvedPath);
  const [open, setOpen] = useState(isActive);
  useEffect(() => { setOpen(isActive); }, [isActive]);

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
      <Link to={resolvedPath}>
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
