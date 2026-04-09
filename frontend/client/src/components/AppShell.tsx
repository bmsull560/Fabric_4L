/**
 * AppShell — Refined Enterprise SaaS layout
 * Fixed sidebar (200px) + sticky header (52px) + scrollable main content
 */
import { useState } from "react";
import { Link, useLocation } from "wouter";
import {
  LayoutDashboard, Settings, Database, Network, GitBranch,
  Share2, Bot, History, ChevronDown, ChevronRight, Bell, Search, User
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  icon: React.ReactNode;
  path: string;
  children?: { label: string; path: string }[];
}

const NAV: NavItem[] = [
  { label: "Command Center",    icon: <LayoutDashboard size={14}/>, path: "/command-center" },
  { label: "Extraction Engine", icon: <Settings size={14}/>,        path: "/extraction-engine" },
  {
    label: "Data Sources", icon: <Database size={14}/>, path: "/data-sources",
    children: [
      { label: "Scraping Targets", path: "/data-sources/targets" },
      { label: "Ingestion Jobs",   path: "/data-sources/jobs" },
    ],
  },
  {
    label: "Ontology", icon: <Network size={14}/>, path: "/ontology",
    children: [
      { label: "Entity Browser",   path: "/ontology/entities" },
      { label: "Extraction Jobs",  path: "/ontology/extractions" },
      { label: "Validation",       path: "/ontology/validation" },
    ],
  },
  {
    label: "Value Trees", icon: <GitBranch size={14}/>, path: "/value-trees",
    children: [
      { label: "Tree Explorer",  path: "/value-trees/explorer" },
      { label: "Normalization",  path: "/value-trees/normalization" },
      { label: "Formulas",       path: "/value-trees/formulas" },
    ],
  },
  {
    label: "Knowledge Graph", icon: <Share2 size={14}/>, path: "/graph",
    children: [
      { label: "Graph Explorer", path: "/graph/explorer" },
      { label: "Query Builder",  path: "/graph/query" },
      { label: "Communities",    path: "/graph/communities" },
    ],
  },
  {
    label: "Agent Workflows", icon: <Bot size={14}/>, path: "/agents",
    children: [
      { label: "Workflow Dashboard",  path: "/agents/dashboard" },
      { label: "Whitespace Analysis", path: "/agents/whitespace" },
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

export default function AppShell({ children }: { children: React.ReactNode }) {
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
        <div className="ml-auto flex items-center gap-2">
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
        <aside className="w-[200px] shrink-0 bg-white border-r border-neutral-200 overflow-y-auto py-3 px-2 space-y-0.5 z-20">
          {NAV.map(item => <SidebarItem key={item.path} item={item} />)}
        </aside>

        {/* Main */}
        <main className="flex-1 overflow-y-auto bg-neutral-50">
          {children}
        </main>
      </div>
    </div>
  );
}
