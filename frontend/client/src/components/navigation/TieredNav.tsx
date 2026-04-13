/**
 * TieredNav — Three-Tier Navigation Component
 * 
 * Progressive disclosure UI model:
 * - Tier 1 (Standard): Command Center, Accounts, Value Models, Business Cases, Workflows, Evidence
 * - Tier 2 (Advanced): Value Tree Explorer, Formula Studio, Graph Explorer, Ontology Browser
 * - Tier 3 (Admin): Formula Governance, Benchmark Policies, Variable Registry, Data Sources, Pack Management
 * 
 * Features:
 * - "Advanced Mode" toggle for Tier 2 surfaces
 * - Admin Control Plane for Tier 3
 * - Progressive disclosure patterns (hide complexity from Tier 1)
 * - Route-aware navigation highlighting
 */

import { useState, useCallback } from "react";
import { Link, useLocation } from "wouter";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, Search, Bell, User, ChevronDown, ChevronRight,
  Briefcase, FileText, Workflow, Shield, BookOpen, GitBranch,
  Share2, Network, History, Settings, Database, Bot, Layers,
  FlaskConical, BarChart3, ListChecks, KeyRound, SlidersHorizontal,
  Users, FolderKanban, Sparkles, ChevronLeft, Eye, EyeOff,
  Lock, Crown, Wrench
} from "lucide-react";

// ── Types ─────────────────────────────────────────────────────────────────────

export type UserTier = "standard" | "advanced" | "admin";

export interface NavItem {
  label: string;
  icon: React.ReactNode;
  path: string;
  tier: UserTier;
  children?: { label: string; path: string; tier?: UserTier }[];
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

// ── Navigation Definitions ─────────────────────────────────────────────────────

/**
 * Tier 1 (Standard): Simplified flows for business users
 * - Command Center, Accounts, Value Models, Business Cases, Workflows, Evidence
 */
const TIER_1_NAV: NavItem[] = [
  { 
    label: "Command Center",  
    icon: <LayoutDashboard size={16}/>, 
    path: "/command-center",
    tier: "standard",
    description: "Overview dashboard and quick actions"
  },
  { 
    label: "Value Packs",     
    icon: <Sparkles size={16}/>,        
    path: "/value-packs",
    tier: "standard",
    description: "Pre-built value models and templates"
  },
  {
    label: "Business Cases", 
    icon: <Briefcase size={16}/>, 
    path: "/agents",
    tier: "standard",
    description: "ROI analysis and business case workflows",
    children: [
      { label: "All Cases",         path: "/agents/business-cases", tier: "standard" },
      { label: "Workflow Dashboard", path: "/agents/dashboard", tier: "standard" },
    ],
  },
  {
    label: "Research",       
    icon: <BookOpen size={16}/>, 
    path: "/research",
    tier: "standard",
    description: "Accounts and data source management",
    children: [
      { label: "Accounts",          path: "/accounts", tier: "standard" },
      { label: "Integrations",      path: "/integrations", tier: "admin" },
      { label: "Ingestion Jobs",    path: "/data-sources/jobs", tier: "standard" },
    ],
  },
  {
    label: "Evidence",       
    icon: <Shield size={16}/>, 
    path: "/audit",
    tier: "standard",
    description: "Decision traces and audit trails",
    children: [
      { label: "Decision Traces",   path: "/audit/traces", tier: "standard" },
      { label: "Lineage Explorer",  path: "/audit/lineage", tier: "standard" },
    ],
  },
  { 
    label: "Settings",       
    icon: <Settings size={16}/>,         
    path: "/settings",
    tier: "standard",
    description: "User preferences and configuration"
  },
];

/**
 * Tier 2 (Advanced): Power-user modeling & inspection tools
 * - Value Tree Explorer, Formula Studio, Graph Explorer, Ontology Browser
 */
const TIER_2_NAV: NavItem[] = [
  { 
    label: "Command Center",    
    icon: <LayoutDashboard size={16}/>, 
    path: "/command-center",
    tier: "standard",
    description: "Overview dashboard"
  },
  { 
    label: "Extraction Engine", 
    icon: <FolderKanban size={16}/>,    
    path: "/extraction-engine",
    tier: "advanced",
    description: "Data extraction and processing pipelines"
  },
  {
    label: "Value Tree Explorer",   
    icon: <GitBranch size={16}/>, 
    path: "/value-trees",
    tier: "advanced",
    description: "Interactive value tree visualization",
    children: [
      { label: "Tree Explorer",    path: "/value-trees/explorer", tier: "advanced" },
      { label: "Normalization",    path: "/value-trees/normalization", tier: "advanced" },
    ],
  },
  {
    label: "Formula Studio",  
    icon: <FlaskConical size={16}/>, 
    path: "/value-trees/formulas",
    tier: "advanced",
    description: "Formula authoring and testing environment"
  },
  {
    label: "Graph Explorer",  
    icon: <Share2 size={16}/>, 
    path: "/graph",
    tier: "advanced",
    description: "Knowledge graph visualization and queries",
    children: [
      { label: "Graph Explorer",   path: "/graph/explorer", tier: "advanced" },
      { label: "Query Builder",    path: "/graph/query", tier: "advanced" },
      { label: "Communities",      path: "/graph/communities", tier: "advanced" },
    ],
  },
  {
    label: "Ontology Browser",        
    icon: <Network size={16}/>, 
    path: "/ontology",
    tier: "advanced",
    description: "Entity types and relationship definitions",
    children: [
      { label: "Entity Browser",   path: "/ontology/entities", tier: "advanced" },
      { label: "Extraction Jobs",  path: "/ontology/extractions", tier: "advanced" },
      { label: "Validation",       path: "/ontology/validation", tier: "advanced" },
    ],
  },
  {
    label: "Agent Workflows", 
    icon: <Bot size={16}/>, 
    path: "/agents",
    tier: "advanced",
    description: "AI agent orchestration and monitoring",
    children: [
      { label: "Workflow Dashboard",  path: "/agents/dashboard", tier: "standard" },
      { label: "Business Cases",      path: "/agents/business-cases", tier: "standard" },
    ],
  },
  {
    label: "Audit & Provenance", 
    icon: <History size={16}/>, 
    path: "/audit",
    tier: "advanced",
    description: "Full audit trails and compliance reports",
    children: [
      { label: "Decision Traces",    path: "/audit/traces", tier: "standard" },
      { label: "Lineage Explorer",   path: "/audit/lineage", tier: "advanced" },
      { label: "Compliance Reports", path: "/audit/reports", tier: "advanced" },
    ],
  },
];

/**
 * Tier 3 (Admin): Governance controls and tenant configuration
 * - Formula Governance, Benchmark Policies, Variable Registry, Data Sources, Pack Management
 */
const TIER_3_NAV: NavItem[] = [
  { 
    label: "Command Center",      
    icon: <LayoutDashboard size={16}/>, 
    path: "/command-center",
    tier: "standard",
    description: "Overview dashboard"
  },
  {
    label: "Formula Governance", 
    icon: <FlaskConical size={16}/>, 
    path: "/admin/formulas",
    tier: "admin",
    description: "Formula lifecycle management and approvals",
    badge: "Admin",
    children: [
      { label: "Formula Registry",  path: "/admin/formulas", tier: "admin" },
      { label: "Version History",   path: "/admin/formulas/versions", tier: "admin" },
      { label: "Approval Queue",    path: "/admin/formulas/approvals", tier: "admin" },
    ],
  },
  {
    label: "Benchmark Policies",  
    icon: <BarChart3 size={16}/>, 
    path: "/admin/benchmarks",
    tier: "admin",
    description: "Industry benchmarks and policy configuration",
    badge: "Admin",
    children: [
      { label: "Benchmark Library", path: "/admin/benchmarks", tier: "admin" },
      { label: "Policy Config",     path: "/admin/benchmarks/policies", tier: "admin" },
    ],
  },
  {
    label: "Variable Registry",   
    icon: <ListChecks size={16}/>, 
    path: "/admin/variables",
    tier: "admin",
    description: "Variable definitions and source bindings",
    badge: "Admin",
    children: [
      { label: "Variable Catalog",  path: "/admin/variables", tier: "admin" },
      { label: "Source Bindings",   path: "/admin/variables/bindings", tier: "admin" },
    ],
  },
  {
    label: "Data Sources",        
    icon: <Database size={16}/>, 
    path: "/data-sources",
    tier: "admin",
    description: "Data source configuration and management",
    badge: "Admin",
    children: [
      { label: "Scraping Targets",  path: "/data-sources/targets", tier: "admin" },
      { label: "Ingestion Jobs",    path: "/data-sources/jobs", tier: "admin" },
    ],
  },
  {
    label: "Pack Management",     
    icon: <Layers size={16}/>, 
    path: "/admin/packs",
    tier: "admin",
    description: "Value pack authoring and distribution",
    badge: "Admin",
  },
  {
    label: "Permissions",         
    icon: <KeyRound size={16}/>, 
    path: "/admin/permissions",
    tier: "admin",
    description: "Role-based access control and teams",
    badge: "Admin",
    children: [
      { label: "Roles & Access",    path: "/admin/permissions", tier: "admin" },
      { label: "Teams",             path: "/admin/permissions/teams", tier: "admin" },
    ],
  },
  {
    label: "Audit / Change Log",  
    icon: <History size={16}/>, 
    path: "/audit",
    tier: "admin",
    description: "System-wide audit and change tracking",
    children: [
      { label: "Decision Traces",   path: "/audit/traces", tier: "standard" },
      { label: "Compliance Reports",path: "/audit/reports", tier: "admin" },
    ],
  },
  { 
    label: "System Settings",     
    icon: <SlidersHorizontal size={16}/>, 
    path: "/settings",
    tier: "admin",
    description: "Tenant-wide system configuration",
    badge: "Admin"
  },
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

// ── Sub-components ─────────────────────────────────────────────────────────────

interface SidebarItemProps {
  item: NavItem;
  currentTier: UserTier;
}

function SidebarItem({ item, currentTier }: SidebarItemProps) {
  const [location] = useLocation();
  const isActive = location.startsWith(item.path);
  const [open, setOpen] = useState(isActive);
  
  const tierStyle = TIER_STYLES[item.tier];

  // Progressive disclosure: hide advanced items in standard mode
  if (currentTier === "standard" && item.tier !== "standard") {
    return null;
  }

  return (
    <div className="group">
      <Link href={item.path}>
        <div
          className={cn(
            "flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-[12px] font-medium transition-all select-none cursor-pointer",
            isActive
              ? tierStyle.active
              : "text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900",
            item.tier === "admin" && !isActive && "hover:bg-amber-50/30"
          )}
          onClick={() => item.children && setOpen(o => !o)}
        >
          <span className={cn("shrink-0", isActive ? tierStyle.icon : "text-neutral-400 group-hover:text-neutral-600")}>
            {item.icon}
          </span>
          <span className="flex-1 truncate">{item.label}</span>
          {item.badge && (
            <span className={cn("text-[9px] px-1.5 py-0.5 rounded border font-semibold", tierStyle.badge)}>
              {item.badge}
            </span>
          )}
          {item.children && (
            <span className="text-neutral-400 transition-transform">
              {open ? <ChevronDown size={12}/> : <ChevronRight size={12}/>}
            </span>
          )}
        </div>
      </Link>
      
      {item.children && open && (
        <div className="ml-4 mt-1 border-l-2 border-neutral-200 pl-3 space-y-0.5">
          {item.children.map(child => {
            // Progressive disclosure for children
            if (currentTier === "standard" && child.tier === "advanced") {
              return null;
            }
            
            const childActive = location === child.path;
            return (
              <Link key={child.path} href={child.path}>
                <div className={cn(
                  "px-2.5 py-1.5 rounded-md text-[11px] transition-colors cursor-pointer",
                  childActive
                    ? tierStyle.active
                    : "text-neutral-500 hover:text-neutral-800 hover:bg-neutral-100"
                )}>
                  {child.label}
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

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
                isAdvancedModeEnabled ? "translate-x-4.5" : "translate-x-0.5"
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
  // Determine which navigation to show based on tier and advanced mode
  const getNavItems = useCallback((): NavItem[] => {
    if (currentTier === "admin") {
      return TIER_3_NAV;
    }
    if (currentTier === "advanced" || isAdvancedModeEnabled) {
      return TIER_2_NAV;
    }
    return TIER_1_NAV;
  }, [currentTier, isAdvancedModeEnabled]);

  const navItems = getNavItems();

  return (
    <aside className="w-[240px] shrink-0 bg-white border-r border-neutral-200 overflow-y-auto z-20 flex flex-col h-full">
      {/* Navigation Items */}
      <div className="flex-1 py-4 px-2 space-y-1">
        {navItems.map(item => (
          <SidebarItem 
            key={`${item.path}-${item.label}`} 
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
