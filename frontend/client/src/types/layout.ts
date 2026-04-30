export type AgentChatMode = "closed" | "modal" | "panel";

export interface LayoutState {
  leftNavCollapsed: boolean;
  mobileNavOpen: boolean;
  agentMode: AgentChatMode;
}
