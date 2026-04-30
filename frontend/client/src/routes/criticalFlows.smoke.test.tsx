import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import ProspectSetup from '../workflow/pages/ProspectSetup';

describe('prospect setup interaction smoke', () => {
  it('submits after minimum context is provided', async () => {
    const user = userEvent.setup();
    const onCreateSetup = vi.fn().mockResolvedValue({ accountId: 'acct-1' });
    render(<ProspectSetup onCreateSetup={onCreateSetup} />);

    await user.type(screen.getByLabelText('New value case prompt'), 'Company: TestCo');
    await user.click(screen.getByRole('button', { name: 'Launch Intelligence' }));

    expect(onCreateSetup).toHaveBeenCalledTimes(1);
    expect(await screen.findByRole('status')).toHaveTextContent('Intelligence launched. Opening workspace...');
  });
});
