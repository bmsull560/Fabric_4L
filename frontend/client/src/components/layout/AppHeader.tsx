"use client";

import { Menu, PanelLeftClose, PanelLeftOpen, Search, Bell } from "lucide-react";

interface AppHeaderProps {
  leftNavCollapsed: boolean;
  onToggleLeftNav: () => void;
  onOpenMobileNav: () => void;
}

export function AppHeader({
  leftNavCollapsed,
  onToggleLeftNav,
  onOpenMobileNav,
}: AppHeaderProps) {
  return (
    <header className="z-20 flex h-14 shrink-0 items-center justify-between border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="flex min-w-0 items-center gap-2">
        <button
          type="button"
          onClick={onOpenMobileNav}
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border hover:bg-accent md:hidden"
          aria-label="Open navigation"
        >
          <Menu className="h-4 w-4" />
        </button>

        <button
          type="button"
          onClick={onToggleLeftNav}
          className="hidden h-9 w-9 items-center justify-center rounded-md border hover:bg-accent md:inline-flex"
          aria-label={leftNavCollapsed ? "Expand navigation" : "Collapse navigation"}
        >
          {leftNavCollapsed ? (
            <PanelLeftOpen className="h-4 w-4" />
          ) : (
            <PanelLeftClose className="h-4 w-4" />
          )}
        </button>

        <div className="min-w-0">
          <div className="text-sm font-medium">Settings</div>
          <div className="truncate text-xs text-muted-foreground">
            Configuration Center
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          type="button"
          className="hidden h-9 items-center gap-2 rounded-md border px-3 text-sm text-muted-foreground hover:bg-accent md:inline-flex"
        >
          <Search className="h-4 w-4" />
          Search
        </button>

        <button
          type="button"
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border hover:bg-accent"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
}
