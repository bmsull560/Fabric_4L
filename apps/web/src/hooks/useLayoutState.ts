import { useCallback, useState } from "react";
import type { AgentChatMode, LayoutState } from "@/types/layout";

export interface LayoutActions {
  toggleLeftNav: () => void;
  openAgentModal: () => void;
  closeAgent: () => void;
  expandAgentPanel: () => void;
  minimizeAgentPanel: () => void;
  setMobileNavOpen: (open: boolean) => void;
}

export function useLayoutState(): LayoutState & LayoutActions {
  const [leftNavCollapsed, setLeftNavCollapsed] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
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

  return {
    leftNavCollapsed,
    mobileNavOpen,
    agentMode,
    toggleLeftNav,
    openAgentModal,
    closeAgent,
    expandAgentPanel,
    minimizeAgentPanel,
    setMobileNavOpen,
  };
}
