/**
 * Page Object for Agent Stream / Right Rail
 *
 * Encapsulates the AG-UI event-driven agent co-pilot panel.
 * Used in contract tests to verify:
 *   - Process step visualization (pending → active → done)
 *   - Message rendering (user + agent)
 *   - Streaming state indicators
 *   - Suggested actions
 *   - Run metadata display
 *
 * Contract: This page object defines the *expected* DOM structure
 *           of the Right Rail. If selectors fail, the component
 *           has drifted from the contract.
 */
import { Page, Locator, expect } from '@playwright/test';

export class AgentStreamPage {
  readonly page: Page;

  // ── Mode Toggle ─────────────────────────────────────────────────────
  readonly detailsButton: Locator;
  readonly agentStreamButton: Locator;

  // ── Messages ────────────────────────────────────────────────────────
  readonly messageList: Locator;
  readonly userMessages: Locator;
  readonly agentMessages: Locator;
  readonly welcomeMessage: Locator;

  // ── Input ───────────────────────────────────────────────────────────
  readonly chatInput: Locator;
  readonly sendButton: Locator;

  // ── Process Steps ───────────────────────────────────────────────────
  readonly processStepsContainer: Locator;
  readonly processStepsHeader: Locator;
  readonly stepRows: Locator;
  readonly doneStepIcons: Locator;
  readonly activeStepIcons: Locator;
  readonly pendingStepIcons: Locator;

  // ── Streaming State ─────────────────────────────────────────────────
  readonly streamingIndicator: Locator;

  // ── Suggested Actions ───────────────────────────────────────────────
  readonly suggestedActions: Locator;

  // ── Metadata ────────────────────────────────────────────────────────
  readonly metadataFooter: Locator;

  constructor(page: Page) {
    this.page = page;

    // Mode toggle
    this.detailsButton = page.getByRole('button', { name: /details/i });
    this.agentStreamButton = page.getByRole('button', { name: /agent stream/i });

    // Messages
    this.messageList = page.locator('[class*="overflow-y-auto"]').last();
    this.userMessages = page.locator('text=You').locator('..');
    this.agentMessages = page.locator('text=ValuePilot').locator('..');
    this.welcomeMessage = page.getByText(/I'm ready to help you with/i);

    // Input
    this.chatInput = page.getByPlaceholder(/ask a follow-up/i);
    this.sendButton = this.chatInput.locator('..').locator('button');

    // Process Steps
    this.processStepsContainer = page.locator('[class*="bg-muted/60"][class*="rounded-lg"]');
    this.processStepsHeader = this.processStepsContainer.locator('button').first();
    this.stepRows = this.processStepsContainer.locator('[class*="flex items-center gap-2 py-1"]');
    this.doneStepIcons = this.stepRows.locator('.text-emerald-500');
    this.activeStepIcons = this.stepRows.locator('.animate-spin');
    this.pendingStepIcons = this.stepRows.locator('.text-muted-foreground\\/40');

    // Streaming
    this.streamingIndicator = page.getByText(/thinking/i);

    // Suggested actions
    this.suggestedActions = page.locator('button').filter({ hasText: /generate|explore|analyze|build|draft/i });

    // Metadata
    this.metadataFooter = page.locator('text=Trace:').locator('..');
  }

  /**
   * Switch to Agent Stream mode
   */
  async switchToAgentStream(): Promise<void> {
    await this.agentStreamButton.click();
  }

  /**
   * Send a message to the agent
   */
  async sendMessage(text: string): Promise<void> {
    await this.chatInput.fill(text);
    await this.sendButton.click();
  }

  /**
   * Wait for the agent to respond (process steps appear then complete)
   */
  async waitForAgentResponse(timeout: number = 15000): Promise<void> {
    // Wait for process steps to appear
    await this.processStepsContainer.waitFor({ state: 'visible', timeout });
    // Wait for "Processing complete" text
    await this.page.getByText(/processing complete/i).waitFor({ state: 'visible', timeout });
  }

  /**
   * Assert the process steps show the expected count
   */
  async assertStepCount(expected: number): Promise<void> {
    await expect(this.processStepsHeader).toContainText(`${expected} steps`);
  }

  /**
   * Assert all steps are done
   */
  async assertAllStepsDone(): Promise<void> {
    await expect(this.processStepsHeader).toContainText('Processing complete');
  }

  /**
   * Assert the chat input is disabled (during streaming)
   */
  async assertInputDisabled(): Promise<void> {
    await expect(this.chatInput).toBeDisabled();
  }

  /**
   * Assert the chat input is enabled (after streaming)
   */
  async assertInputEnabled(): Promise<void> {
    await expect(this.chatInput).toBeEnabled();
  }

  /**
   * Assert a user message is visible
   */
  async assertUserMessageVisible(text: string): Promise<void> {
    await expect(this.page.getByText(text)).toBeVisible();
  }

  /**
   * Assert an agent response contains text
   */
  async assertAgentResponseContains(text: string): Promise<void> {
    await expect(this.page.getByText(text)).toBeVisible();
  }

  /**
   * Assert metadata footer shows trace info
   */
  async assertMetadataVisible(traceId: string): Promise<void> {
    await expect(this.metadataFooter).toContainText(traceId);
  }

  /**
   * Get the number of visible messages
   */
  async getMessageCount(): Promise<number> {
    const agents = await this.page.locator('text=ValuePilot').count();
    const users = await this.page.locator('text=You').count();
    return agents + users;
  }
}
