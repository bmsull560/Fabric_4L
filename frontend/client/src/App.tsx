import { lazy, memo, Suspense, useEffect } from "react";
import {
  // AppShell, // unused - kept for reference
  Layout,
  ErrorBoundary,
  Toaster,
  TooltipProvider,
} from "@/components";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AuthProvider, useAuthContext } from "./contexts/AuthContext";
import { BillingProvider } from "./context/BillingContext";
import { useUserTierStore, useCreateAccount, type UserTier } from "@/hooks";
import { Route, Switch, useLocation, useParams } from "wouter";
import { useAccountContextStore } from "@/stores/accountContextStore";

import { WorkspaceRoutes } from "./routes/workspace";
import { GovernanceRoutes } from "./routes/governance";
import { aliasNamespaceDeprecationMap } from "./routes/deprecationMap";

import {
  getWorkspaceTabOrDefault,
  resolveAccountScopedWorkspacePath,
} from "@/navigation/accountRouting";

// ── Navigate Component for wouter ───────────────────────────────────────────
function Navigate({ to }: { to: string }) {
  const [, navigate] = useLocation();
  useEffect(() => {
    navigate(to);
  }, [navigate, to]);
  return null;
}

// ── Prospect Setup with Navigation ───────────────────────────────────────────
function ProspectSetupWithNav() {
  const [, navigate] = useLocation();
  const createAccount = useCreateAccount();

  const handleCreateSetup = async (payload: {
    companyName: string;
    industry?: string;
    painPoints?: string[];
    stakeholders?: Record<string, string>;
  }) => {
    const result = await createAccount.mutateAsync({
      name: payload.companyName ?? 'Unknown Account',
      industry: payload.industry,
      stage: 'prospect',
      enrichment_input: payload.painPoints?.join('\n'),
    });
    return { accountId: result.account.id };
  };

  return (
    <ProspectSetup
      onNavigateToWorkspace={path => navigate(path)}
      onCreateSetup={handleCreateSetup}
      isSubmitting={createAccount.isPending}
    />
  );
}

// ── Route-level code splitting ────────────────────────────────────────────────
// Existing pages (preserved)
// const LandingPage = lazy(() => import("./pages/LandingPage"));
const CommandCenter = lazy(() => import("./pages/CommandCenter"));
const ValueNarrativeHome = lazy(() => import("./pages/ValueNarrativeHome"));
const ExtractionEngine = lazy(() => import("./pages/ExtractionEngine"));
const IngestionJobs = lazy(() => import("./pages/IngestionJobs"));
const OntologyEditor = lazy(() => import("./pages/OntologyEditor"));
const EntityBrowser = lazy(() => import("./pages/EntityBrowser"));
const EntityDetail = lazy(() => import("./pages/EntityDetail"));
const FormulaBuilder = lazy(() => import("./pages/FormulaBuilder"));
const FormulaList = lazy(() => import("./pages/FormulaList"));
const GraphExplorer = lazy(() => import("./pages/GraphExplorer"));
const AgentWorkflows = lazy(() => import("./pages/AgentWorkflows"));
const BusinessCase = lazy(() => import("./pages/BusinessCase"));
const CFOView = lazy(() => import("./pages/deliverables/CFOView"));
const ExecutiveView = lazy(() => import("./pages/deliverables/ExecutiveView"));
const TechnicalView = lazy(() => import("./pages/deliverables/TechnicalView"));
const IntegrationDashboard = lazy(() => import("./pages/dev/IntegrationDashboard"));
const InteractiveBusinessCase = lazy(
  () => import("./pages/InteractiveBusinessCase")
);
const DecisionTrace = lazy(() => import("./pages/DecisionTrace"));
const GovernanceEvidence = lazy(() => import("./pages/GovernanceEvidence"));
const GovernanceCompliance = lazy(() => import("./pages/GovernanceCompliance"));
const GovernanceAuditLog = lazy(() => import("./pages/GovernanceAuditLog"));
const GovernanceChangeHistory = lazy(() => import("./pages/GovernanceChangeHistory"));
const ValuePacks = lazy(() => import("./pages/ValuePacks"));
const Accounts = lazy(() => import("./pages/Accounts"));
const Integrations = lazy(() => import("./pages/Integrations"));
const FormulaGovernance = lazy(() => import("./pages/admin/FormulaGovernance"));
const BenchmarkPolicies = lazy(() => import("./pages/admin/BenchmarkPolicies"));
const VariableRegistry = lazy(() => import("./pages/admin/VariableRegistry"));
const PackManagement = lazy(() => import("./pages/admin/PackManagement"));
const PermissionsAdmin = lazy(() => import("./pages/admin/PermissionsAdmin"));
const PlatformSettings = lazy(() => import("./pages/admin/PlatformSettings"));
const HealthMonitor = lazy(() => import("./pages/admin/HealthMonitor"));
const BillingSettings = lazy(() =>
  import("./pages/BillingSettings").then(module => ({ default: module.BillingSettings }))
);
const UsageDashboard = lazy(() =>
  import("./pages/UsageDashboard").then(module => ({ default: module.UsageDashboard }))
);
const InvoiceList = lazy(() =>
  import("./pages/InvoiceList").then(module => ({ default: module.InvoiceList }))
);
const PaymentHistory = lazy(() =>
  import("./pages/PaymentHistory").then(module => ({ default: module.PaymentHistory }))
);
const MyModels = lazy(() => import("./pages/MyModels"));
const ValueTreeExplorer = lazy(() => import("./pages/ValueTreeExplorer"));
const BusinessCaseList = lazy(() => import("./pages/BusinessCaseList"));
const OpportunityFinder = lazy(() => import("./pages/OpportunityFinder"));
const WhitespaceAnalysis = lazy(() => import("./pages/WhitespaceAnalysis"));
const SourceConfiguration = lazy(() => import("./pages/SourceConfiguration"));
const NotFound = lazy(() => import("./pages/NotFound"));
const Login = lazy(() => import("./pages/Login"));
const Signup = lazy(() => import("./pages/Signup"));

// ── Workflow Pages ───────────────────────────────────────────────────────────
const ProspectSetup = lazy(() => import("./workflow/pages/ProspectSetup"));
const Intelligence = lazy(() => import("./workflow/pages/Intelligence"));
const AIModel = lazy(() => import("./workflow/pages/AIModel"));
const DriverTree = lazy(() => import("./workflow/pages/DriverTree"));
const Evidence = lazy(() => import("./workflow/pages/Evidence"));
const Calculator = lazy(() => import("./workflow/pages/Calculator"));
const ValueCase = lazy(() => import("./workflow/pages/ValueCase"));

// ── Intelligence Workspace Tabs ──────────────────────────────────────────────
const SignalsTab = lazy(() => import("./pages/intelligence/SignalsTab"));
const DriversTab = lazy(() => import("./pages/intelligence/DriversTab"));
const EvidenceTab = lazy(() => import("./pages/intelligence/EvidenceTab"));
const StakeholdersTab = lazy(
  () => import("./pages/intelligence/StakeholdersTab")
);
// ── DIL Intelligence Tabs ────────────────────────────────────────────────────
const EnrichmentTab = lazy(() => import("./pages/intelligence/EnrichmentTab"));
const HypothesesTab = lazy(() => import("./pages/intelligence/HypothesesTab"));
const CompetitiveTab = lazy(() => import("./pages/intelligence/CompetitiveTab"));
const ROITab = lazy(() => import("./pages/intelligence/ROITab"));
const EvidenceLibraryTab = lazy(() => import("./pages/intelligence/EvidenceLibraryTab"));

// ── Value Studio Workspace Tabs (legacy — kept for backward compat) ──────────
const ActionPlanTab = lazy(() => import("./pages/studio/ActionPlanTab"));
const ValueModelTab = lazy(() => import("./pages/studio/ValueModelTab"));
const NarrativeTab = lazy(() => import("./pages/studio/NarrativeTab"));
const StudioEnrichmentTab = lazy(() => import("./pages/studio/StudioEnrichmentTab"));
const StudioCompetitiveTab = lazy(() => import("./pages/studio/StudioCompetitiveTab"));
const StudioROITab = lazy(() => import("./pages/studio/StudioROITab"));
const StudioEvidenceTab = lazy(() => import("./pages/studio/StudioEvidenceTab"));
// ── New Workflow Tab Pages ────────────────────────────────────────────────────
// Intelligence new tabs
const IntelligenceWorkspacePage = lazy(() => import("./pages/intelligence/IntelligenceWorkspacePage"));
// Value Hypothesis tabs
// Evidence tabs
const AlternativesTab = lazy(() => import("./pages/evidence/AlternativesTab"));
const SolutionCostTab = lazy(() => import("./pages/evidence/SolutionCostTab"));
const HypothesisTab = lazy(() => import("./pages/hypothesis/HypothesisTab"));
const DiscoveryQuestionsTab = lazy(() => import("./pages/hypothesis/DiscoveryQuestionsTab"));
const PersonaFitTab = lazy(() => import("./pages/hypothesis/PersonaFitTab"));
const AssumptionsTab = lazy(() => import("./pages/hypothesis/AssumptionsTab"));
const CalcROITab = lazy(() => import("./pages/calculator/ROITab"));
const CalcValueModelTab = lazy(() => import("./pages/calculator/ValueModelTab"));
const DriverTreePage = lazy(() => import("./pages/drivers/DriverTreePage"));
// Calculator tabs
// Driver Tree (reuses existing DriversTab from intelligence)
// Value Case (reuses NarrativeTab from studio)
// Value Realization (reuses ActionPlanTab from studio)

// ── Minimal inline fallback ──────────────────────────────────────────────────
function PageLoader() {
  return (
    <div className="flex items-center justify-center h-full min-h-[200px]">
      <div className="w-6 h-6 rounded-full border-2 border-border border-t-primary animate-spin" />
    </div>
  );
}

// ── Intelligence Default Redirect ────────────────────────────────────────────
// Redirects /intelligence/:accountId → /intelligence/:accountId/signals
function IntelligenceRedirect() {
  const params = useParams<{ accountId: string }>();
  return (
    <Navigate
      to={resolveAccountScopedWorkspacePath({
        workspace: "intelligence",
        accountId: params.accountId,
      })}
    />
  );
}

// ── Value Studio Default Redirect ────────────────────────────────────────────
// Redirects /studio/:accountId → /studio/:accountId/action-plan
function StudioRedirect() {
  const params = useParams<{ accountId: string }>();
  return (
    <Navigate
      to={resolveAccountScopedWorkspacePath({
        workspace: "studio",
        accountId: params.accountId,
      })}
    />
  );
}
// ── New Workspace Default Redirects ──────────────────────────────────────────
function HypothesisRedirect() {
  const params = useParams<{ accountId: string }>();
  return <Navigate to={`/hypothesis/${params.accountId}/hypothesis`} />;
}
function EvidenceRedirect() {
  const params = useParams<{ accountId: string }>();
  return <Navigate to={`/evidence/${params.accountId}/evidence`} />;
}
function CalculatorRedirect() {
  const params = useParams<{ accountId: string }>();
  return <Navigate to={`/calculator/${params.accountId}/roi`} />;
}

function AccountContextSync() {
  const params = useParams<{ accountId: string }>();
  const setSelectedAccountId = useAccountContextStore(
    state => state.setSelectedAccountId
  );

  useEffect(() => {
    if (params.accountId) {
      setSelectedAccountId(params.accountId);
    }
  }, [params.accountId, setSelectedAccountId]);

  return null;
}

interface WorkspaceContextRedirectProps {
  workspace: "intelligence" | "studio";
  tab?: string;
}

function WorkspaceContextRedirect({
  workspace,
  tab: explicitTab,
}: WorkspaceContextRedirectProps) {
  const params = useParams<{ tab?: string }>();
  const selectedAccountId = useAccountContextStore(
    state => state.selectedAccountId
  );

  const resolvedTab = getWorkspaceTabOrDefault(workspace, explicitTab ?? params.tab);

  return (
    <Navigate
      to={resolveAccountScopedWorkspacePath({
        workspace,
        accountId: selectedAccountId,
        tab: resolvedTab,
      })}
    />
  );
}

function BillingRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuthContext();

  if (!user?.id) {
    return <Navigate to="/home" />;
  }

  return <BillingProvider customerId={user.id}>{children}</BillingProvider>;
}

// ── Route Guard ──────────────────────────────────────────────────────────────
type RequiredUserTier = Exclude<UserTier, "unknown">;

interface RouteGuardProps {
  children: React.ReactNode;
  requiredTier?: RequiredUserTier;
}

function RouteGuard({ children, requiredTier = "standard" }: RouteGuardProps) {
  const [location] = useLocation();
  const { isAuthenticated, isLoading } = useAuthContext();
  const canAccessRouteWithReason = useUserTierStore(
    state => state.canAccessRouteWithReason
  );
  const currentTier = useUserTierStore(state => state.currentTier);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-border border-t-primary animate-spin" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) return <Navigate to="/login" />;

  let accessDecision;
  try {
    accessDecision = canAccessRouteWithReason(requiredTier);
  } catch (error) {
    console.error("[RouteGuard] Permission evaluation failed:", error);
    accessDecision = {
      allowed: false,
      reason: "PERMISSION_EVALUATION_EXCEPTION",
    };
  }

  if (!accessDecision.allowed) {
    console.warn(
      `[RouteGuard] Access denied to ${location}: ${accessDecision.reason}`
    );
    return <Navigate to="/home" />;
  }

  return <>{children}</>;
}

// ── Authenticated Route Wrapper ─────────────────────────────────────────────
interface AuthenticatedRouteProps {
  children: React.ReactNode;
  requiredTier?: RequiredUserTier;
  currentTier: RequiredUserTier;
  effectiveTier: RequiredUserTier;
}


function AppRoutes({ tierProps, isLoading, isAuthenticated }: { tierProps: { currentTier: RequiredUserTier; effectiveTier: RequiredUserTier }; isLoading: boolean; isAuthenticated: boolean; }) {
  void aliasNamespaceDeprecationMap;
  return (
    <>
      {WorkspaceRoutes({ tierProps, AuthenticatedRoute, Navigate, AccountContextSync, WorkspaceContextRedirect, IntelligenceRedirect, StudioRedirect, BillingRoute }, { SignalsTab, DriversTab, EvidenceTab, StakeholdersTab, EnrichmentTab, HypothesesTab, CompetitiveTab, ROITab, EvidenceLibraryTab, ActionPlanTab, ValueModelTab, NarrativeTab, StudioEnrichmentTab, StudioCompetitiveTab, StudioROITab, StudioEvidenceTab })}
      {GovernanceRoutes({ tierProps, AuthenticatedRoute, Navigate, AccountContextSync, WorkspaceContextRedirect, IntelligenceRedirect, StudioRedirect, BillingRoute }, { DecisionTrace, GovernanceEvidence, GovernanceCompliance, GovernanceAuditLog, GovernanceChangeHistory, BenchmarkPolicies, HealthMonitor })}
    </>
  );
}

const AuthenticatedRoute = memo(function AuthenticatedRoute({
  children,
  requiredTier = "standard",
  currentTier,
  effectiveTier,
}: AuthenticatedRouteProps) {
  return (
    <Layout currentTier={currentTier} effectiveTier={effectiveTier}>
      <RouteGuard requiredTier={requiredTier}>
        <ErrorBoundary>{children}</ErrorBoundary>
      </RouteGuard>
    </Layout>
  );
});

// ── Router ───────────────────────────────────────────────────────────────────

function Router() {
  const rawCurrentTier = useUserTierStore(state => state.currentTier);
  const rawEffectiveTier = useUserTierStore(state => state.effectiveTier);
  const { isAuthenticated, isLoading } = useAuthContext();

  const currentTier: RequiredUserTier =
    rawCurrentTier === "unknown" ? "standard" : rawCurrentTier;
  const effectiveTier: RequiredUserTier =
    rawEffectiveTier === "unknown" ? "standard" : rawEffectiveTier;

  // Pre-bound tier props for AuthenticatedRoute to avoid passing on every render
  const tierProps = { currentTier, effectiveTier };

  return (
    <Suspense fallback={<PageLoader />}>
     <Switch>
      {/* ═══════════════════════════════════════════════════════════════
          PUBLIC ROUTES — No AppShell
          ═══════════════════════════════════════════════════════════════ */}
      <Route path="/">
        {isLoading ? (
          <PageLoader />
        ) : isAuthenticated ? (
          <Navigate to="/home" />
        ) : (
          <Navigate to="/login" />
        )}
      </Route>
      <Route path="/login">
        <Login />
      </Route>
      <Route path="/login/callback">
        <Login />
      </Route>
      <Route path="/signup">
        <Signup />
      </Route>

      {/* ═══════════════════════════════════════════════════════════════
          HOME & COMMAND CENTER
          ═══════════════════════════════════════════════════════════════ */}
      <Route path="/home">
        <AuthenticatedRoute {...tierProps}>
          <ValueNarrativeHome />
        </AuthenticatedRoute>
      </Route>
      <Route path="/command-center">
        <AuthenticatedRoute {...tierProps}>
          <CommandCenter />
        </AuthenticatedRoute>
      </Route>

      {/* ═══════════════════════════════════════════════════════════════
          1. ACCOUNTS — Entry Point
          ═══════════════════════════════════════════════════════════════ */}
      <Route path="/accounts">
        <AuthenticatedRoute {...tierProps}>
          <Accounts />
        </AuthenticatedRoute>
      </Route>
      <Route path="/accounts/:id">
        <AuthenticatedRoute {...tierProps}>
          <Accounts />
        </AuthenticatedRoute>
      </Route>
      {/* ═══════════════════════════════════════════════════════════════
          ACCOUNT INTELLIGENCE WORKSPACE — Unified tab-based workspace
          Route: /accounts/:accountId/intelligence/:tabId
          ═══════════════════════════════════════════════════════════════ */}
      <Route path="/accounts/:accountId/intelligence/:tabId">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <IntelligenceWorkspacePage />
        </AuthenticatedRoute>
      </Route>
      <Route path="/accounts/:accountId/intelligence">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <IntelligenceWorkspacePage />
        </AuthenticatedRoute>
      </Route>

      {/* Guided Workflow Routes */}
      <Route path="/workflow/prospect">
        <AuthenticatedRoute {...tierProps}>
          <ProspectSetupWithNav />
        </AuthenticatedRoute>
      </Route>
      <Route path="/workflow/intelligence">
        <AuthenticatedRoute {...tierProps}>
          <Intelligence />
        </AuthenticatedRoute>
      </Route>
      <Route path="/workflow/ai-model">
        <AuthenticatedRoute {...tierProps}>
          <AIModel />
        </AuthenticatedRoute>
      </Route>
      <Route path="/workflow/driver-tree">
        <AuthenticatedRoute {...tierProps}>
          <DriverTree />
        </AuthenticatedRoute>
      </Route>
      <Route path="/workflow/evidence">
        <AuthenticatedRoute {...tierProps}>
          <Evidence />
        </AuthenticatedRoute>
      </Route>
      <Route path="/workflow/calculator">
        <AuthenticatedRoute {...tierProps}>
          <Calculator />
        </AuthenticatedRoute>
      </Route>
      <Route path="/workflow/value-case">
        <AuthenticatedRoute {...tierProps}>
          <ValueCase />
        </AuthenticatedRoute>
      </Route>

      {/* ═══════════════════════════════════════════════════════════════
          WORKSPACE ROUTES — Hypothesis, Driver Tree, Calculator, Value Case, Realization
          ═══════════════════════════════════════════════════════════════ */}
      <Route path="/hypothesis">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="intelligence" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/hypothesis/:accountId">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <HypothesisRedirect />
        </AuthenticatedRoute>
      </Route>
      <Route path="/hypothesis/:accountId/hypothesis">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <HypothesisTab />
        </AuthenticatedRoute>
      </Route>
      <Route path="/hypothesis/:accountId/discovery-questions">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <DiscoveryQuestionsTab />
        </AuthenticatedRoute>
      </Route>
      <Route path="/hypothesis/:accountId/persona-fit">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <PersonaFitTab />
        </AuthenticatedRoute>
      </Route>
      <Route path="/hypothesis/:accountId/assumptions">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <AssumptionsTab />
        </AuthenticatedRoute>
      </Route>

      <Route path="/drivers/:accountId">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <DriverTreePage />
        </AuthenticatedRoute>
      </Route>
      <Route path="/drivers/:accountId/:tab">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <DriverTreePage />
        </AuthenticatedRoute>
      </Route>

      <Route path="/calculator">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="intelligence" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/calculator/:accountId">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <CalculatorRedirect />
        </AuthenticatedRoute>
      </Route>
      <Route path="/calculator/:accountId/roi">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <CalcROITab />
        </AuthenticatedRoute>
      </Route>
      <Route path="/calculator/:accountId/value-model">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <CalcValueModelTab />
        </AuthenticatedRoute>
      </Route>

      <Route path="/value-case/:accountId">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <NarrativeTab />
        </AuthenticatedRoute>
      </Route>
      <Route path="/realization/:accountId">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <ActionPlanTab />
        </AuthenticatedRoute>
      </Route>
      {/* ═══════════════════════════════════════════════════════════════
          LEGACY: VALUE STUDIO — Synthesis Workspace (kept for backward compat)
          ═══════════════════════════════════════════════════════════════ */}
      <Route path="/studio">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/action-plan">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" tab="action-plan" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/value-model">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" tab="value-model" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/narrative">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" tab="narrative" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/enrichment">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" tab="enrichment" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/competitive">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" tab="competitive" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/roi">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" tab="roi" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/evidence">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" tab="evidence" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/:accountId">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <StudioRedirect />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/:accountId/action-plan">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <ActionPlanTab />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/:accountId/value-model">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <ValueModelTab />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/:accountId/narrative">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <NarrativeTab />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/:accountId/enrichment">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <StudioEnrichmentTab />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/:accountId/competitive">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <StudioCompetitiveTab />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/:accountId/roi">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <StudioROITab />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/:accountId/evidence">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <StudioEvidenceTab />
        </AuthenticatedRoute>
      </Route>

      {/* ═══════════════════════════════════════════════════════════════
          4. CONTEXT ENGINE — Vendor Knowledge Base
          ═══════════════════════════════════════════════════════════════ */}
      <Route path="/context/packs">
        <AuthenticatedRoute {...tierProps}>
          <ValuePacks />
        </AuthenticatedRoute>
      </Route>
      <Route path="/context/models">
        <AuthenticatedRoute {...tierProps}>
          <MyModels />
        </AuthenticatedRoute>
      </Route>
      <Route path="/context/formulas">
        <AuthenticatedRoute {...tierProps} requiredTier="advanced">
          <FormulaList />
        </AuthenticatedRoute>
      </Route>
      <Route path="/context/formulas/new">
        <AuthenticatedRoute {...tierProps} requiredTier="advanced">
          <FormulaBuilder isNew />
        </AuthenticatedRoute>
      </Route>
      <Route path="/context/formulas/:formulaId">
        <AuthenticatedRoute {...tierProps} requiredTier="advanced">
          <FormulaBuilder />
        </AuthenticatedRoute>
      </Route>
      <Route path="/context/value-trees/explorer">
        <AuthenticatedRoute {...tierProps} requiredTier="advanced">
          <ValueTreeExplorer />
        </AuthenticatedRoute>
      </Route>
      <Route path="/context/agents">
        <AuthenticatedRoute {...tierProps} requiredTier="advanced">
          <AgentWorkflows />
        </AuthenticatedRoute>
      </Route>
      <Route path="/context/ontology">
        <AuthenticatedRoute {...tierProps} requiredTier="advanced">
          <OntologyEditor />
        </AuthenticatedRoute>
      </Route>
      <Route path="/context/ontology/entities">
        <AuthenticatedRoute {...tierProps} requiredTier="advanced">
          <EntityBrowser />
        </AuthenticatedRoute>
      </Route>
      <Route path="/context/ontology/entities/:entityId">
        <AuthenticatedRoute {...tierProps} requiredTier="advanced">
          <EntityDetail />
        </AuthenticatedRoute>
      </Route>
      <Route path="/context/ontology/graph">
        <AuthenticatedRoute {...tierProps} requiredTier="advanced">
          <GraphExplorer />
        </AuthenticatedRoute>
      </Route>
      <Route path="/context/ingestion/jobs">
        <AuthenticatedRoute {...tierProps} requiredTier="advanced">
          <IngestionJobs />
        </AuthenticatedRoute>
      </Route>
      <Route path="/context/extraction">
        <AuthenticatedRoute {...tierProps} requiredTier="advanced">
          <ExtractionEngine />
        </AuthenticatedRoute>
      </Route>
      <Route path="/context/integrations">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <Integrations />
        </AuthenticatedRoute>
      </Route>
      <Route path="/context/sources">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <SourceConfiguration />
        </AuthenticatedRoute>
      </Route>
      <Route path="/context">
        <Navigate to="/context/packs" />
      </Route>

      {/* ═══════════════════════════════════════════════════════════════
          5. DELIVERABLES — Activation Layer
          ═══════════════════════════════════════════════════════════════ */}
      <Route path="/deliverables/cases">
        <AuthenticatedRoute {...tierProps}>
          <BusinessCaseList />
        </AuthenticatedRoute>
      </Route>
      <Route path="/deliverables/cases/:caseId">
        <AuthenticatedRoute {...tierProps}>
          <BusinessCase />
        </AuthenticatedRoute>
      </Route>
      <Route path="/deliverables/calculators">
        <AuthenticatedRoute {...tierProps} requiredTier="advanced">
          <InteractiveBusinessCase />
        </AuthenticatedRoute>
      </Route>
      <Route path="/deliverables/views/cfo">
        <AuthenticatedRoute {...tierProps}>
          <CFOView />
        </AuthenticatedRoute>
      </Route>
      <Route path="/deliverables/views/executive">
        <AuthenticatedRoute {...tierProps}>
          <ExecutiveView />
        </AuthenticatedRoute>
      </Route>
      <Route path="/deliverables/views/technical">
        <AuthenticatedRoute {...tierProps}>
          <TechnicalView />
        </AuthenticatedRoute>
      </Route>
      <Route path="/deliverables/api">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <Integrations />
        </AuthenticatedRoute>
      </Route>
      <Route path="/deliverables">
        <Navigate to="/deliverables/cases" />
      </Route>

      {/* ═══════════════════════════════════════════════════════════════
          7. SETTINGS — Tenant Configuration (Admin)
          ═══════════════════════════════════════════════════════════════ */}
      <Route path="/settings/content/formulas">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <FormulaGovernance />
        </AuthenticatedRoute>
      </Route>
      <Route path="/settings/content/versions">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <FormulaGovernance />
        </AuthenticatedRoute>
      </Route>
      <Route path="/settings/content/approvals">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <FormulaGovernance />
        </AuthenticatedRoute>
      </Route>
      <Route path="/settings/content">
        <Navigate to="/settings/content/formulas" />
      </Route>
      <Route path="/settings/data/variables">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <VariableRegistry />
        </AuthenticatedRoute>
      </Route>
      <Route path="/settings/data/bindings">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <VariableRegistry />
        </AuthenticatedRoute>
      </Route>
      <Route path="/settings/data/quality">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <VariableRegistry />
        </AuthenticatedRoute>
      </Route>
      <Route path="/settings/data">
        <Navigate to="/settings/data/variables" />
      </Route>
      <Route path="/settings/access/roles">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <PermissionsAdmin />
        </AuthenticatedRoute>
      </Route>
      <Route path="/settings/access/teams">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <PermissionsAdmin />
        </AuthenticatedRoute>
      </Route>
      <Route path="/settings/access/keys">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <PermissionsAdmin />
        </AuthenticatedRoute>
      </Route>
      <Route path="/settings/access">
        <Navigate to="/settings/access/roles" />
      </Route>
      <Route path="/settings/system/settings">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <PlatformSettings />
        </AuthenticatedRoute>
      </Route>
      <Route path="/settings/system/billing">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <BillingRoute>
            <BillingSettings />
          </BillingRoute>
        </AuthenticatedRoute>
      </Route>
      <Route path="/settings/system/billing/usage">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <BillingRoute>
            <UsageDashboard />
          </BillingRoute>
        </AuthenticatedRoute>
      </Route>
      <Route path="/settings/system/billing/invoices">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <BillingRoute>
            <InvoiceList />
          </BillingRoute>
        </AuthenticatedRoute>
      </Route>
      <Route path="/settings/system/billing/payments">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <BillingRoute>
            <PaymentHistory />
          </BillingRoute>
        </AuthenticatedRoute>
      </Route>
      <Route path="/settings">
        <Navigate to="/organization-admin/members" />
      </Route>

      {/* ═══════════════════════════════════════════════════════════════
          DEVELOPER TOOLS
          ═══════════════════════════════════════════════════════════════ */}
      <Route path="/dev/integration">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <Suspense fallback={<PageLoader />}>
            <IntegrationDashboard />
          </Suspense>
        </AuthenticatedRoute>
      </Route>
      {/* ═══════════════════════════════════════════════════════════════
          WORKFLOWS
          ═══════════════════════════════════════════════════════════════ */}
      <Route path="/workflow">
        <AuthenticatedRoute {...tierProps} requiredTier="standard">
          <Navigate to="/workflow/prospect" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/workflow/prospect">
        <AuthenticatedRoute {...tierProps} requiredTier="standard">
          <Suspense fallback={<PageLoader />}>
            <ProspectSetupWithNav />
          </Suspense>
        </AuthenticatedRoute>
      </Route>
      <Route path="/workflow/intelligence">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="intelligence" />
        </AuthenticatedRoute>
      </Route>


      {/* Canonical top-level settings and administration schema */}
      <Route path="/my-settings">
        <Navigate to="/my-settings/profile" />
      </Route>
      <Route path="/my-settings/profile"><Navigate to="/accounts" /></Route>
      <Route path="/my-settings/preferences"><Navigate to="/accounts" /></Route>
      <Route path="/my-settings/notifications"><Navigate to="/accounts" /></Route>
      <Route path="/my-settings/appearance"><Navigate to="/accounts" /></Route>
      <Route path="/my-settings/accounts"><Navigate to="/accounts" /></Route>

      <Route path="/workspace-settings"><Navigate to="/workspace-settings/integrations" /></Route>
      <Route path="/workspace-settings/integrations"><Navigate to="/context/integrations" /></Route>
      <Route path="/workspace-settings/sources"><Navigate to="/context/sources" /></Route>

      <Route path="/organization-admin"><Navigate to="/organization-admin/members" /></Route>
      <Route path="/organization-admin/members"><Navigate to="/settings/access/roles" /></Route>
      <Route path="/organization-admin/roles"><Navigate to="/settings/access/roles" /></Route>
      <Route path="/organization-admin/teams"><Navigate to="/settings/access/teams" /></Route>
      <Route path="/organization-admin/billing"><Navigate to="/settings/system/billing" /></Route>

      <Route path="/platform-configuration"><Navigate to="/platform-configuration/integrations" /></Route>
      <Route path="/platform-configuration/integrations"><Navigate to="/context/integrations" /></Route>
      <Route path="/platform-configuration/api-keys"><Navigate to="/settings/access/keys" /></Route>
      <Route path="/platform-configuration/webhooks"><Navigate to="/settings/system/settings" /></Route>
      <Route path="/platform-configuration/model-routing"><Navigate to="/settings/system/settings" /></Route>
      <Route path="/platform-configuration/feature-flags"><Navigate to="/settings/system/settings" /></Route>

      <Route path="/governance-center"><Navigate to="/governance-center/evidence-policy" /></Route>
      <Route path="/governance-center/evidence-policy"><Navigate to="/governance/evidence" /></Route>
      <Route path="/governance-center/compliance"><Navigate to="/governance/compliance" /></Route>
      <Route path="/governance-center/audit-retention"><Navigate to="/governance/audit/log" /></Route>
      <Route path="/governance-center/residency"><Navigate to="/governance/compliance" /></Route>

      <Route path="/developer-console"><Navigate to="/developer-console/health" /></Route>
      <Route path="/developer-console/health"><Navigate to="/governance/health" /></Route>
      <Route path="/developer-console/traces"><Navigate to="/governance/traces" /></Route>
      <Route path="/developer-console/queue-diagnostics"><Navigate to="/dev/integration" /></Route>
      <Route path="/developer-console/log-diagnostics"><Navigate to="/dev/integration" /></Route>

      {/* ═══════════════════════════════════════════════════════════════
          LEGACY REDIRECTS — Backward Compatibility
          ═══════════════════════════════════════════════════════════════ */}
      {/* Old Discover routes */}
      <Route path="/discover">
        <Navigate to="/accounts" />
      </Route>
      <Route path="/discover/accounts">
        <Navigate to="/accounts" />
      </Route>
      <Route path="/discover/accounts/:id">
        <Navigate to="/accounts" />
      </Route>
      <Route path="/discover/jobs">
        <Navigate to="/context/ingestion/jobs" />
      </Route>
      <Route path="/discover/extraction">
        <Navigate to="/context/extraction" />
      </Route>
      <Route path="/discover/knowledge">
        <Navigate to="/context/ontology" />
      </Route>
      <Route path="/discover/knowledge/entities">
        <Navigate to="/context/ontology/entities" />
      </Route>
      <Route path="/discover/knowledge/graph">
        <Navigate to="/context/ontology/graph" />
      </Route>
      <Route path="/discover/knowledge/ontology">
        <Navigate to="/context/ontology" />
      </Route>
      <Route path="/discover/integrations">
        <Navigate to="/context/integrations" />
      </Route>
      <Route path="/discover/sources">
        <Navigate to="/context/sources" />
      </Route>

      {/* Old Library routes */}
      <Route path="/library">
        <Navigate to="/context/packs" />
      </Route>
      <Route path="/library/packs">
        <Navigate to="/context/packs" />
      </Route>
      <Route path="/library/models">
        <Navigate to="/context/models" />
      </Route>
      <Route path="/library/authoring">
        <Navigate to="/settings/content/formulas" />
      </Route>

      {/* Old Model/Value Studio routes */}
      <Route path="/model">
        <Navigate to="/accounts" />
      </Route>
      <Route path="/model/value-studio">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/model/value-studio/discovery">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="intelligence" tab="signals" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/model/value-studio/mapping">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" tab="action-plan" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/model/value-studio/modeling">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" tab="value-model" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/model/value-studio/validation">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" tab="value-model" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/model/value-studio/narrative">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" tab="narrative" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/model/value-studio/tracking">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" tab="narrative" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/model/value-studio/explorer">
        <Navigate to="/context/value-trees/explorer" />
      </Route>
      <Route path="/model/value-studio/formulas">
        <Navigate to="/context/formulas" />
      </Route>
      <Route path="/model/value-studio/formulas/new">
        <Navigate to="/context/formulas" />
      </Route>

      {/* Old Deliver routes */}
      <Route path="/deliver">
        <Navigate to="/deliverables/cases" />
      </Route>
      <Route path="/deliver/cases">
        <Navigate to="/deliverables/cases" />
      </Route>
      <Route path="/deliver/opportunities">
        <Navigate to="/accounts" />
      </Route>
      <Route path="/deliver/whitespace">
        <Navigate to="/accounts" />
      </Route>
      <Route path="/deliver/agents">
        <Navigate to="/context/agents" />
      </Route>
      <Route path="/deliver/cases/explore">
        <Navigate to="/deliverables/calculators" />
      </Route>


      {/* Old Admin routes */}
      <Route path="/admin">
        <Navigate to="/settings/content/formulas" />
      </Route>
      <Route path="/admin/content">
        <Navigate to="/settings/content/formulas" />
      </Route>
      <Route path="/admin/content/formulas">
        <Navigate to="/settings/content/formulas" />
      </Route>
      <Route path="/admin/content/versions">
        <Navigate to="/settings/content/versions" />
      </Route>
      <Route path="/admin/content/approvals">
        <Navigate to="/settings/content/approvals" />
      </Route>
      <Route path="/admin/content/benchmarks">
        <Navigate to="/governance/benchmarks" />
      </Route>
      <Route path="/admin/data">
        <Navigate to="/settings/data/variables" />
      </Route>
      <Route path="/admin/data/variables">
        <Navigate to="/settings/data/variables" />
      </Route>
      <Route path="/admin/data/bindings">
        <Navigate to="/settings/data/bindings" />
      </Route>
      <Route path="/admin/data/quality">
        <Navigate to="/settings/data/quality" />
      </Route>
      <Route path="/admin/access">
        <Navigate to="/settings/access/roles" />
      </Route>
      <Route path="/admin/access/roles">
        <Navigate to="/settings/access/roles" />
      </Route>
      <Route path="/admin/access/teams">
        <Navigate to="/settings/access/teams" />
      </Route>
      <Route path="/admin/access/keys">
        <Navigate to="/settings/access/keys" />
      </Route>
      <Route path="/admin/system/settings">
        <Navigate to="/settings/system/settings" />
      </Route>
      <Route path="/admin/system/audit">
        <Navigate to="/governance/audit/log" />
      </Route>
      <Route path="/admin/system/health">
        <Navigate to="/governance/health" />
      </Route>

      {/* Old Studio routes */}
      <Route path="/studio/deals">
        <Navigate to="/accounts" />
      </Route>
      <Route path="/studio/build">
        <Navigate to="/accounts" />
      </Route>
      <Route path="/studio/build/discovery">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="intelligence" tab="signals" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/build/mapping">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" tab="action-plan" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/build/modeling">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" tab="value-model" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/build/validation">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" tab="value-model" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/build/narrative">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" tab="narrative" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/build/tracking">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" tab="narrative" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/studio/trees">
        <Navigate to="/accounts" />
      </Route>
      <Route path="/studio/scenarios">
        <Navigate to="/accounts" />
      </Route>

      <AppRoutes tierProps={tierProps} isLoading={isLoading} isAuthenticated={isAuthenticated} />

      {/* ─── Catch-all ─── */}
      <Route>
        <Layout currentTier={currentTier} effectiveTier={effectiveTier}>
          <ErrorBoundary>
            <NotFound />
          </ErrorBoundary>
        </Layout>
      </Route>
     </Switch>
    </Suspense>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="light" switchable>
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

export { Router as AppRouter };
export default App;
