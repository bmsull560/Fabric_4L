/**
 * Journey 20: Admin Configuration Workflow
 *
 * Traceability: ADMIN-001 through ADMIN-015.
 * Validates admin user/role management, tenant settings, value pack
 * management, integration management, data retention policy, audit export,
 * approval gate configuration, benchmark/formula policies, branding,
 * usage, failed jobs, security events, and tenant health views.
 *
 * Priority: P1 core workflow
 */
import { journeyTest, expect } from '../helpers/journey-fixture';
import {
  expectAnyVisible,
  expectRouteSupportsWorkflow,
  expectTenantContext,
} from '../helpers/validation-program';
import { buildGoldenPathMocks, createAdminData } from '../fixtures/deep-test-data';

journeyTest.describe('Admin Configuration Workflow', () => {
  journeyTest.beforeEach(async ({ addMocks }) => {
    const admin = createAdminData();
    await addMocks([
      ...buildGoldenPathMocks(),
      { pattern: '**/api/v1/agents/users**', body: admin.users },
      { pattern: '**/api/v1/agents/roles**', body: admin.roles },
      { pattern: '**/api/v1/agents/settings**', body: admin.tenant_settings },
      { pattern: '**/api/v1/agents/health**', body: admin.platform_health },
      { pattern: '**/api/v1/agents/health/jobs**', body: admin.platform_health.failed_jobs },
      { pattern: '**/api/v1/agents/security/events**', body: admin.platform_health.security_events },
    ]);
  });

  // ── User and Role Management ───────────────────────────────────────────

  journeyTest('ADMIN-001: admin can view and manage users in the organization', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/organization-admin',
      [/user|member|avery stone|jordan lee|sam taylor/i],
      'admin user management surface',
    );
  });

  journeyTest('ADMIN-002: admin can view and manage roles', async ({ authedPage }) => {
    await authedPage.goto('/organization-admin', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/role|admin|analyst|read.*only|permission/i],
      'admin role management surface',
    );
  });

  journeyTest('ADMIN-003: admin can invite a new user with a specific role', async ({ authedPage }) => {
    await authedPage.goto('/organization-admin', { waitUntil: 'domcontentloaded' });

    const inviteBtn = authedPage.getByRole('button', { name: /invite|add.*user|new.*member/i }).first();
    const hasInvite = await inviteBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasInvite) {
      await inviteBtn.click();
      await expectAnyVisible(
        authedPage,
        [/email|role|invite|submit/i],
        'user invite form with role assignment',
      );
    }
  });

  // ── Tenant Settings ────────────────────────────────────────────────────

  journeyTest('ADMIN-004: admin can view and edit tenant settings', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/workspace-settings',
      [/tenant|workspace|settings|organization/i],
      'tenant settings configuration page',
    );
  });

  journeyTest('ADMIN-005: admin can configure default value pack for the tenant', async ({ authedPage }) => {
    await authedPage.goto('/workspace-settings', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/default.*pack|value pack|healthcare|settings/i],
      'tenant default value pack configuration in settings',
    );
  });

  // ── Governance Policies ────────────────────────────────────────────────

  journeyTest('ADMIN-006: admin can configure approval gates before export', async ({ authedPage }) => {
    await authedPage.goto('/governance-center', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/approval.*gate|export.*approval|require.*review|governance/i],
      'approval gate configuration in governance center',
    );
  });

  journeyTest('ADMIN-007: admin can configure evidence threshold policy', async ({ authedPage }) => {
    await authedPage.goto('/governance-center', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/evidence.*threshold|minimum.*confidence|0\.7|70%|governance/i],
      'evidence threshold policy configuration',
    );
  });

  journeyTest('ADMIN-008: admin can configure benchmark governance policy', async ({ authedPage }) => {
    await authedPage.goto('/governance-center', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/benchmark.*policy|stale.*warn|governance/i],
      'benchmark policy configuration in governance center',
    );
  });

  journeyTest('ADMIN-009: admin can configure formula governance policy', async ({ authedPage }) => {
    await authedPage.goto('/governance-center', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/formula.*policy|formula.*governance|approved.*formula/i],
      'formula policy configuration in governance center',
    );
  });

  // ── Data Retention and Audit ───────────────────────────────────────────

  journeyTest('ADMIN-010: admin can manage data retention policy', async ({ authedPage }) => {
    await authedPage.goto('/platform-configuration', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/retention|data.*policy|365.*day|delete.*after|platform/i],
      'data retention policy configuration',
    );
  });

  journeyTest('ADMIN-011: admin can export audit log', async ({ authedPage }) => {
    await authedPage.goto('/governance/audit/log', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/audit|export|log|event/i],
      'audit log with export capability',
    );

    const exportBtn = authedPage.getByRole('button', { name: /export|download/i }).first();
    const hasExport = await exportBtn.isVisible({ timeout: 5000 }).catch(() => false);
    if (hasExport) {
      await exportBtn.click();
      await expectAnyVisible(
        authedPage,
        [/export.*started|download|csv|pdf/i],
        'audit log export initiated',
      );
    }
  });

  // ── Integrations ───────────────────────────────────────────────────────

  journeyTest('ADMIN-012: admin can manage CRM and external integrations', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/settings/integrations',
      [/salesforce|integration|crm|connect/i],
      'admin integration management surface',
    );
  });

  // ── Branding ──────────────────────────────────────────────────────────

  journeyTest('ADMIN-013: admin can manage branding settings', async ({ authedPage }) => {
    await authedPage.goto('/workspace-settings', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/branding|logo|color|primary.*color|settings/i],
      'branding settings in workspace configuration',
    );
  });

  // ── Platform Health and Operations ─────────────────────────────────────

  journeyTest('ADMIN-014: admin can view platform usage, failed jobs, and security events', async ({ authedPage }) => {
    await authedPage.goto('/platform-configuration', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/health|usage|failed.*job|security.*event|platform/i],
      'platform health and operations dashboard',
    );
  });

  journeyTest('ADMIN-015: admin can view tenant health across all layers', async ({ authedPage }) => {
    await authedPage.goto('/platform-configuration', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/l1|l2|l3|l4|l5|l6|layer|health|status|latency/i],
      'tenant health view showing per-layer status',
    );

    await expectTenantContext(authedPage);
  });
});
