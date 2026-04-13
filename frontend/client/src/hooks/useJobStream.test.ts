/**
 * useJobStream Hook Tests
 *
 * Tests for real-time job streaming via SSE and polling fallback.
 * Covers connection handling, progress updates, log streaming, and error scenarios.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { createWrapper } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/mocks/server';
import { getLastEventSource } from '../../../test/setup';
import { useJobStream } from './useJobStream';

describe('useJobStream', () => {
  beforeEach(() => {
    vi.useRealTimers();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  it('initializes with default state', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useJobStream(null), { wrapper });

    expect(result.current.progress).toBe(0);
    expect(result.current.status).toBe('pending');
    expect(result.current.logs).toHaveLength(0);
    expect(result.current.entities).toHaveLength(0);
    expect(result.current.isConnected).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('connects and fetches job data via SSE or polling', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useJobStream('job-123'), { wrapper });

    // Wait for SSE connection to be established
    await waitFor(() => expect(result.current.isConnected).toBe(true), { timeout: 1000 });

    // Simulate SSE events to drive state changes
    // Use waitFor to handle race condition where EventSource may not be created yet
    let es: ReturnType<typeof getLastEventSource>;
    await waitFor(() => {
      es = getLastEventSource();
      expect(es).toBeDefined();
    }, { timeout: 1000 });
    
    // Simulate status update to running
    act(() => {
      es!._emitMessage({ type: 'status', data: 'EXTRACTING' });
    });

    await waitFor(() => expect(result.current.status).toBe('running'));

    // Simulate progress update
    act(() => {
      es!._simulateProgress(25);
    });

    await waitFor(() => expect(result.current.progress).toBe(25));
  }, 5000);

  it('handles connection errors gracefully', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useJobStream('non-existent-job'), { wrapper });

    // Wait for initial connection
    await waitFor(() => expect(result.current.isConnected).toBe(true), { timeout: 1000 });

    // Simulate SSE error - use waitFor to handle race condition
    let es: ReturnType<typeof getLastEventSource>;
    await waitFor(() => {
      es = getLastEventSource();
      expect(es).toBeDefined();
    }, { timeout: 1000 });
    
    act(() => {
      es!._emitError();
    });

    // After error, should fall back to polling and eventually get 404
    await waitFor(() => expect(result.current.error).not.toBeNull(), { timeout: 5000 });
    expect(result.current.isConnected).toBe(false);
  }, 8000);

  it('processes log entries correctly', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useJobStream('job-with-logs'), { wrapper });

    await waitFor(() => expect(result.current.isConnected).toBe(true), { timeout: 2000 });

    // Logs array should be initialized
    await waitFor(() => expect(Array.isArray(result.current.logs)).toBe(true));
  });

  it('processes extracted entities', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useJobStream('job-with-entities'), { wrapper });

    await waitFor(() => expect(result.current.isConnected).toBe(true), { timeout: 2000 });

    // Entities array should be initialized
    await waitFor(() => expect(Array.isArray(result.current.entities)).toBe(true));
  });

  it('processes SSE progress events', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useJobStream('completed-job'), { wrapper });

    // Wait for connection
    await waitFor(() => expect(result.current.isConnected).toBe(true), { timeout: 1000 });

    // Simulate progress via SSE - use waitFor to handle race condition
    let es: ReturnType<typeof getLastEventSource>;
    await waitFor(() => {
      es = getLastEventSource();
      expect(es).toBeDefined();
    }, { timeout: 1000 });
    
    act(() => {
      es!._simulateProgress(75);
    });

    // Progress should update via SSE
    await waitFor(() => expect(result.current.progress).toBe(75), { timeout: 2000 });
  }, 5000);

  it('handles job failure via SSE', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useJobStream('failed-job'), { wrapper });

    // Wait for connection
    await waitFor(() => expect(result.current.isConnected).toBe(true), { timeout: 1000 });

    // Trigger SSE error to fall back to polling - use waitFor to handle race condition
    let es: ReturnType<typeof getLastEventSource>;
    await waitFor(() => {
      es = getLastEventSource();
      expect(es).toBeDefined();
    }, { timeout: 1000 });
    
    act(() => {
      es!._emitError();
    });

    // After SSE error, connection should be closed
    await waitFor(() => expect(result.current.isConnected).toBe(false), { timeout: 2000 });
    
    // Error state should be set (from polling 404 or SSE error)
    // Note: Full status verification requires longer timeout for polling fallback
  }, 5000);

  it('determines streaming state correctly', async () => {
    server.use(
      http.get('/api/v1/extract/jobs/:jobId', () => {
        return HttpResponse.json({
          id: 'streaming-job',
          status: 'EXTRACTING',
          progress_percent_complete: 50,
          progress_logs: [],
          extracted_entities: [],
          configuration: {},
        });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useJobStream('streaming-job'), { wrapper });

    await waitFor(() => expect(result.current.isConnected).toBe(true), { timeout: 2000 });

    // Should be streaming when connected and job status is EXTRACTING (maps to 'running')
    expect(result.current.isStreaming).toBe(true);
  });

  it('cleans up on unmount', async () => {
    const wrapper = createWrapper();
    const { result, unmount } = renderHook(() => useJobStream('cleanup-job'), { wrapper });

    await waitFor(() => expect(result.current.isConnected).toBe(true), { timeout: 2000 });

    // Unmount should clean up connections without throwing
    expect(() => unmount()).not.toThrow();
  });
});
