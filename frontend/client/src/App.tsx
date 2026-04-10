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
import DecisionTrace     from "./pages/DecisionTrace";
import ValuePacks        from "./pages/ValuePacks";
import { FormulaGovernance, BenchmarkPolicies, VariableRegistry } from "./pages/admin";
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
          <RouteGuard><CommandCenter /></RouteGuard>
        </Route>
        
        {/* ── Tier 2: Advanced Routes (protected) ── */}
        <Route path="/extraction-engine">
          <RouteGuard requiredTier="advanced"><ExtractionEngine /></RouteGuard>
        </Route>

        {/* ── Standard user: Value Packs ── */}
        <Route path="/value-packs"             component={ValuePacks}/>

        {/* ── Tier 2: Ontology sub-routes ── */}
        <Route path="/ontology">
          <Redirect to="/ontology/entities"/>
        </Route>
        <Route path="/ontology/entities">
          <RouteGuard requiredTier="advanced"><OntologyBrowser /></RouteGuard>
        </Route>
        <Route path="/ontology/entity-detail">
          <RouteGuard requiredTier="advanced"><EntityDetail /></RouteGuard>
        </Route>
        <Route path="/ontology/extractions">
          <RouteGuard requiredTier="advanced"><OntologyBrowser /></RouteGuard>
        </Route>
        <Route path="/ontology/validation">
          <RouteGuard requiredTier="advanced"><OntologyBrowser /></RouteGuard>
        </Route>

        {/* ── Tier 2: Value Models / Formula Studio sub-routes ── */}
        <Route path="/value-trees">
          <Redirect to="/value-trees/explorer"/>
        </Route>
        <Route path="/value-trees/explorer">
          <RouteGuard requiredTier="advanced"><ValueTreeExplorer /></RouteGuard>
        </Route>
        <Route path="/value-trees/normalization">
          <RouteGuard requiredTier="advanced"><ValueTreeExplorer /></RouteGuard>
        </Route>
        <Route path="/value-trees/formulas">
          <RouteGuard requiredTier="advanced"><FormulaBuilder /></RouteGuard>
        </Route>

        {/* ── Tier 2: Knowledge Graph sub-routes ── */}
        <Route path="/graph">
          <Redirect to="/graph/explorer"/>
        </Route>
        <Route path="/graph/explorer">
          <RouteGuard requiredTier="advanced"><GraphExplorer /></RouteGuard>
        </Route>
        <Route path="/graph/query">
          <RouteGuard requiredTier="advanced"><GraphExplorer /></RouteGuard>
        </Route>
        <Route path="/graph/communities">
          <RouteGuard requiredTier="advanced"><GraphExplorer /></RouteGuard>
        </Route>

        {/* ── Agent Workflows sub-routes ── */}
        <Route path="/agents">
          <Redirect to="/agents/dashboard"/>
        </Route>
        <Route path="/agents/dashboard"        component={AgentWorkflows}/>
        <Route path="/agents/whitespace"       component={AgentWorkflows}/>
        <Route path="/agents/business-cases"   component={BusinessCase}/>

        {/* ── Audit sub-routes ── */}
        <Route path="/audit">
          <Redirect to="/audit/traces"/>
        </Route>
        <Route path="/audit/traces"            component={DecisionTrace}/>
        <Route path="/audit/lineage"           component={DecisionTrace}/>
        <Route path="/audit/reports"           component={DecisionTrace}/>

        {/* ── Research / Data Sources ── */}
        <Route path="/research"                component={CommandCenter}/>
        <Route path="/data-sources"            component={CommandCenter}/>
        <Route path="/data-sources/targets"    component={CommandCenter}/>
        <Route path="/data-sources/jobs"       component={ExtractionEngine}/>

        {/* ── Tier 3: Admin Control Plane ── */}
        <Route path="/admin/formulas">
          <RouteGuard requiredTier="admin"><FormulaGovernance /></RouteGuard>
        </Route>
        <Route path="/admin/formulas/versions">
          <RouteGuard requiredTier="admin"><FormulaGovernance /></RouteGuard>
        </Route>
        <Route path="/admin/formulas/approvals">
          <RouteGuard requiredTier="admin"><FormulaGovernance /></RouteGuard>
        </Route>
        <Route path="/admin/benchmarks">
          <RouteGuard requiredTier="admin"><BenchmarkPolicies /></RouteGuard>
        </Route>
        <Route path="/admin/benchmarks/policies">
          <RouteGuard requiredTier="admin"><BenchmarkPolicies /></RouteGuard>
        </Route>
        <Route path="/admin/variables">
          <RouteGuard requiredTier="admin"><VariableRegistry /></RouteGuard>
        </Route>
        <Route path="/admin/variables/bindings">
          <RouteGuard requiredTier="admin"><VariableRegistry /></RouteGuard>
        </Route>
        <Route path="/admin/permissions">
          <RouteGuard requiredTier="admin"><CommandCenter /></RouteGuard>
        </Route>
        <Route path="/admin/permissions/teams">
          <RouteGuard requiredTier="admin"><CommandCenter /></RouteGuard>
        </Route>

        {/* ── Settings placeholder ── */}
        <Route path="/settings"               component={CommandCenter}/>

        <Route component={NotFound}/>
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
