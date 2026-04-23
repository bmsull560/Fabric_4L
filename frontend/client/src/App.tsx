import { lazy, Suspense, useEffect } from "react";
import {
  AppShell,
  ErrorBoundary,
  Toaster,
  TooltipProvider,
} from "@/components";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AuthProvider, useAuthContext } from "./contexts/AuthContext";
import { useUserTierStore, type UserTier } from "@/hooks";
import { Route, useLocation, useParams } from "wouter";

// ── Navigate Component for wouter ───────────────────────────────────────────
function Navigate({ to }: { to: string }) {
  const [, navigate] = useLocation();
  useEffect(() => { navigate(to); }, [navigate, to]);
  return null;
}

// ── Prospect Setup with Navigation ───────────────────────────────────────────
function ProspectSetupWithNav() {
  const [, navigate] = useLocation();
  return (
    <ProspectSetup
      onNavigateToWorkspace={(path) => navigate(path)}
    />
  );
}

// ── Route-level code splitting ────────────────────────────────────────────────
// Existing pages (preserved)
const LandingPage             = lazy(() => import("./pages/LandingPage"));
const CommandCenter           = lazy(() => import("./pages/CommandCenter"));
const ValueNarrativeHome      = lazy(() => import("./pages/ValueNarrativeHome"));
const ExtractionEngine        = lazy(() => import("./pages/ExtractionEngine"));
const IngestionJobs           = lazy(() => import("./pages/IngestionJobs"));
const OntologyEditor          = lazy(() => import("./pages/OntologyEditor"));
const EntityBrowser           = lazy(() => import("./pages/EntityBrowser"));
const EntityDetail            = lazy(() => import("./pages/EntityDetail"));
const ValueTreeExplorer       = lazy(() => import("./pages/ValueTreeExplorer"));
const FormulaBuilder          = lazy(() => import("./pages/FormulaBuilder"));
const FormulaList             = lazy(() => import("./pages/FormulaList"));
const GraphExplorer           = lazy(() => import("./pages/GraphExplorer"));
const AgentWorkflows          = lazy(() => import("./pages/AgentWorkflows"));
const BusinessCase            = lazy(() => import("./pages/BusinessCase"));
const InteractiveBusinessCase = lazy(() => import("./pages/InteractiveBusinessCase"));
const DecisionTrace           = lazy(() => import("./pages/DecisionTrace"));
const ValuePacks              = lazy(() => import("./pages/ValuePacks"));
const Accounts                = lazy(() => import("./pages/Accounts"));
const Integrations            = lazy(() => import("./pages/Integrations"));
const FormulaGovernance       = lazy(() => import("./pages/admin/FormulaGovernance"));
const BenchmarkPolicies       = lazy(() => import("./pages/admin/BenchmarkPolicies"));
const VariableRegistry        = lazy(() => import("./pages/admin/VariableRegistry"));
const PackManagement          = lazy(() => import("./pages/admin/PackManagement"));
const PermissionsAdmin        = lazy(() => import("./pages/admin/PermissionsAdmin"));
const PlatformSettings        = lazy(() => import("./pages/admin/PlatformSettings"));
const HealthMonitor           = lazy(() => import("./pages/admin/HealthMonitor"));
const MyModels                = lazy(() => import("./pages/MyModels"));
const BusinessCaseList        = lazy(() => import("./pages/BusinessCaseList"));
const OpportunityFinder       = lazy(() => import("./pages/OpportunityFinder"));
const WhitespaceAnalysis      = lazy(() => import("./pages/WhitespaceAnalysis"));
const SourceConfiguration     = lazy(() => import("./pages/SourceConfiguration"));
const NotFound                = lazy(() => import("./pages/NotFound"));
const Login                   = lazy(() => import("./pages/Login"));

// ── Workflow Pages ───────────────────────────────────────────────────────────
const ProspectSetup           = lazy(() => import("./workflow/pages/ProspectSetup"));

// ── Intelligence Workspace Tabs ──────────────────────────────────────────────
const SignalsTab              = lazy(() => import("./pages/intelligence/SignalsTab"));
const DriversTab              = lazy(() => import("./pages/intelligence/DriversTab"));
const EvidenceTab             = lazy(() => import("./pages/intelligence/EvidenceTab"));
const StakeholdersTab         = lazy(() => import("./pages/intelligence/StakeholdersTab"));

// ── Value Studio Workspace Tabs ──────────────────────────────────────────────
const ActionPlanTab           = lazy(() => import("./pages/studio/ActionPlanTab"));
const ValueModelTab           = lazy(() => import("./pages/studio/ValueModelTab"));
const NarrativeTab            = lazy(() => import("./pages/studio/NarrativeTab"));

// ── Minimal inline fallback ──────────────────────────────────────────────────
function PageLoader() {
  return (
    <div className="flex items-center justify-center h-full min-h-[200px]">
      <div className="w-6 h-6 rounded-full border-2 border-neutral-300 border-t-neutral-700 animate-spin" />
    </div>
  );
}

// ── Intelligence Default Redirect ────────────────────────────────────────────
// Redirects /intelligence/:accountId → /intelligence/:accountId/signals
function IntelligenceRedirect() {
  const params = useParams<{ accountId: string }>();
  return <Navigate to={`/intelligence/${params.accountId}/signals`} />;
}

// ── Value Studio Default Redirect ────────────────────────────────────────────
// Redirects /studio/:accountId → /studio/:accountId/action-plan
function StudioRedirect() {
  const params = useParams<{ accountId: string }>();
  return <Navigate to={`/studio/${params.accountId}/action-plan`} />;
}

// ── Route Guard ──────────────────────────────────────────────────────────────
type RequiredUserTier = Exclude<UserTier, 'unknown'>;

function RouteGuard({
  children,
  requiredTier = "standard",
}: {
  children: React.ReactNode;
  requiredTier?: RequiredUserTier;
}) {
  const [location] = useLocation();
  const { isAuthenticated, isLoading } = useAuthContext();
  const canAccessRouteWithReason = useUserTierStore(state => state.canAccessRouteWithReason);

  if (isLoading) return null;
  if (!isAuthenticated) return <Navigate to="/login" />;

  let accessDecision;
  try {
    accessDecision = canAccessRouteWithReason(requiredTier);
  } catch (error) {
    console.error('[RouteGuard] Permission evaluation failed:', error);
    accessDecision = { allowed: false, reason: 'PERMISSION_EVALUATION_EXCEPTION' };
  }

  if (!accessDecision.allowed) {
    console.warn(`[RouteGuard] Access denied to ${location}: ${accessDecision.reason}`);
    return <Navigate to="/home" />;
  }

  return <>{children}</>;
}

// ── Router ───────────────────────────────────────────────────────────────────

function Router() {
  const rawCurrentTier = useUserTierStore(state => state.currentTier);
  const rawEffectiveTier = useUserTierStore(state => state.effectiveTier);
  const { isAuthenticated } = useAuthContext();

  const currentTier: RequiredUserTier = rawCurrentTier === 'unknown' ? 'standard' : rawCurrentTier;
  const effectiveTier: RequiredUserTier = rawEffectiveTier === 'unknown' ? 'standard' : rawEffectiveTier;

  return (
    <Suspense fallback={<PageLoader />}>
      {/* ═══════════════════════════════════════════════════════════════
          PUBLIC ROUTES — Outside AppShell
          ═══════════════════════════════════════════════════════════════ */}
      <Route path="/">
        {isAuthenticated ? <Navigate to="/home" /> : <LandingPage />}
      </Route>
      <Route path="/login">
        <Login />
      </Route>
      <Route path="/login/callback">
        <Login />
      </Route>

      {/* ═══════════════════════════════════════════════════════════════
          AUTHENTICATED ROUTES — Inside AppShell with RouteGuard
          ═══════════════════════════════════════════════════════════════ */}
      <Route>
        <AppShell currentTier={currentTier} effectiveTier={effectiveTier}>

          {/* ─── HOME ─── */}
          <Route path="/home">
            <RouteGuard>
              <ErrorBoundary><ValueNarrativeHome /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/command-center">
            <RouteGuard>
              <ErrorBoundary><CommandCenter /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* ═══════════════════════════════════════════════════════════════
              1. ACCOUNTS — Entry Point
              ═══════════════════════════════════════════════════════════════ */}
          <Route path="/accounts">
            <RouteGuard>
              <ErrorBoundary><Accounts /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/accounts/:id">
            <RouteGuard>
              <ErrorBoundary><Accounts /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* ═══════════════════════════════════════════════════════════════
              2. INTELLIGENCE — Discovery Workspace (Account-Scoped)
              Tabs: Signals → Drivers → Evidence → Stakeholders
              ═══════════════════════════════════════════════════════════════ */}
          <Route path="/intelligence/:accountId">
            <RouteGuard>
              <IntelligenceRedirect />
            </RouteGuard>
          </Route>
          <Route path="/intelligence/:accountId/signals">
            <RouteGuard>
              <ErrorBoundary><SignalsTab /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/intelligence/:accountId/drivers">
            <RouteGuard>
              <ErrorBoundary><DriversTab /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/intelligence/:accountId/evidence">
            <RouteGuard>
              <ErrorBoundary><EvidenceTab /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/intelligence/:accountId/stakeholders">
            <RouteGuard>
              <ErrorBoundary><StakeholdersTab /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* ═══════════════════════════════════════════════════════════════
              3. VALUE STUDIO — Synthesis Workspace (Account-Scoped)
              Tabs: Action Plan → Value Model → Narrative
              ═══════════════════════════════════════════════════════════════ */}
          <Route path="/studio/:accountId">
            <RouteGuard>
              <StudioRedirect />
            </RouteGuard>
          </Route>
          <Route path="/studio/:accountId/action-plan">
            <RouteGuard>
              <ErrorBoundary><ActionPlanTab /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/studio/:accountId/value-model">
            <RouteGuard>
              <ErrorBoundary><ValueModelTab /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/studio/:accountId/narrative">
            <RouteGuard>
              <ErrorBoundary><NarrativeTab /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* ═══════════════════════════════════════════════════════════════
              4. CONTEXT ENGINE — Vendor Knowledge Base
              ═══════════════════════════════════════════════════════════════ */}
          <Route path="/context">
            <Navigate to="/context/packs" />
          </Route>
          <Route path="/context/packs">
            <RouteGuard>
              <ErrorBoundary><ValuePacks /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/context/models">
            <RouteGuard>
              <ErrorBoundary><MyModels /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/context/formulas">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><FormulaList /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/context/formulas/new">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><FormulaBuilder isNew /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/context/formulas/:formulaId">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><FormulaBuilder /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/context/agents">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><AgentWorkflows /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/context/ontology">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><OntologyEditor /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/context/ontology/entities">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><EntityBrowser /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/context/ontology/entities/:entityId">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><EntityDetail /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/context/ontology/graph">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><GraphExplorer /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/context/ingestion/jobs">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><IngestionJobs /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/context/extraction">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><ExtractionEngine /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/context/integrations">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><Integrations /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/context/sources">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><SourceConfiguration /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* ═══════════════════════════════════════════════════════════════
              5. DELIVERABLES — Activation Layer
              ═══════════════════════════════════════════════════════════════ */}
          <Route path="/deliverables">
            <Navigate to="/deliverables/cases" />
          </Route>
          <Route path="/deliverables/cases">
            <RouteGuard>
              <ErrorBoundary><BusinessCaseList /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/deliverables/cases/:caseId">
            <RouteGuard>
              <ErrorBoundary><BusinessCase /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/deliverables/calculators">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><InteractiveBusinessCase /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/deliverables/views/cfo">
            <RouteGuard>
              <ErrorBoundary><BusinessCase /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/deliverables/views/executive">
            <RouteGuard>
              <ErrorBoundary><BusinessCase /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/deliverables/views/technical">
            <RouteGuard>
              <ErrorBoundary><BusinessCase /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/deliverables/api">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><Integrations /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* ═══════════════════════════════════════════════════════════════
              6. GOVERNANCE — Trust Layer
              ═══════════════════════════════════════════════════════════════ */}
          <Route path="/governance">
            <Navigate to="/governance/traces" />
          </Route>
          <Route path="/governance/traces">
            <RouteGuard>
              <ErrorBoundary><DecisionTrace /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/governance/evidence">
            <RouteGuard>
              <ErrorBoundary><DecisionTrace /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/governance/provenance">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><DecisionTrace /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/governance/integrity">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><DecisionTrace /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/governance/compliance">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><DecisionTrace /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/governance/benchmarks">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><BenchmarkPolicies /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/governance/audit">
            <Navigate to="/governance/audit/log" />
          </Route>
          <Route path="/governance/audit/log">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><DecisionTrace /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/governance/audit/changes">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><DecisionTrace /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/governance/health">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><HealthMonitor /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* ═══════════════════════════════════════════════════════════════
              7. SETTINGS — Tenant Configuration (Admin)
              ═══════════════════════════════════════════════════════════════ */}
          <Route path="/settings">
            <Navigate to="/settings/content/formulas" />
          </Route>
          <Route path="/settings/content">
            <Navigate to="/settings/content/formulas" />
          </Route>
          <Route path="/settings/content/formulas">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><FormulaGovernance /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/settings/content/versions">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><FormulaGovernance /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/settings/content/approvals">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><FormulaGovernance /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/settings/data">
            <Navigate to="/settings/data/variables" />
          </Route>
          <Route path="/settings/data/variables">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><VariableRegistry /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/settings/data/bindings">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><VariableRegistry /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/settings/data/quality">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><VariableRegistry /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/settings/access">
            <Navigate to="/settings/access/roles" />
          </Route>
          <Route path="/settings/access/roles">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><PermissionsAdmin /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/settings/access/teams">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><PermissionsAdmin /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/settings/access/keys">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><PermissionsAdmin /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/settings/system/settings">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><PlatformSettings /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* ═══════════════════════════════════════════════════════════════
              LEGACY REDIRECTS — Backward Compatibility
              All old routes redirect to their new canonical homes.
              ═══════════════════════════════════════════════════════════════ */}

          {/* Old Discover routes → Accounts / Context */}
          <Route path="/discover"><Navigate to="/accounts" /></Route>
          <Route path="/discover/accounts"><Navigate to="/accounts" /></Route>
          <Route path="/discover/accounts/:id"><Navigate to="/accounts" /></Route>
          <Route path="/discover/jobs"><Navigate to="/context/ingestion/jobs" /></Route>
          <Route path="/discover/extraction"><Navigate to="/context/extraction" /></Route>
          <Route path="/discover/knowledge"><Navigate to="/context/ontology" /></Route>
          <Route path="/discover/knowledge/entities"><Navigate to="/context/ontology/entities" /></Route>
          <Route path="/discover/knowledge/graph"><Navigate to="/context/ontology/graph" /></Route>
          <Route path="/discover/knowledge/ontology"><Navigate to="/context/ontology" /></Route>
          <Route path="/discover/integrations"><Navigate to="/context/integrations" /></Route>
          <Route path="/discover/sources"><Navigate to="/context/sources" /></Route>

          {/* Old Library routes → Context */}
          <Route path="/library"><Navigate to="/context/packs" /></Route>
          <Route path="/library/packs"><Navigate to="/context/packs" /></Route>
          <Route path="/library/models"><Navigate to="/context/models" /></Route>
          <Route path="/library/authoring"><Navigate to="/settings/content/formulas" /></Route>

          {/* Old Model/Value Studio routes → Accounts (no account context) */}
          <Route path="/model"><Navigate to="/accounts" /></Route>
          <Route path="/model/value-studio"><Navigate to="/accounts" /></Route>
          <Route path="/model/value-studio/discovery"><Navigate to="/accounts" /></Route>
          <Route path="/model/value-studio/mapping"><Navigate to="/accounts" /></Route>
          <Route path="/model/value-studio/modeling"><Navigate to="/accounts" /></Route>
          <Route path="/model/value-studio/validation"><Navigate to="/accounts" /></Route>
          <Route path="/model/value-studio/narrative"><Navigate to="/accounts" /></Route>
          <Route path="/model/value-studio/tracking"><Navigate to="/accounts" /></Route>
          <Route path="/model/value-studio/explorer"><Navigate to="/accounts" /></Route>
          <Route path="/model/value-studio/formulas"><Navigate to="/context/formulas" /></Route>
          <Route path="/model/value-studio/formulas/new"><Navigate to="/context/formulas" /></Route>

          {/* Workflow routes */}
          <Route path="/workflow">
            <RouteGuard requiredTier="standard">
              <ErrorBoundary><Navigate to="/workflow/prospect" /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/workflow/prospect">
            <RouteGuard requiredTier="standard">
              <ErrorBoundary>
                <Suspense fallback={<PageLoader />}>
                  <ProspectSetupWithNav />
                </Suspense>
              </ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/workflow/intelligence"><Navigate to="/accounts" /></Route>
          <Route path="/workflow/ai-model"><Navigate to="/accounts" /></Route>
          <Route path="/workflow/driver-tree"><Navigate to="/accounts" /></Route>
          <Route path="/workflow/evidence"><Navigate to="/accounts" /></Route>
          <Route path="/workflow/calculator"><Navigate to="/accounts" /></Route>
          <Route path="/workflow/value-case"><Navigate to="/accounts" /></Route>

          {/* Old Deliver routes → Deliverables */}
          <Route path="/deliver"><Navigate to="/deliverables/cases" /></Route>
          <Route path="/deliver/cases"><Navigate to="/deliverables/cases" /></Route>
          <Route path="/deliver/opportunities"><Navigate to="/accounts" /></Route>
          <Route path="/deliver/whitespace"><Navigate to="/accounts" /></Route>
          <Route path="/deliver/agents"><Navigate to="/context/agents" /></Route>
          <Route path="/deliver/cases/explore"><Navigate to="/deliverables/calculators" /></Route>

          {/* Old Evidence routes → Governance */}
          <Route path="/evidence"><Navigate to="/governance/traces" /></Route>
          <Route path="/evidence/traces"><Navigate to="/governance/traces" /></Route>
          <Route path="/evidence/export"><Navigate to="/governance/evidence" /></Route>
          <Route path="/evidence/lineage"><Navigate to="/governance/provenance" /></Route>
          <Route path="/evidence/compliance"><Navigate to="/governance/compliance" /></Route>
          <Route path="/evidence/changelog"><Navigate to="/governance/audit/changes" /></Route>

          {/* Old Trust routes → Governance */}
          <Route path="/trust"><Navigate to="/governance/traces" /></Route>
          <Route path="/trust/traces"><Navigate to="/governance/traces" /></Route>
          <Route path="/trust/evidence"><Navigate to="/governance/evidence" /></Route>
          <Route path="/trust/provenance"><Navigate to="/governance/provenance" /></Route>
          <Route path="/trust/integrity"><Navigate to="/governance/integrity" /></Route>
          <Route path="/trust/compliance"><Navigate to="/governance/compliance" /></Route>
          <Route path="/trust/benchmarks"><Navigate to="/governance/benchmarks" /></Route>
          <Route path="/trust/audit"><Navigate to="/governance/audit/log" /></Route>
          <Route path="/trust/audit/log"><Navigate to="/governance/audit/log" /></Route>
          <Route path="/trust/audit/changes"><Navigate to="/governance/audit/changes" /></Route>
          <Route path="/trust/health"><Navigate to="/governance/health" /></Route>

          {/* Old Admin routes → Settings */}
          <Route path="/admin"><Navigate to="/settings/content/formulas" /></Route>
          <Route path="/admin/content"><Navigate to="/settings/content/formulas" /></Route>
          <Route path="/admin/content/formulas"><Navigate to="/settings/content/formulas" /></Route>
          <Route path="/admin/content/versions"><Navigate to="/settings/content/versions" /></Route>
          <Route path="/admin/content/approvals"><Navigate to="/settings/content/approvals" /></Route>
          <Route path="/admin/content/benchmarks"><Navigate to="/governance/benchmarks" /></Route>
          <Route path="/admin/data"><Navigate to="/settings/data/variables" /></Route>
          <Route path="/admin/data/variables"><Navigate to="/settings/data/variables" /></Route>
          <Route path="/admin/data/bindings"><Navigate to="/settings/data/bindings" /></Route>
          <Route path="/admin/data/quality"><Navigate to="/settings/data/quality" /></Route>
          <Route path="/admin/access"><Navigate to="/settings/access/roles" /></Route>
          <Route path="/admin/access/roles"><Navigate to="/settings/access/roles" /></Route>
          <Route path="/admin/access/teams"><Navigate to="/settings/access/teams" /></Route>
          <Route path="/admin/access/keys"><Navigate to="/settings/access/keys" /></Route>
          <Route path="/admin/system/settings"><Navigate to="/settings/system/settings" /></Route>
          <Route path="/admin/system/audit"><Navigate to="/governance/audit/log" /></Route>
          <Route path="/admin/system/health"><Navigate to="/governance/health" /></Route>

          {/* Old Studio routes (non-account-scoped) → Accounts */}
          <Route path="/studio"><Navigate to="/accounts" /></Route>
          <Route path="/studio/deals"><Navigate to="/accounts" /></Route>
          <Route path="/studio/build"><Navigate to="/accounts" /></Route>
          <Route path="/studio/build/discovery"><Navigate to="/accounts" /></Route>
          <Route path="/studio/build/mapping"><Navigate to="/accounts" /></Route>
          <Route path="/studio/build/modeling"><Navigate to="/accounts" /></Route>
          <Route path="/studio/build/validation"><Navigate to="/accounts" /></Route>
          <Route path="/studio/build/narrative"><Navigate to="/accounts" /></Route>
          <Route path="/studio/build/tracking"><Navigate to="/accounts" /></Route>
          <Route path="/studio/trees"><Navigate to="/accounts" /></Route>
          <Route path="/studio/scenarios"><Navigate to="/accounts" /></Route>

          {/* ─── Catch-all ─── */}
          <Route>
            <ErrorBoundary><NotFound /></ErrorBoundary>
          </Route>
        </AppShell>
      </Route>
    </Suspense>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="light">
        <AuthProvider>
          <TooltipProvider>
            <Toaster />
            <Router />
          </TooltipProvider>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
