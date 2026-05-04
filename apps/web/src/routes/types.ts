import type { ComponentType, ReactNode } from "react";

export type RequiredUserTier = "standard" | "advanced" | "admin";

export interface AuthenticatedTierProps {
  currentTier: RequiredUserTier;
  effectiveTier: RequiredUserTier;
}

export interface RouteComposerContext {
  tierProps: AuthenticatedTierProps;
  AuthenticatedRoute: ComponentType<{
    children: ReactNode;
    requiredTier?: RequiredUserTier;
    currentTier: RequiredUserTier;
    effectiveTier: RequiredUserTier;
  }>;
  Navigate: ComponentType<{ to: string }>;
  AccountContextSync: ComponentType;
  WorkspaceContextRedirect: ComponentType<{
    workspace: "intelligence" | "studio";
    tab?: string;
  }>;
  IntelligenceRedirect: ComponentType;
  StudioRedirect: ComponentType;
  BillingRoute: ComponentType<{ children: ReactNode }>;
}
