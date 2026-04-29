/**
 * Intelligence Workspace — Tab Registry
 *
 * Single source of truth for all workspace tabs.
 * Navigation, routing, and shell components all derive from this registry.
 */
import { lazy } from "react";
import type { WorkspaceTabDef, WorkspaceTabId } from "./types";

// ── Lazy-loaded tab components ────────────────────────────────────────────────
const SignalsTab = lazy(() => import("./tabs/signals/SignalsTab"));
const StakeholdersTab = lazy(() => import("./tabs/stakeholders/StakeholdersTab"));
const OntologyMatchTab = lazy(() => import("./tabs/ontology-match/OntologyMatchTab"));
const EnrichmentTab = lazy(() => import("./tabs/enrichment/EnrichmentTab"));
const HypothesesTab = lazy(() => import("./tabs/hypotheses/HypothesesTab"));
const DriversTab = lazy(() => import("./tabs/drivers/DriversTab"));
const EvidenceTab = lazy(() => import("./tabs/evidence/EvidenceTab"));
const AlternativesTab = lazy(() => import("./tabs/alternatives/AlternativesTab"));
const SolutionCostTab = lazy(() => import("./tabs/solution-cost/SolutionCostTab"));
const ROITab = lazy(() => import("./tabs/calculator/ROITab"));
const ValueModelTab = lazy(() => import("./tabs/value-model/ValueModelTab"));
const NarrativeTab = lazy(() => import("./tabs/value-case/NarrativeTab"));
const ActionPlanTab = lazy(() => import("./tabs/value-realization/ActionPlanTab"));

// ── Registry ──────────────────────────────────────────────────────────────────
export const workspaceTabs: WorkspaceTabDef[] = [
  {
    id: "signals",
    label: "Signals",
    description: "Displays raw market signals and triggers workspace generation.",
    component: SignalsTab,
    queryKey: "signals",
    status: "active",
    category: "input",
  },
  {
    id: "enrichment",
    label: "Account Enrichment",
    description: "Shows deep account enrichment data including firmographics and tech stack.",
    component: EnrichmentTab,
    status: "active",
    category: "input",
  },
  {
    id: "stakeholders",
    label: "Stakeholders",
    description: "Identifies key buyer personas and their priorities.",
    component: StakeholdersTab,
    queryKey: "stakeholders",
    status: "active",
    category: "input",
  },
  {
    id: "ontology-match",
    label: "Value Ontology",
    description: "Maps account context to the value ontology.",
    component: OntologyMatchTab,
    status: "stub",
    category: "reasoning",
  },
  {
    id: "hypotheses",
    label: "Value Hypotheses",
    description: "Manages AI-generated value hypotheses for the account.",
    component: HypothesesTab,
    status: "active",
    category: "reasoning",
  },
  {
    id: "drivers",
    label: "Value Drivers",
    description: "Maps signals to specific business value drivers.",
    component: DriversTab,
    queryKey: "drivers",
    status: "active",
    category: "reasoning",
  },
  {
    id: "evidence",
    label: "Evidence",
    description: "Lists verified evidence points supporting the drivers.",
    component: EvidenceTab,
    queryKey: "evidence",
    status: "active",
    category: "reasoning",
  },
  {
    id: "alternatives",
    label: "Alternatives",
    description: "Competitor and alternative solution comparison.",
    component: AlternativesTab,
    status: "stub",
    category: "input",
  },
  {
    id: "solution-cost",
    label: "Solution Cost",
    description: "Pricing and cost inputs for the business case.",
    component: SolutionCostTab,
    status: "stub",
    category: "input",
  },
  {
    id: "calculator",
    label: "ROI Calculator",
    description: "Interactive ROI calculator inputs and outputs.",
    component: ROITab,
    status: "active",
    category: "reasoning",
  },
  {
    id: "value-model",
    label: "Value Model",
    description: "Builds the quantitative value model behind the business case.",
    component: ValueModelTab,
    queryKey: "value-model",
    status: "active",
    category: "reasoning",
  },
  {
    id: "value-case",
    label: "Executive Value Case",
    description: "Generates the final written narrative and messaging.",
    component: NarrativeTab,
    queryKey: "narrative",
    status: "active",
    category: "output",
  },
  {
    id: "value-realization",
    label: "Realization Plan",
    description: "Generates a step-by-step realization plan that turns validated value hypotheses into customer-facing milestones, owners, actions, and success metrics.",
    component: ActionPlanTab,
    queryKey: "action-plan",
    status: "active",
    category: "output",
  },
];

// ── Helpers ───────────────────────────────────────────────────────────────────
export const DEFAULT_TAB: WorkspaceTabId = "signals";

export function getTabDef(tabId: WorkspaceTabId): WorkspaceTabDef | undefined {
  return workspaceTabs.find((t) => t.id === tabId);
}

export function isValidTab(tabId: string | undefined): tabId is WorkspaceTabId {
  return Boolean(tabId) && workspaceTabs.some((t) => t.id === tabId);
}

export function getTabOrDefault(tabId: string | undefined): WorkspaceTabId {
  return isValidTab(tabId) ? tabId : DEFAULT_TAB;
}

export function getActiveTabDefs(): WorkspaceTabDef[] {
  return workspaceTabs.filter((t) => t.status === "active");
}
