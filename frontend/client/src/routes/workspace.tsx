/**
 * WorkspaceRoutes — Intelligence & Studio workspace routes
 *
 * Intelligence (4 tabs): Signals, Stakeholder Map, Ontology Match, Enrichment
 * Studio (legacy): Action Plan, Value Model, Narrative
 *
 * Other workflow steps (Hypothesis, Driver Tree, Calculator, Value Case, Realization)
 * are handled by their own top-level routes in App.tsx.
 */
import { Route } from "wouter";
import type { ComponentType } from "react";
import type { RouteComposerContext } from "./types";

interface WorkspacePages {
  SignalsTab: ComponentType;
  DriversTab: ComponentType;
  EvidenceTab: ComponentType;
  StakeholdersTab: ComponentType;
  EnrichmentTab: ComponentType;
  HypothesesTab: ComponentType;
  CompetitiveTab: ComponentType;
  ROITab: ComponentType;
  EvidenceLibraryTab: ComponentType;
  ActionPlanTab: ComponentType;
  ValueModelTab: ComponentType;
  NarrativeTab: ComponentType;
  StudioEnrichmentTab: ComponentType;
  StudioCompetitiveTab: ComponentType;
  StudioROITab: ComponentType;
  StudioEvidenceTab: ComponentType;
}

export function WorkspaceRoutes(context: RouteComposerContext, p: WorkspacePages) {
  const { tierProps, AuthenticatedRoute, WorkspaceContextRedirect, AccountContextSync, IntelligenceRedirect, StudioRedirect } = context;
  return <>
    {/* ── Intelligence workspace (4 tabs) ── */}
    <Route path="/intelligence"><AuthenticatedRoute {...tierProps}><WorkspaceContextRedirect workspace="intelligence" /></AuthenticatedRoute></Route>
    <Route path="/intelligence/:accountId"><AuthenticatedRoute {...tierProps}><AccountContextSync /><IntelligenceRedirect /></AuthenticatedRoute></Route>
    <Route path="/intelligence/:accountId/signals"><AuthenticatedRoute {...tierProps}><AccountContextSync /><p.SignalsTab /></AuthenticatedRoute></Route>
    <Route path="/intelligence/:accountId/stakeholders"><AuthenticatedRoute {...tierProps}><AccountContextSync /><p.StakeholdersTab /></AuthenticatedRoute></Route>
    <Route path="/intelligence/:accountId/enrichment"><AuthenticatedRoute {...tierProps}><AccountContextSync /><p.EnrichmentTab /></AuthenticatedRoute></Route>

    {/* ── Legacy studio routes (backward compat) ── */}
    <Route path="/studio"><AuthenticatedRoute {...tierProps}><WorkspaceContextRedirect workspace="studio" /></AuthenticatedRoute></Route>
    <Route path="/studio/:tab"><AuthenticatedRoute {...tierProps}><WorkspaceContextRedirect workspace="studio" /></AuthenticatedRoute></Route>
    <Route path="/studio/:accountId"><AuthenticatedRoute {...tierProps}><AccountContextSync /><StudioRedirect /></AuthenticatedRoute></Route>
    <Route path="/studio/:accountId/action-plan"><AuthenticatedRoute {...tierProps}><AccountContextSync /><p.ActionPlanTab /></AuthenticatedRoute></Route>
    <Route path="/studio/:accountId/value-model"><AuthenticatedRoute {...tierProps}><AccountContextSync /><p.ValueModelTab /></AuthenticatedRoute></Route>
    <Route path="/studio/:accountId/narrative"><AuthenticatedRoute {...tierProps}><AccountContextSync /><p.NarrativeTab /></AuthenticatedRoute></Route>
    <Route path="/studio/:accountId/enrichment"><AuthenticatedRoute {...tierProps}><AccountContextSync /><p.StudioEnrichmentTab /></AuthenticatedRoute></Route>
    <Route path="/studio/:accountId/competitive"><AuthenticatedRoute {...tierProps}><AccountContextSync /><p.StudioCompetitiveTab /></AuthenticatedRoute></Route>
    <Route path="/studio/:accountId/roi"><AuthenticatedRoute {...tierProps}><AccountContextSync /><p.StudioROITab /></AuthenticatedRoute></Route>
    <Route path="/studio/:accountId/evidence"><AuthenticatedRoute {...tierProps}><AccountContextSync /><p.StudioEvidenceTab /></AuthenticatedRoute></Route>
  </>;
}
