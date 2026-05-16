/**
 * Page Object for HarnessRunDetail panel
 *
 * Encapsulates the right-rail drawer that opens when a harness run is selected.
 * Follows the same pattern as WorkflowDetail (Sheet/drawer component).
 *
 * Covers:
 *   - Run metadata display (ID, trace ID, type, status, state)
 *   - Checkpoint timeline (chronological list)
 *   - Human gate approve/reject actions
 *   - Terminal gate read-only display
 *
 * Contract: selectors define the expected DOM structure. If they fail,
 * the component has drifted from the contract.
 */
import { Page, Locator, expect } from '@playwright/test';

export class HarnessRunDetailPage {
  readonly page: Page;

  // ── Panel container ──────────────────────────────────────────────────
  readonly panel: Locator;
  readonly closeButton: Locator;

  // ── Run metadata ─────────────────────────────────────────────────────
  readonly runIdDisplay: Locator;
  readonly traceIdDisplay: Locator;
  readonly workflowTypeDisplay: Locator;
  readonly statusDisplay: Locator;
  readonly currentStateDisplay: Locator;

  // ── Checkpoint timeline ──────────────────────────────────────────────
  readonly checkpointTimeline: Locator;
  readonly checkpointItems: Locator;

  // ── Human gate section ───────────────────────────────────────────────
  readonly gateSection: Locator;
  readonly approveButton: Locator;
  readonly rejectButton: Locator;
  readonly gateStatusDisplay: Locator;

  // ── Loading / error states ───────────────────────────────────────────
  readonly loadingIndicator: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;

    // Panel — Sheet component, identified by role or test id
    this.panel = page.getByTestId('harness-run-detail').or(
      page.locator('[data-panel="harness-run-detail"]'),
    );

    this.closeButton = this.panel.getByRole('button', { name: /close/i });

    // Run metadata — each field identified by label proximity or test id
    this.runIdDisplay = page.getByTestId('harness-run-id').or(
      page.locator('[data-field="run-id"]'),
    );
    this.traceIdDisplay = page.getByTestId('harness-trace-id').or(
      page.locator('[data-field="trace-id"]'),
    );
    this.workflowTypeDisplay = page.getByTestId('harness-workflow-type').or(
      page.locator('[data-field="workflow-type"]'),
    );
    this.statusDisplay = page.getByTestId('harness-status').or(
      page.locator('[data-field="harness-status"]'),
    );
    this.currentStateDisplay = page.getByTestId('harness-current-state').or(
      page.locator('[data-field="current-state"]'),
    );

    // Checkpoint timeline
    this.checkpointTimeline = page.getByTestId('checkpoint-timeline').or(
      page.locator('[data-section="checkpoints"]'),
    );
    this.checkpointItems = page.getByTestId('checkpoint-item');

    // Human gate
    this.gateSection = page.getByTestId('human-gate-section').or(
      page.locator('[data-section="human-gate"]'),
    );
    this.approveButton = page.getByRole('button', { name: /approve/i });
    this.rejectButton = page.getByRole('button', { name: /reject/i });
    this.gateStatusDisplay = page.getByTestId('gate-status').or(
      page.locator('[data-field="gate-status"]'),
    );

    // States
    this.loadingIndicator = page.locator('[class*="animate-spin"]').last();
    this.errorMessage = page.getByText(/failed to load|error loading/i);
  }

  // ── Assertions ───────────────────────────────────────────────────────

  /**
   * Assert the panel is open and visible.
   */
  async assertOpen(): Promise<void> {
    await expect(this.panel).toBeVisible({ timeout: 5000 });
  }

  /**
   * Assert the panel is closed / not visible.
   */
  async assertClosed(): Promise<void> {
    await expect(this.panel).not.toBeVisible();
  }

  /**
   * Assert the run ID is displayed within the detail panel.
   */
  async assertRunIdVisible(runId: string): Promise<void> {
    await expect(this.panel.getByText(runId)).toBeVisible({ timeout: 5000 });
  }

  /**
   * Assert the trace ID is displayed within the detail panel.
   */
  async assertTraceIdVisible(traceId: string): Promise<void> {
    await expect(this.panel.getByText(traceId)).toBeVisible({ timeout: 5000 });
  }

  /**
   * Assert a checkpoint state name is visible within the detail panel.
   */
  async assertCheckpointVisible(stateName: string): Promise<void> {
    await expect(this.panel.getByText(stateName)).toBeVisible({ timeout: 5000 });
  }

  /**
   * Assert approve and reject buttons are visible (pending gate).
   */
  async assertGateActionsVisible(): Promise<void> {
    await expect(this.approveButton).toBeVisible({ timeout: 5000 });
    await expect(this.rejectButton).toBeVisible({ timeout: 5000 });
  }

  /**
   * Assert approve and reject buttons are NOT visible (terminal gate).
   */
  async assertGateActionsHidden(): Promise<void> {
    await expect(this.approveButton).not.toBeVisible();
    await expect(this.rejectButton).not.toBeVisible();
  }

  /**
   * Assert approve button is disabled (mutation pending).
   */
  async assertApproveDisabled(): Promise<void> {
    await expect(this.approveButton).toBeDisabled();
  }

  /**
   * Assert reject button is disabled (mutation pending).
   */
  async assertRejectDisabled(): Promise<void> {
    await expect(this.rejectButton).toBeDisabled();
  }

  /**
   * Click the approve button.
   */
  async clickApprove(): Promise<void> {
    await this.approveButton.click();
  }

  /**
   * Click the reject button.
   */
  async clickReject(): Promise<void> {
    await this.rejectButton.click();
  }
}
