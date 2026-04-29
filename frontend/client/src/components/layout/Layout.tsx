/**
 * Layout — Global App Shell
 *
 * Migrated from the prototype's Layout.tsx, adapted to:
 *   - wouter (useLocation) instead of react-router-dom (Outlet)
 *   - Fabric_4L's 7-domain navigation spine with tier-based progressive disclosure
 *   - ThemeContext integration for dark mode
 *   - AuthContext integration for user profile
 *
 * Features:
 *   - Collapsible sidebar (260px expanded / 56px collapsed) with smooth transition
 *   - Header with breadcrumb navigation showing route hierarchy
 *   - Search bar in sidebar with ⌘K shortcut hint
 *   - User profile section at bottom with expandable dropdown
 *   - Dark mode toggle in header
 *   - Notifications bell with indicator dot
 *   - Tier switcher (Standard / Advanced / Admin)
 */
import * as React from "react";
import { memo, useState, useCallback, useMemo } from "react";
import { Link, useLocation } from "wouter";
import {
  Search, Bell, ChevronRight, ChevronDown,
  Building2, Radar, GitBranch, Package, FileOutput, Shield, Settings,
  Command, Sun, Moon, Frame, LifeBuoy, Send,
  PanelLeft, Eye, Lock, Wrench, Crown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/contexts/ThemeContext";
import { useAuthContext } from "@/contexts/AuthContext";
import { useUserTierStore, type UserTier } from "@/hooks";
import { useAccountContextStore } from "@/stores/accountContextStore";
import { resolveWorkspaceRoutePath } from "@/navigation/accountRouting";
import { resolveBreadcrumbs } from "@/navigation/navSchema";

/* ─── Nav Data ─── */
interface NavItem {
  id: string;
  label: string;
  icon: React.ElementType;
  path: string;
  tier: UserTier;
  children?: NavChild[];
  description?: string;
}

interface NavChild {
  id: string;
  label: string;
  path: string;
  tier: UserTier;
  badge?: string;
  children?: NavChild[];
}

const NAV_DOMAINS: NavItem[] = [
  {
    id: "home",
    label: "Home",
    icon: Frame,
    path: "/home",
    tier: "standard",
    description: "Dashboard & prospect prompt builder",
  },
  {
    id: "accounts",
    label: "Accounts",
    icon: Building2,
    path: "/accounts",
    tier: "standard",
    description: "Select or create a prospect account",
  },
  {
    id: "intelligence",
    label: "Intelligence",
    icon: Radar,
    path: "/intelligence",
    tier: "standard",
    description: "Discover and validate prospect pain signals",
    children: [
      { id: "intel-signals", label: "Signals", path: "/intelligence/signals", tier: "standard" },
      { id: "intel-drivers", label: "Drivers", path: "/intelligence/drivers", tier: "standard" },
      { id: "intel-evidence", label: "Evidence", path: "/intelligence/evidence", tier: "standard" },
      { id: "intel-stakeholders", label: "Stakeholders", path: "/intelligence/stakeholders", tier: "standard" },
      { id: "intel-enrichment", label: "Enrichment", path: "/intelligence/enrichment", tier: "advanced" },
      { id: "intel-hypotheses", label: "Hypotheses", path: "/intelligence/hypotheses", tier: "advanced" },
      { id: "intel-competitive", label: "Competitive", path: "/intelligence/competitive", tier: "advanced" },
      { id: "intel-roi", label: "ROI", path: "/intelligence/roi", tier: "advanced" },
      { id: "intel-evidence-library", label: "Evidence Library", path: "/intelligence/evidence-library", tier: "advanced" },
    ],
  },
  {
    id: "studio",
    label: "Value Studio",
    icon: GitBranch,
    path: "/studio",
    tier: "advanced",
    description: "Build the product-anchored business case",
    children: [
      { id: "studio-action-plan", label: "Action Plan", path: "/studio/action-plan", tier: "standard" },
      { id: "studio-value-model", label: "Value Model", path: "/studio/value-model", tier: "standard" },
      { id: "studio-narrative", label: "Narrative", path: "/studio/narrative", tier: "standard" },
      { id: "studio-enrichment", label: "Enrichment", path: "/studio/enrichment", tier: "advanced" },
      { id: "studio-competitive", label: "Competitive", path: "/studio/competitive", tier: "advanced" },
      { id: "studio-roi", label: "ROI", path: "/studio/roi", tier: "advanced" },
      { id: "studio-evidence", label: "Evidence", path: "/studio/evidence", tier: "advanced" },
    ],
  },
  {
    id: "context",
    label: "Context Engine",
    icon: Package,
    path: "/context",
    tier: "advanced",
    description: "Vendor knowledge: Value Packs, models, formulas",
    children: [
      { id: "packs", label: "Value Packs", path: "/context/packs", tier: "standard" },
      { id: "models", label: "Models", path: "/context/models", tier: "standard" },
      { id: "value-trees", label: "Tree Explorer", path: "/context/value-trees/explorer", tier: "advanced" },
      { id: "formulas", label: "Formulas", path: "/context/formulas", tier: "advanced" },
      { id: "agents", label: "Agents", path: "/context/agents", tier: "advanced" },
      { id: "ontology", label: "Ontology", path: "/context/ontology", tier: "advanced" },
      { id: "ingestion", label: "Ingestion", path: "/context/ingestion/jobs", tier: "advanced" },
      { id: "extraction", label: "Extraction", path: "/context/extraction", tier: "advanced" },
      { id: "integrations", label: "Integrations", path: "/context/integrations", tier: "admin", badge: "Admin" },
      { id: "sources", label: "Sources", path: "/context/sources", tier: "admin", badge: "Admin" },
    ],
  },
  {
    id: "deliverables",
    label: "Deliverables",
    icon: FileOutput,
    path: "/deliverables",
    tier: "standard",
    description: "Packaged outputs for sharing with prospects",
    children: [
      { id: "cases", label: "Business Cases", path: "/deliverables/cases", tier: "standard" },
      { id: "calculators", label: "Calculators", path: "/deliverables/calculators", tier: "advanced" },
      { id: "cfo", label: "CFO View", path: "/deliverables/views/cfo", tier: "standard" },
      { id: "executive", label: "Executive View", path: "/deliverables/views/executive", tier: "standard" },
      { id: "technical", label: "Technical View", path: "/deliverables/views/technical", tier: "standard" },
    ],
  },
  {
    id: "governance",
    label: "Governance",
    icon: Shield,
    path: "/governance",
    tier: "admin",
    description: "Audit, provenance, and compliance",
    children: [
      { id: "traces", label: "Decision Traces", path: "/governance/traces", tier: "standard" },
      { id: "evidence-gov", label: "Evidence", path: "/governance/evidence", tier: "standard" },
      { id: "provenance", label: "Provenance", path: "/governance/provenance", tier: "advanced" },
      { id: "integrity", label: "Integrity", path: "/governance/integrity", tier: "advanced" },
      { id: "compliance", label: "Compliance", path: "/governance/compliance", tier: "advanced" },
      { id: "benchmarks", label: "Benchmarks", path: "/governance/benchmarks", tier: "admin", badge: "Admin" },
      { id: "audit-log", label: "Audit Log", path: "/governance/audit/log", tier: "admin", badge: "Admin" },
      { id: "health", label: "System Health", path: "/governance/health", tier: "admin", badge: "Admin" },
    ],
  },
];

const SUPPORT_ITEMS: NavItem[] = [
  {
    id: "settings",
    label: "Settings",
    icon: Settings,
    path: "/settings",
    tier: "admin",
    description: "Platform configuration and user management",
    children: [
      { id: "content-formulas", label: "Formulas", path: "/settings/content/formulas", tier: "admin" },
      { id: "data-variables", label: "Variables", path: "/settings/data/variables", tier: "admin" },
      { id: "access-roles", label: "Roles", path: "/settings/access/roles", tier: "admin" },
      { id: "system-settings", label: "System", path: "/settings/system/settings", tier: "admin" },
      { id: "system-billing", label: "Billing", path: "/settings/system/billing", tier: "admin" },
    ],
  },
];

const BOTTOM_ITEMS = [
  { icon: LifeBuoy, label: "Support" },
  { icon: Send, label: "Feedback" },
];

const TIER_LABELS: Record<UserTier, { label: string; icon: React.ElementType }> = {
  unknown: { label: "Standard", icon: Eye },
  standard: { label: "Standard", icon: Eye },
  advanced: { label: "Advanced", icon: Wrench },
  admin: { label: "Admin", icon: Crown },
};

/* ─── Helpers ─── */
function isItemVisible(tier: UserTier, userTier: UserTier): boolean {
  if (userTier === "admin") return true;
  if (userTier === "advanced") return tier !== "admin";
  return tier === "standard";
}

/* ─── Tooltip ─── */
function SidebarTooltip({ text, children }: { text: string; children: React.ReactNode }) {
  return (
    <div className="group/tooltip relative flex items-center justify-center">
      {children}
      <div className="absolute left-full ml-2 px-2.5 py-1.5 bg-popover text-popover-foreground text-xs font-medium rounded-lg border border-border shadow-lg opacity-0 invisible group-hover/tooltip:opacity-100 group-hover/tooltip:visible transition-all duration-150 whitespace-nowrap z-50">
        {text}
      </div>
    </div>
  );
}

/* ─── Nav Button ─── */
interface NavButtonProps {
  icon: React.ElementType;
  label: string;
  path: string;
  isActive: boolean;
  isCollapsed: boolean;
  badge?: string;
  hasChildren?: boolean;
  isOpen?: boolean;
  onToggle?: () => void;
  onClick: () => void;
}

function NavButton({ icon: Icon, label, path, isActive, isCollapsed, badge, hasChildren, isOpen, onToggle, onClick }: NavButtonProps) {
  if (isCollapsed) {
    return (
      <SidebarTooltip text={label}>
        <Link
          href={path}
          onClick={(e: React.MouseEvent) => { e.preventDefault(); onClick(); }}
          className={cn(
            "w-8 h-8 mx-auto rounded-lg flex items-center justify-center transition-colors",
            isActive
              ? "bg-sidebar-primary/15 text-sidebar-primary"
              : "text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent"
          )}
        >
          <Icon className="w-4 h-4" />
        </Link>
      </SidebarTooltip>
    );
  }

  if (hasChildren) {
    // Parent with children: clicking toggles the section open/closed
    // Use <a> for role="link" semantics but handle via onClick
    return (
      <Link
        href={path}
        onClick={(e: React.MouseEvent) => { e.preventDefault(); if (onToggle) onToggle(); }}
        className={cn(
          "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
          isActive
            ? "bg-sidebar-primary/15 text-sidebar-primary font-semibold"
            : "text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent"
        )}
      >
        <Icon className="w-4 h-4 shrink-0" />
        <span className="text-left flex-1">{label}</span>
        {badge && (
          <span className="text-[9px] px-1.5 py-0.5 rounded border font-semibold bg-destructive/10 text-destructive border-destructive/20">
            {badge}
          </span>
        )}
        <ChevronDown className={cn("w-3 h-3 text-sidebar-foreground/40 transition-transform", isOpen && "rotate-180")} />
      </Link>
    );
  }

  return (
    <Link
      href={path}
      onClick={(e: React.MouseEvent) => { e.preventDefault(); onClick(); }}
      className={cn(
        "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
        isActive
          ? "bg-sidebar-primary/15 text-sidebar-primary font-semibold"
          : "text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent"
      )}
    >
      <Icon className="w-4 h-4 shrink-0" />
      <span className="text-left flex-1">{label}</span>
      {badge && (
        <span className="text-[9px] px-1.5 py-0.5 rounded border font-semibold bg-destructive/10 text-destructive border-destructive/20">
          {badge}
        </span>
      )}
      {isActive && <div className="w-1.5 h-1.5 rounded-full bg-sidebar-primary shrink-0" />}
    </Link>
  );
}

/* ─── Nav Section (domain with children) ─── */
interface NavSectionProps {
  item: NavItem;
  isCollapsed: boolean;
  currentPath: string;
  effectiveTier: UserTier;
  selectedAccountId: string | null;
  onNavigate: (path: string) => void;
}

function NavSection({ item, isCollapsed, currentPath, effectiveTier, selectedAccountId, onNavigate }: NavSectionProps) {
  const resolvedPath = resolveWorkspaceRoutePath(item.path, selectedAccountId);
  const isActive = currentPath === resolvedPath || currentPath.startsWith(resolvedPath + "/");
  const [isOpen, setIsOpen] = useState(isActive);

  const visibleChildren = useMemo(
    () => item.children?.filter(c => isItemVisible(c.tier, effectiveTier)),
    [item.children, effectiveTier]
  );

  const hasChildren = visibleChildren && visibleChildren.length > 0;

  return (
    <div>
      <NavButton
        icon={item.icon}
        label={item.label}
        path={resolvedPath}
        isActive={isActive}
        isCollapsed={isCollapsed}
        hasChildren={!isCollapsed && hasChildren}
        isOpen={isOpen}
        onToggle={() => setIsOpen(o => !o)}
        onClick={() => onNavigate(resolvedPath)}
      />
      {!isCollapsed && hasChildren && isOpen && (
        <div className="ml-7 mt-1 space-y-0.5 border-l border-sidebar-border pl-3">
          {visibleChildren!.map(child => {
            const childResolved = resolveWorkspaceRoutePath(child.path, selectedAccountId);
            const childActive = currentPath === childResolved || currentPath.startsWith(childResolved + "/");
            return (
              <Link
                key={child.id}
                href={childResolved}
                onClick={(e: React.MouseEvent) => { e.preventDefault(); onNavigate(childResolved); }}
                aria-label={`Navigate to ${child.label}`}
                className={cn(
                  "w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-xs transition-colors",
                  childActive
                    ? "text-sidebar-primary font-semibold bg-sidebar-primary/10"
                    : "text-sidebar-foreground/60 hover:text-sidebar-foreground hover:bg-sidebar-accent"
                )}
              >
                <span className="flex-1 text-left">{child.label}</span>
                {child.badge && (
                  <span className="text-[8px] px-1 py-0.5 rounded border font-semibold bg-destructive/10 text-destructive border-destructive/20">
                    {child.badge}
                  </span>
                )}
                {childActive && <div className="w-1 h-1 rounded-full bg-sidebar-primary shrink-0" />}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ─── Tier Switcher (compact) ─── */
interface TierSwitcherProps {
  currentTier: UserTier;
  onTierChange: (tier: UserTier) => void;
  isCollapsed: boolean;
}

function TierSwitcher({ currentTier, onTierChange, isCollapsed }: TierSwitcherProps) {
  const [isOpen, setIsOpen] = useState(false);
  const TierIcon = TIER_LABELS[currentTier].icon;

  if (isCollapsed) {
    return (
      <SidebarTooltip text={`${TIER_LABELS[currentTier].label} Mode`}>
        <button
          onClick={() => {
            const tiers: UserTier[] = ["standard", "advanced", "admin"];
            const idx = tiers.indexOf(currentTier);
            onTierChange(tiers[(idx + 1) % tiers.length]);
          }}
          className="w-8 h-8 mx-auto rounded-lg flex items-center justify-center text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent transition-colors"
        >
          <TierIcon className="w-4 h-4" />
        </button>
      </SidebarTooltip>
    );
  }

  return (
    <div className="px-3 pb-2">
      <button
        onClick={() => setIsOpen(o => !o)}
        className="w-full flex items-center gap-2.5 px-2 py-2 rounded-lg hover:bg-sidebar-accent transition-colors text-left"
      >
        <div className="w-6 h-6 rounded-md bg-sidebar-primary/15 flex items-center justify-center shrink-0">
          <TierIcon className="w-3 h-3 text-sidebar-primary" />
        </div>
        <span className="text-xs font-medium text-sidebar-foreground flex-1">
          {TIER_LABELS[currentTier].label} Mode
        </span>
        <ChevronDown className={cn("w-3 h-3 text-sidebar-foreground/40 transition-transform", isOpen && "rotate-180")} />
      </button>
      {isOpen && (
        <div className="mt-1 ml-2 space-y-0.5">
          {(["standard", "advanced", "admin"] as UserTier[]).map(tier => {
            const TIcon = TIER_LABELS[tier].icon;
            return (
              <button
                key={tier}
                onClick={() => { onTierChange(tier); setIsOpen(false); }}
                className={cn(
                  "w-full flex items-center gap-2 px-3 py-1.5 text-xs rounded-md transition-colors",
                  currentTier === tier
                    ? "text-sidebar-primary font-semibold bg-sidebar-primary/10"
                    : "text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent"
                )}
              >
                <TIcon className="w-3 h-3" />
                <span>{TIER_LABELS[tier].label}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ─── Main Layout Component ─── */
interface LayoutProps {
  children: React.ReactNode;
  currentTier?: UserTier;
  effectiveTier?: UserTier;
}

const Layout = memo(function Layout({
  children,
  currentTier: externalCurrentTier,
  effectiveTier: externalEffectiveTier,
}: LayoutProps) {
  const [location, navigate] = useLocation();
  const { theme, toggleTheme, switchable } = useTheme();
  const { user, logout } = useAuthContext();

  // Tier management — read primitive values directly from zustand store.
  // We compute effectiveTier locally instead of using the store's getter because:
  // 1. Zustand v5 persist hydrates async; the getter may not trigger re-renders
  //    when the store transitions from default ("standard") to hydrated ("advanced")
  // 2. External props from Router can also be stale during the hydration window
  // By subscribing to primitive values (currentTier, isAdvancedModeEnabled),
  // zustand's useSyncExternalStore guarantees re-renders on state changes.
  const rawCurrentTier = useUserTierStore(state => state.currentTier);
  const isAdvancedModeEnabled = useUserTierStore(state => state.isAdvancedModeEnabled);
  const setTier = useUserTierStore(state => state.setTier);

  const currentTier: UserTier = rawCurrentTier === "unknown" ? "standard" : rawCurrentTier as UserTier;
  // Compute effectiveTier locally (mirrors store getter logic)
  const effectiveTier: UserTier = (currentTier === "standard" && isAdvancedModeEnabled)
    ? "advanced"
    : currentTier;

  // Account context (lifted from NavSection for single subscription)
  const selectedAccountId = useAccountContextStore(state => state.selectedAccountId);

  // Layout state
  const [collapsed, setCollapsed] = useState(false);
  const [userOpen, setUserOpen] = useState(false);

  const isDark = theme === "dark";

  const handleToggleTheme = useCallback(() => {
    if (toggleTheme) {
      toggleTheme();
    } else {
      // Fallback: direct DOM manipulation (matches prototype behavior)
      const next = !isDark;
      if (next) {
        document.documentElement.classList.add("dark");
        localStorage.setItem("vp-theme", "dark");
      } else {
        document.documentElement.classList.remove("dark");
        localStorage.setItem("vp-theme", "light");
      }
    }
  }, [toggleTheme, isDark]);

  const handleNavigate = useCallback((path: string) => {
    navigate(path);
  }, [navigate]);

  const handleTierChange = useCallback((tier: UserTier) => {
    setTier(tier);
  }, [setTier]);

  // Breadcrumbs
  const breadcrumbs = useMemo(() => resolveBreadcrumbs(location), [location]);

  // User display
  const userEmail = user?.email ?? "";
  const userName = user?.email
    ? user.email.split("@")[0].split(".").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")
    : "User";
  const userInitials = userName.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase() || "U";

  // Filter nav items by tier
  const visibleDomains = useMemo(
    () => NAV_DOMAINS.filter(item => isItemVisible(item.tier, effectiveTier)),
    [effectiveTier]
  );
  const visibleSupport = useMemo(
    () => SUPPORT_ITEMS.filter(item => isItemVisible(item.tier, effectiveTier)),
    [effectiveTier]
  );

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* ─── SIDEBAR ─── */}
      <aside
        className="shrink-0 h-full bg-sidebar border-r border-sidebar-border flex flex-col overflow-hidden transition-[width] duration-300 ease-in-out"
        style={{ width: collapsed ? 56 : 260 }}
      >
        {/* Company Header */}
        <div className="px-3 py-3 flex items-center" style={{ justifyContent: collapsed ? "center" : "stretch" }}>
          {collapsed ? (
            <SidebarTooltip text="Value Fabric">
              <div
                className="w-8 h-8 rounded-lg bg-sidebar-primary flex items-center justify-center shrink-0 cursor-pointer"
                onClick={() => handleNavigate("/home")}
              >
                <Frame className="w-4 h-4 text-sidebar-primary-foreground" />
              </div>
            </SidebarTooltip>
          ) : (
            <button
              onClick={() => handleNavigate("/home")}
              className="w-full flex items-center gap-2.5 px-2 py-1.5 rounded-lg hover:bg-sidebar-accent transition-colors text-left"
            >
              <div className="w-8 h-8 rounded-lg bg-sidebar-primary flex items-center justify-center shrink-0">
                <Frame className="w-4 h-4 text-sidebar-primary-foreground" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-sidebar-foreground truncate leading-tight">Value Fabric</p>
                <p className="text-[10px] text-sidebar-foreground/50 leading-tight">Intelligence Platform</p>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-sidebar-foreground/40 shrink-0" />
            </button>
          )}
        </div>

        {/* Search */}
        <div className="px-3 pb-2">
          {collapsed ? (
            <SidebarTooltip text="Search">
              <div className="w-8 h-8 mx-auto rounded-lg hover:bg-sidebar-accent flex items-center justify-center cursor-pointer transition-colors">
                <Search className="w-4 h-4 text-sidebar-foreground/50" />
              </div>
            </SidebarTooltip>
          ) : (
            <div className="flex items-center gap-2 px-3 py-2 bg-sidebar-accent rounded-lg border border-sidebar-border">
              <Search className="w-3.5 h-3.5 text-sidebar-foreground/40" />
              <span className="text-xs text-sidebar-foreground/40 flex-1">Search</span>
              <kbd className="hidden sm:inline-flex h-5 items-center gap-1 rounded border border-sidebar-border bg-sidebar px-1.5 text-[10px] font-medium text-sidebar-foreground/50">
                <Command className="w-2.5 h-2.5" />K
              </kbd>
            </div>
          )}
        </div>

        {/* Scrollable nav */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden px-3 space-y-5 min-h-0">
          {/* Workflow Section */}
          <div>
            {!collapsed && (
              <p className="px-3 pb-1.5 text-[10px] font-semibold text-sidebar-foreground/40 uppercase tracking-wider">Workflow</p>
            )}
            <div className="space-y-0.5">
              {visibleDomains.map(item => (
                <NavSection
                  key={item.id}
                  item={item}
                  isCollapsed={collapsed}
                  currentPath={location}
                  effectiveTier={effectiveTier}
                  selectedAccountId={selectedAccountId}
                  onNavigate={handleNavigate}
                />
              ))}
            </div>
          </div>

          {/* Support Section */}
          {visibleSupport.length > 0 && (
            <div>
              {!collapsed && (
                <p className="px-3 pb-1.5 text-[10px] font-semibold text-sidebar-foreground/40 uppercase tracking-wider">Setup</p>
              )}
              <div className="space-y-0.5">
                {visibleSupport.map(item => (
                  <NavSection
                    key={item.id}
                    item={item}
                    isCollapsed={collapsed}
                    currentPath={location}
                    effectiveTier={effectiveTier}
                    selectedAccountId={selectedAccountId}
                    onNavigate={handleNavigate}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Bottom nav items */}
        <div className="px-3 pb-2 space-y-0.5">
          {BOTTOM_ITEMS.map(item =>
            collapsed ? (
              <SidebarTooltip key={item.label} text={item.label}>
                <div className="w-8 h-8 mx-auto rounded-lg flex items-center justify-center text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent transition-colors cursor-pointer">
                  <item.icon className="w-4 h-4" />
                </div>
              </SidebarTooltip>
            ) : (
              <button
                key={item.label}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent transition-colors"
              >
                <item.icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </button>
            )
          )}
        </div>

        {/* Tier Switcher */}
        <div className="border-t border-sidebar-border pt-2">
          <TierSwitcher
            currentTier={currentTier}
            onTierChange={handleTierChange}
            isCollapsed={collapsed}
          />
        </div>

        {/* User Profile */}
        <div className="border-t border-sidebar-border pt-2 pb-3">
          {collapsed ? (
            <SidebarTooltip text={userName}>
              <button
                onClick={() => setUserOpen(!userOpen)}
                className="w-8 h-8 mx-auto rounded-full bg-sidebar-primary/20 flex items-center justify-center hover:bg-sidebar-accent transition-colors"
              >
                <span className="text-[10px] font-bold text-sidebar-primary">{userInitials}</span>
              </button>
            </SidebarTooltip>
          ) : (
            <div className="px-3">
              <button
                onClick={() => setUserOpen(!userOpen)}
                className="w-full flex items-center gap-2.5 px-2 py-2 rounded-lg hover:bg-sidebar-accent transition-colors text-left"
              >
                <div className="w-8 h-8 rounded-full bg-sidebar-primary/20 flex items-center justify-center shrink-0">
                  <span className="text-xs font-bold text-sidebar-primary">{userInitials}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-sidebar-foreground truncate leading-tight">{userName}</p>
                  <p className="text-[10px] text-sidebar-foreground/50 truncate leading-tight">{userEmail}</p>
                </div>
                <ChevronDown className={cn("w-3.5 h-3.5 text-sidebar-foreground/40 shrink-0 transition-transform", userOpen && "rotate-180")} />
              </button>
              {userOpen && (
                <div className="mt-1 ml-2 space-y-0.5">
                  <button
                    aria-label="View profile"
                    className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-sidebar-foreground/70 hover:text-sidebar-foreground rounded-md hover:bg-sidebar-accent"
                  >
                    Profile
                  </button>
                  <button
                    onClick={() => handleNavigate("/settings/system/settings")}
                    className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-sidebar-foreground/70 hover:text-sidebar-foreground rounded-md hover:bg-sidebar-accent"
                  >
                    Settings
                  </button>
                  <button
                    onClick={() => logout()}
                    className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-sidebar-foreground/70 hover:text-sidebar-foreground rounded-md hover:bg-sidebar-accent"
                  >
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </aside>

      {/* ─── MAIN CONTENT ─── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Bar */}
        <header className="h-14 bg-card border-b border-border flex items-center justify-between px-4 shrink-0">
          {/* Left: Collapse toggle + Breadcrumb */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="p-2 rounded-lg hover:bg-muted transition-colors"
              title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              <PanelLeft className={cn("w-4 h-4 text-muted-foreground transition-transform duration-300", collapsed && "rotate-180")} />
            </button>
            <div className="w-px h-5 bg-border" />
            <div className="flex items-center gap-2 text-sm">
              {breadcrumbs.map((crumb, i) => (
                <React.Fragment key={i}>
                  {i > 0 && <ChevronRight className="w-3.5 h-3.5 text-muted-foreground/40" />}
                  {i === breadcrumbs.length - 1 ? (
                    <span className="text-foreground font-medium">{crumb.label}</span>
                  ) : (
                    <span
                      className="text-muted-foreground cursor-pointer hover:text-foreground transition-colors"
                      onClick={() => crumb.path && handleNavigate(crumb.path)}
                    >
                      {crumb.label}
                    </span>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-1.5">
            <button
              onClick={handleToggleTheme}
              className="p-2 rounded-lg hover:bg-muted transition-colors"
              title={isDark ? "Switch to light mode" : "Switch to dark mode"}
            >
              {isDark ? <Sun className="w-4 h-4 text-muted-foreground" /> : <Moon className="w-4 h-4 text-muted-foreground" />}
            </button>
            <button
              className="p-2 rounded-lg hover:bg-muted transition-colors relative"
              aria-label="Notifications"
            >
              <Bell className="w-4 h-4 text-muted-foreground" />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-primary" aria-hidden="true" />
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
});

export default Layout;
