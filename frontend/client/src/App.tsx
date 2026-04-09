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
import NotFound          from "./pages/NotFound";

function Router() {
  return (
    <AppShell>
      <Switch>
        <Route path="/">
          <Redirect to="/command-center"/>
        </Route>
        <Route path="/command-center"          component={CommandCenter}/>
        <Route path="/extraction-engine"       component={ExtractionEngine}/>
        {/* Ontology sub-routes */}
        <Route path="/ontology">
          <Redirect to="/ontology/entities"/>
        </Route>
        <Route path="/ontology/entities"       component={OntologyBrowser}/>
        <Route path="/ontology/entity-detail"  component={EntityDetail}/>
        <Route path="/ontology/extractions"    component={OntologyBrowser}/>
        <Route path="/ontology/validation"     component={OntologyBrowser}/>
        {/* Value Trees sub-routes */}
        <Route path="/value-trees">
          <Redirect to="/value-trees/explorer"/>
        </Route>
        <Route path="/value-trees/explorer"    component={ValueTreeExplorer}/>
        <Route path="/value-trees/normalization" component={ValueTreeExplorer}/>
        <Route path="/value-trees/formulas"    component={FormulaBuilder}/>
        {/* Knowledge Graph sub-routes */}
        <Route path="/graph">
          <Redirect to="/graph/explorer"/>
        </Route>
        <Route path="/graph/explorer"          component={GraphExplorer}/>
        <Route path="/graph/query"             component={GraphExplorer}/>
        <Route path="/graph/communities"       component={GraphExplorer}/>
        {/* Agent Workflows sub-routes */}
        <Route path="/agents">
          <Redirect to="/agents/dashboard"/>
        </Route>
        <Route path="/agents/dashboard"        component={AgentWorkflows}/>
        <Route path="/agents/whitespace"       component={AgentWorkflows}/>
        <Route path="/agents/business-cases"   component={BusinessCase}/>
        {/* Audit sub-routes */}
        <Route path="/audit">
          <Redirect to="/audit/traces"/>
        </Route>
        <Route path="/audit/traces"            component={DecisionTrace}/>
        <Route path="/audit/lineage"           component={DecisionTrace}/>
        <Route path="/audit/reports"           component={DecisionTrace}/>
        {/* Data sources placeholder */}
        <Route path="/data-sources"            component={CommandCenter}/>
        <Route path="/data-sources/targets"    component={CommandCenter}/>
        <Route path="/data-sources/jobs"       component={CommandCenter}/>
        {/* Settings placeholder */}
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
