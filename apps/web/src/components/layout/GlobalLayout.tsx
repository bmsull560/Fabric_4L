"use client";

import { Suspense, useCallback, useState } from "react";
import { Outlet, useMatch } from "react-router-dom";
import { Spinner } from "@/components/ui/spinner";
import { LeftNavigation } from "./LeftNavigation";
import { AppHeader } from "./AppHeader";
import { AgentChat } from "./AgentChat";
import { AgentSidePanel } from "./AgentSidePanel";
import { MobileNavigation } from "./MobileNavigation";
import type { AgentChatMode } from "@/types/layout";
import type { UserTier } from "@/navigation/navHelpers";

// ── Workspace Layout Wrapper ──────────────────────────────────────────────────
// Workspace routes (intelligence, hypothesis, drivers, calculator, etc.) need
// full-bleed layout without padding/max-width constraints so their internal
// shells (account header + tab bar + scrollable canvas + right rail) fill the
// entire content area. Regular pages keep the padded container.

export function WorkspaceLayoutWrapper({ children }: { children: React.ReactNode }) {
  // Hooks must be called unconditionally on every render — do not use ||
  // short-circuiting because it changes the hook count between renders.
  const matchIntelligence = useMatch("/intelligence/*");
  const matchHypothesis = useMatch("/hypothesis/*");
  const matchDrivers = useMatch("/drivers/*");
  const matchCalculator = useMatch("/calculator/*");
  const matchValueCase = useMatch("/value-case/*");
  const matchRealization = useMatch("/realization/*");
  const matchPersonal = useMatch("/personal/*");
  const matchSettings = useMatch("/settings/*");

  const isWorkspace = Boolean(
    matchIntelligence
      || matchHypothesis
      || matchDrivers
      || matchCalculator
      || matchValueCase
      || matchRealization
  );

  const isSettings = Boolean(matchPersonal || matchSettings);

  const noPadding = isWorkspace || isSettings;

  return (
    <main className="min-h-0 flex-1 overflow-auto">
      {noPadding ? (
        <div className="h-full">
          <Suspense
            fallback={
              <div className="flex h-full min-h-[200px] items-center justify-center">
                <Spinner className="h-6 w-6" />
              </div>
            }
          >
            {children}
          </Suspense>
        </div>
      ) : (
        <div className="mx-auto w-full max-w-screen-2xl p-4 md:p-6">
          <Suspense
            fallback={
              <div className="flex h-full min-h-[200px] items-center justify-center">
                <Spinner className="h-6 w-6" />
              </div>
            }
          >
            {children}
          </Suspense>
        </div>
      )}
    </main>
  );
}

export function GlobalLayout() {
  const [leftNavCollapsed, setLeftNavCollapsed] = useState(false);
  // Mobile navigation uses persistent icon rail (MobilePersistentSidebar).
  // Hamburger menu drawer is not implemented; no open/close state needed.
  const [currentTier, setCurrentTier] = useState<UserTier>("standard");
  const [isAdvancedModeEnabled, setIsAdvancedModeEnabled] = useState(false);
  const [agentMode, setAgentMode] = useState<AgentChatMode>("closed");

  const toggleLeftNav = useCallback(() => {
    setLeftNavCollapsed((current) => !current);
  }, []);

  const openAgentModal = useCallback(() => {
    setAgentMode("modal");
  }, []);

  const closeAgent = useCallback(() => {
    setAgentMode("closed");
  }, []);

  const expandAgentPanel = useCallback(() => {
    setAgentMode("panel");
    setLeftNavCollapsed(true);
  }, []);

  const minimizeAgentPanel = useCallback(() => {
    setAgentMode("modal");
  }, []);

  const agentPanelOpen = agentMode === "panel";

  return (
    <div
      className={[
        "grid h-screen overflow-hidden bg-background text-foreground",
        agentPanelOpen
          ? "grid-cols-[auto_minmax(0,1fr)_minmax(360px,420px)]"
          : "grid-cols-[auto_minmax(0,1fr)]",
      ].join(" ")}
    >
      <LeftNavigation
        collapsed={leftNavCollapsed}
        onToggle={toggleLeftNav}
      />

      <MobileNavigation
        currentTier={currentTier}
        onTierChange={setCurrentTier}
        isAdvancedModeEnabled={isAdvancedModeEnabled}
        onAdvancedModeToggle={setIsAdvancedModeEnabled}
      />

      <div className="flex min-w-0 flex-col overflow-hidden">
        <AppHeader
          onToggleLeftNav={toggleLeftNav}
          // Mobile nav is persistent icon rail; no hamburger toggle needed.
          leftNavCollapsed={leftNavCollapsed}
        />

        <main className="min-h-0 flex-1 overflow-auto">
          <WorkspaceLayoutWrapper>
            <Outlet />
          </WorkspaceLayoutWrapper>
        </main>
      </div>

      {agentPanelOpen && (
        <AgentSidePanel
          onClose={closeAgent}
          onMinimize={minimizeAgentPanel}
        />
      )}

      {agentMode !== "panel" && (
        <AgentChat
          mode={agentMode}
          onOpen={openAgentModal}
          onClose={closeAgent}
          onExpand={expandAgentPanel}
        />
      )}
    </div>
  );
}
