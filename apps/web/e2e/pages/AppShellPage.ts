import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for App Shell (navigation, header, sidebar)
 *
 * New 7-step methodology-driven navigation:
 *   Home, Accounts, Prospect Setup, Intelligence, Value Hypothesis,
 *   Driver Tree, Evidence, Calculator, Value Case
 *
 * Lower section: Setup, Settings, Operations, Support, Feedback
 */
export class AppShellPage {
  readonly page: Page;

  // Navigation sidebar
  readonly sidebar: Locator;
  readonly navigation: Locator;

  // Top-level workflow links (new 7-step spine)
  readonly homeLink: Locator;
  readonly accountsLink: Locator;
  readonly prospectSetupLink: Locator;
  readonly intelligenceLink: Locator;
  readonly valueHypothesisLink: Locator;
  readonly driverTreeLink: Locator;
  readonly evidenceLink: Locator;
  readonly calculatorLink: Locator;
  readonly valueCaseLink: Locator;

  // Legacy aliases (kept for backward-compat tests)
  readonly libraryLink: Locator;
  readonly discoverLink: Locator;
  readonly modelLink: Locator;
  readonly deliverLink: Locator;
  readonly governLink: Locator;
  readonly adminSection: Locator;

  // Legacy sub-nav aliases
  readonly valuePacksLink: Locator;
  readonly ingestionJobsLink: Locator;
  readonly extractionEngineLink: Locator;
  readonly knowledgeModelLink: Locator;
  readonly entityBrowserLink: Locator;
  readonly graphExplorerLink: Locator;
  readonly ontologyEditorLink: Locator;
  readonly valueStudioLink: Locator;
  readonly explorerLink: Locator;
  readonly formulaBuilderLink: Locator;
  readonly businessCasesLink: Locator;
  readonly agentDashboardLink: Locator;
  readonly decisionTracesLink: Locator;
  readonly commandCenterLink: Locator;
  readonly valueTreesLink: Locator;

  // Header controls
  readonly modePill: Locator;
  readonly notificationButton: Locator;
  readonly userButton: Locator;

  // Tier switcher
  readonly tierSwitcherButton: Locator;
  readonly advancedModeToggle: Locator;

  // Mobile menu (hamburger)
  readonly mobileMenuButton: Locator;

  constructor(page: Page) {
    this.page = page;

    // App shell containers
    this.sidebar = page.locator('aside').first();
    this.navigation = page.locator('aside').first();

    // New 7-step workflow links
    this.homeLink = page.getByRole('link', { name: /^Home$/i });
    this.accountsLink = page.getByRole('link', { name: /^Accounts$/i });
    this.prospectSetupLink = page.getByRole('link', { name: /prospect setup/i });
    this.intelligenceLink = page.getByRole('link', { name: /^Intelligence$/i });
    this.valueHypothesisLink = page.getByRole('link', { name: /value hypothesis/i });
    this.driverTreeLink = page.getByRole('link', { name: /driver tree/i });
    this.evidenceLink = page.getByRole('link', { name: /^Evidence$/i });
    this.calculatorLink = page.getByRole('link', { name: /^Calculator$/i });
    this.valueCaseLink = page.getByRole('link', { name: /value case/i });

    // Legacy aliases - point at nearest equivalent
    this.libraryLink = this.homeLink;
    this.discoverLink = this.intelligenceLink;
    this.modelLink = this.valueHypothesisLink;
    this.deliverLink = this.valueCaseLink;
    this.governLink = page.getByRole('link', { name: /^Govern$/i });
    this.adminSection = page.getByRole('link', { name: /^Govern$/i });

    // Legacy sub-nav (may not exist in new nav)
    this.valuePacksLink = page.getByRole('link', { name: /value packs/i });
    this.ingestionJobsLink = page.getByRole('link', { name: /ingestion/i });
    this.extractionEngineLink = page.getByRole('link', { name: /extraction/i });
    this.knowledgeModelLink = page.getByRole('link', { name: /knowledge model/i });
    this.entityBrowserLink = page.getByRole('link', { name: /entity browser/i });
    this.graphExplorerLink = page.getByRole('link', { name: /graph explorer/i });
    this.ontologyEditorLink = page.getByRole('link', { name: /ontology editor/i });
    this.valueStudioLink = page.getByRole('link', { name: /value studio/i });
    this.explorerLink = page.getByRole('link', { name: /^Explorer$/i });
    this.formulaBuilderLink = page.getByRole('link', { name: /formula builder/i });
    this.businessCasesLink = page.getByRole('link', { name: /business cases/i });
    this.agentDashboardLink = page.getByRole('link', { name: /agent dashboard/i });
    this.decisionTracesLink = page.getByRole('link', { name: /decision traces/i });
    this.commandCenterLink = this.homeLink;
    this.valueTreesLink = this.explorerLink;

    // Header controls
    this.modePill = page.locator('header').locator('span').filter({ hasText: /mode$/i }).first();
    this.notificationButton = page.locator('header button').filter({ has: page.locator('svg') }).first();
    this.userButton = page.locator('header button').last();

    // Tier switcher (at bottom of sidebar)
    this.tierSwitcherButton = page.locator('aside button').filter({ hasText: /Mode$/i }).first();
    this.advancedModeToggle = page.locator('aside').getByText(/advanced mode/i).locator('..');

    // Mobile
    this.mobileMenuButton = page.getByRole('button', { name: /menu|navigation/i }).or(
      page.locator('[aria-label*="menu"]').first()
    );
  }

  /**
   * Navigate to a specific route via sidebar
   */
  async navigateTo(route: string): Promise<void> {
    switch (route.toLowerCase()) {
      case 'home':
        await this.homeLink.click();
        break;
      case 'accounts':
        await this.accountsLink.click();
        break;
      case 'prospect-setup':
        await this.prospectSetupLink.click();
        break;
      case 'intelligence':
        await this.intelligenceLink.click();
        break;
      case 'value-hypothesis':
        await this.valueHypothesisLink.click();
        break;
      case 'driver-tree':
        await this.driverTreeLink.click();
        break;
      case 'evidence':
        await this.evidenceLink.click();
        break;
      case 'calculator':
        await this.calculatorLink.click();
        break;
      case 'value-case':
        await this.valueCaseLink.click();
        break;
      // Legacy aliases
      case 'library':
      case 'value-packs':
        await this.homeLink.click();
        break;
      case 'discover':
        await this.intelligenceLink.click();
        break;
      case 'model':
      case 'formula-builder':
        await this.valueHypothesisLink.click();
        break;
      case 'deliver':
      case 'business-cases':
        await this.valueCaseLink.click();
        break;
      case 'govern':
        await this.governLink.click();
        break;
      default:
        throw new Error(`Unknown route: ${route}`);
    }
  }

  /**
   * Check if a navigation link is visible (indicating tier access)
   */
  async isNavigationLinkVisible(linkName: string): Promise<boolean> {
    const escaped = linkName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const link = this.page.getByRole('link', { name: new RegExp(escaped, 'i') });
    return link.isVisible();
  }

  /**
   * Get all visible navigation items
   */
  async getVisibleNavigationItems(): Promise<string[]> {
    const links = this.sidebar.getByRole('link');
    const texts: string[] = [];
    const count = await links.count();
    for (let i = 0; i < count; i++) {
      const text = await links.nth(i).textContent();
      if (text) texts.push(text.trim());
    }
    return texts;
  }

  /**
   * Open mobile navigation menu
   */
  async openMobileMenu(): Promise<void> {
    await this.mobileMenuButton.click();
  }

  /**
   * Assert navigation sidebar is visible
   */
  async assertSidebarVisible(): Promise<void> {
    await expect(this.sidebar).toBeVisible();
  }

  /**
   * Assert specific navigation links are visible based on tier.
   * New structure: All 7 workflow steps are visible to standard+.
   */
  async assertNavigationForTier(tier: 'standard' | 'advanced' | 'admin'): Promise<void> {
    // All tiers see the 7-step workflow
    await expect(this.homeLink).toBeVisible();
    await expect(this.accountsLink).toBeVisible();
    await expect(this.intelligenceLink).toBeVisible();
    await expect(this.evidenceLink).toBeVisible();
    await expect(this.calculatorLink).toBeVisible();
    await expect(this.valueCaseLink).toBeVisible();
  }
}
