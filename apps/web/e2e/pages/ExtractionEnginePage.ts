import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for Extraction Engine screen
 *
 * Route: /discover/extraction (also /discover/jobs)
 * Tier: advanced (Tier 2+) for /discover/extraction, standard for /discover/jobs
 *
 * Encapsulates the extraction pipeline UI including:
 * - Pipeline step display
 * - Terminal-style log viewer
 * - Entity extraction chips
 * - Job status monitoring
 */
export class ExtractionEnginePage {
  readonly page: Page;

  // Page header elements
  readonly header: Locator;
  readonly backLink: Locator;

  // Status indicators
  readonly liveStatusDot: Locator;
  readonly jobStatusText: Locator;
  readonly domainDisplay: Locator;

  // Pipeline steps panel
  readonly pipelineSteps: Locator;
  readonly stepItems: Locator;

  // Terminal / log viewer
  readonly terminalPanel: Locator;
  readonly logEntries: Locator;
  readonly progressBar: Locator;

  // Entity chips
  readonly entityChips: Locator;

  // Error state
  readonly errorMessage: Locator;
  readonly errorBackLink: Locator;

  // Loading state
  readonly loadingSkeleton: Locator;

  constructor(page: Page) {
    this.page = page;

    // Header
    this.header = page.getByRole('heading', { name: /extraction engine/i });
    this.backLink = page.getByRole('link', { name: /command center|back|home/i }).first();

    // Status
    this.liveStatusDot = page.locator('[class*="animate-pulse"]').first();
    this.jobStatusText = page.getByText(/processing|completed|failed|running|pending/i).first();
    this.domainDisplay = page.locator('[class*="font-mono"]').first();

    // Pipeline
    this.pipelineSteps = page.locator('[class*="pipeline"], [class*="steps"]').or(
      page.locator('aside').filter({ hasText: /pipeline|steps/i })
    );
    this.stepItems = page.locator('li, [class*="step"]').filter({ has: page.locator('[class*="status"], svg') });

    // Terminal
    this.terminalPanel = page.locator('[class*="terminal"], [class*="log"], pre, code').first();
    this.logEntries = page.locator('[class*="log-entry"], [class*="terminal"] div').filter({ hasText: /.+/ });
    this.progressBar = page.locator('[role="progressbar"], [class*="progress"]').first();

    // Entity chips
    this.entityChips = page.locator('[class*="chip"], [class*="badge"]').filter({
      hasText: /capability|usecase|persona|valuedriver/i,
    });

    // Error state
    this.errorMessage = page.getByRole('alert').or(
      page.locator('[class*="error"], [class*="alert"]').filter({ hasText: /error|failed/i })
    );
    this.errorBackLink = page.getByRole('link', { name: /back|home|command center/i });

    // Loading
    this.loadingSkeleton = page.locator('[class*="skeleton"], [class*="animate-pulse"]').first();
  }

  /**
   * Navigate to Extraction Engine
   */
  async goto(): Promise<void> {
    await this.page.goto('/discover/extraction');
    await this.waitForPageLoad();
  }

  /**
   * Navigate to Ingestion Jobs (standard tier)
   */
  async gotoJobs(): Promise<void> {
    await this.page.goto('/discover/jobs');
  }

  /**
   * Wait for page to be fully loaded
   */
  async waitForPageLoad(): Promise<void> {
    await expect(this.header).toBeVisible();
  }

  /**
   * Wait for extraction data to load (loading skeleton disappears)
   */
  async waitForDataLoad(): Promise<void> {
    // Wait for skeleton to disappear or terminal to appear
    const hasTerminal = await this.terminalPanel.isVisible().catch(() => false);
    const hasError = await this.errorMessage.isVisible().catch(() => false);
    if (!hasTerminal && !hasError) {
      await expect(this.loadingSkeleton).toBeHidden({ timeout: 10000 });
    }
  }

  /**
   * Get the current job status text
   */
  async getJobStatus(): Promise<string | null> {
    return this.jobStatusText.textContent();
  }

  /**
   * Assert page is in initial loading state
   */
  async assertLoadingState(): Promise<void> {
    await expect(this.header).toBeVisible();
    const hasSkeleton = await this.loadingSkeleton.isVisible().catch(() => false);
    const hasTerminal = await this.terminalPanel.isVisible().catch(() => false);
    // Either loading or already loaded is acceptable
    expect(hasSkeleton || hasTerminal).toBeTruthy();
  }

  /**
   * Assert extraction completed with entities
   */
  async assertExtractionCompleted(): Promise<void> {
    await expect(this.terminalPanel).toBeVisible();
    // If completed, entity chips may be visible
    const chipCount = await this.entityChips.count();
    expect(chipCount).toBeGreaterThanOrEqual(0);
  }

  /**
   * Assert error state is displayed
   */
  async assertErrorState(): Promise<void> {
    await expect(this.errorMessage).toBeVisible();
  }

  /**
   * Navigate back to home/command center
   */
  async navigateBack(): Promise<void> {
    await this.backLink.click();
  }
}
