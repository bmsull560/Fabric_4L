import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import ProspectSetup from './ProspectSetup';

describe('ProspectSetup example prompt submission', () => {
  it('submits the Medtronic example from the beginning step with full payload', async () => {
    const user = userEvent.setup();
    const onCreateSetup = vi.fn().mockResolvedValue({ accountId: 'acct-medtronic-001' });

    render(
      <MemoryRouter>
        <ProspectSetup onCreateSetup={onCreateSetup} />
      </MemoryRouter>
    );

    // 1. Verify we are at the beginning step (Launch Intelligence is disabled before context)
    const launchButton = screen.getByRole('button', { name: 'Launch Intelligence' });
    expect(launchButton).toBeDisabled();

    // 2. Restore the Medtronic example activity (simulates clicking the recent-activity menu)
    const recentActivityTrigger = screen.getByRole('button', { name: /recent value cases/i });
    await user.click(recentActivityTrigger);

    const medtronicActivity = await screen.findByText('Medtronic launch readiness setup');
    await user.click(medtronicActivity);

    // 3. Verify the prompt textarea is populated with the Medtronic example
    const promptTextarea = screen.getByLabelText(/new value case prompt/i);
    expect(promptTextarea.value).toContain('Company: Medtronic');
    expect(promptTextarea.value).toContain('medtronic.com');
    expect(promptTextarea.value).toContain('Medical Devices');

    // 4. Launch Intelligence should now be enabled
    expect(launchButton).toBeEnabled();

    // 5. Submit the prompt
    await user.click(launchButton);

    // 6. Verify onCreateSetup was called with the expected payload shape
    expect(onCreateSetup).toHaveBeenCalledTimes(1);
    const payload = onCreateSetup.mock.calls[0][0];

    // Core identifiers
    expect(payload.companyName).toBe('Medtronic');
    expect(payload.companyDomain).toBe('medtronic.com');
    expect(payload.industry).toBe('Medical Devices');

    // Parsed business context
    expect(payload.buyingContext).toBe(
      'New product launch readiness across distributed field teams'
    );
    expect(payload.whyNow).toBe(
      'Need stronger rep ramp, compliant messaging, and executive discovery prep'
    );
    expect(payload.knownInitiative).toBe('Field launch enablement refresh');

    // Stakeholders
    expect(payload.stakeholders).toMatchObject({
      economicBuyer: 'VP Sales',
      champion: 'Sales Enablement Leader',
      evaluator: 'RevOps / IT',
      compliance: 'Regulatory and legal operations',
    });

    // Business pains & friction
    expect(payload.businessPain).toEqual([
      'Rep onboarding is slow for complex offerings',
      'Messaging consistency is difficult across field teams',
      'Launch content is fragmented across systems',
    ]);
    expect(payload.currentFriction).toEqual([
      'Multiple systems create version confusion',
      'Coaching quality varies by manager',
    ]);
    expect(payload.desiredOutcomes).toEqual([
      'Faster rep ramp time',
      'More consistent compliant messaging',
      'Better launch readiness',
    ]);

    // Outputs & mode
    expect(payload.desiredOutputs).toEqual([
      'account_brief',
      'discovery_prep',
      'value_hypotheses',
    ]);
    expect(payload.outputType).toBe('account_brief');
    expect(['Fast', 'Balanced', 'Deep']).toContain(payload.mode);
    expect(['light', 'standard', 'deep']).toContain(payload.enrichmentDepth);

    // Flags
    expect(payload.useUploadedFiles).toBeTypeOf('boolean');
    expect(payload.usePriorAccountContext).toBeTypeOf('boolean');
    expect(payload.runWebEnrichment).toBeTypeOf('boolean');
    expect(payload.complianceSensitive).toBeTypeOf('boolean');

    // Freeform prompt is preserved
    expect(payload.freeformPrompt).toContain('Company: Medtronic');
  });

  it('submits the Goldman Sachs minimal example successfully', async () => {
    const user = userEvent.setup();
    const onCreateSetup = vi.fn().mockResolvedValue({ accountId: 'acct-gs-001' });

    render(
      <MemoryRouter>
        <ProspectSetup onCreateSetup={onCreateSetup} />
      </MemoryRouter>
    );

    const recentActivityTrigger = screen.getByRole('button', { name: /recent value cases/i });
    await user.click(recentActivityTrigger);

    const gsActivity = await screen.findByText('Financial services coaching setup');
    await user.click(gsActivity);

    const launchButton = screen.getByRole('button', { name: 'Launch Intelligence' });
    expect(launchButton).toBeEnabled();

    await user.click(launchButton);

    expect(onCreateSetup).toHaveBeenCalledTimes(1);
    const payload = onCreateSetup.mock.calls[0][0];

    expect(payload.companyName).toBe('Goldman Sachs');
    expect(payload.desiredOutputs).toEqual([
      'executive_summary',
      'value_hypotheses',
    ]);
    expect(payload.freeformPrompt).toContain('Goldman Sachs');
  });
});
