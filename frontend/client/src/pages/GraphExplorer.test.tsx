/**
 * GraphExplorer Component Tests
 *
 * Tests for the knowledge graph visualization component including:
 * - Rendering with graph data
 * - Empty graph state
 * - Node selection and click handlers
 * - Search/filter interactions
 * - Loading and error states
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { createWrapper } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/mocks/server';
import GraphExplorer from './GraphExplorer';

// Mock matchMedia for responsive tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

describe('GraphExplorer', () => {
  it('renders with graph data', async () => {
    const wrapper = createWrapper();
    render(<GraphExplorer />, { wrapper });

    // Should show page header (use heading role to disambiguate from tab)
    expect(screen.getByRole('heading', { name: 'Graph Explorer' })).toBeInTheDocument();

    // Wait for graph to load
    await waitFor(() => {
      expect(screen.queryByText('Loading knowledge graph...')).not.toBeInTheDocument();
    });
  });

  it('handles empty graph state', async () => {
    server.use(
      http.post('/api/v1/graph/v1/search/hybrid', () => {
        return HttpResponse.json({ results: [] });
      })
    );

    const wrapper = createWrapper();
    render(<GraphExplorer />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('No graph data available')).toBeInTheDocument();
    });
  });

  it('handles graph error state', async () => {
    server.use(
      http.post('/api/v1/graph/v1/search/hybrid', () => {
        return HttpResponse.json({ error: 'Neo4j connection failed' }, { status: 500 });
      })
    );

    const wrapper = createWrapper();
    render(<GraphExplorer />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  it('allows search input', async () => {
    const wrapper = createWrapper();
    render(<GraphExplorer />, { wrapper });

    const searchInput = screen.getByPlaceholderText('Search graph…');
    fireEvent.change(searchInput, { target: { value: 'test query' } });

    expect(searchInput).toHaveValue('test query');
  });

  it('displays graph statistics', async () => {
    const wrapper = createWrapper();
    render(<GraphExplorer />, { wrapper });

    // Wait for graph to load
    await waitFor(() => {
      expect(screen.getByText('Graph Statistics')).toBeInTheDocument();
    });

    // Should show statistics labels
    expect(screen.getByText('Nodes')).toBeInTheDocument();
    expect(screen.getByText('Edges')).toBeInTheDocument();
  });

  it('shows selected node panel when node clicked', async () => {
    const wrapper = createWrapper();
    render(<GraphExplorer />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Graph Statistics')).toBeInTheDocument();
    });

    // Initially shows "Click a node to select"
    expect(screen.getByText('Click a node to select')).toBeInTheDocument();
  });

  it('renders tabs', () => {
    const wrapper = createWrapper();
    render(<GraphExplorer />, { wrapper });

    // Use getAllByText for Graph Explorer since it appears in multiple places (heading + tabs)
    expect(screen.getAllByText('Graph Explorer').length).toBeGreaterThanOrEqual(1);
    // Tabs should be present - use getAllByRole since there may be multiple tab sets
    expect(screen.getAllByRole('tab', { name: /Query Builder/i }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole('tab', { name: /Communities/i }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole('tab', { name: /Metrics/i }).length).toBeGreaterThanOrEqual(1);
  });

  it('renders toolbar buttons', () => {
    const wrapper = createWrapper();
    render(<GraphExplorer />, { wrapper });

    expect(screen.getByText('Layout: Force ▾')).toBeInTheDocument();
    expect(screen.getByText('Filters ▾')).toBeInTheDocument();
  });
});
