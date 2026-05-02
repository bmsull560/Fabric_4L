/**
 * AG-UI Protocol Mock Fixtures for Playwright Contract Tests
 *
 * Provides deterministic mock responses that simulate the AG-UI event
 * lifecycle. These mocks intercept the /agent-stream/chat endpoint and
 * return canned responses so tests can verify UI behavior without a
 * live backend.
 *
 * Contract: These mocks define the *expected* backend contract.
 *           If the backend changes its response shape, these mocks
 *           must be updated — and the tests will catch the drift.
 */
import { Page, Route } from '@playwright/test';

// ── AG-UI Event Types (mirroring frontend/client/src/agui/events.ts) ────────

export interface MockAgentResponse {
  content: string;
  metadata?: {
    trace_id?: string;
    workflow_id?: string;
    tenant_id?: string;
    audit_event_id?: string;
  };
}

/**
 * Mock the /agent-stream/chat endpoint with a deterministic response.
 * The frontend's AgentEventClient will synthesize AG-UI events from this.
 */
export async function mockAgentStreamChat(
  page: Page,
  response: MockAgentResponse,
  options?: { delay?: number; status?: number },
): Promise<void> {
  await page.route('**/agent-stream/chat', async (route: Route) => {
    if (options?.delay) {
      await new Promise((resolve) => setTimeout(resolve, options.delay));
    }
    await route.fulfill({
      status: options?.status ?? 200,
      contentType: 'application/json',
      body: JSON.stringify(response),
    });
  });
}

/**
 * Mock the /agent-stream/chat endpoint to return an error.
 */
export async function mockAgentStreamError(
  page: Page,
  statusCode: number = 500,
  message: string = 'Internal server error',
): Promise<void> {
  await page.route('**/agent-stream/chat', async (route: Route) => {
    await route.fulfill({
      status: statusCode,
      contentType: 'application/json',
      body: JSON.stringify({ error: message }),
    });
  });
}

/**
 * Mock the /agent-stream/chat endpoint to hang (simulate timeout).
 */
export async function mockAgentStreamTimeout(page: Page): Promise<void> {
  await page.route('**/agent-stream/chat', async (route: Route) => {
    // Never fulfill — simulates a timeout
    await new Promise(() => {});
  });
}

// ── Canned Responses ────────────────────────────────────────────────────────

export const CANNED_RESPONSES = {
  signals: {
    content:
      'I found 6 pain signals for this account. The highest-confidence signal is "Supply chain visibility gaps" at 87% confidence, sourced from their Q3 earnings call transcript.',
    metadata: {
      trace_id: 'trace-test-001',
      workflow_id: 'wf-signals-001',
      tenant_id: 'tenant-test',
      audit_event_id: 'audit-001',
    },
  } satisfies MockAgentResponse,

  drivers: {
    content:
      'The value driver tree shows 3 primary drivers: Operational Efficiency (weight: 0.4), Revenue Growth (weight: 0.35), and Risk Reduction (weight: 0.25).',
    metadata: {
      trace_id: 'trace-test-002',
      workflow_id: 'wf-drivers-001',
      tenant_id: 'tenant-test',
      audit_event_id: 'audit-002',
    },
  } satisfies MockAgentResponse,

  'value-model': {
    content:
      'Based on the inputs, the projected 3-year ROI is 287%. Conservative estimate: $1.2M, Expected: $2.1M, Optimistic: $3.4M.',
    metadata: {
      trace_id: 'trace-test-003',
      workflow_id: 'wf-model-001',
      tenant_id: 'tenant-test',
      audit_event_id: 'audit-003',
    },
  } satisfies MockAgentResponse,
};

// ── Workflow Mocks ──────────────────────────────────────────────────────────

export interface MockWorkflowStatus {
  workflow_instance_id: string;
  workflow_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  current_state: string | null;
  current_node: string | null;
  progress_percentage: number;
}

/**
 * Mock the workflow status endpoint.
 */
export async function mockWorkflowStatus(
  page: Page,
  workflowId: string,
  status: MockWorkflowStatus,
): Promise<void> {
  await page.route(`**/workflows/${workflowId}`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(status),
    });
  });
}
