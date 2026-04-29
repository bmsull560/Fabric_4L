/**
 * Intelligence Workspace — Shared Types
 */
import type { ComponentType } from "react";

export interface WorkspaceTabProps {
  accountId: string;
  workspaceId?: string;
  organizationId?: string;
}

export type WorkspaceTabId =
  | "signals"
  | "stakeholders"
  | "ontology-match"
  | "enrichment"
  | "hypotheses"
  | "drivers"
  | "evidence"
  | "alternatives"
  | "solution-cost"
  | "calculator"
  | "value-model"
  | "value-case"
  | "value-realization";

export type WorkspaceTabStatus = "active" | "stub";

export type WorkspaceTabCategory = "input" | "reasoning" | "output";

export interface WorkspaceTabDef {
  id: WorkspaceTabId;
  label: string;
  description: string;
  component: ComponentType<WorkspaceTabProps> | null;
  queryKey?: string;
  status: WorkspaceTabStatus;
  category: WorkspaceTabCategory;
}
