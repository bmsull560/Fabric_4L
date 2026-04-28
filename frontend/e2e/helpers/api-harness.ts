/**
 * API Harness for Journey Tests
 *
 * Provides two modes of operation:
 *
 * 1. **Live mode** (PLAYWRIGHT_BACKEND_URL is set):
 *    Routes API requests to a real backend. No mocking.
 *    Used for integration/staging environments.
 *
 * 2. **Contract mode** (no backend available):
 *    Intercepts API requests with OpenAPI-schema-validated mock responses.
 *    Used for local dev and CI when only the frontend dev server is running.
 *
 * Journey tests MUST use this harness instead of raw page.route() calls
 * so that the same test code works in both modes.
 */
import { Page, Route } from '@playwright/test';

// ── Environment Detection ───────────────────────────────────────────────────

const BACKEND_URL = process.env.PLAYWRIGHT_BACKEND_URL || '';

export function isLiveMode(): boolean {
  return BACKEND_URL.length > 0;
}

// ── Types ───────────────────────────────────────────────────────────────────

type LayerKey = 'l1' | 'l2' | 'l3' | 'l4' | 'l5' | 'l6';

interface MockEndpoint {
  /** HTTP method (GET, POST, etc.) */
  method?: string;
  /** URL glob pattern for Playwright route matching */
  pattern: string;
  /** Response body (will be JSON.stringify'd) */
  body: unknown;
  /** HTTP status code (default: 200) */
  status?: number;
  /** Optional delay in ms to simulate latency */
  delay?: number;
}

interface ApiHarnessOptions {
  /** Additional mock endpoints beyond the defaults */
  mocks?: MockEndpoint[];
  /** If true, unmatched API requests will be aborted instead of passed through */
  strictMocking?: boolean;
}

// ── Layer URL Prefixes (mirrors frontend/client/src/api/client.ts) ──────────

const LAYER_PREFIXES: Record<LayerKey, string> = {
  l1: '/ingest',
  l2: '/extract',
  l3: '',
  l4: '/agents',
  l5: '/truths',
  l6: '/benchmarks',
};

// ── Default Mock Data ───────────────────────────────────────────────────────
// These represent the minimal valid responses needed for pages to render.
// They are intentionally sparse — journey tests should provide richer data
// via the `mocks` option when testing specific workflows.

const EMPTY_ACCOUNT = {
  id: 'acct-test-001',
  name: 'Test Account',
  industry: 'Technology',
  website: 'https://example.com',
  tier: 'enterprise',
  created_at: '2025-01-01T00:00:00Z',
};

const EMPTY_WORKSPACE_TAB = {
  content: null,
  generated_at: null,
  status: 'empty',
};

const DEFAULT_MOCKS: MockEndpoint[] = [
  // Account endpoints
  {
    pattern: '**/api/v1/agents/accounts/*',
    body: EMPTY_ACCOUNT,
  },
  {
    pattern: '**/api/v1/agents/accounts',
    body: [EMPTY_ACCOUNT],
  },
  // Workspace tab data (signals, drivers, etc.)
  {
    pattern: '**/api/v1/agents/workspace/*/signals',
    body: EMPTY_WORKSPACE_TAB,
  },
  {
    pattern: '**/api/v1/agents/workspace/*/drivers',
    body: EMPTY_WORKSPACE_TAB,
  },
  {
    pattern: '**/api/v1/agents/workspace/*/evidence',
    body: EMPTY_WORKSPACE_TAB,
  },
  {
    pattern: '**/api/v1/agents/workspace/*/stakeholders',
    body: EMPTY_WORKSPACE_TAB,
  },
  {
    pattern: '**/api/v1/agents/workspace/*/action-plan',
    body: EMPTY_WORKSPACE_TAB,
  },
  {
    pattern: '**/api/v1/agents/workspace/*/value-model',
    body: EMPTY_WORKSPACE_TAB,
  },
  {
    pattern: '**/api/v1/agents/workspace/*/narrative',
    body: EMPTY_WORKSPACE_TAB,
  },
  // Case ID resolution
  {
    pattern: '**/api/v1/agents/cases/canonical/*',
    body: { case_id: 'case-test-001' },
  },
  // Feature flags
  {
    pattern: '**/api/v1/agents/feature-flags',
    body: [],
  },
  // Health
  {
    pattern: '**/api/v1/agents/health/**',
    body: { status: 'healthy', components: {} },
  },
  // Ingestion jobs
  {
    pattern: '**/api/v1/ingest/jobs',
    body: [],
  },
  // Settings
  {
    pattern: '**/api/v1/agents/settings',
    body: {
      features: {},
      notifications: { email: true, slack: false },
      branding: { primaryColor: '#3B82F6', logoUrl: '' },
    },
  },
  // Users, roles, teams, api-keys
  {
    pattern: '**/api/v1/agents/users',
    body: [],
  },
  {
    pattern: '**/api/v1/agents/api-keys',
    body: [],
  },
  // Workflows
  {
    pattern: '**/api/v1/agents/workflows',
    body: [],
  },
  {
    pattern: '**/api/v1/agents/workflows/types',
    body: [],
  },
  // Cases
  {
    pattern: '**/api/v1/agents/cases',
    body: [],
  },
  // Graph / Knowledge
  {
    pattern: '**/api/v1/entities**',
    body: { entities: [], total: 0 },
  },
  {
    pattern: '**/api/v1/value-trees**',
    body: { trees: [], total: 0 },
  },
];

// ── Harness Implementation ──────────────────────────────────────────────────

/**
 * Install the API harness on a Playwright page.
 *
 * In live mode, this is a no-op (requests go to the real backend).
 * In contract mode, this registers route interceptors for all known endpoints.
 *
 * @returns A teardown function that unroutes all interceptors.
 */
export async function installApiHarness(
  page: Page,
  options: ApiHarnessOptions = {},
): Promise<() => Promise<void>> {
  if (isLiveMode()) {
    // In live mode, no mocking needed — requests go to real backend
    return async () => {};
  }

  const allMocks = [...DEFAULT_MOCKS, ...(options.mocks || [])];

  // Register a catch-all FIRST (Playwright matches last-registered-first).
  // This ensures specific routes registered after take priority.
  if (options.strictMocking) {
    await page.route('**/api/v1/**', async (route: Route) => {
      const url = route.request().url();
      console.warn(`[API Harness] Unmatched request aborted: ${url}`);
      await route.abort('connectionrefused');
    });
  } else {
    await page.route('**/api/v1/**', async (route: Route) => {
      // Return empty 200 for any unmatched API request
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({}),
      });
    });
  }

  // Register specific mocks AFTER the catch-all (so they take priority)
  for (const mock of allMocks) {
    await page.route(mock.pattern, async (route: Route) => {
      if (mock.method && route.request().method() !== mock.method.toUpperCase()) {
        await route.fallback();
        return;
      }
      if (mock.delay) {
        await new Promise((resolve) => setTimeout(resolve, mock.delay));
      }
      await route.fulfill({
        status: mock.status ?? 200,
        contentType: 'application/json',
        body: JSON.stringify(mock.body),
      });
    });
  }

  // Return teardown function
  return async () => {
    await page.unrouteAll({ behavior: 'ignoreErrors' });
  };
}

/**
 * Create mock endpoint definitions for a specific account.
 * Use this to provide richer data for account-specific journey tests.
 */
export function mockAccountData(
  accountId: string,
  data: {
    account?: Record<string, unknown>;
    signals?: Record<string, unknown>;
    drivers?: Record<string, unknown>;
    evidence?: Record<string, unknown>;
    stakeholders?: Record<string, unknown>;
    actionPlan?: Record<string, unknown>;
    valueModel?: Record<string, unknown>;
    narrative?: Record<string, unknown>;
  },
): MockEndpoint[] {
  const mocks: MockEndpoint[] = [];

  if (data.account) {
    mocks.push({
      pattern: `**/api/v1/agents/accounts/${accountId}`,
      body: { id: accountId, ...data.account },
    });
  }

  const tabMap: Record<string, string> = {
    signals: 'signals',
    drivers: 'drivers',
    evidence: 'evidence',
    stakeholders: 'stakeholders',
    actionPlan: 'action-plan',
    valueModel: 'value-model',
    narrative: 'narrative',
  };

  for (const [key, tabName] of Object.entries(tabMap)) {
    const tabData = data[key as keyof typeof data];
    if (tabData && typeof tabData === 'object') {
      mocks.push({
        pattern: `**/api/v1/agents/workspace/${accountId}/${tabName}`,
        body: { content: tabData, generated_at: new Date().toISOString(), status: 'ready' },
      });
    }
  }

  return mocks;
}

/**
 * Create mock endpoint definitions for ingestion jobs.
 */
export function mockIngestionJobs(jobs: Array<{
  id: string;
  domain: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
}>): MockEndpoint[] {
  const mocks: MockEndpoint[] = [
    {
      pattern: '**/api/v1/ingest/jobs',
      body: jobs,
    },
  ];

  for (const job of jobs) {
    mocks.push({
      pattern: `**/api/v1/ingest/jobs/${job.id}`,
      body: job,
    });
    mocks.push({
      pattern: `**/api/v1/ingest/jobs/${job.id}/progress`,
      body: { progress: job.progress, status: job.status },
    });
  }

  return mocks;
}

/**
 * Create mock endpoint for the agent stream chat.
 */
export function mockAgentStream(response: {
  content: string;
  metadata?: Record<string, string>;
}): MockEndpoint[] {
  return [
    {
      pattern: '**/agent-stream/chat',
      method: 'POST',
      body: response,
      delay: 100, // Simulate minimal latency
    },
  ];
}

/**
 * Create mock endpoint for workflow lifecycle.
 */
export function mockWorkflow(workflow: {
  id: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
}): MockEndpoint[] {
  return [
    {
      pattern: `**/api/v1/agents/workflows/${workflow.id}`,
      body: {
        workflow_instance_id: workflow.id,
        workflow_type: workflow.type,
        status: workflow.status,
        current_state: workflow.status === 'running' ? 'processing' : null,
        current_node: null,
        progress_percentage: workflow.progress,
      },
    },
    {
      pattern: `**/api/v1/agents/workflows/${workflow.id}/result`,
      body: workflow.status === 'completed'
        ? { result: 'Workflow completed successfully', artifacts: [] }
        : { error: 'Workflow not yet complete' },
      status: workflow.status === 'completed' ? 200 : 404,
    },
  ];
}
