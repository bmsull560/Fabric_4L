import { lazy, memo, Suspense, useEffect } from "react";
import {
  AppShell,
  ErrorBoundary,
  Toaster,
  TooltipProvider,
} from "@/components";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AuthProvider, useAuthContext } from "./contexts/AuthContext";
import { BillingProvider } from "./context/BillingContext";
import { useUserTierStore, type UserTier } from "@/hooks";
import { Route, useLocation, useParams } from "wouter";
import { useAccountContextStore } from "@/stores/accountContextStore";

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
  return <ProspectSetup onNavigateToWorkspace={path => navigate(path)} />;
}

// ── Route-level code splitting ────────────────────────────────────────────────
// Existing pages (preserved)
const LandingPage = lazy(() => import("./pages/LandingPage"));
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
const InteractiveBusinessCase = lazy(
  () => import("./pages/InteractiveBusinessCase")
);
const DecisionTrace = lazy(() => import("./pages/DecisionTrace"));
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
const BusinessCaseList = lazy(() => import("./pages/BusinessCaseList"));
const OpportunityFinder = lazy(() => import("./pages/OpportunityFinder"));
const WhitespaceAnalysis = lazy(() => import("./pages/WhitespaceAnalysis"));
const SourceConfiguration = lazy(() => import("./pages/SourceConfiguration"));
const NotFound = lazy(() => import("./pages/NotFound"));
const Login = lazy(() => import("./pages/Login"));

// ── Workflow Pages ───────────────────────────────────────────────────────────
const ProspectSetup = lazy(() => import("./workflow/pages/ProspectSetup"));

// ── Intelligence Workspace Tabs ──────────────────────────────────────────────
const SignalsTab = lazy(() => import("./pages/intelligence/SignalsTab"));
const DriversTab = lazy(() => import("./pages/intelligence/DriversTab"));
const EvidenceTab = lazy(() => import("./pages/intelligence/EvidenceTab"));
const StakeholdersTab = lazy(
  () => import("./pages/intelligence/StakeholdersTab")
);

// ── Value Studio Workspace Tabs ──────────────────────────────────────────────
const ActionPlanTab = lazy(() => import("./pages/studio/ActionPlanTab"));
const ValueModelTab = lazy(() => import("./pages/studio/ValueModelTab"));
const NarrativeTab = lazy(() => import("./pages/studio/NarrativeTab"));

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
  return <Navigate to={`/intelligence/${params.accountId}/signals`} />;
}

// ── Value Studio Default Redirect ────────────────────────────────────────────
// Redirects /studio/:accountId → /studio/:accountId/action-plan
function StudioRedirect() {
  const params = useParams<{ accountId: string }>();
  return <Navigate to={`/studio/${params.accountId}/action-plan`} />;
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

  if (!selectedAccountId) {
    return <Navigate to="/accounts" />;
  }

  const intelligenceTabs = new Set([
    "signals",
    "drivers",
    "evidence",
    "stakeholders",
  ]);
  const studioTabs = new Set(["action-plan", "value-model", "narrative"]);

  if (workspace === "intelligence") {
    const resolvedTabCandidate = explicitTab ?? params.tab;
    const tab =
      resolvedTabCandidate && intelligenceTabs.has(resolvedTabCandidate)
        ? resolvedTabCandidate
        : "signals";
    return <Navigate to={`/intelligence/${selectedAccountId}/${tab}`} />;
  }

  const resolvedTabCandidate = explicitTab ?? params.tab;
  const tab =
    resolvedTabCandidate && studioTabs.has(resolvedTabCandidate)
      ? resolvedTabCandidate
      : "action-plan";
  return <Navigate to={`/studio/${selectedAccountId}/${tab}`} />;
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

const AuthenticatedRoute = memo(function AuthenticatedRoute({
  children,
  requiredTier = "standard",
  currentTier,
  effectiveTier,
}: AuthenticatedRouteProps) {
  return (
    <AppShell currentTier={currentTier} effectiveTier={effectiveTier}>
      <RouteGuard requiredTier={requiredTier}>
        <ErrorBoundary>{children}</ErrorBoundary>
      </RouteGuard>
    </AppShell>
  );
});

// ── Router ───────────────────────────────────────────────────────────────────

function Router() {
  const rawCurrentTier = useUserTierStore(state => state.currentTier);
  const rawEffectiveTier = useUserTierStore(state => state.effectiveTier);
  const { isAuthenticated } = useAuthContext();

  const currentTier: RequiredUserTier =
    rawCurrentTier === "unknown" ? "standard" : rawCurrentTier;
  const effectiveTier: RequiredUserTier =
    rawEffectiveTier === "unknown" ? "standard" : rawEffectiveTier;

  // Pre-bound tier props for AuthenticatedRoute to avoid passing on every render
  const tierProps = { currentTier, effectiveTier };

  return (
    <Suspense fallback={<PageLoader />}>
      {/* ═══════════════════════════════════════════════════════════════
          PUBLIC ROUTES — No AppShell
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
          2. INTELLIGENCE — Discovery Workspace
          ═══════════════════════════════════════════════════════════════ */}
      <Route path="/intelligence">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="intelligence" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/intelligence/signals">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="intelligence" tab="signals" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/intelligence/drivers">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="intelligence" tab="drivers" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/intelligence/evidence">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="intelligence" tab="evidence" />
        </AuthenticatedRoute>
      </Route>
      <Route path="/intelligence/stakeholders">
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect
            workspace="intelligence"
            tab="stakeholders"
          />
        </AuthenticatedRoute>
      </Route>
      <Route path="/intelligence/:accountId">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <IntelligenceRedirect />
        </AuthenticatedRoute>
      </Route>
      <Route path="/intelligence/:accountId/signals">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <SignalsTab />
        </AuthenticatedRoute>
      </Route>
      <Route path="/intelligence/:accountId/drivers">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <DriversTab />
        </AuthenticatedRoute>
      </Route>
      <Route path="/intelligence/:accountId/evidence">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <EvidenceTab />
        </AuthenticatedRoute>
      </Route>
      <Route path="/intelligence/:accountId/stakeholders">
        <AuthenticatedRoute {...tierProps}>
          <AccountContextSync />
          <StakeholdersTab />
        </AuthenticatedRoute>
      </Route>

      {/* ═══════════════════════════════════════════════════════════════
          3. VALUE STUDIO — Synthesis Workspace
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

      {/* ═══════════════════════════════════════════════════════════════
          4. CONTEXT ENGINE — Vendor Knowledge Base
          ═══════════════════════════════════════════════════════════════ */}
      <Route path="/context">
        <Navigate to="/context/packs" />
      </Route>
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

      {/* ═══════════════════════════════════════════════════════════════
          5. DELIVERABLES — Activation Layer
          ═══════════════════════════════════════════════════════════════ */}
      <Route path="/deliverables">
        <Navigate to="/deliverables/cases" />
      </Route>
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
          <BusinessCase />
        </AuthenticatedRoute>
      </Route>
      <Route path="/deliverables/views/executive">
        <AuthenticatedRoute {...tierProps}>
          <BusinessCase />
        </AuthenticatedRoute>
      </Route>
      <Route path="/deliverables/views/technical">
        <AuthenticatedRoute {...tierProps}>
          <BusinessCase />
        </AuthenticatedRoute>
      </Route>
      <Route path="/deliverables/api">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <Integrations />
        </AuthenticatedRoute>
      </Route>

      {/* ═══════════════════════════════════════════════════════════════
          6. GOVERNANCE — Trust Layer
          ═══════════════════════════════════════════════════════════════ */}
      <Route path="/governance">
        <Navigate to="/governance/traces" />
      </Route>
      <Route path="/governance/traces">
        <AuthenticatedRoute {...tierProps}>
          <DecisionTrace />
        </AuthenticatedRoute>
      </Route>
      <Route path="/governance/evidence">
        <AuthenticatedRoute {...tierProps}>
          <DecisionTrace />
        </AuthenticatedRoute>
      </Route>
      <Route path="/governance/provenance">
        <AuthenticatedRoute {...tierProps} requiredTier="advanced">
          <DecisionTrace />
        </AuthenticatedRoute>
      </Route>
      <Route path="/governance/integrity">
        <AuthenticatedRoute {...tierProps} requiredTier="advanced">
          <DecisionTrace />
        </AuthenticatedRoute>
      </Route>
      <Route path="/governance/compliance">
        <AuthenticatedRoute {...tierProps} requiredTier="advanced">
          <DecisionTrace />
        </AuthenticatedRoute>
      </Route>
      <Route path="/governance/benchmarks">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <BenchmarkPolicies />
        </AuthenticatedRoute>
      </Route>
      <Route path="/governance/audit">
        <Navigate to="/governance/audit/log" />
      </Route>
      <Route path="/governance/audit/log">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <DecisionTrace />
        </AuthenticatedRoute>
      </Route>
      <Route path="/governance/audit/changes">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <DecisionTrace />
        </AuthenticatedRoute>
      </Route>
      <Route path="/governance/health">
        <AuthenticatedRoute {...tierProps} requiredTier="admin">
          <HealthMonitor />
        </AuthenticatedRoute>
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
      <Route path="/settings/data">
        <Navigate to="/settings/data/variables" />
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
      <Route path="/settings/access">
        <Navigate to="/settings/access/roles" />
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
      <Route path="/workflow/ai-model">
        <Navigate to="/accounts" />
      </Route>
      <Route path="/workflow/driver-tree">
        <Navigate to="/accounts" />
      </Route>
      <Route path="/workflow/evidence">
        <Navigate to="/accounts" />
      </Route>
      <Route path="/workflow/calculator">
        <Navigate to="/accounts" />
      </Route>
      <Route path="/workflow/value-case">
        <Navigate to="/accounts" />
      </Route>

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
        <AuthenticatedRoute {...tierProps}>
          <WorkspaceContextRedirect workspace="studio" tab="value-model" />
        </AuthenticatedRoute>
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

      {/* Old Evidence routes */}
      <Route path="/evidence">
        <Navigate to="/governance/traces" />
      </Route>
      <Route path="/evidence/traces">
        <Navigate to="/governance/traces" />
      </Route>
      <Route path="/evidence/export">
        <Navigate to="/governance/evidence" />
      </Route>
      <Route path="/evidence/lineage">
        <Navigate to="/governance/provenance" />
      </Route>
      <Route path="/evidence/compliance">
        <Navigate to="/governance/compliance" />
      </Route>
      <Route path="/evidence/changelog">
        <Navigate to="/governance/audit/changes" />
      </Route>

      {/* Old Trust routes */}
      <Route path="/trust">
        <Navigate to="/governance/traces" />
      </Route>
      <Route path="/trust/traces">
        <Navigate to="/governance/traces" />
      </Route>
      <Route path="/trust/evidence">
        <Navigate to="/governance/evidence" />
      </Route>
      <Route path="/trust/provenance">
        <Navigate to="/governance/provenance" />
      </Route>
      <Route path="/trust/integrity">
        <Navigate to="/governance/integrity" />
      </Route>
      <Route path="/trust/compliance">
        <Navigate to="/governance/compliance" />
      </Route>
      <Route path="/trust/benchmarks">
        <Navigate to="/governance/benchmarks" />
      </Route>
      <Route path="/trust/audit">
        <Navigate to="/governance/audit/log" />
      </Route>
      <Route path="/trust/audit/log">
        <Navigate to="/governance/audit/log" />
      </Route>
      <Route path="/trust/audit/changes">
        <Navigate to="/governance/audit/changes" />
      </Route>
      <Route path="/trust/health">
        <Navigate to="/governance/health" />
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

      {/* ─── Catch-all ─── */}
      <Route>
        <AppShell currentTier={currentTier} effectiveTier={effectiveTier}>
          <ErrorBoundary>
            <NotFound />
          </ErrorBoundary>
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
