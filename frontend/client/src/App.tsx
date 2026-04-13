import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Route, Switch, Redirect, useLocation } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import AppShell from "./components/AppShell";
import { useUserTierStore, getRouteTier, type UserTier } from "./stores/userTierStore";

// Pages
import CommandCenter     from "./pages/CommandCenter";
import ExtractionEngine  from "./pages/ExtractionEngine";
import OntologyBrowser   from "./pages/OntologyBrowser";
import EntityDetail      from "./pages/EntityDetail";
import ValueTreeExplorer from "./pages/ValueTreeExplorer";
import FormulaBuilder    from "./pages/FormulaBuilder";
import GraphExplorer     from "./pages/GraphExplorer";
import AgentWorkflows    from "./pages/AgentWorkflows";
import BusinessCase      from "./pages/BusinessCase";
import InteractiveBusinessCase from "./pages/InteractiveBusinessCase";
import DecisionTrace     from "./pages/DecisionTrace";
import ValuePacks        from "./pages/ValuePacks";
import { FormulaGovernance, BenchmarkPolicies, VariableRegistry, PackManagement, PermissionsAdmin } from "./pages/admin";
import NotFound          from "./pages/NotFound";

/**
 * Route Guard Component — Enforces tier-based access control
 * Redirects users to appropriate tier if they lack permissions
 */
const TIER_HIERARCHY: Record<UserTier, number> = {
  standard: 1,
  advanced: 2,
  admin: 3,
};

function getMaxTier(a: UserTier, b: UserTier): UserTier {
  return TIER_HIERARCHY[a] >= TIER_HIERARCHY[b] ? a : b;
}

function RouteGuard({ 
  children, 
  requiredTier = "standard" 
}: { 
  children: React.ReactNode; 
  requiredTier?: UserTier;
}) {
  const [location] = useLocation();
  const canAccessRoute = useUserTierStore(state => state.canAccessRoute);
  const effectiveTier = useUserTierStore(state => state.effectiveTier);
  
  // Get the route's inherent tier requirement
  const routeTier = getRouteTier(location);
  
  // Use the MORE restrictive of: prop-specified tier OR route's inherent tier
  const effectiveRequiredTier = getMaxTier(requiredTier, routeTier);
  
  // Check if user can access this route
  if (!canAccessRoute(effectiveRequiredTier)) {
    // Redirect based on user's effective tier
    if (effectiveTier === "standard") {
      return <Redirect to="/command-center" />;
    } else if (effectiveTier === "advanced") {
      return <Redirect to="/extraction-engine" />;
    }
    return <Redirect to="/command-center" />;
  }
  
  return <>{children}</>;
}

function Router() {
  const currentTier = useUserTierStore(state => state.currentTier);
  const effectiveTier = useUserTierStore(state => state.effectiveTier);
  
  return (
    <AppShell currentTier={currentTier} effectiveTier={effectiveTier}>
      <Switch>
        <Route path="/">
          <Redirect to="/command-center"/>
        </Route>

        {/* ── Tier 1: Standard User Routes ── */}
        <Route path="/command-center">
          <RouteGuard>
            <ErrorBoundary><CommandCenter /></ErrorBoundary>
          </RouteGuard>
        </Route>
        
        {/* ── Tier 2: Advanced Routes (protected) ── */}
        <Route path="/extraction-engine">
          <RouteGuard requiredTier="advanced">
            <ErrorBoundary><ExtractionEngine /></ErrorBoundary>
          </RouteGuard>
        </Route>

        {/* ── Standard user: Value Packs ── */}
        <Route path="/value-packs">
          <RouteGuard>
            <ErrorBoundary><ValuePacks /></ErrorBoundary>
          </RouteGuard>
        </Route>

        {/* ── Tier 2: Ontology sub-routes ── */}
        <Route path="/ontology">
          <Redirect to="/ontology/entities"/>
        </Route>
        <Route path="/ontology/entities">
          <RouteGuard requiredTier="advanced">
            <ErrorBoundary><OntologyBrowser /></ErrorBoundary>
          </RouteGuard>
        </Route>
        <Route path="/ontology/entity-detail">
          <RouteGuard requiredTier="advanced">
            <ErrorBoundary><EntityDetail /></ErrorBoundary>
          </RouteGuard>
        </Route>
        <Route path="/ontology/extractions">
          <RouteGuard requiredTier="advanced">
            <ErrorBoundary><OntologyBrowser /></ErrorBoundary>
          </RouteGuard>
        </Route>
        <Route path="/ontology/validation">
          <RouteGuard requiredTier="advanced">
            <ErrorBoundary><OntologyBrowser /></ErrorBoundary>
          </RouteGuard>
        </Route>

        {/* ── Tier 2: Value Models / Formula Studio sub-routes ── */}
        <Route path="/value-trees">
          <Redirect to="/value-trees/explorer"/>
        </Route>
        <Route path="/value-trees/explorer">
          <RouteGuard requiredTier="advanced">
            <ErrorBoundary><ValueTreeExplorer /></ErrorBoundary>
          </RouteGuard>
        </Route>
        <Route path="/value-trees/normalization">
          <RouteGuard requiredTier="advanced">
            <ErrorBoundary><ValueTreeExplorer /></ErrorBoundary>
          </RouteGuard>
        </Route>
        <Route path="/value-trees/formulas">
          <RouteGuard requiredTier="advanced">
            <ErrorBoundary><FormulaBuilder /></ErrorBoundary>
          </RouteGuard>
        </Route>

        {/* ── Tier 2: Knowledge Graph sub-routes ── */}
        <Route path="/graph">
          <Redirect to="/graph/explorer"/>
        </Route>
        <Route path="/graph/explorer">
          <RouteGuard requiredTier="advanced">
            <ErrorBoundary><GraphExplorer /></ErrorBoundary>
          </RouteGuard>
        </Route>
        <Route path="/graph/query">
          <RouteGuard requiredTier="advanced">
            <ErrorBoundary><GraphExplorer /></ErrorBoundary>
          </RouteGuard>
        </Route>
        <Route path="/graph/communities">
          <RouteGuard requiredTier="advanced">
            <ErrorBoundary><GraphExplorer /></ErrorBoundary>
          </RouteGuard>
        </Route>

        {/* ── Agent Workflows sub-routes ── */}
        <Route path="/agents">
          <Redirect to="/agents/dashboard"/>
        </Route>
        <Route path="/agents/dashboard">
          <ErrorBoundary><AgentWorkflows /></ErrorBoundary>
        </Route>
        <Route path="/agents/whitespace">
          <ErrorBoundary><AgentWorkflows /></ErrorBoundary>
        </Route>
        <Route path="/agents/business-cases">
          <ErrorBoundary><BusinessCase /></ErrorBoundary>
        </Route>
        <Route path="/agents/business-cases/explore">
          <ErrorBoundary><InteractiveBusinessCase /></ErrorBoundary>
        </Route>

        {/* ── Audit sub-routes ── */}
        <Route path="/audit">
          <Redirect to="/audit/traces"/>
        </Route>
        <Route path="/audit/traces">
          <ErrorBoundary><DecisionTrace /></ErrorBoundary>
        </Route>
        <Route path="/audit/lineage">
          <ErrorBoundary><DecisionTrace /></ErrorBoundary>
        </Route>
        <Route path="/audit/reports">
          <ErrorBoundary><DecisionTrace /></ErrorBoundary>
        </Route>

        {/* ── Research / Data Sources ── */}
        <Route path="/research">
          <ErrorBoundary><CommandCenter /></ErrorBoundary>
        </Route>
        <Route path="/data-sources">
          <ErrorBoundary><CommandCenter /></ErrorBoundary>
        </Route>
        <Route path="/data-sources/targets">
          <ErrorBoundary><CommandCenter /></ErrorBoundary>
        </Route>
        <Route path="/data-sources/jobs">
          <ErrorBoundary><ExtractionEngine /></ErrorBoundary>
        </Route>

        {/* ── Tier 3: Admin Control Plane ── */}
        <Route path="/admin/formulas">
          <RouteGuard requiredTier="admin">
            <ErrorBoundary><FormulaGovernance /></ErrorBoundary>
          </RouteGuard>
        </Route>
        <Route path="/admin/formulas/versions">
          <RouteGuard requiredTier="admin">
            <ErrorBoundary><FormulaGovernance /></ErrorBoundary>
          </RouteGuard>
        </Route>
        <Route path="/admin/formulas/approvals">
          <RouteGuard requiredTier="admin">
            <ErrorBoundary><FormulaGovernance /></ErrorBoundary>
          </RouteGuard>
        </Route>
        <Route path="/admin/benchmarks">
          <RouteGuard requiredTier="admin">
            <ErrorBoundary><BenchmarkPolicies /></ErrorBoundary>
          </RouteGuard>
        </Route>
        <Route path="/admin/benchmarks/policies">
          <RouteGuard requiredTier="admin">
            <ErrorBoundary><BenchmarkPolicies /></ErrorBoundary>
          </RouteGuard>
        </Route>
        <Route path="/admin/variables">
          <RouteGuard requiredTier="admin">
            <ErrorBoundary><VariableRegistry /></ErrorBoundary>
          </RouteGuard>
        </Route>
        <Route path="/admin/variables/bindings">
          <RouteGuard requiredTier="admin">
            <ErrorBoundary><VariableRegistry /></ErrorBoundary>
          </RouteGuard>
        </Route>
        <Route path="/admin/packs">
          <RouteGuard requiredTier="admin">
            <ErrorBoundary><PackManagement /></ErrorBoundary>
          </RouteGuard>
        </Route>
        <Route path="/admin/permissions">
          <RouteGuard requiredTier="admin">
            <ErrorBoundary><PermissionsAdmin /></ErrorBoundary>
          </RouteGuard>
        </Route>
        <Route path="/admin/permissions/teams">
          <RouteGuard requiredTier="admin">
            <ErrorBoundary><PermissionsAdmin /></ErrorBoundary>
          </RouteGuard>
        </Route>

        {/* ── Settings placeholder ── */}
        <Route path="/settings">
          <ErrorBoundary><CommandCenter /></ErrorBoundary>
        </Route>

        <Route>
          <ErrorBoundary><NotFound /></ErrorBoundary>
        </Route>
      </Switch>
    </AppShell>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="light">
        <TooltipProvider>
          <Toaster/>
          <Router/>
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
