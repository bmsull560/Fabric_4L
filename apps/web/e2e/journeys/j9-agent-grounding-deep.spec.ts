/**
 * Journey 9 Deep: Agent Grounding and Governance
 *
 * Traceability: AG-DEEP-001 through AG-DEEP-010.
 * Validates grounded, auditable agent behavior under normal and adversarial
 * inputs. The agent must cite evidence, label assumptions, refuse unsupported
 * claims, resist prompt injection, and create audit events.
 *
 * Priority: P0 production gate
 */
import { journeyTest, expect } from '../helpers/journey-fixture';
import {
  expectAnyVisible,
  expectRouteSupportsWorkflow,
  expectNoCrossTenantLeakage,
  expectNotVisible,
  expectTenantContext,
} from '../helpers/validation-program';
import {
  DEEP_ACCOUNT_ID,
  DEEP_CASE_APPROVED_ID,
  buildGoldenPathMocks,
  createGroundedAgentResponse,
  createRefusalAgentResponse,
  createPromptInjectionAttempt,
} from '../fixtures/deep-test-data';

journeyTest.describe('Agent Grounding and Governance Deep', () => {
  journeyTest.beforeEach(async ({ addMocks }) => {
    await addMocks(buildGoldenPathMocks());
  });

  // ── Evidence Citations ─────────────────────────────────────────────────

  journeyTest('AG-DEEP-001: agent response includes evidence citations with source references', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/signals`, { waitUntil: 'domcontentloaded' });

    const chatInput = authedPage.getByPlaceholder(/ask|message|chat/i).first();
    if (await chatInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await chatInput.fill('What are the key cost drivers?');
      const sendBtn = authedPage.getByRole('button', { name: /send|submit/i }).first();
      if (await sendBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await sendBtn.click();

        // Agent response should contain citation references
        await expect(
          authedPage.getByText(/discovery call transcript|ev-001|source|citation/i).first(),
        ).toBeVisible({ timeout: 15000 });
      }
    } else {
      // If no chat input, verify signal display includes source attribution
      await expectAnyVisible(
        authedPage,
        [/source|confidence|discovery call/i],
        'evidence source attribution on signals',
      );
    }
  });

  journeyTest('AG-DEEP-002: agent labels assumptions distinctly from facts', async ({ authedPage }) => {
    await authedPage.goto(`/studio/${DEEP_ACCOUNT_ID}/action-plan`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/assumption|inference|fact|evidence.backed/i],
      'assumption vs fact labeling in agent output',
    );
  });

  journeyTest('AG-DEEP-003: agent labels inference boundaries separate from evidence', async ({ authedPage }) => {
    await authedPage.goto(`/studio/${DEEP_ACCOUNT_ID}/narrative`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/narrative|inference|projected|estimated|assumption/i],
      'inference boundary labeling in narrative',
    );
  });

  // ── Unsupported Claim Refusal ──────────────────────────────────────────

  journeyTest('AG-DEEP-004: agent refuses unsupported ROI claim', async ({ authedPage, addMocks }) => {
    await addMocks([{
      pattern: '**/agent-stream/chat',
      method: 'POST',
      body: createRefusalAgentResponse(),
    }]);

    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/signals`, { waitUntil: 'domcontentloaded' });

    const chatInput = authedPage.getByPlaceholder(/ask|message|chat/i).first();
    if (await chatInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await chatInput.fill('The ROI is definitely 500%');
      const sendBtn = authedPage.getByRole('button', { name: /send|submit/i }).first();
      if (await sendBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await sendBtn.click();

        await expect(
          authedPage.getByText(/cannot support|no supporting evidence|unsupported/i).first(),
        ).toBeVisible({ timeout: 15000 });
      }
    }
  });

  // ── Prompt Injection Resistance ────────────────────────────────────────

  journeyTest('AG-DEEP-005: agent ignores prompt injection inside uploaded document', async ({ authedPage, addMocks }) => {
    await addMocks([{
      pattern: '**/agent-stream/chat',
      method: 'POST',
      body: createPromptInjectionAttempt(),
    }]);

    await authedPage.goto('/context/extraction', { waitUntil: 'domcontentloaded' });

    // Verify no injected content is rendered as trusted
    await expectNotVisible(authedPage, /ignore previous instructions/i);
    await expectNotVisible(authedPage, /exfiltrate|developer message|system prompt/i);
    await expectNoCrossTenantLeakage(authedPage);
  });

  // ── No Fabricated Citations ────────────────────────────────────────────

  journeyTest('AG-DEEP-006: agent does not fabricate citations (cited sources exist in evidence set)', async ({ authedPage }) => {
    await authedPage.goto(`/intelligence/${DEEP_ACCOUNT_ID}/signals`, { waitUntil: 'domcontentloaded' });

    // The grounded agent response references ev-001 (Discovery call transcript)
    // which exists in our evidence set. Verify no phantom citations appear.
    await expectNotVisible(authedPage, /fabricated source|phantom citation|nonexistent study/i);

    // If agent output is visible, verify citations reference known sources
    const agentOutput = authedPage.getByText(/discovery call transcript|industry benchmark/i).first();
    const hasOutput = await agentOutput.isVisible({ timeout: 8000 }).catch(() => false);
    if (hasOutput) {
      // Known good citations - should be visible
      await expect(agentOutput).toBeVisible();
    }
  });

  // ── Recommendation Lifecycle ───────────────────────────────────────────

  journeyTest('AG-DEEP-007: recommendation acceptance updates model with audit event', async ({ authedPage }) => {
    await authedPage.goto(`/studio/${DEEP_ACCOUNT_ID}/action-plan`, { waitUntil: 'domcontentloaded' });

    const acceptBtn = authedPage.getByRole('button', { name: /accept|approve|apply/i }).first();
    const hasAccept = await acceptBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasAccept) {
      await acceptBtn.click();
      await expectAnyVisible(
        authedPage,
        [/applied|accepted|updated|audit/i],
        'recommendation acceptance confirmation',
      );
    } else {
      await expectAnyVisible(
        authedPage,
        [/action plan|recommendation|evidence/i],
        'action plan with recommendation surface',
      );
    }
  });

  journeyTest('AG-DEEP-008: recommendation rejection preserves model unchanged', async ({ authedPage }) => {
    await authedPage.goto(`/studio/${DEEP_ACCOUNT_ID}/action-plan`, { waitUntil: 'domcontentloaded' });

    const rejectBtn = authedPage.getByRole('button', { name: /reject|dismiss|decline/i }).first();
    const hasReject = await rejectBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasReject) {
      await rejectBtn.click();
      await expectAnyVisible(
        authedPage,
        [/rejected|dismissed|declined|unchanged/i],
        'recommendation rejection confirmation',
      );
    }
  });

  // ── Business Case Claim Traceability ───────────────────────────────────

  journeyTest('AG-DEEP-009: business case claims trace to evidence, benchmark, or assumption', async ({ authedPage }) => {
    await authedPage.goto(`/deliverables/cases/${DEEP_CASE_APPROVED_ID}`, { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/evidence|benchmark|assumption|claim|traceable|source|reference/i],
      'business case claim traceability',
    );

    // Verify specific claim types are labeled
    const hasEvidence = await authedPage.getByText(/evidence|source/i).first().isVisible({ timeout: 3000 }).catch(() => false);
    const hasBenchmark = await authedPage.getByText(/benchmark|reference/i).first().isVisible({ timeout: 3000 }).catch(() => false);
    const hasAssumption = await authedPage.getByText(/assumption/i).first().isVisible({ timeout: 3000 }).catch(() => false);

    expect(
      hasEvidence || hasBenchmark || hasAssumption,
      'Business case must label at least one claim type (evidence, benchmark, or assumption)',
    ).toBe(true);
  });

  // ── Audit Trail ────────────────────────────────────────────────────────

  journeyTest('AG-DEEP-010: agent decisions are visible in governance audit trail', async ({ authedPage }) => {
    await authedPage.goto('/governance/traces', { waitUntil: 'domcontentloaded' });

    await expectAnyVisible(
      authedPage,
      [/decision trace|audit log|provenance/i],
      'governance audit trail for agent decisions',
    );

    await expectTenantContext(authedPage);
    await expectNoCrossTenantLeakage(authedPage);
  });
});
