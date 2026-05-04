/**
 * Collaboration, Notifications, and Tasks Suite
 *
 * Traceability: COLLAB-001, NOTIFY-001, TASK-001, REVIEWER-ASSIGN-001.
 * Collaboration features must be covered as workflows that reviewers, admins,
 * and account teams can actually reach through authenticated navigation.
 */
import { journeyTest } from '../helpers/journey-fixture';
import { expectRouteSupportsWorkflow } from '../helpers/validation-program';

journeyTest.describe('Collaboration, Notifications, and Tasks Suite', () => {
  journeyTest.beforeEach(async ({ addMocks }) => {
    await addMocks([
      {
        pattern: '**/api/v1/agents/users',
        body: [
          { id: 'user-reviewer', name: 'Value Engineering Lead', role: 'Reviewer', status: 'Active' },
          { id: 'user-viewer', name: "Liam O'Brien", role: 'Viewer', status: 'Invited' },
        ],
      },
      {
        pattern: '**/api/v1/notifications**',
        body: [{ id: 'notif-review', type: 'review_requested', status: 'unread' }],
      },
      {
        pattern: '**/api/v1/tasks**',
        body: [{ id: 'task-001', title: 'Review evidence package', status: 'open', assignee: 'Value Engineering Lead' }],
      },
    ]);
  });

  journeyTest('Step 1 [COLLAB-001]: admin can invite teammates and manage reviewer access', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/settings/team',
      [/team members/i, /invite user/i, /manage/i, /viewer/i, /active/i],
      'team member invite, reviewer assignment, and access-management workflow',
    );
  });

  journeyTest('Step 2 [COLLAB-002]: pending invitations expose resend and lifecycle controls', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/settings/team/invitations',
      [/pending invitations/i, /resend/i, /invitation/i, /team/i],
      'invitation resend and pending invite workflow',
    );
  });

  journeyTest('Step 3 [NOTIFY-001]: user can configure review, ingestion, and collaboration notification channels', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/personal/notifications',
      [/notification channels/i, /event subscriptions/i, /email/i, /review/i, /ingestion/i],
      'notification channel and event subscription workflow',
    );
  });

  journeyTest('Step 4 [TASK-001]: reviewer task context is reachable through governance and audit surfaces', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/governance/audit/changes',
      [/change/i, /history/i, /review/i, /task/i, /audit/i],
      'reviewer task lifecycle and audit workflow',
    );
  });

  journeyTest('Step 5 [COMMENTS-001]: evidence review surfaces expose collaboration-ready context', async ({ authedPage }) => {
    await expectRouteSupportsWorkflow(
      authedPage,
      '/governance/evidence',
      [/evidence/i, /truth objects/i, /search claim/i, /status/i, /confidence/i],
      'reviewer-accessible evidence-review context for comment and mention workflow integration',
    );
  });
});
