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
import { Route, useLocation, Link } from "wouter";

// ── Navigate Component for wouter ───────────────────────────────────────────
// Replacement for React Router's <Navigate />, which doesn't exist in wouter
// Uses useEffect to avoid navigation during render (React best practice)
function Navigate({ to }: { to: string }) {
  const [, navigate] = useLocation();

  useEffect(() => {
    navigate(to);
  }, [navigate, to]);

  return null;
}

// ── Route-level code splitting ────────────────────────────────────────────────
// Each page is loaded only when its route is first visited, reducing the initial
// JS bundle by ~60–70% and improving Time-to-Interactive for all users.
const LandingPage            = lazy(() => import("./pages/LandingPage"));
const CommandCenter          = lazy(() => import("./pages/CommandCenter"));
const ValueNarrativeHome    = lazy(() => import("./pages/ValueNarrativeHome"));
const ExtractionEngine       = lazy(() => import("./pages/ExtractionEngine"));
const IngestionJobs          = lazy(() => import("./pages/IngestionJobs"));
const OntologyEditor         = lazy(() => import("./pages/OntologyEditor"));
const EntityBrowser          = lazy(() => import("./pages/EntityBrowser"));
const EntityDetail           = lazy(() => import("./pages/EntityDetail"));
const ValueTreeExplorer      = lazy(() => import("./pages/ValueTreeExplorer"));
const FormulaBuilder         = lazy(() => import("./pages/FormulaBuilder"));
const FormulaList            = lazy(() => import("./pages/FormulaList"));
const GraphExplorer          = lazy(() => import("./pages/GraphExplorer"));
const AgentWorkflows         = lazy(() => import("./pages/AgentWorkflows"));
const BusinessCase           = lazy(() => import("./pages/BusinessCase"));
const InteractiveBusinessCase = lazy(() => import("./pages/InteractiveBusinessCase"));
const DecisionTrace          = lazy(() => import("./pages/DecisionTrace"));
const ValuePacks             = lazy(() => import("./pages/ValuePacks"));
const Accounts               = lazy(() => import("./pages/Accounts"));
const Integrations           = lazy(() => import("./pages/Integrations"));
const FormulaGovernance      = lazy(() => import("./pages/admin/FormulaGovernance"));
const BenchmarkPolicies      = lazy(() => import("./pages/admin/BenchmarkPolicies"));
const VariableRegistry       = lazy(() => import("./pages/admin/VariableRegistry"));
const PackManagement         = lazy(() => import("./pages/admin/PackManagement"));
const PermissionsAdmin       = lazy(() => import("./pages/admin/PermissionsAdmin"));
const PlatformSettings       = lazy(() => import("./pages/admin/PlatformSettings"));
const HealthMonitor          = lazy(() => import("./pages/admin/HealthMonitor"));
const MyModels               = lazy(() => import("./pages/MyModels"));
const BusinessCaseList       = lazy(() => import("./pages/BusinessCaseList"));
const OpportunityFinder      = lazy(() => import("./pages/OpportunityFinder"));
const WhitespaceAnalysis     = lazy(() => import("./pages/WhitespaceAnalysis"));
const SourceConfiguration    = lazy(() => import("./pages/SourceConfiguration"));
const NotFound               = lazy(() => import("./pages/NotFound"));
const Login                  = lazy(() => import("./pages/Login"));
// ── Value Studio — 6-Stage Pipeline ──────────────────────────────────────────
const Stage1Discovery        = lazy(() => import("./pages/value-studio/Stage1Discovery"));
const Stage2Mapping          = lazy(() => import("./pages/value-studio/Stage2Mapping"));
const Stage3Modeling         = lazy(() => import("./pages/value-studio/Stage3Modeling"));
const Stage4Validation       = lazy(() => import("./pages/value-studio/Stage4Validation"));
const Stage5Narrative        = lazy(() => import("./pages/value-studio/Stage5Narrative"));
const Stage6Tracking         = lazy(() => import("./pages/value-studio/Stage6Tracking"));

// Minimal inline fallback — shown during chunk download (typically <200 ms on broadband)
function PageLoader() {
  return (
    <div className="flex items-center justify-center h-full min-h-[200px]">
      <div className="w-6 h-6 rounded-full border-2 border-neutral-300 border-t-neutral-700 animate-spin" />
    </div>
  );
}

/**
 * Route Guard Component — Enforces authentication and tier-based access control
 * Requires valid authentication before checking tier permissions.
 * Uses canonical route tier mapping from userTierStore.
 * SECURITY: Fails closed on any exception or error during permission evaluation.
 */
// Exclude 'unknown' from RouteGuard required tier - routes must have explicit tier requirements
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
  const effectiveTier = useUserTierStore(state => state.effectiveTier);

  // Wait for auth state to be determined before rendering
  if (isLoading) {
    return null;
  }

  // Navigate unauthenticated users to login
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  // Check if user can access this route based on tier
  // SECURITY: Wrap in try-catch to fail closed on any exception
  let accessDecision;
  try {
    accessDecision = canAccessRouteWithReason(requiredTier);
  } catch (error) {
    // SECURITY: Fail closed on any permission evaluation error
    console.error('[RouteGuard] Permission evaluation failed:', error);
    accessDecision = { allowed: false, reason: 'PERMISSION_EVALUATION_EXCEPTION' };
  }

  if (!accessDecision.allowed) {
    // SECURITY: Log denied access attempts for monitoring
    console.warn(`[RouteGuard] Access denied to ${location}: ${accessDecision.reason}`);
    
    // SECURITY: Navigate all denied requests to safe fallback
    // Regardless of tier, unauthorized access attempts go to /home
    return <Navigate to="/home" />;
  }

  return <>{children}</>;
}

function Router() {
  const rawCurrentTier = useUserTierStore(state => state.currentTier);
  const rawEffectiveTier = useUserTierStore(state => state.effectiveTier);
  const { isAuthenticated, isLoading } = useAuthContext();
  
  // SECURITY: Sanitize tier values - 'unknown' tier should never be passed to UI
  // This ensures AppShell only receives valid, renderable tier values
  const currentTier: RequiredUserTier = rawCurrentTier === 'unknown' ? 'standard' : rawCurrentTier;
  const effectiveTier: RequiredUserTier = rawEffectiveTier === 'unknown' ? 'standard' : rawEffectiveTier;

  return (
    <Suspense fallback={<PageLoader />}>
      {/* ═══════════════════════════════════════════════════════════════
          PUBLIC ROUTES — Outside AppShell (unauthenticated)
          ═══════════════════════════════════════════════════════════════ */}
      
      {/* Landing Page — Marketing/Login page */}
      <Route path="/">
        {isAuthenticated ? <Navigate to="/home" /> : <LandingPage />}
      </Route>

        {/* Legacy Login route — handles OIDC callbacks */}
        <Route path="/login">
          <Login />
        </Route>
        <Route path="/login/callback">
          <Login /> {/* Handles OIDC callback with code+state */}
        </Route>

        {/* ═══════════════════════════════════════════════════════════════
            AUTHENTICATED ROUTES — Inside AppShell with RouteGuard
            ═══════════════════════════════════════════════════════════════ */}
        <Route>
          <AppShell currentTier={currentTier} effectiveTier={effectiveTier}>
          {/* ═══════════════════════════════════════════════════════════════
              HOME — Dashboard (All Tiers)
              ═══════════════════════════════════════════════════════════════ */}
          <Route path="/home">
            <RouteGuard>
              <ErrorBoundary><ValueNarrativeHome /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* ═══════════════════════════════════════════════════════════════
              LIBRARY — Content Catalog (All Tiers)
              ═══════════════════════════════════════════════════════════════ */}
          <Route path="/library">
            <Navigate to="/library/packs"/>
          </Route>
          <Route path="/library/packs">
            <RouteGuard>
              <ErrorBoundary><ValuePacks /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/library/models">
            <RouteGuard>
              <ErrorBoundary><MyModels /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/library/authoring">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><PackManagement /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* ═══════════════════════════════════════════════════════════════
              DISCOVER — Research & Data (Tier 1+, progressive disclosure)
              ═══════════════════════════════════════════════════════════════ */}
          <Route path="/discover">
            <Navigate to="/discover/accounts"/>
          </Route>
          <Route path="/discover/accounts">
            <RouteGuard>
              <ErrorBoundary><Accounts /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/discover/accounts/:id">
            <RouteGuard>
              <ErrorBoundary><Accounts /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/discover/jobs">
            <RouteGuard>
              <ErrorBoundary><IngestionJobs /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/discover/extraction">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><ExtractionEngine /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* Discover → Knowledge Model (Tier 2+) */}
          <Route path="/discover/knowledge">
            <Navigate to="/discover/knowledge/entities"/>
          </Route>
          <Route path="/discover/knowledge/entities">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><EntityBrowser /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/discover/knowledge/graph">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><GraphExplorer /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/discover/knowledge/ontology">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><OntologyEditor /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* Discover → Admin (Tier 3) */}
          <Route path="/discover/integrations">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><Integrations /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/discover/sources">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><SourceConfiguration /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* ═══════════════════════════════════════════════════════════════
              MODEL — Build Value Models (Tier 2+)
              ═══════════════════════════════════════════════════════════════ */}
          <Route path="/model">
            <Navigate to="/model/value-studio/explorer"/>
          </Route>
          <Route path="/model/value-studio">
            <Navigate to="/model/value-studio/discovery"/>
          </Route>
          {/* ── Value Studio 6-Stage Pipeline ── */}
          <Route path="/model/value-studio/discovery">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><Stage1Discovery /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/model/value-studio/mapping">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><Stage2Mapping /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/model/value-studio/modeling">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><Stage3Modeling /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/model/value-studio/validation">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><Stage4Validation /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/model/value-studio/narrative">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><Stage5Narrative /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/model/value-studio/tracking">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><Stage6Tracking /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/model/value-studio/explorer">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><ValueTreeExplorer /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/model/value-studio/normalization">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><ValueTreeExplorer /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/model/value-studio/formulas">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><FormulaList /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/model/value-studio/formulas/new">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><FormulaBuilder isNew /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/model/value-studio/formulas/:formulaId">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><FormulaBuilder /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* ═══════════════════════════════════════════════════════════════
              DELIVER — Output & Workflows (All Tiers)
              ═══════════════════════════════════════════════════════════════ */}
          <Route path="/deliver">
            <Navigate to="/deliver/cases"/>
          </Route>
          <Route path="/deliver/cases">
            <RouteGuard>
              <ErrorBoundary><BusinessCaseList /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/deliver/cases/:caseId">
            <RouteGuard>
              <ErrorBoundary><BusinessCase /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/deliver/opportunities">
            <RouteGuard>
              <ErrorBoundary><OpportunityFinder /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/deliver/whitespace">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><WhitespaceAnalysis /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/deliver/agents">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><AgentWorkflows /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/deliver/cases/explore">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><InteractiveBusinessCase /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* ═══════════════════════════════════════════════════════════════
              EVIDENCE — Audit & Provenance (All Tiers)
              ═══════════════════════════════════════════════════════════════ */}
          <Route path="/evidence">
            <Navigate to="/evidence/traces"/>
          </Route>
          <Route path="/evidence/traces">
            <RouteGuard>
              <ErrorBoundary><DecisionTrace /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/evidence/export">
            <RouteGuard>
              <ErrorBoundary><DecisionTrace /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/evidence/lineage">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><DecisionTrace /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/evidence/compliance">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><DecisionTrace /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/evidence/changelog">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><DecisionTrace /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* ═══════════════════════════════════════════════════════════════
              GOVERN — Admin Control Plane (Tier 3)
              ═══════════════════════════════════════════════════════════════ */}
          <Route path="/admin">
            <Navigate to="/admin/content/formulas"/>
          </Route>

          {/* Govern → Content */}
          <Route path="/admin/content">
            <Navigate to="/admin/content/formulas"/>
          </Route>
          <Route path="/admin/content/formulas">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><FormulaGovernance /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/admin/content/versions">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><FormulaGovernance /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/admin/content/approvals">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><FormulaGovernance /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/admin/content/benchmarks">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><BenchmarkPolicies /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* Govern → Data */}
          <Route path="/admin/data">
            <Navigate to="/admin/data/variables"/>
          </Route>
          <Route path="/admin/data/variables">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><VariableRegistry /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/admin/data/bindings">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><VariableRegistry /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/admin/data/quality">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><VariableRegistry /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* Govern → Access */}
          <Route path="/admin/access">
            <Navigate to="/admin/access/roles"/>
          </Route>
          <Route path="/admin/access/roles">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><PermissionsAdmin /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/admin/access/teams">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><PermissionsAdmin /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/admin/access/keys">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><PermissionsAdmin /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* Govern → System */}
          <Route path="/admin/system">
            <Navigate to="/admin/system/settings"/>
          </Route>
          <Route path="/admin/system/settings">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><PlatformSettings /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/admin/system/audit">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><DecisionTrace /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/admin/system/health">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><HealthMonitor /></ErrorBoundary>
            </RouteGuard>
          </Route>

              {/* Catch-all for authenticated routes */}
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
            <Toaster/>
            <Router/>
          </TooltipProvider>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
