import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Router } from 'wouter';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/mocks/server';
import DecisionTrace from './DecisionTrace';

function createWrapper(path: string = '/') {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false, staleTime: 0 } },
    });

    return (
      <Router ssrPath={path}>
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      </Router>
    );
  };
}

function registerTraceHandlers() {
  server.use(
    http.get('/api/v1/graph/audit/logs', () => {
      return HttpResponse.json({
        entries: [
          {
            id: 'audit-1',
            timestamp: '2024-01-15T10:00:00Z',
            source: 'provenance',
            event_type: 'create',
            entity_id: 'test-entity-123',
            entity_type: 'business_case',
            action: 'create',
            agent: 'user@example.com',
            details: {},
          },
        ],
        total: 1,
        page: 1,
        per_page: 20,
      });
    }),
    http.get('/api/v1/graph/provenance/:entityId', () => {
      return HttpResponse.json({
        entity_id: 'test-entity-123',
        entity_type: 'business_case',
        entity_name: 'Test Business Case',
        source: 'extraction',
        extraction_job_id: 'job-123',
        confidence_score: 0.95,
        created_at: '2024-01-15T10:00:00Z',
        steps: [
          {
            step: 1,
            label: 'Entity Extraction',
            detail: 'Extracted from source',
            timestamp: '2024-01-15T10:00:00Z',
            agent: 'extraction_agent',
          },
        ],
      });
    })
  );
}

describe('DecisionTrace trace-specific behavior', () => {
  it('renders trace-specific title for /governance/traces', async () => {
    registerTraceHandlers();
    render(<DecisionTrace />, { wrapper: createWrapper('/governance/traces') });

    expect(await screen.findByRole('heading', { name: 'Decision Traces' })).toBeInTheDocument();
  });

  it('renders audit-specific title for /governance/audit/log', async () => {
    registerTraceHandlers();
    render(<DecisionTrace />, { wrapper: createWrapper('/governance/audit/log') });

    expect(await screen.findByText('Audit Log')).toBeInTheDocument();
  });

  it('allows selecting entity to view provenance timeline', async () => {
    registerTraceHandlers();
    render(<DecisionTrace />, { wrapper: createWrapper('/governance/traces') });

    await waitFor(() => {
      expect(screen.getByText('business_case')).toBeInTheDocument();
    });

    await userEvent.click(await screen.findByRole('button', { name: /view/i }));

    await waitFor(() => {
      expect(screen.getByText('Provenance Timeline')).toBeInTheDocument();
    });
  });
});
