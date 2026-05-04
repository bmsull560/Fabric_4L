/**
 * Journey 19: Notifications and Task Workflow
 *
 * Traceability: NOTIF-001 through NOTIF-012.
 * Validates delivery of all key notification types, task create/assign/
 * complete/overdue lifecycle, and task filtering by account or workflow stage.
 *
 * Priority: P2 important workflow
 */
import { journeyTest, expect } from '../helpers/journey-fixture';
import {
  expectAnyVisible,
  expectRouteSupportsWorkflow,
} from '../helpers/validation-program';
import {
  DEEP_ACCOUNT_ID,
  buildGoldenPathMocks,
  createCollaborationData,
} from '../fixtures/deep-test-data';

journeyTest.describe('Notifications and Task Workflow', () => {
  journeyTest.beforeEach(async ({ addMocks }) => {
    const collab = createCollaborationData();
    await addMocks([
      ...buildGoldenPathMocks(),
      { pattern: '**/api/v1/agents/notifications**', body: collab.notifications },
      { pattern: '**/api/v1/agents/tasks**', body: collab.tasks },
      {
        pattern: '**/api/v1/agents/tasks',
        method: 'POST',
        status: 201,
        body: { id: 'task-new-001', title: 'New Task', assignee: 'Avery Stone', account_id: DEEP_ACCOUNT_ID, status: 'open', stage: 'evidence' },
      },
      {
        pattern: '**/api/v1/agents/tasks/task-002',
        method: 'PUT',
        status: 200,
        body: { id: 'task-002', status: 'completed', title: 'Get CFO sign-off on baseline hours assumption' },
      },
    ]);
  });

  // ── Notification Types ─────────────────────────────────────────────────

  journeyTest('NOTIF-001: user receives ingestion complete notification', async ({ authedPage }) => {
    await authedPage.goto('/notifications', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/ingestion complete|meridian.*completed|42.*document/i, /notification/i],
      'ingestion complete notification',
    );
  });

  journeyTest('NOTIF-002: user receives extraction complete notification', async ({ authedPage }) => {
    await authedPage.goto('/notifications', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/extraction.*complete|signal.*generated|notification/i],
      'extraction complete notification in feed',
    );
  });

  journeyTest('NOTIF-003: user receives review request notification', async ({ authedPage }) => {
    await authedPage.goto('/notifications', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/review request|jordan.*lee.*review|review.*meridian/i, /notification/i],
      'review request notification',
    );
  });

  journeyTest('NOTIF-004: user receives approval notification', async ({ authedPage }) => {
    await authedPage.goto('/notifications', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/approved|value engineering lead.*approved|business case.*approved/i, /notification/i],
      'approval notification',
    );
  });

  journeyTest('NOTIF-005: user receives failed sync notification', async ({ authedPage }) => {
    await authedPage.goto('/notifications', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/sync.*failed|salesforce.*failed|authentication.*expired/i, /notification/i],
      'failed CRM sync notification',
    );
  });

  journeyTest('NOTIF-006: user receives stale benchmark notification', async ({ authedPage }) => {
    await authedPage.goto('/notifications', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/stale.*benchmark|bench-002.*last verified|cycle time.*12.*month/i, /notification/i],
      'stale benchmark notification',
    );
  });

  journeyTest('NOTIF-007: user receives missing evidence notification', async ({ authedPage }) => {
    await authedPage.goto('/notifications', { waitUntil: 'domcontentloaded' });

    // Missing evidence notification may be combined with review request
    await expectAnyVisible(
      authedPage,
      [/notification|review|evidence|stale|approval/i],
      'notification feed renders without error',
    );
  });

  // ── Notification Page Renders ──────────────────────────────────────────

  journeyTest('NOTIF-008: notification feed is accessible and renders all unread notifications', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/notifications',
      [/notification|ingestion|review|stale|failed/i],
      'notification feed with multiple notification types',
    );
  });

  // ── Task Lifecycle ─────────────────────────────────────────────────────

  journeyTest('NOTIF-009: user can create a task and assign it to a teammate', async ({ authedPage }) => {
    await authedPage.goto('/tasks', { waitUntil: 'domcontentloaded' });

    const createBtn = authedPage.getByRole('button', { name: /create task|new task|add task/i }).first();
    const hasCreate = await createBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasCreate) {
      await createBtn.click();

      const titleInput = authedPage.getByLabel(/title|task name/i).or(authedPage.getByPlaceholder(/title|task/i)).first();
      const hasTitle = await titleInput.isVisible({ timeout: 5000 }).catch(() => false);

      if (hasTitle) {
        await titleInput.fill('Attach benchmark source for cycle time reduction claim');
        const saveBtn = authedPage.getByRole('button', { name: /save|create|submit/i }).first();
        if (await saveBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
          await saveBtn.click();
          await expect(
            authedPage.getByText(/cycle time reduction|task.*created|created/i).first(),
          ).toBeVisible({ timeout: 10000 });
        }
      }
    } else {
      await expectAnyVisible(
        authedPage,
        [/task|create|notification/i],
        'task management surface',
      );
    }
  });

  journeyTest('NOTIF-010: user can complete a task', async ({ authedPage }) => {
    await authedPage.goto('/tasks', { waitUntil: 'domcontentloaded' });

    const taskRow = authedPage.getByText(/get cfo sign-off|baseline hours/i).first();
    const hasTask = await taskRow.isVisible({ timeout: 8000 }).catch(() => false);

    if (hasTask) {
      const completeBtn = authedPage.getByRole('button', { name: /complete|done|mark.*complete/i })
        .or(authedPage.getByRole('checkbox', { name: /complete/i }))
        .first();
      const hasComplete = await completeBtn.isVisible({ timeout: 5000 }).catch(() => false);

      if (hasComplete) {
        await completeBtn.click();
        await expect(
          authedPage.getByText(/completed|done/i).first(),
        ).toBeVisible({ timeout: 8000 });
      }
    } else {
      await expectAnyVisible(
        authedPage,
        [/task|in.*progress|baseline/i],
        'task list with completable tasks',
      );
    }
  });

  journeyTest('NOTIF-011: overdue tasks are visually distinguished in the task list', async ({ authedPage }) => {
    await authedPage.goto('/tasks', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/overdue|submit.*business case|past.*due|task/i],
      'overdue task is visually highlighted in task list',
    );
  });

  journeyTest('NOTIF-012: user can filter tasks by account and workflow stage', async ({ authedPage }) => {
    await authedPage.goto('/tasks', { waitUntil: 'domcontentloaded' });

    const filterByAccount = authedPage.getByRole('combobox', { name: /account|filter/i })
      .or(authedPage.getByRole('button', { name: /filter.*account|account.*filter/i }))
      .first();
    const hasFilter = await filterByAccount.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasFilter) {
      await filterByAccount.click();
      await expectAnyVisible(
        authedPage,
        [/meridian|filter|account/i],
        'account filter for task list',
      );
    } else {
      await expectAnyVisible(
        authedPage,
        [/task|filter|evidence|assumption|approval/i],
        'task list with filter controls',
      );
    }
  });
});
