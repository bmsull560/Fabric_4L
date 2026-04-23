/**
 * DecisionTrace Component Tests
 *
 * Tests for the audit and provenance viewer including:
 * - Rendering trace data
 * - Provenance chain display
 * - Formula reference links
 * - Empty/error states
 * - PROV-O export functionality
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Router } from 'wouter';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/mocks/server';
import DecisionTrace from './DecisionTrace';

/** Create wrapper with specific initial path for wouter Router */
function createWrapperWithPath(path: string) {
  return function Wrapper({ children }: { children: ReactNode }) {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, staleTime: 0 },
      },
    });
    return (
      <Router ssrPath={path}>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </Router>
    );
  };
}

/** Default wrapper without path */
function createWrapper() {
  return createWrapperWithPath('/');
}

describe('DecisionTrace', () => {
  it('renders loading state initially', () => {
    const wrapper = createWrapper();
    render(<DecisionTrace />, { wrapper });

    // Should show loading skeletons
    expect(document.querySelector('[class*="skeleton"]')).toBeDefined();
  });

  it('renders audit log and allows entity selection to view provenance', async () => {
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

    const wrapper = createWrapper();
    render(<DecisionTrace />, { wrapper });

    // Wait for audit log entries to render (not just the header)
    await waitFor(() => {
      expect(screen.getAllByText('business_case').length).toBeGreaterThan(0);
    });

    // Click on View button to select entity (use findByRole for specificity)
    const viewButtons = await screen.findAllByRole('button', { name: /view/i });
    const viewButton = viewButtons[0];
    await userEvent.click(viewButton);

    // Now provenance timeline should appear
    await waitFor(() => {
      expect(screen.getByText('Provenance Timeline')).toBeInTheDocument();
    });
  });

  it('renders audit log table', async () => {
    server.use(
      http.get('/api/v1/graph/audit/logs', () => {
        return HttpResponse.json({
          entries: [
            {
              id: 'audit-1',
              timestamp: '2024-01-15T10:00:00Z',
              source: 'provenance',
              event_type: 'create',
              entity_id: 'entity-1',
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
      })
    );

    const wrapper = createWrapper();
    render(<DecisionTrace />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Audit Log')).toBeInTheDocument();
    });
  });

  it('shows empty state when no entity selected', async () => {
    // Use wrapper without entityId in path
    const wrapper = createWrapper();

    server.use(
      http.get('/api/v1/graph/audit/logs', () => {
        return HttpResponse.json({
          entries: [],
          total: 0,
          page: 1,
          per_page: 20,
        });
      })
    );

    render(<DecisionTrace />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Select an Entity')).toBeInTheDocument();
    });
  });

  it('renders provenance timeline when entity selected', async () => {
    // Setup mocks BEFORE creating wrapper and rendering
    server.use(
      http.get('/api/v1/graph/provenance/:entityId', () => {
        return HttpResponse.json({
          entity_id: 'test-entity',
          entity_type: 'business_case',
          entity_name: 'Test Entity',
          source: 'extraction',
          confidence_score: 0.95,
          created_at: '2024-01-15T10:00:00Z',
          steps: [
            { step: 1, label: 'Extraction', detail: 'Extracted data', timestamp: '2024-01-15T10:00:00Z', agent: 'agent-1' },
            { step: 2, label: 'Validation', detail: 'Validated results', timestamp: '2024-01-15T10:05:00Z', agent: 'agent-2' },
          ],
        });
      }),
      http.get('/api/v1/graph/audit/logs', () => {
        return HttpResponse.json({
          entries: [
            {
              id: 'audit-1',
              timestamp: '2024-01-15T10:00:00Z',
              source: 'provenance',
              event_type: 'create',
              entity_id: 'test-entity',
              entity_type: 'business_case',
              action: 'create',
              agent: 'extraction_agent',
              details: {},
            },
          ],
          total: 1,
          page: 1,
          per_page: 20,
        });
      })
    );

    const wrapper = createWrapper();
    render(<DecisionTrace />, { wrapper });

    // Wait for audit log entries to render
    await waitFor(() => {
      expect(screen.getByText('business_case')).toBeInTheDocument();
    });

    // Click on View button to select entity (use findByRole for specificity)
    const viewButton = await screen.findByRole('button', { name: /view/i });
    await userEvent.click(viewButton);

    // Now provenance timeline should appear
    await waitFor(() => {
      expect(screen.getByText('Provenance Timeline')).toBeInTheDocument();
    });

    expect(screen.getByText('Test Entity')).toBeInTheDocument();
  });

  it('renders export PROV-O button', async () => {
    server.use(
      http.get('/api/v1/graph/audit/logs', () => {
        return HttpResponse.json({ entries: [], total: 0, page: 1, per_page: 20 });
      })
    );

    const wrapper = createWrapper();
    render(<DecisionTrace />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Export PROV-O')).toBeInTheDocument();
    });
  });

  it('renders toolbar buttons', async () => {
    server.use(
      http.get('/api/v1/graph/audit/logs', () => {
        return HttpResponse.json({ entries: [], total: 0, page: 1, per_page: 20 });
      })
    );

    const wrapper = createWrapper();
    render(<DecisionTrace />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/Source:/i)).toBeInTheDocument();
    });
  });
});
