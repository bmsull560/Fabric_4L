import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Router } from 'wouter';
import { memoryLocation } from 'wouter/memory-location';

const authState = vi.hoisted(() => ({ isAuthenticated: false, isLoading: false }));

vi.mock('@/components', () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => <div data-testid="app-shell">{children}</div>,
  Layout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Toaster: () => null,
  TooltipProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuthContext: () => ({ ...authState, user: authState.isAuthenticated ? { id: 'u1' } : null }),
}));

const tierStore = {
  currentTier: 'admin',
  effectiveTier: 'admin',
  canAccessRouteWithReason: () => ({ allowed: true, reason: 'ok' }),
};

vi.mock('@/hooks', () => ({
  useUserTierStore: (selector: (state: typeof tierStore) => unknown) => selector(tierStore),
  useCreateAccount: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

vi.mock('../pages/Login', () => ({ default: () => <div>Login Page</div> }));
vi.mock('../pages/ValueNarrativeHome', () => ({ default: () => <div>Workspace Home</div> }));

import { AppRouter } from '../App';

function renderAt(path: string) {
  const { hook } = memoryLocation({ path });
  return render(<Router hook={hook}><AppRouter /></Router>);
}

describe('critical route smoke', () => {
  beforeEach(() => {
    authState.isLoading = false;
    authState.isAuthenticated = false;
  });

  it('auth-gates private route users to login', async () => {
    renderAt('/home');
    expect(await screen.findByText('Login Page')).toBeInTheDocument();
  });

  it('loads workspace shell for authenticated users', async () => {
    authState.isAuthenticated = true;
    renderAt('/home');
    expect(await screen.findByText('Workspace Home')).toBeInTheDocument();
  });
});

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
