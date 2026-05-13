/**
 * CONTRACT TEST: Agent Workflow Lifecycle (AG-UI Protocol)
 *
 * These tests define the behavioral contract for the agent co-pilot
 * powered by the AG-UI event layer. They verify:
 *
 *   1. Run lifecycle: idle → running → finished (or error)
 *   2. Step progression: pending → active → done visualization
 *   3. Message flow: user sends → steps appear → agent responds
 *   4. Error handling: backend failure → error state → retry
 *   5. Streaming UX: input disabled during processing
 *   6. Metadata: trace/workflow IDs surfaced after completion
 *   7. Tab-specific steps: each workspace tab has its own step template
 *
 * TDD Status: FAILING (initial state)
 * These tests define the expected behavior. Implementation must be
 * wired up to make them pass. If all tests pass, there is <1% chance
 * the agent workflow is not functioning as intended.
 *
 * References:
 *   - AG-UI Protocol: https://docs.ag-ui.com/concepts/events
 *   - UI Contracts: Data, Behavior, Rendering
 *   - CONTRACT.md §2.6 (UI State Machine)
 */
import { test, expect, type Page, type Route } from '../fixtures/contract-test';
import { setUserTier, clearUserTier, seedAuthState, clearAuthState } from '../fixtures';
import {
  mockAgentStreamChat,
  mockAgentStreamError,
  CANNED_RESPONSES,
} from '../fixtures/agui-mocks';
import {
  setSelectedAccount,
  clearSelectedAccount,
  TEST_ACCOUNTS,
} from '../fixtures/account-helpers';
import { AgentStreamPage } from '../pages/AgentStreamPage';

// ── Workspace API Mocking ──────────────────────────────────────────────────
// The workspace pages require successful API responses to render the
// IntelligenceShell/ValueStudioShell (which contains the Agent Stream panel).
// Without mocking, pages show "Failed to load..." and never render the RightRail.

const MOCK_CASE_ID = 'case-agent-test-001';
const CASE_STORAGE_KEY = `vf.workspace.case.${TEST_ACCOUNTS.meridian.id}`;

const MOCK_ACCOUNT = {
  id: TEST_ACCOUNTS.meridian.id,
  name: TEST_ACCOUNTS.meridian.name,
  domain: 'meridianautomotive.com',
  industry: 'Manufacturing',
  stage: 'customer',
  provider: 'manual',
  provider_record_id: TEST_ACCOUNTS.meridian.id,
  sync_status: 'synced',
  employees: 5000,
  annual_revenue: 250000000,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-06-01T00:00:00Z',
};

/** Tab-specific mock workspace data with at least one item to prevent auto-generate */
function getMockWorkspaceData(tabKey: string): unknown {
  const mocks: Record<string, unknown> = {
    signals: { signals: [{ id: 's1', name: 'Cost Reduction', category: 'Operational', confidence: 85, impact: 'high', trend: 'up' }] },
    drivers: { drivers: [{ id: 'd1', name: 'Labor Efficiency', parentSignal: 'Cost Reduction', impact: 'high' }] },
    evidence: { evidence: [{ id: 'e1', title: 'Q3 Report', excerpt: 'Cost savings identified', source: 'internal', match_score: 0.9 }] },
    stakeholders: { stakeholders: [{ id: 'st1', name: 'Jane Doe', title: 'VP Operations', influence: 'high', priority: 'champion' }] },
    'value-model': { valueLines: [{ id: 'v1', driver: 'Efficiency', category: 'hard', conservative: 500000, expected: 1000000, optimistic: 1500000 }] },
    narrative: { narratives: [{ id: 'n1', title: 'Value Narrative v1', status: 'draft', sections: [], created_at: '2024-06-01T00:00:00Z' }] },
    'action-plan': { action_plan: { phases: [{ id: 'p1', name: 'Phase 1', tasks: [] }], timeline: '6 months' } },
  };
  return mocks[tabKey] ?? {};
}

/**
 * Mock all workspace APIs so the page renders fully (IntelligenceShell + RightRail).
 * Uses /api/v1/ prefix to avoid intercepting Vite source file requests.
 * Routes registered in priority order (catch-all first = lowest priority).
 */
async function mockWorkspaceApis(page: Page): Promise<void> {
  // Catch-all for unhandled API v1 requests (lowest priority)
  await page.route('**/api/v1/**', async (route: Route) => {
    await route.fulfill({ json: {} });
  });

  // Workspace generate endpoint
  await page.route('**/agents/analysis/cases/*/workspace/generate', async (route: Route) => {
    await route.fulfill({ json: { status: 'complete' } });
  });

  // Workspace tab data
  await page.route('**/agents/analysis/cases/*/workspace/*', async (route: Route) => {
    const url = route.request().url();
    const tabMatch = url.match(/\/workspace\/([^?/]+)/);
    const tabKey = tabMatch?.[1] ?? 'signals';
    await route.fulfill({ json: getMockWorkspaceData(tabKey) });
  });

  // Canonical case ID lookup
  await page.route('**/agents/analysis/cases**', async (route: Route) => {
    const url = route.request().url();
    // Only intercept the lookup (GET with query params), not POST
    if (route.request().method() === 'GET') {
      await route.fulfill({
        json: { items: [{ case_id: MOCK_CASE_ID, id: MOCK_CASE_ID }] },
      });
    } else {
      await route.fulfill({ json: { case_id: MOCK_CASE_ID, id: MOCK_CASE_ID } });
    }
  });

  // Account detail endpoint (highest priority - registered last)
  await page.route(`**/agents/accounts/${TEST_ACCOUNTS.meridian.id}`, async (route: Route) => {
    await route.fulfill({ json: MOCK_ACCOUNT });
  });
}

/**
 * Pre-seed localStorage with the case ID to avoid the case lookup API call.
 */
async function seedCaseId(page: Page): Promise<void> {
  await page.addInitScript(({ key, value }) => {
    window.localStorage.setItem(key, value);
  }, { key: CASE_STORAGE_KEY, value: MOCK_CASE_ID });
}

test.describe('Contract: Agent Workflow Lifecycle', () => {
  let agentPage: AgentStreamPage;

  test.beforeEach(async ({ page }) => {
    // Set up: seed auth, admin tier (full access), selected account, mock backend
    await seedAuthState(page);
    await setUserTier(page, 'admin');
    await setSelectedAccount(page, TEST_ACCOUNTS.meridian);
    await seedCaseId(page);
    await mockWorkspaceApis(page);
    agentPage = new AgentStreamPage(page);
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
    await clearSelectedAccount(page);
    await clearAuthState(page);
  });

  // ── 1. Run Lifecycle ──────────────────────────────────────────────────

  test.describe('Run Lifecycle', () => {
    test('should start in idle state with welcome message', async ({ page }) => {
      await page.goto('/intelligence/acct-meridian-001/signals');
      await page.waitForLoadState('networkidle');
      await agentPage.switchToAgentStream();

      // Contract: welcome message is visible on initial load
      await expect(agentPage.welcomeMessage).toBeVisible();
      // Contract: input is enabled in idle state
      await agentPage.assertInputEnabled();
      // Contract: no process steps visible in idle state
      await expect(agentPage.processStepsContainer).not.toBeVisible();
    });

    test('should transition to running state when user sends a message', async ({ page }) => {
      // Mock a slow response to catch the running state
      await mockAgentStreamChat(page, CANNED_RESPONSES.signals, { delay: 2000 });
      await page.goto('/intelligence/acct-meridian-001/signals');
      await page.waitForLoadState('networkidle');
      await agentPage.switchToAgentStream();

      await agentPage.sendMessage('What pain signals do you see?');

      // Contract: user message appears immediately
      await agentPage.assertUserMessageVisible('What pain signals do you see?');
      // Contract: process steps appear during running state
      await expect(agentPage.processStepsContainer).toBeVisible({ timeout: 5000 });
      // Contract: input is disabled during processing
      await agentPage.assertInputDisabled();
    });

    test('should transition to finished state after agent responds', async ({ page }) => {
      await mockAgentStreamChat(page, CANNED_RESPONSES.signals);
      await page.goto('/intelligence/acct-meridian-001/signals');
      await page.waitForLoadState('networkidle');
      await agentPage.switchToAgentStream();

      await agentPage.sendMessage('Analyze the signals');

      // Contract: agent response appears
      await agentPage.waitForAgentResponse();
      await agentPage.assertAgentResponseContains('6 pain signals');
      // Contract: input re-enabled after completion
      await agentPage.assertInputEnabled();
    });

    test('should transition to error state on backend failure', async ({ page }) => {
      await mockAgentStreamError(page, 500, 'Internal server error');
      await page.goto('/intelligence/acct-meridian-001/signals');
      await page.waitForLoadState('networkidle');
      await agentPage.switchToAgentStream();

      await agentPage.sendMessage('Analyze the signals');

      // Contract: error message appears in chat
      await expect(page.getByText(/couldn't complete|error occurred/i)).toBeVisible({ timeout: 10000 });
      // Contract: input re-enabled after error (retryable)
      await agentPage.assertInputEnabled();
    });
  });

  // ── 2. Step Progression ───────────────────────────────────────────────

  test.describe('Step Progression', () => {
    test('should display 4 steps for the signals tab', async ({ page }) => {
      await mockAgentStreamChat(page, CANNED_RESPONSES.signals, { delay: 1000 });
      await page.goto('/intelligence/acct-meridian-001/signals');
      await page.waitForLoadState('networkidle');
      await agentPage.switchToAgentStream();

      await agentPage.sendMessage('Analyze signals');

      // Contract: signals tab has exactly 4 steps
      await expect(agentPage.processStepsContainer).toBeVisible({ timeout: 5000 });
      await agentPage.assertStepCount(4);
    });

    test('should show step labels matching the signals template', async ({ page }) => {
      await mockAgentStreamChat(page, CANNED_RESPONSES.signals, { delay: 1000 });
      await page.goto('/intelligence/acct-meridian-001/signals');
      await page.waitForLoadState('networkidle');
      await agentPage.switchToAgentStream();

      await agentPage.sendMessage('Analyze signals');

      // Contract: step labels match AgentEventClient.TAB_STEP_TEMPLATES.signals
      await expect(agentPage.processStepsContainer).toBeVisible({ timeout: 5000 });
      await expect(page.getByText('Loading account context')).toBeVisible();
      await expect(page.getByText('Analyzing pain signals')).toBeVisible();
      await expect(page.getByText('Scoring confidence levels')).toBeVisible();
      await expect(page.getByText('Synthesizing findings')).toBeVisible();
    });

    test('should mark all steps as done when processing completes', async ({ page }) => {
      await mockAgentStreamChat(page, CANNED_RESPONSES.signals);
      await page.goto('/intelligence/acct-meridian-001/signals');
      await page.waitForLoadState('networkidle');
      await agentPage.switchToAgentStream();

      await agentPage.sendMessage('Analyze signals');

      // Contract: all steps done, header shows "Processing complete"
      await agentPage.waitForAgentResponse();
      await agentPage.assertAllStepsDone();
    });

    test('should auto-collapse steps after completion', async ({ page }) => {
      await mockAgentStreamChat(page, CANNED_RESPONSES.signals);
      await page.goto('/intelligence/acct-meridian-001/signals');
      await page.waitForLoadState('networkidle');
      await agentPage.switchToAgentStream();

      await agentPage.sendMessage('Analyze signals');
      await agentPage.waitForAgentResponse();

      // Contract: steps auto-collapse after 1.5s
      await page.waitForTimeout(2000);
      // Step rows should not be visible (collapsed), but header still is
      await expect(agentPage.processStepsHeader).toBeVisible();
      await expect(agentPage.stepRows.first()).not.toBeVisible();
    });

    test('should show error state on step failure', async ({ page }) => {
      await mockAgentStreamError(page, 500);
      await page.goto('/intelligence/acct-meridian-001/signals');
      await page.waitForLoadState('networkidle');
      await agentPage.switchToAgentStream();

      await agentPage.sendMessage('Analyze signals');

      // Contract: process steps show "Processing failed"
      await expect(page.getByText(/processing failed/i)).toBeVisible({ timeout: 10000 });
    });
  });

  // ── 3. Message Flow ───────────────────────────────────────────────────

  test.describe('Message Flow', () => {
    test('should maintain conversation history across multiple exchanges', async ({ page }) => {
      await mockAgentStreamChat(page, CANNED_RESPONSES.signals);
      await page.goto('/intelligence/acct-meridian-001/signals');
      await page.waitForLoadState('networkidle');
      await agentPage.switchToAgentStream();

      // First exchange
      await agentPage.sendMessage('First question');
      await agentPage.waitForAgentResponse();

      // Second exchange
      await mockAgentStreamChat(page, {
        content: 'Here is my follow-up response.',
        metadata: { trace_id: 'trace-002' },
      });
      await agentPage.sendMessage('Follow-up question');
      await agentPage.waitForAgentResponse();

      // Contract: both user messages visible
      await agentPage.assertUserMessageVisible('First question');
      await agentPage.assertUserMessageVisible('Follow-up question');
    });

    test('should not send empty messages', async ({ page }) => {
      await page.goto('/intelligence/acct-meridian-001/signals');
      await page.waitForLoadState('networkidle');
      await agentPage.switchToAgentStream();

      // Contract: send button is disabled when input is empty
      await agentPage.chatInput.fill('');
      await expect(agentPage.sendButton).toBeDisabled();
    });

    test('should send message on Enter key', async ({ page }) => {
      await mockAgentStreamChat(page, CANNED_RESPONSES.signals);
      await page.goto('/intelligence/acct-meridian-001/signals');
      await page.waitForLoadState('networkidle');
      await agentPage.switchToAgentStream();

      await agentPage.chatInput.fill('Enter key test');
      await agentPage.chatInput.press('Enter');

      // Contract: message sent via Enter key
      await agentPage.assertUserMessageVisible('Enter key test');
    });
  });

  // ── 4. Tab-Specific Steps ─────────────────────────────────────────────

  test.describe('Tab-Specific Step Templates', () => {
    const tabStepExpectations: Array<{
      tab: string;
      route: string;
      expectedSteps: string[];
    }> = [
      {
        tab: 'signals',
        route: '/intelligence/acct-meridian-001/signals',
        expectedSteps: [
          'Loading account context',
          'Analyzing pain signals',
          'Scoring confidence levels',
          'Synthesizing findings',
        ],
      },
      {
        tab: 'drivers',
        route: '/intelligence/acct-meridian-001/drivers',
        expectedSteps: [
          'Loading account context',
          'Mapping value drivers',
          'Analyzing driver hierarchy',
          'Synthesizing recommendations',
        ],
      },
      {
        tab: 'evidence',
        route: '/intelligence/acct-meridian-001/evidence',
        expectedSteps: [
          'Loading account context',
          'Searching evidence base',
          'Matching claims to evidence',
          'Synthesizing findings',
        ],
      },
      {
        tab: 'stakeholders',
        route: '/intelligence/acct-meridian-001/stakeholders',
        expectedSteps: [
          'Loading account context',
          'Mapping buyer personas',
          'Analyzing influence network',
          'Synthesizing engagement plan',
        ],
      },
      {
        tab: 'value-model',
        route: '/studio/acct-meridian-001/value-model',
        expectedSteps: [
          'Loading account context',
          'Gathering model inputs',
          'Running financial calculations',
          'Synthesizing value model',
        ],
      },
      {
        tab: 'narrative',
        route: '/studio/acct-meridian-001/narrative',
        expectedSteps: [
          'Loading account context',
          'Analyzing target audience',
          'Drafting narrative structure',
          'Finalizing narrative',
        ],
      },
    ];

    for (const { tab, route, expectedSteps } of tabStepExpectations) {
      test(`should show correct steps for ${tab} tab`, async ({ page }) => {
        await mockAgentStreamChat(
          page,
          CANNED_RESPONSES[tab as keyof typeof CANNED_RESPONSES] ?? {
            content: `Response for ${tab}`,
            metadata: { trace_id: `trace-${tab}` },
          },
          { delay: 1000 },
        );
        await page.goto(route);
        await page.waitForLoadState('networkidle');
        await agentPage.switchToAgentStream();

        await agentPage.sendMessage(`Analyze ${tab}`);

        // Contract: step labels match the tab-specific template
        await expect(agentPage.processStepsContainer).toBeVisible({ timeout: 5000 });
        for (const stepLabel of expectedSteps) {
          await expect(page.getByText(stepLabel)).toBeVisible();
        }
      });
    }
  });

  // ── 5. Metadata ───────────────────────────────────────────────────────

  test.describe('Run Metadata', () => {
    test('should display trace ID after run completes', async ({ page }) => {
      await mockAgentStreamChat(page, CANNED_RESPONSES.signals);
      await page.goto('/intelligence/acct-meridian-001/signals');
      await page.waitForLoadState('networkidle');
      await agentPage.switchToAgentStream();

      await agentPage.sendMessage('Analyze signals');
      await agentPage.waitForAgentResponse();

      // Contract: trace ID visible in metadata footer
      await agentPage.assertMetadataVisible('trace-test-001');
    });

    test('should display workflow ID after run completes', async ({ page }) => {
      await mockAgentStreamChat(page, CANNED_RESPONSES.signals);
      await page.goto('/intelligence/acct-meridian-001/signals');
      await page.waitForLoadState('networkidle');
      await agentPage.switchToAgentStream();

      await agentPage.sendMessage('Analyze signals');
      await agentPage.waitForAgentResponse();

      // Contract: workflow ID visible in metadata footer
      await expect(page.getByText('wf-signals-001')).toBeVisible();
    });
  });
});
