import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Route, Switch, Redirect, useLocation } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import AppShell from "./components/AppShell";
import { useUserTierStore, type UserTier } from "./stores/userTierStore";

// Pages — Canonical Navigation Taxonomy
// Home, Library, Discover, Model, Deliver, Evidence, Govern
import CommandCenter     from "./pages/CommandCenter";      // Home dashboard
import ExtractionEngine  from "./pages/ExtractionEngine";    // Discover/extraction
import OntologyBrowser   from "./pages/OntologyBrowser";     // Discover/knowledge/ontology
import EntityDetail      from "./pages/EntityDetail";        // Discover/knowledge/entities
import ValueTreeExplorer from "./pages/ValueTreeExplorer";   // Model/value-studio/explorer
import FormulaBuilder    from "./pages/FormulaBuilder";      // Model/value-studio/formulas
import GraphExplorer     from "./pages/GraphExplorer";      // Discover/knowledge/graph
import AgentWorkflows    from "./pages/AgentWorkflows";    // Deliver/agents
import BusinessCase      from "./pages/BusinessCase";       // Deliver/cases
import InteractiveBusinessCase from "./pages/InteractiveBusinessCase"; // Deliver/cases/explore
import DecisionTrace     from "./pages/DecisionTrace";      // Evidence/traces
import ValuePacks        from "./pages/ValuePacks";         // Library/packs
import Accounts          from "./pages/Accounts";          // Discover/accounts
import Integrations      from "./pages/Integrations";      // Discover/integrations
import { FormulaGovernance, BenchmarkPolicies, VariableRegistry, PackManagement, PermissionsAdmin } from "./pages/admin";
import NotFound          from "./pages/NotFound";

/**
 * Route Guard Component — Enforces tier-based access control
 * Uses canonical route tier mapping from userTierStore
 */
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

  // Check if user can access this route
  if (!canAccessRoute(requiredTier)) {
    // Redirect based on user's effective tier
    if (effectiveTier === "standard") {
      return <Redirect to="/home" />;
    } else if (effectiveTier === "advanced") {
      return <Redirect to="/home" />;
    }
    return <Redirect to="/home" />;
  }

  return <>{children}</>;
}

function Router() {
  const currentTier = useUserTierStore(state => state.currentTier);
  const effectiveTier = useUserTierStore(state => state.effectiveTier);

  return (
    <AppShell currentTier={currentTier} effectiveTier={effectiveTier}>
      <Switch>
        {/* Root redirect to Home */}
        <Route path="/">
          <Redirect to="/home"/>
        </Route>

        {/* ═══════════════════════════════════════════════════════════════
            HOME — Dashboard (All Tiers)
            ═══════════════════════════════════════════════════════════════ */}
        <Route path="/home">
          <RouteGuard>
            <ErrorBoundary><CommandCenter /></ErrorBoundary>
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

        {/* Catch-all */}
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
