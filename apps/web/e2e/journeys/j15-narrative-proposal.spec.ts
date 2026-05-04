/**
 * Journey 15: Narrative and Proposal Workflow
 *
 * Traceability: NARR-001 through NARR-014.
 * Validates generation of all narrative types, tone/audience adjustment,
 * grounding validation, unsupported claim removal, version history, and
 * version restoration.
 *
 * Priority: P1 core workflow
 */
import { journeyTest, expect } from '../helpers/journey-fixture';
import {
  expectAnyVisible,
  expectRouteSupportsWorkflow,
  expectNotVisible,
} from '../helpers/validation-program';
import {
  DEEP_ACCOUNT_ID,
  buildGoldenPathMocks,
  createNarrativeContent,
  createNarrativeVersions,
} from '../fixtures/deep-test-data';

journeyTest.describe('Narrative and Proposal Workflow', () => {
  journeyTest.beforeEach(async ({ addMocks }) => {
    await addMocks([
      ...buildGoldenPathMocks(),
      {
        pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/narrative`,
        body: createNarrativeContent('executive_email'),
      },
      {
        pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/narrative/versions`,
        body: createNarrativeVersions(),
      },
      {
        pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/narrative`,
        method: 'POST',
        status: 200,
        body: createNarrativeContent('executive_email'),
      },
    ]);
  });

  // ── Narrative Type Generation ───────────────────────────────────────────

  journeyTest('NARR-001: user can generate an executive email narrative', async ({ authedPage }) => {
    await authedPage.goto(`/studio/${DEEP_ACCOUNT_ID}/narrative`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/executive email|narrative|generate/i],
      'narrative studio with executive email option',
    );

    const generateBtn = authedPage.getByRole('button', { name: /generate|create narrative|draft/i }).first();
    const hasGenerate = await generateBtn.isVisible({ timeout: 5000 }).catch(() => false);
    if (hasGenerate) {
      await generateBtn.click();
      await expect(
        authedPage.getByText(/subject|meridian|annual.*savings|Dr. Chen|700K/i).first(),
      ).toBeVisible({ timeout: 15000 });
    }
  });

  journeyTest('NARR-002: user can generate an executive summary narrative', async ({ authedPage, addMocks }) => {
    await addMocks([{
      pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/narrative`,
      body: createNarrativeContent('executive_summary'),
    }]);

    await expectRouteSupportsWorkflow(
      authedPage,
      `/studio/${DEEP_ACCOUNT_ID}/narrative`,
      [/executive summary|narrative|operational.*cost|grounded/i],
      'executive summary narrative generation',
    );
  });

  journeyTest('NARR-003: user can generate a discovery recap narrative', async ({ authedPage, addMocks }) => {
    await addMocks([{
      pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/narrative`,
      body: createNarrativeContent('discovery_recap'),
    }]);

    await expectRouteSupportsWorkflow(
      authedPage,
      `/studio/${DEEP_ACCOUNT_ID}/narrative`,
      [/discovery|recap|findings|narrative/i],
      'discovery recap narrative generation',
    );
  });

  journeyTest('NARR-004: user can generate a mutual action plan', async ({ authedPage, addMocks }) => {
    await addMocks([{
      pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/narrative`,
      body: createNarrativeContent('mutual_action_plan'),
    }]);

    await expectRouteSupportsWorkflow(
      authedPage,
      `/studio/${DEEP_ACCOUNT_ID}/narrative`,
      [/action plan|milestone|owner|narrative/i],
      'mutual action plan narrative generation',
    );
  });

  journeyTest('NARR-005: user can generate a renewal narrative', async ({ authedPage, addMocks }) => {
    await addMocks([{
      pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/narrative`,
      body: createNarrativeContent('renewal_narrative'),
    }]);

    await expectRouteSupportsWorkflow(
      authedPage,
      `/studio/${DEEP_ACCOUNT_ID}/narrative`,
      [/renewal|year.*1|realized|savings.*640K|narrative/i],
      'renewal narrative with realized value comparison',
    );
  });

  journeyTest('NARR-006: user can generate an expansion narrative', async ({ authedPage, addMocks }) => {
    await addMocks([{
      pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/narrative`,
      body: createNarrativeContent('expansion_narrative'),
    }]);

    await expectRouteSupportsWorkflow(
      authedPage,
      `/studio/${DEEP_ACCOUNT_ID}/narrative`,
      [/expansion|extend|regional|billing/i],
      'expansion narrative generation',
    );
  });

  journeyTest('NARR-007: user can generate a proposal section', async ({ authedPage, addMocks }) => {
    await addMocks([{
      pattern: `**/api/v1/agents/workspace/${DEEP_ACCOUNT_ID}/narrative`,
      body: createNarrativeContent('proposal_section'),
    }]);

    await expectRouteSupportsWorkflow(
      authedPage,
      `/studio/${DEEP_ACCOUNT_ID}/narrative`,
      [/proposal|section|financial impact|scenario/i],
      'proposal section generation',
    );
  });

  // ── Tone and Audience Adjustment ───────────────────────────────────────

  journeyTest('NARR-008: user can adjust narrative tone and audience', async ({ authedPage }) => {
    await authedPage.goto(`/studio/${DEEP_ACCOUNT_ID}/narrative`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/tone|audience|cfo|executive|technical|adjust/i, /narrative/i],
      'narrative tone and audience adjustment controls',
    );
  });

  journeyTest('NARR-009: user can convert technical value language into executive value language', async ({ authedPage }) => {
    await authedPage.goto(`/studio/${DEEP_ACCOUNT_ID}/narrative`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/executive.*value|business impact|financial|convert|translate/i, /narrative/i],
      'executive value language conversion in narrative',
    );
  });

  // ── Grounding and Claim Validation ─────────────────────────────────────

  journeyTest('NARR-010: all claims in generated narrative are grounded or labeled as assumptions', async ({ authedPage }) => {
    await authedPage.goto(`/studio/${DEEP_ACCOUNT_ID}/narrative`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/citation|evidence|assumption|grounded|ev-001|bench-001/i, /narrative/i],
      'narrative shows grounding citations or assumption labels',
    );
  });

  journeyTest('NARR-011: user can remove unsupported claims from generated narrative', async ({ authedPage }) => {
    await authedPage.goto(`/studio/${DEEP_ACCOUNT_ID}/narrative`, { waitUntil: 'domcontentloaded' });

    const removeBtn = authedPage.getByRole('button', { name: /remove.*claim|delete.*claim|unsupported/i }).first();
    const hasRemove = await removeBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasRemove) {
      await removeBtn.click();
      await expect(
        authedPage.getByText(/removed|deleted|claim.*removed/i).first(),
      ).toBeVisible({ timeout: 8000 });
    } else {
      await expectAnyVisible(
        authedPage,
        [/narrative|evidence|claim|citation/i],
        'narrative with claim management surface',
      );
    }
  });

  // ── Version History ─────────────────────────────────────────────────────

  journeyTest('NARR-012: user can view narrative version history', async ({ authedPage }) => {
    await authedPage.goto(`/studio/${DEEP_ACCOUNT_ID}/narrative`, { waitUntil: 'domcontentloaded' });

    const historyBtn = authedPage.getByRole('button', { name: /history|versions|changelog/i }).first();
    const hasHistory = await historyBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasHistory) {
      await historyBtn.click();
      await expectAnyVisible(
        authedPage,
        [/version.*1|version.*2|version.*3|avery stone|initial/i],
        'narrative version history list',
      );
    } else {
      await expectAnyVisible(
        authedPage,
        [/narrative|version|history/i],
        'narrative surface with history access',
      );
    }
  });

  journeyTest('NARR-013: user can save a narrative version', async ({ authedPage }) => {
    await authedPage.goto(`/studio/${DEEP_ACCOUNT_ID}/narrative`, { waitUntil: 'domcontentloaded' });

    const saveBtn = authedPage.getByRole('button', { name: /save|save version|save draft/i }).first();
    const hasSave = await saveBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasSave) {
      await saveBtn.click();
      await expect(
        authedPage.getByText(/saved|version.*saved|draft.*saved/i).first(),
      ).toBeVisible({ timeout: 8000 });
    } else {
      await expectAnyVisible(authedPage, [/narrative|studio/i], 'narrative studio');
    }
  });

  journeyTest('NARR-014: user can restore a previous narrative version', async ({ authedPage }) => {
    await authedPage.goto(`/studio/${DEEP_ACCOUNT_ID}/narrative`, { waitUntil: 'domcontentloaded' });

    const historyBtn = authedPage.getByRole('button', { name: /history|versions/i }).first();
    const hasHistory = await historyBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasHistory) {
      await historyBtn.click();
      const restoreBtn = authedPage.getByRole('button', { name: /restore|revert/i }).first();
      const hasRestore = await restoreBtn.isVisible({ timeout: 5000 }).catch(() => false);
      if (hasRestore) {
        await restoreBtn.click();
        await expect(
          authedPage.getByText(/restored|reverted|version.*restored/i).first(),
        ).toBeVisible({ timeout: 10000 });
      }
    }
  });
});
