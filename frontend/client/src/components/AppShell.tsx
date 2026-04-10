/**
 * AppShell — Refined Enterprise SaaS layout
 * Three-mode navigation per gap analysis spec:
 *   Standard  — task-oriented for business users
 *   Advanced  — power-user modeling & inspection tools
 *   Admin     — tenant governance & configuration
 *
 * Fixed sidebar (216px) + sticky header (52px) + scrollable main content
 */
import { useState } from "react";
import { Link, useLocation } from "wouter";
import {
  LayoutDashboard, Search, Bell, User, ChevronDown, ChevronRight,
  Briefcase, FileText, Workflow, Shield, BookOpen, GitBranch,
  Share2, Network, History, Settings, Database, Bot, Layers,
  FlaskConical, BarChart3, ListChecks, KeyRound, SlidersHorizontal,
  Users, FolderKanban, Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ── Types ─────────────────────────────────────────────────────────────────────

type UserMode = "standard" | "advanced" | "admin";

interface NavItem {
  label: string;
  icon: React.ReactNode;
  path: string;
  children?: { label: string; path: string }[];
}

// ── Navigation definitions per mode ──────────────────────────────────────────

const STANDARD_NAV: NavItem[] = [
  { label: "Command Center",  icon: <LayoutDashboard size={14}/>, path: "/command-center" },
  { label: "Value Packs",     icon: <Sparkles size={14}/>,        path: "/value-packs" },
  {
    label: "Business Cases", icon: <Briefcase size={14}/>, path: "/agents",
    children: [
      { label: "All Cases",         path: "/agents/business-cases" },
      { label: "Workflow Dashboard", path: "/agents/dashboard" },
    ],
  },
  {
    label: "Research",       icon: <BookOpen size={14}/>, path: "/research",
    children: [
      { label: "Accounts",          path: "/data-sources/targets" },
      { label: "Ingestion Jobs",    path: "/data-sources/jobs" },
    ],
  },
  {
    label: "Evidence",       icon: <Shield size={14}/>, path: "/audit",
    children: [
      { label: "Decision Traces",   path: "/audit/traces" },
      { label: "Lineage Explorer",  path: "/audit/lineage" },
    ],
  },
  { label: "Settings",       icon: <Settings size={14}/>,         path: "/settings" },
];

const ADVANCED_NAV: NavItem[] = [
  { label: "Command Center",    icon: <LayoutDashboard size={14}/>, path: "/command-center" },
  { label: "Extraction Engine", icon: <FolderKanban size={14}/>,    path: "/extraction-engine" },
  {
    label: "Value Models",   icon: <GitBranch size={14}/>, path: "/value-trees",
    children: [
      { label: "Tree Explorer",    path: "/value-trees/explorer" },
      { label: "Normalization",    path: "/value-trees/normalization" },
      { label: "Formula Studio",   path: "/value-trees/formulas" },
    ],
  },
  {
    label: "Graph Explorer",  icon: <Share2 size={14}/>, path: "/graph",
    children: [
      { label: "Graph Explorer",   path: "/graph/explorer" },
      { label: "Query Builder",    path: "/graph/query" },
      { label: "Communities",      path: "/graph/communities" },
    ],
  },
  {
    label: "Ontology",        icon: <Network size={14}/>, path: "/ontology",
    children: [
      { label: "Entity Browser",   path: "/ontology/entities" },
      { label: "Extraction Jobs",  path: "/ontology/extractions" },
      { label: "Validation",       path: "/ontology/validation" },
    ],
  },
  {
    label: "Agent Workflows", icon: <Bot size={14}/>, path: "/agents",
    children: [
      { label: "Workflow Dashboard",  path: "/agents/dashboard" },
      { label: "Business Cases",      path: "/agents/business-cases" },
    ],
  },
  {
    label: "Audit & Provenance", icon: <History size={14}/>, path: "/audit",
    children: [
      { label: "Decision Traces",    path: "/audit/traces" },
      { label: "Lineage Explorer",   path: "/audit/lineage" },
      { label: "Compliance Reports", path: "/audit/reports" },
    ],
  },
];

const ADMIN_NAV: NavItem[] = [
  { label: "Command Center",      icon: <LayoutDashboard size={14}/>, path: "/command-center" },
  {
    label: "Formula Governance", icon: <FlaskConical size={14}/>, path: "/admin/formulas",
    children: [
      { label: "Formula Registry",  path: "/admin/formulas" },
      { label: "Version History",   path: "/admin/formulas/versions" },
      { label: "Approval Queue",    path: "/admin/formulas/approvals" },
    ],
  },
  {
    label: "Benchmark Policies",  icon: <BarChart3 size={14}/>, path: "/admin/benchmarks",
    children: [
      { label: "Benchmark Library", path: "/admin/benchmarks" },
      { label: "Policy Config",     path: "/admin/benchmarks/policies" },
    ],
  },
  {
    label: "Variable Registry",   icon: <ListChecks size={14}/>, path: "/admin/variables",
    children: [
      { label: "Variable Catalog",  path: "/admin/variables" },
      { label: "Source Bindings",   path: "/admin/variables/bindings" },
    ],
  },
  {
    label: "Data Sources",        icon: <Database size={14}/>, path: "/data-sources",
    children: [
      { label: "Scraping Targets",  path: "/data-sources/targets" },
      { label: "Ingestion Jobs",    path: "/data-sources/jobs" },
    ],
  },
  {
    label: "Permissions",         icon: <KeyRound size={14}/>, path: "/admin/permissions",
    children: [
      { label: "Roles & Access",    path: "/admin/permissions" },
      { label: "Teams",             path: "/admin/permissions/teams" },
    ],
  },
  {
    label: "Audit / Change Log",  icon: <History size={14}/>, path: "/audit",
    children: [
      { label: "Decision Traces",   path: "/audit/traces" },
      { label: "Compliance Reports",path: "/audit/reports" },
    ],
  },
  { label: "Settings",            icon: <SlidersHorizontal size={14}/>, path: "/settings" },
];

const MODE_LABELS: Record<UserMode, string> = {
  standard: "Standard",
  advanced: "Advanced",
  admin:    "Admin",
};

const MODE_COLORS: Record<UserMode, string> = {
  standard: "bg-blue-600 text-white",
  advanced: "bg-violet-600 text-white",
  admin:    "bg-amber-600 text-white",
};

const MODE_PILL: Record<UserMode, string> = {
  standard: "bg-blue-50 text-blue-700 border-blue-200",
  advanced: "bg-violet-50 text-violet-700 border-violet-200",
  admin:    "bg-amber-50 text-amber-700 border-amber-200",
};

// ── Sub-components ────────────────────────────────────────────────────────────

function SidebarItem({ item }: { item: NavItem }) {
  const [location] = useLocation();
  const isActive = location.startsWith(item.path);
  const [open, setOpen] = useState(isActive);

  return (
    <div>
      <Link href={item.path}>
        <div
          className={cn(
            "flex items-center gap-2 px-3 py-2 rounded-md text-[12px] font-medium transition-colors select-none",
            isActive
              ? "bg-blue-50 text-blue-700"
              : "text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900"
          )}
          onClick={() => item.children && setOpen(o => !o)}
        >
          <span className={cn("shrink-0", isActive ? "text-blue-600" : "text-neutral-400")}>
            {item.icon}
          </span>
          <span className="flex-1 truncate">{item.label}</span>
          {item.children && (
            <span className="text-neutral-400">
              {open ? <ChevronDown size={11}/> : <ChevronRight size={11}/>}
            </span>
          )}
        </div>
      </Link>
      {item.children && open && (
        <div className="ml-5 mt-0.5 border-l border-neutral-200 pl-3 pb-1 space-y-0.5">
          {item.children.map(child => {
            const childActive = location === child.path;
            return (
              <Link key={child.path} href={child.path}>
                <div className={cn(
                  "px-2 py-1.5 rounded text-[11px] transition-colors",
                  childActive
                    ? "text-blue-700 font-semibold"
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

function ModeSwitcher({ mode, onChange }: { mode: UserMode; onChange: (m: UserMode) => void }) {
  return (
    <div className="px-2 pb-3 pt-1">
      <p className="text-[9px] uppercase tracking-widest text-neutral-400 font-semibold px-1 mb-1.5">View mode</p>
      <div className="flex rounded-md overflow-hidden border border-neutral-200 text-[10px] font-semibold">
        {(["standard", "advanced", "admin"] as UserMode[]).map((m) => (
          <button
            key={m}
            onClick={() => onChange(m)}
            className={cn(
              "flex-1 py-1.5 transition-colors capitalize",
              mode === m
                ? MODE_COLORS[m]
                : "bg-white text-neutral-500 hover:bg-neutral-50"
            )}
          >
            {MODE_LABELS[m]}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Main AppShell ─────────────────────────────────────────────────────────────

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [mode, setMode] = useState<UserMode>("standard");

  const nav =
    mode === "standard" ? STANDARD_NAV :
    mode === "advanced" ? ADVANCED_NAV :
    ADMIN_NAV;

  return (
    <div className="flex flex-col h-screen bg-background overflow-hidden">
      {/* Header */}
      <header className="h-[52px] shrink-0 bg-white border-b border-neutral-200 flex items-center px-4 gap-4 z-30">
        <Link href="/command-center">
          <div className="flex flex-col leading-none cursor-pointer select-none">
            <span className="text-[14px] font-extrabold text-neutral-900 tracking-tight">Value Fabric</span>
            <span className="text-[10px] text-neutral-400 font-normal">Intelligence Platform</span>
          </div>
        </Link>
        <div className="flex-1 max-w-xs">
          <div className="flex items-center gap-2 h-7 px-3 bg-neutral-100 rounded-full text-[11px] text-neutral-400 border border-neutral-200">
            <Search size={11} className="shrink-0"/>
            <span>Search entities, domains, cases…</span>
          </div>
        </div>
        <div className="ml-auto flex items-center gap-3">
          {/* Active mode pill */}
          <span className={cn(
            "text-[10px] font-semibold px-2.5 py-0.5 rounded-full border",
            MODE_PILL[mode]
          )}>
            {MODE_LABELS[mode]} mode
          </span>
          <button className="w-7 h-7 rounded-full border border-neutral-200 bg-neutral-50 flex items-center justify-center text-neutral-500 hover:bg-neutral-100 transition-colors">
            <Bell size={12}/>
          </button>
          <button className="w-7 h-7 rounded-full bg-neutral-800 text-white flex items-center justify-center text-[10px] font-bold">
            <User size={12}/>
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-[216px] shrink-0 bg-white border-r border-neutral-200 overflow-y-auto z-20 flex flex-col">
          <div className="flex-1 py-3 px-2 space-y-0.5">
            {nav.map(item => <SidebarItem key={item.path} item={item} />)}
          </div>
          {/* Mode switcher pinned to bottom */}
          <div className="border-t border-neutral-100 mt-2">
            <ModeSwitcher mode={mode} onChange={setMode}/>
          </div>
        </aside>

        {/* Main */}
        <main className="flex-1 overflow-y-auto bg-neutral-50">
          {children}
        </main>
      </div>
    </div>
  );
}
