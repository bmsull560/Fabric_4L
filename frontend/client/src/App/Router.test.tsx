import { describe, it, expect, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { render, screen, waitFor } from '@testing-library/react';
import { Router } from 'wouter';
import { memoryLocation } from 'wouter/memory-location';

vi.mock('@/components', () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Layout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  ErrorBoundary: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Toaster: () => null,
  TooltipProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuthContext: () => ({
    isAuthenticated: true,
    isLoading: false,
    user: { id: 'test-user' },
  }),
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

vi.mock('../pages/DecisionTrace', () => ({ default: () => <div>Decision Trace Viewer</div> }));
vi.mock('../pages/GovernanceEvidence', () => ({ default: () => <div>Governance Evidence Page</div> }));
vi.mock('../pages/GovernanceCompliance', () => ({ default: () => <div>Governance Compliance Page</div> }));
vi.mock('../pages/GovernanceAuditLog', () => ({ default: () => <div>Governance Audit Log Page</div> }));
vi.mock('../pages/GovernanceChangeHistory', () => ({ default: () => <div>Governance Change History Page</div> }));

vi.mock('../pages/NotFound', () => ({ default: () => <div>Not Found Page</div> }));
vi.mock('../pages/Login', () => ({ default: () => <div>Login Page</div> }));
vi.mock('../pages/LandingPage', () => ({ default: () => <div>Landing Page</div> }));
vi.mock('../pages/Signup', () => ({ default: () => <div>Signup Page</div> }));

import { AppRouter } from '../App';

function renderAt(path: string) {
  const { hook } = memoryLocation({ path });
  return render(
    <Router hook={hook}>
      <AppRouter />
    </Router>
  );
}

describe('App governance router', () => {

  it('redirects /governance to the governance traces page', async () => {
    renderAt('/governance');

    expect(await screen.findByText('Decision Trace Viewer')).toBeInTheDocument();
    expect(screen.queryByText('Governance Evidence Page')).not.toBeInTheDocument();
  });
  it('does not render Decision Trace Viewer at /governance/evidence', async () => {
    renderAt('/governance/evidence');

    await waitFor(() => {
      expect(screen.getByText('Governance Evidence Page')).toBeInTheDocument();
    });
    expect(screen.queryByText('Decision Trace Viewer')).not.toBeInTheDocument();
  });

  it('mounts compliance page at /governance/compliance', async () => {
    renderAt('/governance/compliance');

    expect(await screen.findByText('Governance Compliance Page')).toBeInTheDocument();
  });

  it('mounts audit-specific pages for audit routes', async () => {
    const { unmount } = renderAt('/governance/audit/log');
    expect(await screen.findByText('Governance Audit Log Page')).toBeInTheDocument();
    unmount();

    renderAt('/governance/audit/changes');
    expect(await screen.findByText('Governance Change History Page')).toBeInTheDocument();
  });
});


describe('route literal deduplication for canonical sections', () => {
  it('keeps canonical route path literals out of App.tsx', () => {
    const appSource = readFileSync('client/src/App.tsx', 'utf8');
    const canonicalLiterals = [
      '/intelligence',
      '/intelligence/signals',
      '/intelligence/drivers',
      '/intelligence/evidence',
      '/intelligence/stakeholders',
      '/intelligence/enrichment',
      '/intelligence/hypotheses',
      '/intelligence/competitive',
      '/intelligence/roi',
      '/intelligence/evidence-library',
      '/intelligence/:accountId',
      '/intelligence/:accountId/signals',
      '/intelligence/:accountId/drivers',
      '/intelligence/:accountId/evidence',
      '/intelligence/:accountId/stakeholders',
      '/intelligence/:accountId/enrichment',
      '/intelligence/:accountId/hypotheses',
      '/intelligence/:accountId/competitive',
      '/intelligence/:accountId/roi',
      '/intelligence/:accountId/evidence-library',
      '/studio',
      '/studio/action-plan',
      '/studio/value-model',
      '/studio/narrative',
      '/studio/enrichment',
      '/studio/competitive',
      '/studio/roi',
      '/studio/evidence',
      '/studio/:accountId',
      '/studio/:accountId/action-plan',
      '/studio/:accountId/value-model',
      '/studio/:accountId/narrative',
      '/studio/:accountId/enrichment',
      '/studio/:accountId/competitive',
      '/studio/:accountId/roi',
      '/studio/:accountId/evidence',
      '/governance',
      '/governance/traces',
      '/governance/evidence',
      '/governance/provenance',
      '/governance/integrity',
      '/governance/compliance',
      '/governance/benchmarks',
      '/governance/audit',
      '/governance/audit/log',
      '/governance/audit/changes',
      '/governance/health',
      '/trust',
      '/trust/traces',
      '/trust/evidence',
      '/trust/provenance',
      '/trust/integrity',
      '/trust/compliance',
      '/trust/benchmarks',
      '/trust/audit',
      '/trust/audit/log',
      '/trust/audit/changes',
      '/trust/health',
      '/evidence',
      '/evidence/traces',
      '/evidence/export',
      '/evidence/lineage',
      '/evidence/compliance',
      '/evidence/changelog',
    ];

    for (const literal of canonicalLiterals) {
      expect(appSource).not.toContain(`Route path="${literal}"`);
    }
  });
});
