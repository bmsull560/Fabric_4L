/**
 * AppShell — Refined Enterprise SaaS layout
 * Three-mode navigation per gap analysis spec:
 *   Standard  — task-oriented for business users
 *   Advanced  — power-user modeling & inspection tools
 *   Admin     — tenant governance & configuration
 *
 * Fixed sidebar (216px) + sticky header (52px) + scrollable main content
 */
import { useState, useCallback } from "react";
import { Link } from "wouter";
import { TieredNav, type UserTier } from "./navigation/TieredNav";
import { Search, Bell, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { useI18n } from "@/i18n";

// ── Types ─────────────────────────────────────────────────────────────────────

type UserMode = "standard" | "advanced" | "admin";

const MODE_PILL: Record<UserMode, string> = {
  standard: "bg-blue-50 text-blue-700 border-blue-200",
  advanced: "bg-violet-50 text-violet-700 border-violet-200",
  admin:    "bg-amber-50 text-amber-700 border-amber-200",
};

// ── Main AppShell ─────────────────────────────────────────────────────────────

interface AppShellProps {
  children: React.ReactNode;
  currentTier?: UserTier;
  effectiveTier?: UserTier;
}

export default function AppShell({ 
  children, 
  currentTier: externalCurrentTier,
  effectiveTier: externalEffectiveTier 
}: AppShellProps) {
  const { t } = useI18n();
  // Use internal state if external props not provided (backward compatibility)
  const [internalMode, setInternalMode] = useState<UserTier>("standard");
  const [isAdvancedMode, setIsAdvancedMode] = useState(false);
  
  const currentTier = externalCurrentTier || internalMode;
  const effectiveTier = externalEffectiveTier || (isAdvancedMode && internalMode === "standard" ? "advanced" : internalMode);
  
  const handleTierChange = useCallback((tier: UserTier) => {
    if (!externalCurrentTier) {
      setInternalMode(tier);
    }
  }, [externalCurrentTier]);
  
  const handleAdvancedModeToggle = useCallback((enabled: boolean) => {
    setIsAdvancedMode(enabled);
  }, []);

  return (
    <div className="flex flex-col h-screen bg-background overflow-hidden">
      {/* Header */}
      <header className="h-[52px] shrink-0 bg-white border-b border-neutral-200 flex items-center px-4 gap-4 z-30">
        <Link href="/command-center">
          <div className="flex flex-col leading-none cursor-pointer select-none">
            <span className="text-[14px] font-extrabold text-neutral-900 tracking-tight">{t("appShell.platformName")}</span>
            <span className="text-[10px] text-neutral-400 font-normal">{t("appShell.platformTagline")}</span>
          </div>
        </Link>
        <div className="flex-1 max-w-xs">
          <div className="flex items-center gap-2 h-7 px-3 bg-neutral-100 rounded-full text-[11px] text-neutral-400 border border-neutral-200">
            <Search size={11} className="shrink-0"/>
            <span>{t("appShell.searchPlaceholder")}</span>
          </div>
        </div>
        <div className="ml-auto flex items-center gap-3">
          {/* Active mode pill */}
          <span className={cn(
            "text-[10px] font-semibold px-2.5 py-0.5 rounded-full border",
            MODE_PILL[currentTier as UserMode]
          )}>
            {`${t(`appShell.modes.${currentTier as UserMode}`)} ${t("appShell.modeSuffix")}`}
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
        {/* Sidebar - Using TieredNav for progressive disclosure */}
        <TieredNav
          currentTier={currentTier}
          onTierChange={handleTierChange}
          isAdvancedModeEnabled={isAdvancedMode}
          onAdvancedModeToggle={handleAdvancedModeToggle}
        />

        {/* Main */}
        <main className="flex-1 overflow-y-auto bg-neutral-50" data-tier={effectiveTier}>
          {children}
        </main>
      </div>
    </div>
  );
}
