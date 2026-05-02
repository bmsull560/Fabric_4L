import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import ProspectSetup from '@/workflow/pages/ProspectSetup';

describe('ProspectSetup behavior primitives', () => {
  it('keeps launch action disabled without minimum prompt context (validation)', () => {
    render(<MemoryRouter><ProspectSetup /></MemoryRouter>);
    expect(screen.getByRole('button', { name: 'Launch Intelligence' })).toBeDisabled();
  });

  it('renders external loading state for launch action', () => {
    render(<MemoryRouter><ProspectSetup isSubmitting /></MemoryRouter>);
    expect(screen.getByRole('button', { name: 'Launching...' })).toBeDisabled();
  });

  it('renders submission error when creation fails', async () => {
    const user = userEvent.setup();
    const onCreateSetup = vi.fn().mockRejectedValue(new Error('boom'));
    render(<MemoryRouter><ProspectSetup onCreateSetup={onCreateSetup} /></MemoryRouter>);

    await user.type(screen.getByLabelText('New value case prompt'), 'Company: FailureCo');
    await user.click(screen.getByRole('button', { name: 'Launch Intelligence' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to launch intelligence. Please review the input and try again.');
  });
});
