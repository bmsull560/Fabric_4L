import { lazy, Suspense } from "react";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Route, Switch, Redirect, useLocation } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AuthProvider, useAuthContext } from "./contexts/AuthContext";
import AppShell from "./components/AppShell";
import { useUserTierStore, type UserTier } from "./stores/userTierStore";

// ── Route-level code splitting ────────────────────────────────────────────────
// Each page is loaded only when its route is first visited, reducing the initial
// JS bundle by ~60–70% and improving Time-to-Interactive for all users.
const LandingPage            = lazy(() => import("./pages/LandingPage"));
const CommandCenter          = lazy(() => import("./pages/CommandCenter"));
const ValueNarrativeHome    = lazy(() => import("./pages/ValueNarrativeHome"));
const ExtractionEngine       = lazy(() => import("./pages/ExtractionEngine"));
const OntologyBrowser        = lazy(() => import("./pages/OntologyBrowser"));
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
const NotFound               = lazy(() => import("./pages/NotFound"));
const Login                  = lazy(() => import("./pages/Login"));

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

  // Redirect unauthenticated users to login
  if (!isAuthenticated) {
    return <Redirect to="/login" />;
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
    
    // SECURITY: Redirect all denied requests to safe fallback
    // Regardless of tier, unauthorized access attempts go to /home
    return <Redirect to="/home" />;
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
      <Switch>
        {/* ═══════════════════════════════════════════════════════════════
            PUBLIC ROUTES — Outside AppShell (unauthenticated)
            ═══════════════════════════════════════════════════════════════ */}
        
        {/* Landing Page — Marketing/Login page */}
        <Route path="/">
          {isAuthenticated ? <Redirect to="/home" /> : <LandingPage />}
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
            <Switch>

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
            <Redirect to="/library/packs"/>
          </Route>
          <Route path="/library/packs">
            <RouteGuard>
              <ErrorBoundary><ValuePacks /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/library/models">
            <RouteGuard>
              <ErrorBoundary><ValuePacks /></ErrorBoundary>
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
            <Redirect to="/discover/accounts"/>
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
              <ErrorBoundary><ExtractionEngine /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/discover/extraction">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><ExtractionEngine /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* Discover → Knowledge Model (Tier 2+) */}
          <Route path="/discover/knowledge">
            <Redirect to="/discover/knowledge/entities"/>
          </Route>
          <Route path="/discover/knowledge/entities">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><EntityDetail /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/discover/knowledge/graph">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><GraphExplorer /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/discover/knowledge/ontology">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><OntologyBrowser /></ErrorBoundary>
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
              <ErrorBoundary><Integrations /></ErrorBoundary>
            </RouteGuard>
          </Route>

          {/* ═══════════════════════════════════════════════════════════════
              MODEL — Build Value Models (Tier 2+)
              ═══════════════════════════════════════════════════════════════ */}
          <Route path="/model">
            <Redirect to="/model/value-studio/explorer"/>
          </Route>
          <Route path="/model/value-studio">
            <Redirect to="/model/value-studio/explorer"/>
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
            <Redirect to="/deliver/cases"/>
          </Route>
          <Route path="/deliver/cases">
            <RouteGuard>
              <ErrorBoundary><BusinessCase /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/deliver/opportunities">
            <RouteGuard>
              <ErrorBoundary><BusinessCase /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/deliver/whitespace">
            <RouteGuard requiredTier="advanced">
              <ErrorBoundary><AgentWorkflows /></ErrorBoundary>
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
            <Redirect to="/evidence/traces"/>
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
            <Redirect to="/admin/content/formulas"/>
          </Route>

          {/* Govern → Content */}
          <Route path="/admin/content">
            <Redirect to="/admin/content/formulas"/>
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
            <Redirect to="/admin/data/variables"/>
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
            <Redirect to="/admin/access/roles"/>
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
            <Redirect to="/admin/system/settings"/>
          </Route>
          <Route path="/admin/system/settings">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><CommandCenter /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/admin/system/audit">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><DecisionTrace /></ErrorBoundary>
            </RouteGuard>
          </Route>
          <Route path="/admin/system/health">
            <RouteGuard requiredTier="admin">
              <ErrorBoundary><CommandCenter /></ErrorBoundary>
            </RouteGuard>
          </Route>

              {/* Catch-all for authenticated routes */}
              <Route>
                <ErrorBoundary><NotFound /></ErrorBoundary>
              </Route>
            </Switch>
          </AppShell>
        </Route>
      </Switch>
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
