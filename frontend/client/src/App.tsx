import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Route, Switch, Redirect } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import AppShell from "./components/AppShell";

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
import { FormulaGovernance, BenchmarkPolicies, VariableRegistry } from "./pages/AdminScreens";
import NotFound          from "./pages/NotFound";

function Router() {
  return (
    <AppShell>
      <Switch>
        <Route path="/">
          <Redirect to="/command-center"/>
        </Route>

        {/* ── Core ── */}
        <Route path="/command-center"          component={CommandCenter}/>
        <Route path="/extraction-engine"       component={ExtractionEngine}/>

        {/* ── Standard user: Value Packs ── */}
        <Route path="/value-packs"             component={ValuePacks}/>

        {/* ── Ontology sub-routes ── */}
        <Route path="/ontology">
          <Redirect to="/ontology/entities"/>
        </Route>
        <Route path="/ontology/entities"       component={OntologyBrowser}/>
        <Route path="/ontology/entity-detail"  component={EntityDetail}/>
        <Route path="/ontology/extractions"    component={OntologyBrowser}/>
        <Route path="/ontology/validation"     component={OntologyBrowser}/>

        {/* ── Value Models / Formula Studio sub-routes ── */}
        <Route path="/value-trees">
          <Redirect to="/value-trees/explorer"/>
        </Route>
        <Route path="/value-trees/explorer"      component={ValueTreeExplorer}/>
        <Route path="/value-trees/normalization" component={ValueTreeExplorer}/>
        <Route path="/value-trees/formulas"      component={FormulaBuilder}/>

        {/* ── Knowledge Graph sub-routes ── */}
        <Route path="/graph">
          <Redirect to="/graph/explorer"/>
        </Route>
        <Route path="/graph/explorer"          component={GraphExplorer}/>
        <Route path="/graph/query"             component={GraphExplorer}/>
        <Route path="/graph/communities"       component={GraphExplorer}/>

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

        {/* ── Admin screens ── */}
        <Route path="/admin/formulas">
          <FormulaGovernance/>
        </Route>
        <Route path="/admin/formulas/versions">
          <FormulaGovernance/>
        </Route>
        <Route path="/admin/formulas/approvals">
          <FormulaGovernance/>
        </Route>
        <Route path="/admin/benchmarks">
          <BenchmarkPolicies/>
        </Route>
        <Route path="/admin/benchmarks/policies">
          <BenchmarkPolicies/>
        </Route>
        <Route path="/admin/variables">
          <VariableRegistry/>
        </Route>
        <Route path="/admin/variables/bindings">
          <VariableRegistry/>
        </Route>
        <Route path="/admin/permissions"       component={CommandCenter}/>
        <Route path="/admin/permissions/teams" component={CommandCenter}/>

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
