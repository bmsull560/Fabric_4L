/**
 * TieredNav — Single-Spine Navigation with Progressive Disclosure
 *
 * Navigation Taxonomy:
 * - Home: Dashboard (all tiers)
 * - Library: Content catalog (all tiers)
 * - Discover: Research & data (Tier 1+ with progressive disclosure)
 * - Model: Build value models (Tier 2+)
 * - Deliver: Output & workflows (all tiers)
 * - Evidence: Audit & provenance (all tiers)
 * - Govern: Admin controls (Tier 3)
 *
 * Features:
 * - Single stable navigation spine that grows with tier
 * - Progressive disclosure hides advanced items from lower tiers
 * - Route-aware highlighting
 * - Tier switcher in footer
 */

import { useState, useCallback, useMemo, memo } from "react";
import { Link, useLocation } from "wouter";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, Search, ChevronDown, ChevronRight,
  Briefcase, Shield, GitBranch,
  Settings, Package, Eye, Lock, Crown, Wrench
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

// ── Single Navigation Spine ───────────────────────────────────────────────────

/**
 * NAV_SPINE — Single source of truth for all navigation
 * Progressive disclosure: items filtered by user tier at render time
 */
const NAV_SPINE: NavItem[] = [
  {
    id: "home",
    label: "Home",
    icon: <LayoutDashboard size={16}/>,
    path: "/home",
    tier: "standard",
    description: "Dashboard and quick actions"
  },
  {
    id: "library",
    label: "Library",
    icon: <Package size={16}/>,
    path: "/library",
    tier: "standard",
    description: "Content catalog and value packs",
    children: [
      { id: "packs", label: "Value Packs", path: "/library/packs", tier: "standard" },
      { id: "models", label: "My Models", path: "/library/models", tier: "standard" },
      { id: "authoring", label: "Pack Authoring", path: "/library/authoring", tier: "admin", badge: "Admin" }
    ]
  },
  {
    id: "discover",
    label: "Discover",
    icon: <Search size={16}/>,
    path: "/discover",
    tier: "standard",
    description: "Research accounts and manage data",
    children: [
      { id: "accounts", label: "Accounts", path: "/discover/accounts", tier: "standard" },
      { id: "jobs", label: "Ingestion Jobs", path: "/discover/jobs", tier: "standard" },
      { id: "extraction", label: "Extraction Engine", path: "/discover/extraction", tier: "advanced" },
      {
        id: "knowledge",
        label: "Knowledge Model",
        path: "/discover/knowledge",
        tier: "advanced",
        children: [
          { id: "entities", label: "Entity Browser", path: "/discover/knowledge/entities", tier: "advanced" },
          { id: "graph", label: "Graph Explorer", path: "/discover/knowledge/graph", tier: "advanced" },
          { id: "ontology", label: "Ontology Editor", path: "/discover/knowledge/ontology", tier: "advanced" }
        ]
      },
      { id: "integrations", label: "Integrations", path: "/discover/integrations", tier: "admin", badge: "Admin" },
      { id: "sources", label: "Source Configuration", path: "/discover/sources", tier: "admin", badge: "Admin" }
    ]
  },
  {
    id: "model",
    label: "Model",
    icon: <GitBranch size={16}/>,
    path: "/model",
    tier: "advanced",
    description: "Build value trees and formulas",
    children: [
      {
        id: "value-studio",
        label: "Value Studio",
        path: "/model/value-studio",
        tier: "advanced",
        children: [
          { id: "explorer", label: "Explorer", path: "/model/value-studio/explorer", tier: "advanced" },
          { id: "normalization", label: "Normalization", path: "/model/value-studio/normalization", tier: "advanced" },
          { id: "formulas", label: "Formula Builder", path: "/model/value-studio/formulas", tier: "advanced" }
        ]
      }
    ]
  },
  {
    id: "deliver",
    label: "Deliver",
    icon: <Briefcase size={16}/>,
    path: "/deliver",
    tier: "standard",
    description: "Output business cases and workflows",
    children: [
      { id: "cases", label: "Business Cases", path: "/deliver/cases", tier: "standard" },
      { id: "opportunities", label: "Opportunity Finder", path: "/deliver/opportunities", tier: "standard" },
      { id: "whitespace", label: "Whitespace Analysis", path: "/deliver/whitespace", tier: "advanced" },
      { id: "agents", label: "Agent Dashboard", path: "/deliver/agents", tier: "advanced" },
      { id: "explore", label: "Interactive Explorer", path: "/deliver/cases/explore", tier: "advanced" }
    ]
  },
  {
    id: "evidence",
    label: "Evidence",
    icon: <Shield size={16}/>,
    path: "/evidence",
    tier: "standard",
    description: "Audit trails and compliance proof",
    children: [
      { id: "traces", label: "Decision Traces", path: "/evidence/traces", tier: "standard" },
      { id: "export", label: "Export Reports", path: "/evidence/export", tier: "standard" },
      { id: "lineage", label: "Lineage Explorer", path: "/evidence/lineage", tier: "advanced" },
      { id: "compliance", label: "Compliance Reports", path: "/evidence/compliance", tier: "advanced" },
      { id: "changelog", label: "Full Change Log", path: "/evidence/changelog", tier: "admin", badge: "Admin" }
    ]
  },
  {
    id: "govern",
    label: "Govern",
    icon: <Settings size={16}/>,
    path: "/admin",
    tier: "admin",
    description: "Platform governance and configuration",
    badge: "Admin",
    children: [
      {
        id: "content",
        label: "Content Governance",
        path: "/admin/content",
        tier: "admin",
        children: [
          { id: "formulas", label: "Formula Registry", path: "/admin/content/formulas", tier: "admin" },
          { id: "versions", label: "Version History", path: "/admin/content/versions", tier: "admin" },
          { id: "approvals", label: "Approval Queue", path: "/admin/content/approvals", tier: "admin" },
          { id: "benchmarks", label: "Benchmark Policies", path: "/admin/content/benchmarks", tier: "admin" }
        ]
      },
      {
        id: "data",
        label: "Data Governance",
        path: "/admin/data",
        tier: "admin",
        children: [
          { id: "variables", label: "Variable Registry", path: "/admin/data/variables", tier: "admin" },
          { id: "bindings", label: "Source Bindings", path: "/admin/data/bindings", tier: "admin" },
          { id: "quality", label: "Quality Rules", path: "/admin/data/quality", tier: "admin" }
        ]
      },
      {
        id: "access",
        label: "Access Control",
        path: "/admin/access",
        tier: "admin",
        children: [
          { id: "roles", label: "Roles & Permissions", path: "/admin/access/roles", tier: "admin" },
          { id: "teams", label: "Teams", path: "/admin/access/teams", tier: "admin" },
          { id: "keys", label: "API Keys", path: "/admin/access/keys", tier: "admin" }
        ]
      },
      {
        id: "system",
        label: "System",
        path: "/admin/system",
        tier: "admin",
        children: [
          { id: "settings", label: "Platform Settings", path: "/admin/system/settings", tier: "admin" },
          { id: "audit", label: "Audit Log", path: "/admin/system/audit", tier: "admin" },
          { id: "health", label: "Health Monitor", path: "/admin/system/health", tier: "admin" }
        ]
      }
    ]
  }
];

// ── Styling Constants ──────────────────────────────────────────────────────────

const TIER_STYLES = {
  standard: {
    badge: "bg-blue-50 text-blue-700 border-blue-200",
    icon: "text-blue-600",
    active: "bg-blue-50 text-blue-700",
    hover: "hover:bg-blue-50/50 hover:text-blue-700",
  },
  advanced: {
    badge: "bg-violet-50 text-violet-700 border-violet-200",
    icon: "text-violet-600",
    active: "bg-violet-50 text-violet-700",
    hover: "hover:bg-violet-50/50 hover:text-violet-700",
  },
  admin: {
    badge: "bg-amber-50 text-amber-700 border-amber-200",
    icon: "text-amber-600",
    active: "bg-amber-50 text-amber-700",
    hover: "hover:bg-amber-50/50 hover:text-amber-700",
  },
} as const;

const TIER_LABELS: Record<UserTier, { label: string; description: string; icon: React.ReactNode }> = {
  standard: {
    label: "Standard",
    description: "Simplified flows for business users",
    icon: <Eye size={14}/>
  },
  advanced: {
    label: "Advanced",
    description: "Power-user modeling & inspection tools",
    icon: <Wrench size={14}/>
  },
  admin: {
    label: "Admin",
    description: "Governance controls & tenant configuration",
    icon: <Crown size={14}/>
  },
};

// ── Visibility Filter ─────────────────────────────────────────────────────────

/**
 * Check if a nav item should be visible for the given tier
 * - Standard users see: standard items
 * - Advanced users see: standard + advanced items
 * - Admin users see: all items
 */
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

// SidebarItem is wrapped in memo so it only re-renders when its own props change.
// Without this, every location change re-renders the entire nav spine.
const SidebarItem = memo(function SidebarItem({ item, currentTier, depth = 0 }: SidebarItemProps) {
  const [location] = useLocation();
  const isActive = location.startsWith(item.path);
  const [open, setOpen] = useState(isActive);

  const tierStyle = TIER_STYLES[item.tier];

  // Memoize child filtering — only recomputes when item.children or currentTier changes
  const visibleChildren = useMemo(
    () => item.children?.filter(child => isItemVisible(child, currentTier)),
    [item.children, currentTier]
  );
  const hasVisibleChildren = visibleChildren && visibleChildren.length > 0;

  // Indentation based on depth
  const getIndentClass = (d: number): string => {
    if (d === 0) return "";
    if (d === 1) return "ml-4 mt-1 border-l-2 border-neutral-200 pl-3 space-y-0.5";
    return "ml-3 pl-2 space-y-0.5";
  };
  const indentClass = getIndentClass(depth);

  return (
    <div className="group">
      <Link href={item.path}>
        <div
          className={cn(
            "flex items-center gap-2.5 px-3 py-2 rounded-lg text-[12px] font-medium transition-all select-none cursor-pointer",
            isActive
              ? tierStyle.active
              : "text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900",
            item.tier === "admin" && !isActive && "hover:bg-amber-50/30",
            depth > 0 && "py-1.5 text-[11px]"
          )}
          onClick={(e) => {
            if (hasVisibleChildren) {
              e.preventDefault();
              setOpen(o => !o);
            }
          }}
        >
          {item.icon && (
            <span className={cn("shrink-0", isActive ? tierStyle.icon : "text-neutral-400 group-hover:text-neutral-600")}>
              {item.icon}
            </span>
          )}
          <span className="flex-1 truncate">{item.label}</span>
          {item.badge && (
            <span className={cn("text-[9px] px-1.5 py-0.5 rounded border font-semibold", tierStyle.badge)}>
              {item.badge}
            </span>
          )}
          {hasVisibleChildren && (
            <span className="text-neutral-400 transition-transform">
              {open ? <ChevronDown size={12}/> : <ChevronRight size={12}/>}
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
}); // end memo(SidebarItem)

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
  onAdvancedModeToggle 
}: TierSwitcherProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="border-t border-neutral-200 bg-white">
      {/* Current Tier Display */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-3 py-3 flex items-center gap-3 hover:bg-neutral-50 transition-colors"
      >
        <div className={cn(
          "w-8 h-8 rounded-lg flex items-center justify-center",
          currentTier === "standard" && "bg-blue-100 text-blue-700",
          currentTier === "advanced" && "bg-violet-100 text-violet-700",
          currentTier === "admin" && "bg-amber-100 text-amber-700",
        )}>
          {TIER_LABELS[currentTier].icon}
        </div>
        <div className="flex-1 text-left">
          <p className="text-[12px] font-semibold text-neutral-800">{TIER_LABELS[currentTier].label} Mode</p>
          <p className="text-[10px] text-neutral-500 truncate">{TIER_LABELS[currentTier].description}</p>
        </div>
        <ChevronDown 
          size={14} 
          className={cn("text-neutral-400 transition-transform", isExpanded && "rotate-180")}
        />
      </button>

      {/* Expanded Tier Selection */}
      {isExpanded && (
        <div className="px-3 pb-3 space-y-2">
          {/* Advanced Mode Toggle */}
          <div className="flex items-center justify-between py-2 px-2 bg-neutral-50 rounded-lg">
            <div className="flex items-center gap-2">
              <Wrench size={12} className="text-violet-600" />
              <span className="text-[11px] font-medium text-neutral-700">Advanced Mode</span>
            </div>
            <button
              onClick={() => onAdvancedModeToggle(!isAdvancedModeEnabled)}
              className={cn(
                "w-9 h-5 rounded-full transition-colors relative",
                isAdvancedModeEnabled ? "bg-violet-600" : "bg-neutral-300"
              )}
            >
              <span className={cn(
                "absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform",
                isAdvancedModeEnabled ? "translate-x-5" : "translate-x-0.5"
              )} />
            </button>
          </div>

          {/* Tier Selection Buttons */}
          <div className="space-y-1">
            {(Object.keys(TIER_LABELS) as UserTier[]).map((tier) => (
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
                    ? tier === "standard" ? "bg-blue-50 text-blue-700" :
                      tier === "advanced" ? "bg-violet-50 text-violet-700" :
                      "bg-amber-50 text-amber-700"
                    : "text-neutral-600 hover:bg-neutral-100",
                  tier === "admin" && "opacity-50 cursor-not-allowed"
                )}
              >
                <span className={cn(
                  "w-5 h-5 rounded flex items-center justify-center",
                  tier === "standard" ? "bg-blue-100 text-blue-600" :
                  tier === "advanced" ? "bg-violet-100 text-violet-600" :
                  "bg-amber-100 text-amber-600"
                )}>
                  {tier === "standard" ? <Eye size={10}/> :
                   tier === "advanced" ? <Wrench size={10}/> :
                   <Lock size={10}/>}
                </span>
                <span className="flex-1 text-left">{TIER_LABELS[tier].label}</span>
                {tier === "admin" && <Lock size={10} className="text-neutral-400" />}
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
  // Memoize effectiveTier and visibleNavItems so the NAV_SPINE.filter() call
  // only runs when currentTier or isAdvancedModeEnabled actually changes,
  // not on every route change that re-renders the parent AppShell.
  const effectiveTier = useMemo<UserTier>(
    () => (currentTier === "standard" && isAdvancedModeEnabled ? "advanced" : currentTier),
    [currentTier, isAdvancedModeEnabled]
  );

  const visibleNavItems = useMemo(
    () => NAV_SPINE.filter(item => isItemVisible(item, effectiveTier)),
    [effectiveTier]
  );

  return (
    <aside className="w-[240px] shrink-0 bg-white border-r border-neutral-200 overflow-y-auto z-20 flex flex-col h-full">
      {/* Navigation Items */}
      <div className="flex-1 py-4 px-2 space-y-1">
        {visibleNavItems.map(item => (
          <SidebarItem
            key={item.id}
            item={item}
            currentTier={currentTier}
          />
        ))}
      </div>

      {/* Tier Switcher */}
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
