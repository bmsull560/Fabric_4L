/**
 * useWorkflows Hook Tests
 *
 * Comprehensive test coverage for workflow management hooks including:
 * - useActiveWorkflows: Polling workflow list
 * - useWorkflowHistory: Historical workflow data
 * - useWorkflowSSE: Real-time SSE updates
 * - useCreateWorkflow: Workflow creation mutation
 * - useCancelWorkflow: Workflow cancellation mutation
 */
import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../test/mocks/server';
import {
  useActiveWorkflows,
  useWorkflowHistory,
  useWorkflowSSE,
  useCreateWorkflow,
  useCancelWorkflow,
} from './useWorkflows';

describe('useActiveWorkflows', () => {
  it('fetches and normalizes active workflows', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useActiveWorkflows(), { wrapper });

    // Initially loading
    expect(result.current.isLoading).toBe(true);

    // Wait for data to load
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Verify paginated response structure
    expect(result.current.data?.items).toHaveLength(3);
    expect(result.current.data?.total).toBe(3);
    expect(result.current.data?.has_more).toBe(false);
    expect(result.current.data?.items[0]).toMatchObject({
      id: 'wf-1',
      name: 'Market Analysis Workflow',
      status: 'running',
      progress: 65,
    });
  });

  it('handles empty workflow list', async () => {
    // Override handler to return empty paginated response
    server.use(
      http.get('/api/v1/agents/workflows/active', () => {
        return HttpResponse.json({
          items: [],
          total: 0,
          limit: 50,
          offset: 0,
          has_more: false,
        });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useActiveWorkflows(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items).toHaveLength(0);
    expect(result.current.data?.total).toBe(0);
  });

  it('handles malformed workflow data gracefully', async () => {
    server.use(
      http.get('/api/v1/agents/workflows/active', () => {
        return HttpResponse.json({
          items: [
            { workflow_id: 'wf-bad', status: 'unknown_status', progress_percentage: 'invalid' },
            { workflow_id: '', status: 'running' }, // Empty ID should be filtered
            { workflow_instance_id: 'wf-alt', workflow_type: 'test', status: 'running' },
          ],
          total: 3,
          limit: 50,
          offset: 0,
          has_more: false,
        });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useActiveWorkflows(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Should filter out empty ID workflows
    const workflows = result.current.data?.items || [];
    const badWorkflow = workflows.find(w => w.id === 'wf-bad');
    expect(badWorkflow?.status).toBe('created'); // Unknown status normalized to created
    expect(badWorkflow?.progress).toBe(0); // Invalid progress normalized to 0
  });

  it('handles API error', async () => {
    server.resetHandlers();
    server.use(
      http.get('/api/v1/agents/workflows/active', () => {
        return HttpResponse.json({ error: 'Service unavailable' }, { status: 500 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useActiveWorkflows(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 });
    expect(result.current.error).toBeDefined();
  });
});

describe('useWorkflowHistory', () => {
  it('fetches workflow history with pagination', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useWorkflowHistory(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.items).toHaveLength(3);
    expect(result.current.data?.total).toBe(3);
    expect(result.current.data?.items[2]).toMatchObject({
      id: 'wf-3',
      status: 'succeeded',
      progress: 100,
    });
  });
});

describe('useWorkflowSSE', () => {
  it('connects to SSE and receives updates', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useWorkflowSSE('wf-1'), { wrapper });

    // Wait for connection
    await waitFor(() => expect(result.current.isConnected).toBe(true));

    // Verify initial state
    expect(result.current.workflow).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('returns null workflow when workflowId is null', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useWorkflowSSE(null), { wrapper });

    // Should not be connected and have null workflow
    expect(result.current.isConnected).toBe(false);
    expect(result.current.workflow).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('handles SSE connection errors', async () => {
    // Mock console.warn to suppress expected warnings
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    const wrapper = createWrapper();
    const { result } = renderHook(() => useWorkflowSSE('wf-error'), { wrapper });

    // Wait for connection state (it may error)
    await waitFor(() => {
      // Either connected or errored
      return result.current.isConnected === true || result.current.error !== null;
    }, { timeout: 3000 });

    consoleSpy.mockRestore();
  });
});

describe('useCreateWorkflow', () => {
  it('creates workflow successfully', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateWorkflow(), { wrapper });

    // Mutate to create workflow
    result.current.mutate({ name: 'Test Workflow', type: 'analysis' });

    // Wait for settled state: not pending AND success in same assertion block
    await waitFor(() => {
      expect(result.current.isPending).toBe(false);
      expect(result.current.isSuccess).toBe(true);
    });
    expect(result.current.data).toBeDefined();
  });

  it('handles creation error', async () => {
    server.use(
      http.post('/api/v1/agents/workflows', () => {
        return HttpResponse.json({ error: 'Invalid workflow type' }, { status: 400 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateWorkflow(), { wrapper });

    result.current.mutate({ name: 'Bad Workflow', type: 'invalid_type' });

    // Wait for settled state: not pending AND error in same assertion block
    await waitFor(() => {
      expect(result.current.isPending).toBe(false);
      expect(result.current.isError).toBe(true);
    });
  });
});

describe('useCancelWorkflow', () => {
  it('cancels workflow successfully', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCancelWorkflow(), { wrapper });

    result.current.mutate('wf-1');

    // Wait for settled state: not pending AND success in same assertion block
    await waitFor(() => {
      expect(result.current.isPending).toBe(false);
      expect(result.current.isSuccess).toBe(true);
    });
  });

  it('handles cancellation error', async () => {
    server.use(
      http.delete('/api/v1/agents/workflows/:id', () => {
        return HttpResponse.json({ error: 'Workflow not found' }, { status: 404 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useCancelWorkflow(), { wrapper });

    result.current.mutate('non-existent-wf');

    // Wait for settled state: not pending AND error in same assertion block
    await waitFor(() => {
      expect(result.current.isPending).toBe(false);
      expect(result.current.isError).toBe(true);
    });
  });
});
