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
import {
  NAVIGATION_SCHEMA,
  TIER_LABELS as NAV_TIER_LABELS,
  getBreadcrumbLabels,
  getConfigurationSlice,
  getGovernanceSlice,
  getSettingsSlice,
  getSidebarTreeModel,
} from "@/navigation/schema";

/* ─── Nav Data ─── */
interface NavItem {
  id: string;
  label: string;
  icon: React.ElementType;
  path: string;
  tier: UserTier;
  children?: NavItem[];
  badge?: string;
}

const ICONS: Record<string, React.ElementType> = {
  home: Frame,
  accounts: Building2,
  intelligence: Radar,
  studio: GitBranch,
  context: Package,
  deliverables: FileOutput,
  governance: Shield,
  settings: Settings,
};

const TIER_ICON: Record<Exclude<UserTier, "unknown">, React.ElementType> = {
  standard: Eye,
  advanced: Wrench,
  admin: Crown,
};

function withIcons(items: readonly NavItem[]): NavItem[] {
  return items.map(item => ({
    ...item,
    icon: ICONS[item.id] ?? Settings,
    children: item.children ? withIcons(item.children as NavItem[]) : undefined,
  }));
}

const BOTTOM_ITEMS = [
  { icon: LifeBuoy, label: "Support" },
  { icon: Send, label: "Feedback" },
];

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
  effectiveTier: Exclude<UserTier, "unknown">;
  selectedAccountId: string | null;
  onNavigate: (path: string) => void;
}

function NavSection({ item, isCollapsed, currentPath, effectiveTier, selectedAccountId, onNavigate }: NavSectionProps) {
  const resolvedPath = resolveWorkspaceRoutePath(item.path, selectedAccountId);
  const isActive = currentPath === resolvedPath || currentPath.startsWith(resolvedPath + "/");
  const [isOpen, setIsOpen] = useState(isActive);

  const visibleChildren = useMemo(
    () => item.children,
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
  currentTier: Exclude<UserTier, "unknown">;
  onTierChange: (tier: Exclude<UserTier, "unknown">) => void;
  isCollapsed: boolean;
}

function TierSwitcher({ currentTier, onTierChange, isCollapsed }: TierSwitcherProps) {
  const [isOpen, setIsOpen] = useState(false);
  const safeTier = currentTier === "unknown" ? "standard" : currentTier;
  const TierIcon = TIER_ICON[safeTier];

  if (isCollapsed) {
    return (
      <SidebarTooltip text={`${NAV_TIER_LABELS[safeTier].label} Mode`}>
        <button
          onClick={() => {
            const tiers: Array<Exclude<UserTier, "unknown">> = ["standard", "advanced", "admin"];
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
          {NAV_TIER_LABELS[safeTier].label} Mode
        </span>
        <ChevronDown className={cn("w-3 h-3 text-sidebar-foreground/40 transition-transform", isOpen && "rotate-180")} />
      </button>
      {isOpen && (
        <div className="mt-1 ml-2 space-y-0.5">
          {(["standard", "advanced", "admin"] as Array<Exclude<UserTier, "unknown">>).map(tier => {
            const TIcon = TIER_ICON[tier as Exclude<UserTier, "unknown">];
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
                <span>{NAV_TIER_LABELS[tier as Exclude<UserTier, "unknown">].label}</span>
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

  const currentTier: Exclude<UserTier, "unknown"> = rawCurrentTier === "unknown" ? "standard" : rawCurrentTier as Exclude<UserTier, "unknown">;
  // Compute effectiveTier locally (mirrors store getter logic)
  const effectiveTier: Exclude<UserTier, "unknown"> = (currentTier === "standard" && isAdvancedModeEnabled)
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
  const breadcrumbs = useMemo(() => getBreadcrumbLabels(location), [location]);

  // User display
  const userEmail = user?.email ?? "";
  const userName = user?.email
    ? user.email.split("@")[0].split(".").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")
    : "User";
  const userInitials = userName.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase() || "U";

  // Filter nav items by tier
  const visibleDomains = useMemo(
    () => withIcons(getSidebarTreeModel(effectiveTier).filter(item => !item.tags?.includes("settings")) as NavItem[]),
    [effectiveTier]
  );
  const visibleSupport = useMemo(
    () => withIcons(getSidebarTreeModel(effectiveTier, [...getSettingsSlice(), ...getConfigurationSlice(), ...getGovernanceSlice()]) as NavItem[]),
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
