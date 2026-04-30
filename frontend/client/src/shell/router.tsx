import { lazy } from "react";
import { createBrowserRouter, Navigate, useNavigate, useParams } from "react-router-dom";
import { Route as WouterRoute } from "wouter";
import { WouterAdapter } from "@/components/routing/WouterAdapter";
import { useAuthContext } from "@/contexts/AuthContext";
import { GlobalLayout } from "@/components/layout/GlobalLayout";
import { ProtectedRoute } from "@/components/routing/ProtectedRoute";
import { AccountContextSync } from "@/components/routing/AccountContextSync";
import { AccountScopedRedirect } from "@/components/routing/AccountScopedRedirect";
import { WorkspacePage } from "@/components/routing/WorkspacePage";
import { useAccountContextStore } from "@/stores/accountContextStore";
import { useCreateAccount } from "@/hooks/useAccounts";
import { SettingsLayout } from "@/app/settings/SettingsLayout";

// Settings pages — Personal
const PersonalProfile = lazy(() => import("@/app/settings/pages/PersonalProfile").then(m => ({ default: m.PersonalProfile })));
const PersonalSecurity = lazy(() => import("@/app/settings/pages/PersonalSecurity").then(m => ({ default: m.PersonalSecurity })));
const PersonalPreferences = lazy(() => import("@/app/settings/pages/PersonalPreferences").then(m => ({ default: m.PersonalPreferences })));
const PersonalNotifications = lazy(() => import("@/app/settings/pages/PersonalNotifications").then(m => ({ default: m.PersonalNotifications })));
const PersonalSessions = lazy(() => import("@/app/settings/pages/PersonalSessions").then(m => ({ default: m.PersonalSessions })));

// Settings pages — Account & Billing
const BillingWorkspace = lazy(() => import("@/app/settings/pages/BillingWorkspace").then(m => ({ default: m.BillingWorkspace })));
const BillingSubscription = lazy(() => import("@/app/settings/pages/BillingSubscription").then(m => ({ default: m.BillingSubscription })));
const BillingUsage = lazy(() => import("@/app/settings/pages/BillingUsage").then(m => ({ default: m.BillingUsage })));
const BillingPaymentMethods = lazy(() => import("@/app/settings/pages/BillingPaymentMethods").then(m => ({ default: m.BillingPaymentMethods })));
const BillingInvoices = lazy(() => import("@/app/settings/pages/BillingInvoices").then(m => ({ default: m.BillingInvoices })));

// Settings pages — Team & Access
const TeamMembers = lazy(() => import("@/app/settings/pages/TeamMembers").then(m => ({ default: m.TeamMembers })));
const TeamInvitations = lazy(() => import("@/app/settings/pages/TeamInvitations").then(m => ({ default: m.TeamInvitations })));
const TeamRoles = lazy(() => import("@/app/settings/pages/TeamRoles").then(m => ({ default: m.TeamRoles })));
const TeamPermissions = lazy(() => import("@/app/settings/pages/TeamPermissions").then(m => ({ default: m.TeamPermissions })));
const TeamApiKeys = lazy(() => import("@/app/settings/pages/TeamApiKeys").then(m => ({ default: m.TeamApiKeys })));

// Settings pages — Data & Integrations
const DataSources = lazy(() => import("@/app/settings/pages/DataSources").then(m => ({ default: m.DataSources })));
const DataIntegrations = lazy(() => import("@/app/settings/pages/DataIntegrations").then(m => ({ default: m.DataIntegrations })));
const DataVariables = lazy(() => import("@/app/settings/pages/DataVariables").then(m => ({ default: m.DataVariables })));
const DataValuePacks = lazy(() => import("@/app/settings/pages/DataValuePacks").then(m => ({ default: m.DataValuePacks })));
const DataIngestionRules = lazy(() => import("@/app/settings/pages/DataIngestionRules").then(m => ({ default: m.DataIngestionRules })));

// Settings pages — Governance
const GovernancePolicies = lazy(() => import("@/app/settings/pages/GovernancePolicies").then(m => ({ default: m.GovernancePolicies })));
const GovernanceCompliance = lazy(() => import("@/app/settings/pages/GovernanceCompliance").then(m => ({ default: m.GovernanceCompliance })));
const GovernanceHealth = lazy(() => import("@/app/settings/pages/GovernanceHealth").then(m => ({ default: m.GovernanceHealth })));
const GovernanceAuditTrail = lazy(() => import("@/app/settings/pages/GovernanceAuditTrail").then(m => ({ default: m.GovernanceAuditTrail })));
const GovernanceAdminControls = lazy(() => import("@/app/settings/pages/GovernanceAdminControls").then(m => ({ default: m.GovernanceAdminControls })));

const Login = lazy(() => import("@/pages/Login"));
const Signup = lazy(() => import("@/pages/Signup"));
const ValueNarrativeHome = lazy(() => import("@/pages/ValueNarrativeHome"));
const Accounts = lazy(() => import("@/pages/Accounts"));
const CommandCenter = lazy(() => import("@/pages/CommandCenter"));

// ── Workspace Tab Pages ───────────────────────────────────────────────────────
const SignalsTab = lazy(() => import("@/pages/intelligence/SignalsTab"));
const StakeholdersTab = lazy(() => import("@/pages/intelligence/StakeholdersTab"));
const EnrichmentTab = lazy(() => import("@/pages/intelligence/EnrichmentTab"));
const OntologyMatchTab = lazy(() => import("@/pages/intelligence/OntologyMatchTab"));
const HypothesesTab = lazy(() => import("@/pages/intelligence/HypothesesTab"));
const DiscoveryQuestionsTab = lazy(() => import("@/pages/hypothesis/DiscoveryQuestionsTab"));
const PersonaFitTab = lazy(() => import("@/pages/hypothesis/PersonaFitTab"));
const AssumptionsTab = lazy(() => import("@/pages/hypothesis/AssumptionsTab"));
const DriverTreePage = lazy(() => import("@/pages/drivers/DriverTreePage"));
const CalcROITab = lazy(() => import("@/pages/calculator/ROITab"));
const CalcValueModelTab = lazy(() => import("@/pages/calculator/ValueModelTab"));
const ValueCasePage = lazy(() => import("@/pages/value-case/ValueCasePage"));
const RealizationPage = lazy(() => import("@/pages/realization/RealizationPage"));

// ── Studio Tabs (legacy) ──
const ActionPlanTab = lazy(() => import("@/pages/studio/ActionPlanTab"));
const ValueModelTab = lazy(() => import("@/pages/studio/ValueModelTab"));
const NarrativeTab = lazy(() => import("@/pages/studio/NarrativeTab"));
const StudioEnrichmentTab = lazy(() => import("@/pages/studio/StudioEnrichmentTab"));
const StudioCompetitiveTab = lazy(() => import("@/pages/studio/StudioCompetitiveTab"));
const StudioROITab = lazy(() => import("@/pages/studio/StudioROITab"));
const StudioEvidenceTab = lazy(() => import("@/pages/studio/StudioEvidenceTab"));

// ── Context Engine ──
const ValuePacks = lazy(() => import("@/pages/ValuePacks"));
const MyModels = lazy(() => import("@/pages/MyModels"));
const FormulaList = lazy(() => import("@/pages/FormulaList"));
const FormulaBuilder = lazy(() => import("@/pages/FormulaBuilder"));
const ValueTreeExplorer = lazy(() => import("@/pages/ValueTreeExplorer"));
const AgentWorkflows = lazy(() => import("@/pages/AgentWorkflows"));
const OntologyEditor = lazy(() => import("@/pages/OntologyEditor"));
const EntityBrowser = lazy(() => import("@/pages/EntityBrowser"));
const EntityDetail = lazy(() => import("@/pages/EntityDetail"));
const GraphExplorer = lazy(() => import("@/pages/GraphExplorer"));
const IngestionJobs = lazy(() => import("@/pages/IngestionJobs"));
const ExtractionEngine = lazy(() => import("@/pages/ExtractionEngine"));
const Integrations = lazy(() => import("@/pages/Integrations"));
const SourceConfiguration = lazy(() => import("@/pages/SourceConfiguration"));

// ── Deliverables ──
const BusinessCaseList = lazy(() => import("@/pages/BusinessCaseList"));
const BusinessCase = lazy(() => import("@/pages/BusinessCase"));
const InteractiveBusinessCase = lazy(() => import("@/pages/InteractiveBusinessCase"));
const CFOView = lazy(() => import("@/pages/deliverables/CFOView"));
const ExecutiveView = lazy(() => import("@/pages/deliverables/ExecutiveView"));
const TechnicalView = lazy(() => import("@/pages/deliverables/TechnicalView"));

// ── Governance ──
const DecisionTracePage = lazy(() => import("@/pages/DecisionTrace"));
const GovernanceEvidencePage = lazy(() => import("@/pages/GovernanceEvidence"));
const GovernanceCompliancePage = lazy(() => import("@/pages/GovernanceCompliance"));
const GovernanceAuditLogPage = lazy(() => import("@/pages/GovernanceAuditLog"));
const GovernanceChangeHistoryPage = lazy(() => import("@/pages/GovernanceChangeHistory"));
const BenchmarkPoliciesPage = lazy(() => import("@/pages/admin/BenchmarkPolicies"));
const HealthMonitorPage = lazy(() => import("@/pages/admin/HealthMonitor"));

// ── Workflow ──
const ProspectSetup = lazy(() => import("@/workflow/pages/ProspectSetup"));
const WorkflowIntelligence = lazy(() => import("@/workflow/pages/Intelligence"));
const AIModel = lazy(() => import("@/workflow/pages/AIModel"));
const WorkflowDriverTree = lazy(() => import("@/workflow/pages/DriverTree"));
const WorkflowEvidence = lazy(() => import("@/workflow/pages/Evidence"));
const WorkflowCalculator = lazy(() => import("@/workflow/pages/Calculator"));
const WorkflowValueCase = lazy(() => import("@/workflow/pages/ValueCase"));

// ── Dev Tools ──
const IntegrationDashboard = lazy(() => import("@/pages/dev/IntegrationDashboard"));
const NotFound = lazy(() => import("@/pages/NotFound"));

// ── Wouter Bridge for legacy wouter-based pages inside React Router ──
function WouterBridge({ path, children }: { path?: string; children: React.ReactNode }) {
  return (
    <WouterAdapter>
      {path ? <WouterRoute path={path}>{children}</WouterRoute> : children}
    </WouterAdapter>
  );
}

function ProspectSetupWithNav() {
  const navigate = useNavigate();
  const createAccount = useCreateAccount();

  const handleCreateSetup = async (payload: {
    companyName?: string;
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

function StudioAccountRedirect() {
  const selectedAccountId = useAccountContextStore((state) => state.selectedAccountId);
  const { tab } = useParams<{ tab?: string }>();
  if (!selectedAccountId) {
    return <Navigate to="/accounts" replace />;
  }
  const targetTab = tab || "action-plan";
  return <Navigate to={`/studio/${selectedAccountId}/${targetTab}`} replace />;
}

function RootRedirect() {
  const { isAuthenticated, isLoading } = useAuthContext();

  if (isLoading) {
    return (
      <div className="flex h-full min-h-[200px] items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-border border-t-primary" />
      </div>
    );
  }

  return isAuthenticated ? (
    <Navigate to="/home" replace />
  ) : (
    <Navigate to="/login" replace />
  );
}

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <Login />,
  },
  {
    path: "/login/callback",
    element: <Login />,
  },
  {
    path: "/signup",
    element: <Signup />,
  },
  {
    element: <GlobalLayout />,
    children: [
      {
        path: "/",
        element: <RootRedirect />,
      },
      {
        path: "/home",
        element: (
          <ProtectedRoute>
            <ValueNarrativeHome />
          </ProtectedRoute>
        ),
      },
      {
        path: "/command-center",
        element: (
          <ProtectedRoute>
            <CommandCenter />
          </ProtectedRoute>
        ),
      },
      {
        path: "/accounts",
        element: (
          <ProtectedRoute>
            <Accounts />
          </ProtectedRoute>
        ),
      },
      {
        path: "/accounts/:id",
        element: (
          <ProtectedRoute>
            <Accounts />
          </ProtectedRoute>
        ),
      },

      // ═══════════════════════════════════════════════════════════════
      // FUNCTIONAL WORKSPACES — Intelligence, Hypothesis, Driver Tree,
      // Calculator, Value Case, Value Realization
      // ═══════════════════════════════════════════════════════════════

      // ── Intelligence (4 tabs) ──
      {
        path: "/intelligence",
        element: (
          <ProtectedRoute>
            <AccountScopedRedirect basePath="/intelligence" defaultTab="signals" />
          </ProtectedRoute>
        ),
      },
      {
        path: "/intelligence/:accountId",
        element: (
          <ProtectedRoute>
            <AccountContextSync />
            <Navigate to="signals" replace />
          </ProtectedRoute>
        ),
      },
      {
        path: "/intelligence/:accountId/signals",
        element: (
          <ProtectedRoute>
            <AccountContextSync />
            <WorkspacePage path="/intelligence/:accountId/signals">
              <SignalsTab />
            </WorkspacePage>
          </ProtectedRoute>
        ),
      },
      {
        path: "/intelligence/:accountId/stakeholders",
        element: (
          <ProtectedRoute>
            <AccountContextSync />
            <WorkspacePage path="/intelligence/:accountId/stakeholders">
              <StakeholdersTab />
            </WorkspacePage>
          </ProtectedRoute>
        ),
      },
      {
        path: "/intelligence/:accountId/ontology-match",
        element: (
          <ProtectedRoute>
            <AccountContextSync />
            <WorkspacePage path="/intelligence/:accountId/ontology-match">
              <OntologyMatchTab />
            </WorkspacePage>
          </ProtectedRoute>
        ),
      },
      {
        path: "/intelligence/:accountId/enrichment",
        element: (
          <ProtectedRoute>
            <AccountContextSync />
            <WorkspacePage path="/intelligence/:accountId/enrichment">
              <EnrichmentTab />
            </WorkspacePage>
          </ProtectedRoute>
        ),
      },

      // ── Hypothesis (4 tabs) ──
      {
        path: "/hypothesis",
        element: (
          <ProtectedRoute>
            <AccountScopedRedirect basePath="/hypothesis" defaultTab="hypothesis" />
          </ProtectedRoute>
        ),
      },
      {
        path: "/hypothesis/:accountId",
        element: (
          <ProtectedRoute>
            <AccountContextSync />
            <Navigate to="hypothesis" replace />
          </ProtectedRoute>
        ),
      },
      {
        path: "/hypothesis/:accountId/hypothesis",
        element: (
          <ProtectedRoute>
            <AccountContextSync />
            <WorkspacePage path="/hypothesis/:accountId/hypothesis">
              <HypothesesTab />
            </WorkspacePage>
          </ProtectedRoute>
        ),
      },
      {
        path: "/hypothesis/:accountId/discovery-questions",
        element: (
          <ProtectedRoute>
            <AccountContextSync />
            <WorkspacePage path="/hypothesis/:accountId/discovery-questions">
              <DiscoveryQuestionsTab />
            </WorkspacePage>
          </ProtectedRoute>
        ),
      },
      {
        path: "/hypothesis/:accountId/persona-fit",
        element: (
          <ProtectedRoute>
            <AccountContextSync />
            <WorkspacePage path="/hypothesis/:accountId/persona-fit">
              <PersonaFitTab />
            </WorkspacePage>
          </ProtectedRoute>
        ),
      },
      {
        path: "/hypothesis/:accountId/assumptions",
        element: (
          <ProtectedRoute>
            <AccountContextSync />
            <WorkspacePage path="/hypothesis/:accountId/assumptions">
              <AssumptionsTab />
            </WorkspacePage>
          </ProtectedRoute>
        ),
      },

      // ── Driver Tree (3 tabs) ──
      {
        path: "/drivers",
        element: (
          <ProtectedRoute>
            <AccountScopedRedirect basePath="/drivers" />
          </ProtectedRoute>
        ),
      },
      {
        path: "/drivers/:accountId",
        element: (
          <ProtectedRoute>
            <AccountContextSync />
            <WorkspacePage path="/drivers/:accountId">
              <DriverTreePage />
            </WorkspacePage>
          </ProtectedRoute>
        ),
      },
      {
        path: "/drivers/:accountId/:tab",
        element: (
          <ProtectedRoute>
            <AccountContextSync />
            <WorkspacePage path="/drivers/:accountId/:tab">
              <DriverTreePage />
            </WorkspacePage>
          </ProtectedRoute>
        ),
      },

      // ── Calculator (2 tabs) ──
      {
        path: "/calculator",
        element: (
          <ProtectedRoute>
            <AccountScopedRedirect basePath="/calculator" defaultTab="roi" />
          </ProtectedRoute>
        ),
      },
      {
        path: "/calculator/:accountId",
        element: (
          <ProtectedRoute>
            <AccountContextSync />
            <Navigate to="roi" replace />
          </ProtectedRoute>
        ),
      },
      {
        path: "/calculator/:accountId/roi",
        element: (
          <ProtectedRoute>
            <AccountContextSync />
            <WorkspacePage path="/calculator/:accountId/roi">
              <CalcROITab />
            </WorkspacePage>
          </ProtectedRoute>
        ),
      },
      {
        path: "/calculator/:accountId/value-model",
        element: (
          <ProtectedRoute>
            <AccountContextSync />
            <WorkspacePage path="/calculator/:accountId/value-model">
              <CalcValueModelTab />
            </WorkspacePage>
          </ProtectedRoute>
        ),
      },

      // ── Value Case ──
      {
        path: "/value-case",
        element: (
          <ProtectedRoute>
            <AccountScopedRedirect basePath="/value-case" />
          </ProtectedRoute>
        ),
      },
      {
        path: "/value-case/:accountId",
        element: (
          <ProtectedRoute>
            <AccountContextSync />
            <WorkspacePage path="/value-case/:accountId">
              <ValueCasePage />
            </WorkspacePage>
          </ProtectedRoute>
        ),
      },

      // ── Value Realization ──
      {
        path: "/realization",
        element: (
          <ProtectedRoute>
            <AccountScopedRedirect basePath="/realization" />
          </ProtectedRoute>
        ),
      },
      {
        path: "/realization/:accountId",
        element: (
          <ProtectedRoute>
            <AccountContextSync />
            <WorkspacePage path="/realization/:accountId">
              <RealizationPage />
            </WorkspacePage>
          </ProtectedRoute>
        ),
      },

      // ═══════════════════════════════════════════════════════════════
      // CONTEXT ENGINE
      // ═══════════════════════════════════════════════════════════════
      { path: "/context", element: <Navigate to="/context/packs" replace /> },
      { path: "/context/packs", element: <ProtectedRoute><ValuePacks /></ProtectedRoute> },
      { path: "/context/models", element: <ProtectedRoute><MyModels /></ProtectedRoute> },
      { path: "/context/formulas", element: <ProtectedRoute requiredTier="advanced"><WouterBridge><FormulaList /></WouterBridge></ProtectedRoute> },
      { path: "/context/formulas/new", element: <ProtectedRoute requiredTier="advanced"><WouterBridge path="/context/formulas/new"><FormulaBuilder isNew /></WouterBridge></ProtectedRoute> },
      { path: "/context/formulas/:formulaId", element: <ProtectedRoute requiredTier="advanced"><WouterBridge path="/context/formulas/:formulaId"><FormulaBuilder /></WouterBridge></ProtectedRoute> },
      { path: "/context/value-trees/explorer", element: <ProtectedRoute requiredTier="advanced"><WouterBridge><ValueTreeExplorer /></WouterBridge></ProtectedRoute> },
      { path: "/context/agents", element: <ProtectedRoute requiredTier="advanced"><AgentWorkflows /></ProtectedRoute> },
      { path: "/context/ontology", element: <ProtectedRoute requiredTier="advanced"><OntologyEditor /></ProtectedRoute> },
      { path: "/context/ontology/entities", element: <ProtectedRoute requiredTier="advanced"><EntityBrowser /></ProtectedRoute> },
      { path: "/context/ontology/entities/:entityId", element: <ProtectedRoute requiredTier="advanced"><WouterBridge path="/context/ontology/entities/:entityId"><EntityDetail /></WouterBridge></ProtectedRoute> },
      { path: "/context/ontology/graph", element: <ProtectedRoute requiredTier="advanced"><GraphExplorer /></ProtectedRoute> },
      { path: "/context/ingestion/jobs", element: <ProtectedRoute requiredTier="advanced"><WouterBridge><IngestionJobs /></WouterBridge></ProtectedRoute> },
      { path: "/context/extraction", element: <ProtectedRoute requiredTier="advanced"><ExtractionEngine /></ProtectedRoute> },
      { path: "/context/integrations", element: <ProtectedRoute requiredTier="admin"><WouterBridge><Integrations /></WouterBridge></ProtectedRoute> },
      { path: "/context/sources", element: <ProtectedRoute requiredTier="admin"><SourceConfiguration /></ProtectedRoute> },
      { path: "/graph-explorer", element: <ProtectedRoute requiredTier="advanced"><GraphExplorer /></ProtectedRoute> },
      { path: "/formula-builder", element: <ProtectedRoute requiredTier="advanced"><WouterBridge><FormulaBuilder /></WouterBridge></ProtectedRoute> },

      // ═══════════════════════════════════════════════════════════════
      // DELIVERABLES
      // ═══════════════════════════════════════════════════════════════
      { path: "/deliverables", element: <Navigate to="/deliverables/cases" replace /> },
      { path: "/deliverables/cases", element: <ProtectedRoute><WouterBridge><BusinessCaseList /></WouterBridge></ProtectedRoute> },
      { path: "/deliverables/cases/:caseId", element: <ProtectedRoute><WouterBridge><BusinessCase /></WouterBridge></ProtectedRoute> },
      { path: "/deliverables/calculators", element: <ProtectedRoute requiredTier="advanced"><WouterBridge><InteractiveBusinessCase /></WouterBridge></ProtectedRoute> },
      { path: "/deliverables/views/cfo", element: <ProtectedRoute><WouterBridge><CFOView /></WouterBridge></ProtectedRoute> },
      { path: "/deliverables/views/executive", element: <ProtectedRoute><WouterBridge><ExecutiveView /></WouterBridge></ProtectedRoute> },
      { path: "/deliverables/views/technical", element: <ProtectedRoute><WouterBridge><TechnicalView /></WouterBridge></ProtectedRoute> },
      { path: "/deliverables/api", element: <ProtectedRoute requiredTier="admin"><WouterBridge><Integrations /></WouterBridge></ProtectedRoute> },

      // ═══════════════════════════════════════════════════════════════
      // GOVERNANCE (top-level)
      // ═══════════════════════════════════════════════════════════════
      { path: "/governance", element: <Navigate to="/governance/traces" replace /> },
      { path: "/governance/traces", element: <ProtectedRoute><DecisionTracePage /></ProtectedRoute> },
      { path: "/governance/evidence", element: <ProtectedRoute><GovernanceEvidencePage /></ProtectedRoute> },
      { path: "/governance/provenance", element: <ProtectedRoute requiredTier="advanced"><DecisionTracePage /></ProtectedRoute> },
      { path: "/governance/integrity", element: <ProtectedRoute requiredTier="advanced"><DecisionTracePage /></ProtectedRoute> },
      { path: "/governance/compliance", element: <ProtectedRoute requiredTier="advanced"><GovernanceCompliancePage /></ProtectedRoute> },
      { path: "/governance/benchmarks", element: <ProtectedRoute requiredTier="admin"><BenchmarkPoliciesPage /></ProtectedRoute> },
      { path: "/governance/audit", element: <Navigate to="/governance/audit/log" replace /> },
      { path: "/governance/audit/log", element: <ProtectedRoute requiredTier="admin"><GovernanceAuditLogPage /></ProtectedRoute> },
      { path: "/governance/audit/changes", element: <ProtectedRoute requiredTier="admin"><GovernanceChangeHistoryPage /></ProtectedRoute> },
      { path: "/governance/health", element: <ProtectedRoute requiredTier="admin"><HealthMonitorPage /></ProtectedRoute> },

      // ═══════════════════════════════════════════════════════════════
      // LEGACY REDIRECTS
      // ═══════════════════════════════════════════════════════════════
      { path: "/trust", element: <Navigate to="/governance/traces" replace /> },
      { path: "/trust/traces", element: <Navigate to="/governance/traces" replace /> },
      { path: "/trust/evidence", element: <Navigate to="/governance/evidence" replace /> },
      { path: "/trust/provenance", element: <Navigate to="/governance/provenance" replace /> },
      { path: "/trust/integrity", element: <Navigate to="/governance/integrity" replace /> },
      { path: "/trust/compliance", element: <Navigate to="/governance/compliance" replace /> },
      { path: "/trust/benchmarks", element: <Navigate to="/governance/benchmarks" replace /> },
      { path: "/trust/audit", element: <Navigate to="/governance/audit/log" replace /> },
      { path: "/trust/audit/log", element: <Navigate to="/governance/audit/log" replace /> },
      { path: "/trust/audit/changes", element: <Navigate to="/governance/audit/changes" replace /> },
      { path: "/trust/health", element: <Navigate to="/governance/health" replace /> },

      { path: "/evidence", element: <Navigate to="/governance/traces" replace /> },
      { path: "/evidence/traces", element: <Navigate to="/governance/traces" replace /> },
      { path: "/evidence/export", element: <Navigate to="/governance/evidence" replace /> },
      { path: "/evidence/lineage", element: <Navigate to="/governance/provenance" replace /> },
      { path: "/evidence/compliance", element: <Navigate to="/governance/compliance" replace /> },
      { path: "/evidence/changelog", element: <Navigate to="/governance/audit/changes" replace /> },

      { path: "/governance-center", element: <Navigate to="/governance/evidence" replace /> },
      { path: "/governance-center/evidence-policy", element: <Navigate to="/governance/evidence" replace /> },
      { path: "/governance-center/compliance", element: <Navigate to="/governance/compliance" replace /> },
      { path: "/governance-center/audit-retention", element: <Navigate to="/governance/audit/log" replace /> },
      { path: "/governance-center/residency", element: <Navigate to="/governance/compliance" replace /> },

      { path: "/developer-console", element: <Navigate to="/governance/health" replace /> },
      { path: "/developer-console/health", element: <Navigate to="/governance/health" replace /> },
      { path: "/developer-console/traces", element: <Navigate to="/governance/traces" replace /> },
      { path: "/developer-console/queue-diagnostics", element: <Navigate to="/dev/integration" replace /> },
      { path: "/developer-console/log-diagnostics", element: <Navigate to="/dev/integration" replace /> },

      { path: "/discover", element: <Navigate to="/accounts" replace /> },
      { path: "/discover/accounts", element: <Navigate to="/accounts" replace /> },
      { path: "/discover/jobs", element: <Navigate to="/context/ingestion/jobs" replace /> },
      { path: "/discover/extraction", element: <Navigate to="/context/extraction" replace /> },
      { path: "/discover/knowledge", element: <Navigate to="/context/ontology" replace /> },
      { path: "/discover/knowledge/entities", element: <Navigate to="/context/ontology/entities" replace /> },
      { path: "/discover/knowledge/graph", element: <Navigate to="/context/ontology/graph" replace /> },
      { path: "/discover/knowledge/ontology", element: <Navigate to="/context/ontology" replace /> },
      { path: "/discover/integrations", element: <Navigate to="/context/integrations" replace /> },
      { path: "/discover/sources", element: <Navigate to="/context/sources" replace /> },

      { path: "/library", element: <Navigate to="/context/packs" replace /> },
      { path: "/library/packs", element: <Navigate to="/context/packs" replace /> },
      { path: "/library/models", element: <Navigate to="/context/models" replace /> },

      { path: "/deliver", element: <Navigate to="/deliverables/cases" replace /> },
      { path: "/deliver/cases", element: <Navigate to="/deliverables/cases" replace /> },
      { path: "/deliver/agents", element: <Navigate to="/context/agents" replace /> },
      { path: "/deliver/cases/explore", element: <Navigate to="/deliverables/calculators" replace /> },

      // ═══════════════════════════════════════════════════════════════
      // WORKFLOW
      // ═══════════════════════════════════════════════════════════════
      { path: "/workflow", element: <Navigate to="/workflow/prospect" replace /> },
      { path: "/workflow/prospect", element: <ProtectedRoute><ProspectSetupWithNav /></ProtectedRoute> },
      { path: "/workflow/intelligence", element: <ProtectedRoute><WorkflowIntelligence /></ProtectedRoute> },
      { path: "/workflow/ai-model", element: <ProtectedRoute><AIModel /></ProtectedRoute> },
      { path: "/workflow/driver-tree", element: <ProtectedRoute><WorkflowDriverTree /></ProtectedRoute> },
      { path: "/workflow/evidence", element: <ProtectedRoute><WorkflowEvidence /></ProtectedRoute> },
      { path: "/workflow/calculator", element: <ProtectedRoute><WorkflowCalculator /></ProtectedRoute> },
      { path: "/workflow/value-case", element: <ProtectedRoute><WorkflowValueCase /></ProtectedRoute> },

      // ═══════════════════════════════════════════════════════════════
      // VALUE STUDIO (legacy workspace)
      // ═══════════════════════════════════════════════════════════════
      { path: "/studio", element: <ProtectedRoute><StudioAccountRedirect /></ProtectedRoute> },
      { path: "/studio/:tab", element: <ProtectedRoute><StudioAccountRedirect /></ProtectedRoute> },
      { path: "/studio/:accountId", element: <ProtectedRoute><AccountContextSync /><Navigate to="action-plan" replace /></ProtectedRoute> },
      { path: "/studio/:accountId/action-plan", element: <ProtectedRoute><AccountContextSync /><WorkspacePage path="/studio/:accountId/action-plan"><ActionPlanTab /></WorkspacePage></ProtectedRoute> },
      { path: "/studio/:accountId/value-model", element: <ProtectedRoute><AccountContextSync /><WorkspacePage path="/studio/:accountId/value-model"><ValueModelTab /></WorkspacePage></ProtectedRoute> },
      { path: "/studio/:accountId/narrative", element: <ProtectedRoute><AccountContextSync /><WorkspacePage path="/studio/:accountId/narrative"><NarrativeTab /></WorkspacePage></ProtectedRoute> },
      { path: "/studio/:accountId/enrichment", element: <ProtectedRoute><AccountContextSync /><WorkspacePage path="/studio/:accountId/enrichment"><StudioEnrichmentTab /></WorkspacePage></ProtectedRoute> },
      { path: "/studio/:accountId/competitive", element: <ProtectedRoute><AccountContextSync /><WorkspacePage path="/studio/:accountId/competitive"><StudioCompetitiveTab /></WorkspacePage></ProtectedRoute> },
      { path: "/studio/:accountId/roi", element: <ProtectedRoute><AccountContextSync /><WorkspacePage path="/studio/:accountId/roi"><StudioROITab /></WorkspacePage></ProtectedRoute> },
      { path: "/studio/:accountId/evidence", element: <ProtectedRoute><AccountContextSync /><WorkspacePage path="/studio/:accountId/evidence"><StudioEvidenceTab /></WorkspacePage></ProtectedRoute> },

      // ═══════════════════════════════════════════════════════════════
      // DEVELOPER TOOLS
      // ═══════════════════════════════════════════════════════════════
      { path: "/dev/integration", element: <ProtectedRoute requiredTier="admin"><IntegrationDashboard /></ProtectedRoute> },

      // ═══════════════════════════════════════════════════════════════
      // SETTINGS — Personal (all authenticated users)
      // ═══════════════════════════════════════════════════════════════
      {
        handle: { settingsLayout: true },
        element: (
          <ProtectedRoute>
            <SettingsLayout />
          </ProtectedRoute>
        ),
        children: [
          { path: "/personal", element: <Navigate to="/personal/profile" replace /> },
          { path: "/personal/profile", element: <PersonalProfile />, handle: { title: "Profile", category: "Personal Settings" } },
          { path: "/personal/security", element: <PersonalSecurity />, handle: { title: "Security", category: "Personal Settings" } },
          { path: "/personal/preferences", element: <PersonalPreferences />, handle: { title: "Preferences", category: "Personal Settings" } },
          { path: "/personal/notifications", element: <PersonalNotifications />, handle: { title: "Notifications", category: "Personal Settings" } },
          { path: "/personal/sessions", element: <PersonalSessions />, handle: { title: "Active Sessions", category: "Personal Settings" } },
        ],
      },

      // ═══════════════════════════════════════════════════════════════
      // SETTINGS — Tenant / Workspace / Admin
      // ═══════════════════════════════════════════════════════════════
      {
        handle: { settingsLayout: true },
        element: (
          <ProtectedRoute requiredTier="admin">
            <SettingsLayout />
          </ProtectedRoute>
        ),
        children: [
          { path: "/settings", element: <Navigate to="/settings/workspace" replace /> },

          // Account & Billing
          { path: "/settings/workspace", element: <BillingWorkspace />, handle: { title: "Workspace", category: "Account & Billing" } },
          { path: "/settings/billing", element: <BillingSubscription />, handle: { title: "Subscription", category: "Account & Billing" } },
          { path: "/settings/billing/subscription", element: <BillingSubscription />, handle: { title: "Subscription", category: "Account & Billing" } },
          { path: "/settings/billing/usage", element: <BillingUsage />, handle: { title: "Usage", category: "Account & Billing" } },
          { path: "/settings/billing/payment-methods", element: <BillingPaymentMethods />, handle: { title: "Payment Methods", category: "Account & Billing" } },
          { path: "/settings/billing/invoices", element: <BillingInvoices />, handle: { title: "Invoices", category: "Account & Billing" } },

          // Team & Access
          { path: "/settings/team", element: <TeamMembers />, handle: { title: "Team Members", category: "Team & Access" } },
          { path: "/settings/team/invitations", element: <TeamInvitations />, handle: { title: "Invitations", category: "Team & Access" } },
          { path: "/settings/team/roles", element: <TeamRoles />, handle: { title: "Roles", category: "Team & Access" } },
          { path: "/settings/team/permissions", element: <TeamPermissions />, handle: { title: "Permissions", category: "Team & Access" } },
          { path: "/settings/team/api-keys", element: <TeamApiKeys />, handle: { title: "API Keys", category: "Team & Access" } },

          // Data & Integrations
          { path: "/settings/data/sources", element: <DataSources />, handle: { title: "Data Sources", category: "Data & Integrations" } },
          { path: "/settings/data/integrations", element: <DataIntegrations />, handle: { title: "Integrations", category: "Data & Integrations" } },
          { path: "/settings/data/variables", element: <DataVariables />, handle: { title: "Variables", category: "Data & Integrations" } },
          { path: "/settings/data/value-packs", element: <DataValuePacks />, handle: { title: "Value Packs", category: "Data & Integrations" } },
          { path: "/settings/data/ingestion-rules", element: <DataIngestionRules />, handle: { title: "Ingestion Rules", category: "Data & Integrations" } },

          // Governance
          { path: "/settings/governance", element: <Navigate to="/settings/governance/policies" replace /> },
          { path: "/settings/governance/policies", element: <GovernancePolicies />, handle: { title: "Policies", category: "Governance" } },
          { path: "/settings/governance/compliance", element: <GovernanceCompliance />, handle: { title: "Compliance", category: "Governance" } },
          { path: "/settings/governance/health", element: <GovernanceHealth />, handle: { title: "Health", category: "Governance" } },
          { path: "/settings/governance/audit-trail", element: <GovernanceAuditTrail />, handle: { title: "Audit Trail", category: "Governance" } },
          { path: "/settings/governance/admin-controls", element: <GovernanceAdminControls />, handle: { title: "Admin Controls", category: "Governance" } },

          // Legacy redirects (old wouter settings URLs)
          { path: "/settings/content/*", element: <Navigate to="/settings/governance/policies" replace /> },
          { path: "/settings/access/roles", element: <Navigate to="/settings/team/roles" replace /> },
          { path: "/settings/access/teams", element: <Navigate to="/settings/team" replace /> },
          { path: "/settings/access/keys", element: <Navigate to="/settings/team/api-keys" replace /> },
          { path: "/settings/system/settings", element: <Navigate to="/settings/workspace" replace /> },
          { path: "/settings/system/billing", element: <Navigate to="/settings/billing" replace /> },
          { path: "/settings/system/billing/usage", element: <Navigate to="/settings/billing/usage" replace /> },
          { path: "/settings/system/billing/invoices", element: <Navigate to="/settings/billing/invoices" replace /> },
          { path: "/settings/system/billing/payments", element: <Navigate to="/settings/billing/payment-methods" replace /> },
        ],
      },
    ],
  },
  { path: "*", element: <NotFound /> },
]);
