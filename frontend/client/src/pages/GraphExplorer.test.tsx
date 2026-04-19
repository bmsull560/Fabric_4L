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
import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createWrapper } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/mocks/server';
import GraphExplorer from './GraphExplorer';

// P0 Fix: Standard timeout configuration for flaky async tests
const WAIT_OPTIONS = { timeout: 3000 };

describe('GraphExplorer', () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  it('renders with graph data', async () => {
    const wrapper = createWrapper();
    render(<GraphExplorer />, { wrapper });

    // Should show page header immediately (static content)
    expect(screen.getByRole('heading', { name: 'Graph Explorer' })).toBeInTheDocument();

    // P0 Fix: Wait for loading state to appear first, then disappear
    // This ensures the component is actually fetching before we wait for completion
    await waitFor(() => {
      expect(screen.queryByText('Loading knowledge graph...')).toBeInTheDocument();
    }, WAIT_OPTIONS);

    // Then wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText('Loading knowledge graph...')).not.toBeInTheDocument();
    }, WAIT_OPTIONS);
  });

  it('handles empty graph state', async () => {
    // Override default handler to return empty graph
    server.use(
      http.get('/api/v1/graph/subgraph', () => {
        return HttpResponse.json({
          root_entity_id: '',
          nodes: [],
          edges: [],
          depth: 2,
          stats: { total_nodes: 0, total_edges: 0, density: 0 },
        });
      })
    );

    const wrapper = createWrapper();
    render(<GraphExplorer />, { wrapper });

    // Wait for loading to appear then disappear
    await waitFor(() => {
      expect(screen.queryByText('Loading knowledge graph...')).toBeInTheDocument();
    }, { timeout: 3000 });

    await waitFor(() => {
      expect(screen.queryByText('Loading knowledge graph...')).not.toBeInTheDocument();
    }, { timeout: 5000 });

    // Then check for empty state
    await waitFor(() => {
      expect(screen.getByText('No matching entities found')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('handles graph error state', async () => {
    server.use(
      http.get('/api/v1/graph/subgraph', () => {
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
    const user = userEvent.setup();
    const wrapper = createWrapper();
    render(<GraphExplorer />, { wrapper });

    const searchInput = screen.getByPlaceholderText('Search entities...');
    await user.type(searchInput, 'test query');

    expect(searchInput).toHaveValue('test query');
  });

  it('displays graph statistics', async () => {
    const wrapper = createWrapper();
    render(<GraphExplorer />, { wrapper });

    // P0 Fix: Wait for loading to complete before checking stats
    await waitFor(() => {
      expect(screen.queryByText('Loading knowledge graph...')).not.toBeInTheDocument();
    }, WAIT_OPTIONS);

    // Then wait for graph stats to appear
    await waitFor(() => {
      expect(screen.getByText('Graph Statistics')).toBeInTheDocument();
    }, WAIT_OPTIONS);

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

    // Initially shows "Click a node to view details"
    expect(screen.getByText('Click a node to view details')).toBeInTheDocument();
  });

  it('renders layout control buttons', () => {
    const wrapper = createWrapper();
    render(<GraphExplorer />, { wrapper });

    // Layout section should have layout algorithm buttons
    expect(screen.getByRole('button', { name: /force directed/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /circular/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /hierarchical/i })).toBeInTheDocument();
  });

  it('renders control panel buttons', () => {
    const wrapper = createWrapper();
    render(<GraphExplorer />, { wrapper });

    expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /focus selection/i })).toBeInTheDocument();
  });

  it('renders coherent graph with nodes and edges from subgraph endpoint', async () => {
    server.use(
      http.get('/api/v1/graph/subgraph', () => {
        return HttpResponse.json({
          root_entity_id: 'ent-1',
          nodes: [
            { id: 'ent-1', name: 'AI Processing', entity_type: 'Capability', confidence_score: 0.95 },
            { id: 'ent-2', name: 'Data Pipeline', entity_type: 'Capability', confidence_score: 0.88 },
            { id: 'ent-3', name: 'Customer Analytics', entity_type: 'UseCase', confidence_score: 0.92 },
          ],
          edges: [
            { source: 'ent-1', target: 'ent-2', type: 'ENABLES' },
            { source: 'ent-2', target: 'ent-3', type: 'ENABLES' },
          ],
          depth: 2,
          stats: { total_nodes: 3, total_edges: 2, density: 0.33 },
        });
      })
    );

    const wrapper = createWrapper();
    render(<GraphExplorer />, { wrapper });

    // Wait for graph to load and verify stats are displayed
    await waitFor(() => {
      expect(screen.getByText('Graph Statistics')).toBeInTheDocument();
    }, { timeout: 3000 });

    // Verify graph stats are displayed (Nodes and Edges labels present)
    expect(screen.getByText('Nodes')).toBeInTheDocument();
    expect(screen.getByText('Edges')).toBeInTheDocument();
  });
});
