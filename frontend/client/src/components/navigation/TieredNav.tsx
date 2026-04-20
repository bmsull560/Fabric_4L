/**
 * TieredNav — Single-Spine Navigation with Progressive Disclosure
 *
 * Refactored 4-Layer Navigation Model:
 * - Home: Dashboard (all tiers)
 * - Context Engine: Foundation layer — knowledge, ontology, data (Tier 1+ with progressive disclosure)
 * - Value Studio: Core workflow — deal-specific value creation (Tier 1+ with progressive disclosure)
 * - Deliver: Activation layer — outputs, calculators, APIs (Tier 1+ with progressive disclosure)
 * - Trust: Governance & observability — audit, provenance, compliance (Tier 1+ with progressive disclosure)
 * - Admin: System configuration — content, data, access, settings (Tier 3)
 *
 * The narrative arc: Context → Studio → Deliver → Trust
 * "What does the system know?" → "How do I build value?" → "How do I deliver impact?" → "Can I trust this?"
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
 * Refactored 4-Layer Navigation:
 * 1. Context Engine → 2. Value Studio → 3. Delivery → 4. Governance & Trust → Admin
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

  // ═══════════════════════════════════════════════════════════════════════════
  // 1. CONTEXT ENGINE — Foundation Layer
  // "What does the system know and how does it reason?"
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: "context",
    label: "Context Engine",
    icon: <Package size={16}/>,
    path: "/context",
    tier: "standard",
    description: "Knowledge, ontology, and system intelligence",
    children: [
      // Knowledge & Logic (All Tiers)
      { id: "packs", label: "Value Packs", path: "/context/packs", tier: "standard" },
      { id: "models", label: "Models", path: "/context/models", tier: "standard" },
      { id: "formulas", label: "Formulas", path: "/context/formulas", tier: "advanced" },
      { id: "agents", label: "Agents", path: "/context/agents", tier: "advanced" },

      // Ontology & Schema (Advanced+)
      {
        id: "ontology",
        label: "Ontology",
        path: "/context/ontology",
        tier: "advanced",
        children: [
          { id: "ontology-editor", label: "Schema Editor", path: "/context/ontology", tier: "advanced" },
          { id: "entities", label: "Entities", path: "/context/ontology/entities", tier: "advanced" },
          { id: "graph", label: "Graph View", path: "/context/ontology/graph", tier: "advanced" }
        ]
      },

      // Data Ingestion (Advanced+)
      { id: "ingestion", label: "Ingestion Jobs", path: "/context/ingestion/jobs", tier: "advanced" },
      { id: "extraction", label: "Extraction", path: "/context/extraction", tier: "advanced" },

      // Integrations (Admin)
      { id: "integrations", label: "Integrations", path: "/context/integrations", tier: "admin", badge: "Admin" },
      { id: "sources", label: "Sources", path: "/context/sources", tier: "admin", badge: "Admin" }
    ]
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // 2. VALUE STUDIO — Core Workflow Layer
  // "How do I create and prove value for this specific deal?"
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: "studio",
    label: "Value Studio",
    icon: <GitBranch size={16}/>,
    path: "/studio",
    tier: "standard",
    description: "Build and prove value for specific deals",
    children: [
      // Deal Context (All Tiers)
      { id: "deals", label: "Deals", path: "/studio/deals", tier: "standard" },

      // 6-Stage Value Construction Pipeline (Advanced+)
      {
        id: "build",
        label: "Build Value",
        path: "/studio/build",
        tier: "advanced",
        children: [
          { id: "discovery",  label: "1. Discovery",  path: "/studio/build/discovery",  tier: "advanced" },
          { id: "mapping",    label: "2. Mapping",    path: "/studio/build/mapping",    tier: "advanced" },
          { id: "modeling",   label: "3. Modeling",   path: "/studio/build/modeling",   tier: "advanced" },
          { id: "validation", label: "4. Validation", path: "/studio/build/validation", tier: "advanced" },
          { id: "narrative",  label: "5. Narrative",  path: "/studio/build/narrative",  tier: "advanced" },
          { id: "tracking",   label: "6. Tracking",   path: "/studio/build/tracking",   tier: "advanced" }
        ]
      },

      // Value Exploration (Advanced+)
      { id: "trees", label: "Value Trees", path: "/studio/trees", tier: "advanced" },
      { id: "scenarios", label: "Scenarios", path: "/studio/scenarios", tier: "advanced" }
    ]
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // 3. DELIVERY ORCHESTRATOR — Activation Layer
  // "How does value leave the system and create impact?"
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: "deliver",
    label: "Deliver",
    icon: <Briefcase size={16}/>,
    path: "/deliver",
    tier: "standard",
    description: "Activate and distribute value",
    children: [
      // Executive Outputs (All Tiers)
      { id: "cases", label: "Business Cases", path: "/deliver/cases", tier: "standard" },

      // Interactive Tools (Advanced+)
      { id: "calculators", label: "Calculators", path: "/deliver/calculators", tier: "advanced" },

      // Stakeholder Views (All Tiers)
      {
        id: "views",
        label: "Stakeholder Views",
        path: "/deliver/views",
        tier: "standard",
        children: [
          { id: "cfo", label: "CFO View", path: "/deliver/views/cfo", tier: "standard" },
          { id: "executive", label: "Executive View", path: "/deliver/views/executive", tier: "standard" },
          { id: "technical", label: "Technical View", path: "/deliver/views/technical", tier: "standard" }
        ]
      },

      // API & Integration (Admin)
      { id: "api", label: "API & Webhooks", path: "/deliver/api", tier: "admin", badge: "Admin" },
      { id: "embeds", label: "Embeds", path: "/deliver/embeds", tier: "admin", badge: "Admin" }
    ]
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // 4. GOVERNANCE & TRUST — Trust Layer
  // "Can I trust this, and can I prove it?"
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: "trust",
    label: "Trust",
    icon: <Shield size={16}/>,
    path: "/trust",
    tier: "standard",
    description: "Provenance, audit, and compliance",
    children: [
      // Evidence & Traces (All Tiers)
      { id: "traces", label: "Decision Traces", path: "/trust/traces", tier: "standard" },
      { id: "evidence", label: "Evidence", path: "/trust/evidence", tier: "standard" },

      // Traceability (Advanced+)
      { id: "provenance", label: "Provenance", path: "/trust/provenance", tier: "advanced" },
      { id: "integrity", label: "Integrity", path: "/trust/integrity", tier: "advanced" },
      { id: "compliance", label: "Compliance", path: "/trust/compliance", tier: "advanced" },

      // System Integrity & Audit (Admin)
      { id: "benchmarks", label: "Benchmarks", path: "/trust/benchmarks", tier: "admin", badge: "Admin" },
      {
        id: "audit",
        label: "Audit",
        path: "/trust/audit",
        tier: "admin",
        badge: "Admin",
        children: [
          { id: "audit-log", label: "Audit Log", path: "/trust/audit/log", tier: "admin" },
          { id: "changes", label: "Change History", path: "/trust/audit/changes", tier: "admin" }
        ]
      },
      { id: "health", label: "System Health", path: "/trust/health", tier: "admin", badge: "Admin" }
    ]
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // ADMIN — System Configuration (Control Plane)
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: "admin",
    label: "Admin",
    icon: <Settings size={16}/>,
    path: "/admin",
    tier: "admin",
    description: "Platform configuration and governance",
    badge: "Admin",
    children: [
      {
        id: "content",
        label: "Content",
        path: "/admin/content",
        tier: "admin",
        children: [
          { id: "formulas", label: "Formula Registry", path: "/admin/content/formulas", tier: "admin" },
          { id: "versions", label: "Version History", path: "/admin/content/versions", tier: "admin" },
          { id: "approvals", label: "Approval Queue", path: "/admin/content/approvals", tier: "admin" }
        ]
      },
      {
        id: "data",
        label: "Data",
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
        label: "Access",
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
          { id: "settings", label: "Settings", path: "/admin/system/settings", tier: "admin" }
        ]
      }
    ]
  }
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
    if (d === 1) return "ml-4 mt-1 border-l-2 border-border pl-3 space-y-0.5";
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
              : "text-muted-foreground hover:bg-muted hover:text-foreground",
            item.tier === "admin" && !isActive && "hover:bg-destructive/5",
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
            <span className={cn("shrink-0", isActive ? tierStyle.icon : "text-muted-foreground group-hover:text-muted-foreground/80")}>
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
            <span className="text-muted-foreground transition-transform">
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
    <div className="border-t border-border bg-card">
      {/* Current Tier Display */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-3 py-3 flex items-center gap-3 hover:bg-muted/50 transition-colors"
      >
        <div className={cn(
          "w-8 h-8 rounded-lg flex items-center justify-center",
          currentTier === "standard" && "bg-primary/10 text-primary",
          currentTier === "advanced" && "bg-accent/10 text-accent",
          currentTier === "admin" && "bg-destructive/10 text-destructive",
        )}>
          {TIER_LABELS[currentTier].icon}
        </div>
        <div className="flex-1 text-left">
          <p className="text-[12px] font-semibold text-foreground">{TIER_LABELS[currentTier].label} Mode</p>
          <p className="text-[10px] text-muted-foreground truncate">{TIER_LABELS[currentTier].description}</p>
        </div>
        <ChevronDown 
          size={14} 
          className={cn("text-muted-foreground transition-transform", isExpanded && "rotate-180")}
        />
      </button>

      {/* Expanded Tier Selection */}
      {isExpanded && (
        <div className="px-3 pb-3 space-y-2">
          {/* Advanced Mode Toggle */}
          <div className="flex items-center justify-between py-2 px-2 bg-muted/50 rounded-lg">
            <div className="flex items-center gap-2">
              <Wrench size={12} className="text-accent" />
              <span className="text-[11px] font-medium text-foreground">Advanced Mode</span>
            </div>
            <button
              onClick={() => onAdvancedModeToggle(!isAdvancedModeEnabled)}
              className={cn(
                "w-9 h-5 rounded-full transition-colors relative",
                isAdvancedModeEnabled ? "bg-accent" : "bg-muted-foreground/30"
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
                    ? tier === "standard" ? "bg-primary/10 text-primary" :
                      tier === "advanced" ? "bg-accent/10 text-accent" :
                      "bg-destructive/10 text-destructive"
                    : "text-muted-foreground hover:bg-muted",
                  tier === "admin" && "opacity-50 cursor-not-allowed"
                )}
              >
                <span className={cn(
                  "w-5 h-5 rounded flex items-center justify-center",
                  tier === "standard" ? "bg-primary/10 text-primary" :
                  tier === "advanced" ? "bg-accent/10 text-accent" :
                  "bg-destructive/10 text-destructive"
                )}>
                  {tier === "standard" ? <Eye size={10}/> :
                   tier === "advanced" ? <Wrench size={10}/> :
                   <Lock size={10}/>}
                </span>
                <span className="flex-1 text-left">{TIER_LABELS[tier].label}</span>
                {tier === "admin" && <Lock size={10} className="text-muted-foreground" />}
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
    <aside className="w-[240px] shrink-0 bg-card border-r border-border overflow-y-auto z-20 flex flex-col h-full">
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
