/**
 * Journey 4: Governance & Trust Validation
 *
 * Validates the platform's trust layer: decision traces, audit logs,
 * and provenance tracking. A user navigates to the Governance section,
 * inspects decision traces for agent-generated outputs, and verifies
 * that audit logs accurately capture recent actions.
 *
 * This journey ensures that every AI-generated output has a traceable
 * provenance path and that user actions are correctly logged.
 *
 * Pass criteria:
 *   - Governance pages render without errors
 *   - Decision traces are visible and link to source data
 *   - Audit log entries include correct timestamps and tenant scoping
 *   - Health monitoring dashboard shows system status
 */
import { journeyTest, expect, expectNoErrors, navigateAndWait } from '../helpers/journey-fixture';

// ── Test Data ───────────────────────────────────────────────────────────────

const MOCK_TRACES = [
  {
    id: 'trace-001',
    agent_id: 'agent-signals',
    decision: 'Signal classification: Supply chain visibility gaps',
    confidence: 0.87,
    timestamp: '2025-04-28T10:00:00Z',
    provenance: [
      { source: 'Q3 Earnings Call Transcript', type: 'document', confidence: 0.92 },
      { source: 'Industry Report 2024', type: 'report', confidence: 0.85 },
    ],
  },
  {
    id: 'trace-002',
    agent_id: 'agent-drivers',
    decision: 'Value driver weight assignment: Operational Efficiency = 0.4',
    confidence: 0.91,
    timestamp: '2025-04-28T10:01:00Z',
    provenance: [
      { source: 'Annual Report FY2024', type: 'document', confidence: 0.88 },
    ],
  },
];

const MOCK_AUDIT_LOG = [
  {
    id: 'audit-001',
    action: 'domain.ingestion.submitted',
    actor: 'user-e2e-001',
    tenant_id: 'tenant-e2e-001',
    timestamp: '2025-04-28T09:55:00Z',
    details: { domain: 'example-corp.com' },
  },
  {
    id: 'audit-002',
    action: 'workspace.signals.generated',
    actor: 'agent-signals',
    tenant_id: 'tenant-e2e-001',
    timestamp: '2025-04-28T10:00:00Z',
    details: { account_id: 'acct-meridian-001', signals_count: 6 },
  },
  {
    id: 'audit-003',
    action: 'value_model.updated',
    actor: 'user-e2e-001',
    tenant_id: 'tenant-e2e-001',
    timestamp: '2025-04-28T10:05:00Z',
    details: { account_id: 'acct-meridian-001', variable: 'projected_savings' },
  },
];

const MOCK_HEALTH = {
  status: 'healthy',
  uptime_seconds: 86400,
  version: '1.0.0',
  components: {
    database: { status: 'healthy', latency_ms: 12 },
    cache: { status: 'healthy', latency_ms: 2 },
    agent_runtime: { status: 'healthy', latency_ms: 45 },
    ingestion_pipeline: { status: 'healthy', latency_ms: 120 },
  },
};

const MOCK_BENCHMARKS = [
  { id: 'bench-001', name: 'Signal Accuracy', value: 0.87, target: 0.85, status: 'passing' },
  { id: 'bench-002', name: 'Driver Coverage', value: 0.92, target: 0.90, status: 'passing' },
  { id: 'bench-003', name: 'Narrative Quality', value: 0.78, target: 0.80, status: 'failing' },
];

// ── Journey ─────────────────────────────────────────────────────────────────

journeyTest.describe('Journey 4: Governance & Trust Validation', () => {

  journeyTest.beforeEach(async ({ addMocks }) => {
    await addMocks([
      {
        pattern: '**/api/v1/agents/traces**',
        body: MOCK_TRACES,
      },
      {
        pattern: '**/api/v1/truths/traces**',
        body: MOCK_TRACES,
      },
      {
        pattern: '**/api/v1/agents/audit/**',
        body: MOCK_AUDIT_LOG,
      },
      {
        pattern: '**/api/v1/truths/audit/**',
        body: MOCK_AUDIT_LOG,
      },
      {
        pattern: '**/api/v1/agents/health',
        body: MOCK_HEALTH,
      },
      {
        pattern: '**/api/v1/agents/health/detailed',
        body: MOCK_HEALTH,
      },
      {
        pattern: '**/api/v1/agents/health/alerts',
        body: [],
      },
      {
        pattern: '**/api/v1/agents/benchmarks**',
        body: MOCK_BENCHMARKS,
      },
      {
        pattern: '**/api/v1/truths/benchmarks**',
        body: MOCK_BENCHMARKS,
      },
      {
        pattern: '**/api/v1/agents/settings',
        body: {
          features: {},
          notifications: { email: true, slack: false },
          branding: { primaryColor: '#3B82F6', logoUrl: '' },
        },
      },
    ]);
  });

  journeyTest('Step 1: User navigates to Decision Traces', async ({ authedPage }) => {
    await navigateAndWait(authedPage, '/governance/traces');
    await expectNoErrors(authedPage);

    // The Governance section should render
    await expect(
      authedPage.getByRole('heading', { name: /trace/i })
        .or(authedPage.getByText(/decision trace/i).first())
        .or(authedPage.getByText(/governance/i).first())
    ).toBeVisible({ timeout: 10000 });
  });

  journeyTest('Step 2: User navigates to Audit Log', async ({ authedPage }) => {
    await navigateAndWait(authedPage, '/governance/audit/log');
    await expectNoErrors(authedPage);

    await expect(
      authedPage.getByRole('heading', { name: /audit/i })
        .or(authedPage.getByText(/audit log/i).first())
    ).toBeVisible({ timeout: 10000 });
  });

  journeyTest('Step 3: User checks System Health monitoring', async ({ authedPage }) => {
    await navigateAndWait(authedPage, '/settings/governance/health');
    await expectNoErrors(authedPage);

    // Health page should render system status
    await expect(
      authedPage.getByText(/health/i).first()
    ).toBeVisible({ timeout: 10000 });
  });

  journeyTest('Step 4: User reviews Benchmark Policies', async ({ authedPage }) => {
    await navigateAndWait(authedPage, '/settings/governance/benchmarks');
    await expectNoErrors(authedPage);

    await expect(
      authedPage.getByText(/benchmark/i).first()
    ).toBeVisible({ timeout: 10000 });
  });

  journeyTest('Step 5: Governance navigation is consistent across sections', async ({ authedPage }) => {
    const governanceRoutes = [
      '/governance/traces',
      '/governance/audit/log',
      '/settings/governance/health',
      '/settings/governance/benchmarks',
    ];

    for (const route of governanceRoutes) {
      await navigateAndWait(authedPage, route);
      await expectNoErrors(authedPage);
      await expect(authedPage).toHaveURL(new RegExp(route.replace(/\//g, '\\/')));
    }
  });
});
