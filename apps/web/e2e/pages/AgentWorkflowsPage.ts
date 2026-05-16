/**
 * Page Object for AgentWorkflows (/context/agents)
 *
 * Encapsulates the AgentWorkflows page including the Harness Runs tab.
 * The page has four tabs:
 *   - Workflow Dashboard (existing)
 *   - Whitespace Analysis (existing)
 *   - Business Cases (existing)
 *   - Harness Runs (new — this page object targets this tab)
 *
 * Contract: selectors define the expected DOM structure. If they fail,
 * the component has drifted from the contract.
 */
import { Page, Locator } from '@playwright/test';

export class AgentWorkflowsPage {
  readonly page: Page;

  // ── Page-level ───────────────────────────────────────────────────────
  readonly pageTitle: Locator;

  // ── Tab navigation ───────────────────────────────────────────────────
  readonly workflowDashboardTab: Locator;
  readonly harnessRunsTab: Locator;

  // ── Harness Runs list ────────────────────────────────────────────────
  readonly harnessRunsSection: Locator;
  readonly harnessRunRows: Locator;

  // ── Loading / empty / error states ──────────────────────────────────
  readonly loadingIndicator: Locator;
  readonly emptyMessage: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;

    // Page title
    this.pageTitle = page.getByRole('heading', { name: /workflow dashboard/i });

    // Tabs — WfPrimitives Tabs renders triggers as <button role="tab">.
    // Fallback to role="button" covers non-standard implementations.
    this.workflowDashboardTab = page.getByRole('tab', { name: /workflow dashboard/i }).or(
      page.getByRole('button', { name: /workflow dashboard/i }),
    );
    this.harnessRunsTab = page.getByRole('tab', { name: /harness runs/i }).or(
      page.getByRole('button', { name: /harness runs/i }),
    );

    // Harness Runs list container — identified by section heading
    this.harnessRunsSection = page.getByTestId('harness-runs-section').or(
      page.locator('[data-section="harness-runs"]'),
    );

    // Individual run rows — each row is a clickable element in the list
    this.harnessRunRows = page.getByTestId('harness-run-row');

    // States — reuse QueryState patterns from the app
    this.loadingIndicator = page.getByText(/loading/i).or(
      page.locator('[class*="animate-spin"]').first(),
    );
    this.emptyMessage = page.getByText(/no harness runs found/i);
    this.errorMessage = page.getByText(/failed to load|error loading/i);
  }

  // ── Navigation ───────────────────────────────────────────────────────

  async goto(): Promise<void> {
    await this.page.goto('/context/agents', { waitUntil: 'domcontentloaded' });
  }

  // ── Tab interactions ─────────────────────────────────────────────────

  async openHarnessRunsTab(): Promise<void> {
    await this.harnessRunsTab.click();
  }

  // ── Run list interactions ────────────────────────────────────────────

  /**
   * Click the nth run row (0-indexed) to open its detail panel.
   */
  async clickRunRow(index = 0): Promise<void> {
    await this.harnessRunRows.nth(index).click();
  }

  /**
   * Get a run row by its run ID text.
   */
  getRunRowById(runId: string): Locator {
    return this.harnessRunRows.filter({ hasText: runId });
  }

  /**
   * Get the status badge within a specific run row (by index).
   */
  getRunStatusBadge(index = 0): Locator {
    return this.harnessRunRows.nth(index).locator('[class*="badge"], [class*="Badge"]').first();
  }
}
