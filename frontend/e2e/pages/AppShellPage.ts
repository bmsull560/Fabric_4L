import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for App Shell (navigation, header, sidebar)
 *
 * Canonical navigation taxonomy:
 *   Home, Library, Discover, Model, Deliver, Evidence, Govern
 */
export class AppShellPage {
  readonly page: Page;

  // Navigation sidebar
  readonly sidebar: Locator;
  readonly navigation: Locator;

  // Top-level navigation links (single-spine)
  readonly homeLink: Locator;
  readonly libraryLink: Locator;
  readonly discoverLink: Locator;
  readonly modelLink: Locator;
  readonly deliverLink: Locator;
  readonly evidenceLink: Locator;
  readonly governLink: Locator;

  // Sub-navigation links — Library
  readonly valuePacksLink: Locator;

  // Sub-navigation links — Discover
  readonly accountsLink: Locator;
  readonly ingestionJobsLink: Locator;
  readonly extractionEngineLink: Locator;
  readonly knowledgeModelLink: Locator;
  readonly entityBrowserLink: Locator;
  readonly graphExplorerLink: Locator;
  readonly ontologyEditorLink: Locator;

  // Sub-navigation links — Model
  readonly valueStudioLink: Locator;
  readonly explorerLink: Locator;
  readonly formulaBuilderLink: Locator;

  // Sub-navigation links — Deliver
  readonly businessCasesLink: Locator;
  readonly agentDashboardLink: Locator;

  // Sub-navigation links — Evidence
  readonly decisionTracesLink: Locator;

  // Admin / Govern section
  readonly adminSection: Locator;

  // Legacy aliases for backward compatibility
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

    // Top-level spine links
    this.homeLink = page.getByRole('link', { name: /^Home$/i });
    this.libraryLink = page.getByRole('link', { name: /^Library$/i });
    this.discoverLink = page.getByRole('link', { name: /^Discover$/i });
    this.modelLink = page.getByRole('link', { name: /^Model$/i });
    this.deliverLink = page.getByRole('link', { name: /^Deliver$/i });
    this.evidenceLink = page.getByRole('link', { name: /^Evidence$/i });
    this.governLink = page.getByRole('link', { name: /^Govern$/i });

    // Library sub-nav
    this.valuePacksLink = page.getByRole('link', { name: /value packs/i });

    // Discover sub-nav
    this.accountsLink = page.getByRole('link', { name: /^Accounts$/i });
    this.ingestionJobsLink = page.getByRole('link', { name: /ingestion jobs/i });
    this.extractionEngineLink = page.getByRole('link', { name: /extraction engine/i });
    this.knowledgeModelLink = page.getByRole('link', { name: /knowledge model/i });
    this.entityBrowserLink = page.getByRole('link', { name: /entity browser/i });
    this.graphExplorerLink = page.getByRole('link', { name: /graph explorer/i });
    this.ontologyEditorLink = page.getByRole('link', { name: /ontology editor/i });

    // Model sub-nav
    this.valueStudioLink = page.getByRole('link', { name: /value studio/i });
    this.explorerLink = page.getByRole('link', { name: /^Explorer$/i });
    this.formulaBuilderLink = page.getByRole('link', { name: /formula builder/i });

    // Deliver sub-nav
    this.businessCasesLink = page.getByRole('link', { name: /business cases/i });
    this.agentDashboardLink = page.getByRole('link', { name: /agent dashboard/i });

    // Evidence sub-nav
    this.decisionTracesLink = page.getByRole('link', { name: /decision traces/i });

    // Admin / Govern
    this.adminSection = page.getByRole('link', { name: /^Govern$/i });

    // Legacy aliases
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
      case 'library':
      case 'value-packs':
        await this.valuePacksLink.click();
        break;
      case 'discover':
        await this.discoverLink.click();
        break;
      case 'extraction-engine':
        await this.extractionEngineLink.click();
        break;
      case 'graph-explorer':
        await this.graphExplorerLink.click();
        break;
      case 'model':
        await this.modelLink.click();
        break;
      case 'formula-builder':
        await this.formulaBuilderLink.click();
        break;
      case 'deliver':
      case 'business-cases':
        await this.businessCasesLink.click();
        break;
      case 'evidence':
      case 'decision-traces':
        await this.decisionTracesLink.click();
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
    const link = this.page.getByRole('link', { name: new RegExp(linkName, 'i') });
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
   * Uses the canonical single-spine nav: Home/Library/Discover always visible,
   * Model only for advanced+, Govern only for admin.
   */
  async assertNavigationForTier(tier: 'standard' | 'advanced' | 'admin'): Promise<void> {
    // All tiers see Home, Library, Discover, Deliver, Evidence
    await expect(this.homeLink).toBeVisible();
    await expect(this.libraryLink).toBeVisible();
    await expect(this.discoverLink).toBeVisible();
    await expect(this.deliverLink).toBeVisible();
    await expect(this.evidenceLink).toBeVisible();

    // Advanced and above see Model
    if (tier === 'advanced' || tier === 'admin') {
      await expect(this.modelLink).toBeVisible();
    }

    // Admin only sees Govern
    if (tier === 'admin') {
      await expect(this.adminSection).toBeVisible();
    }
  }
}
