import { describe, it, expect } from 'vitest';
import type { ReactNode } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse, passthrough } from 'msw';
import { server } from '../../../../test/mocks/server';
import GovernanceEvidencePage from './GovernanceEvidencePage';
import GovernanceCompliancePage from './GovernanceCompliancePage';
import GovernanceAuditLogPage from './GovernanceAuditLogPage';
import GovernanceAuditChangesPage from './GovernanceAuditChangesPage';

function wrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe('governance pages (L5)', () => {
  it('renders governance evidence using /api/v1/truths* handler', async () => {
    server.use(
      http.get(/.*/, ({ request }) => {
        const url = new URL(request.url);
        if (url.pathname === '/api/v1/truths') {
          return HttpResponse.json({
            items: [{ id: 'truth-1', claim: 'SOC2 evidence linked', status: 'active' }],
            total: 1,
          });
        }
        return passthrough();
      })
    );

    render(<GovernanceEvidencePage />, { wrapper });

    expect(await screen.findByRole('heading', { name: 'Governance Evidence' })).toBeInTheDocument();
    expect(await screen.findByText('SOC2 evidence linked')).toBeInTheDocument();
  });

  it('renders governance compliance using maturity-ladder and freshness summary handlers', async () => {
    server.use(
      http.get(/.*/, ({ request }) => {
        const url = new URL(request.url);
        if (url.pathname === '/api/v1/maturity-ladder') {
          return HttpResponse.json([{ level: 'L3', description: 'managed' }]);
        }
        if (url.pathname === '/api/v1/truths/freshness-summary') {
          return HttpResponse.json({ fresh: 10, stale: 1 });
        }
        return passthrough();
      })
    );

    render(<GovernanceCompliancePage />, { wrapper });

    expect(await screen.findByRole('heading', { name: 'Governance Compliance' })).toBeInTheDocument();
    expect(await screen.findByText('L3')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/"fresh": 10/)).toBeInTheDocument();
    });
  });

  it('renders audit log and audit changes pages with audit-specific handlers', async () => {
    server.use(
      http.get(/.*/, ({ request }) => {
        const url = new URL(request.url);
        if (url.pathname === '/api/v1/truths/audit/log') {
          return HttpResponse.json([{ id: 'a-1', action: 'created', timestamp: '2026-01-01T00:00:00Z' }]);
        }
        if (url.pathname === '/api/v1/truths/audit/changes') {
          return HttpResponse.json([{ id: 'c-1', action: 'updated status', timestamp: '2026-01-01T00:00:00Z' }]);
        }
        return passthrough();
      })
    );

    render(<GovernanceAuditLogPage />, { wrapper });
    expect(await screen.findByRole('heading', { name: 'Governance Audit Log' })).toBeInTheDocument();
    expect(await screen.findByText('created')).toBeInTheDocument();

    render(<GovernanceAuditChangesPage />, { wrapper });
    expect(await screen.findByRole('heading', { name: 'Governance Audit Changes' })).toBeInTheDocument();
    expect(await screen.findByText('updated status')).toBeInTheDocument();
  });
});
