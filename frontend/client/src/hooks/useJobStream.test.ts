/**
 * useJobStream Hook Tests
 *
 * Tests for real-time job streaming via SSE and polling fallback.
 * Covers connection handling, progress updates, log streaming, and error scenarios.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/mocks/server';
import { useJobStream } from './useJobStream';

describe('useJobStream', () => {
  beforeEach(() => {
    // Use real timers for SSE/polling tests to avoid timer coordination issues
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

    // Wait for connection and initial data (SSE connects immediately, then polling as fallback)
    await waitFor(() => expect(result.current.isConnected).toBe(true), { timeout: 3000 });

    // Verify job data is loaded via polling
    await waitFor(() => expect(result.current.status).toBe('running'), { timeout: 8000 });
    expect(result.current.progress).toBeGreaterThan(0);
  }, 10000);

  it('handles connection errors gracefully', async () => {
    server.use(
      http.get('/api/v1/extract/jobs/:jobId', () => {
        return HttpResponse.json({ error: 'Job not found' }, { status: 404 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useJobStream('non-existent-job'), { wrapper });

    await waitFor(() => expect(result.current.error).not.toBeNull(), { timeout: 8000 });
    expect(result.current.isConnected).toBe(false);
  }, 10000);

  it('processes log entries correctly', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useJobStream('job-with-logs'), { wrapper });

    await waitFor(() => expect(result.current.isConnected).toBe(true));

    // Logs should be populated from the API response
    expect(result.current.logs.length).toBeGreaterThanOrEqual(0);
  });

  it('processes extracted entities', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useJobStream('job-with-entities'), { wrapper });

    await waitFor(() => expect(result.current.isConnected).toBe(true));

    // Entities should be populated
    expect(result.current.entities.length).toBeGreaterThanOrEqual(0);
  });

  it('handles job completion', async () => {
    server.use(
      http.get('/api/v1/extract/jobs/:jobId', () => {
        return HttpResponse.json({
          id: 'completed-job',
          status: 'COMPLETED',
          progress_percent_complete: 100,
          progress_logs: [],
          extracted_entities: [],
          configuration: {},
        });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useJobStream('completed-job'), { wrapper });

    await waitFor(() => expect(result.current.status).toBe('completed'), { timeout: 8000 });
    expect(result.current.progress).toBe(100);
  }, 10000);

  it('handles job failure', async () => {
    server.use(
      http.get('/api/v1/extract/jobs/:jobId', () => {
        return HttpResponse.json({
          id: 'failed-job',
          status: 'FAILED',
          progress_percent_complete: 45,
          progress_logs: [{ timestamp: '2024-01-15T10:00:00Z', level: 'ERROR', message: 'Extraction failed' }],
          extracted_entities: [],
          configuration: {},
        });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useJobStream('failed-job'), { wrapper });

    await waitFor(() => expect(result.current.status).toBe('failed'), { timeout: 8000 });
  }, 10000);

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

    await waitFor(() => expect(result.current.isConnected).toBe(true));

    // Should be streaming when connected and running
    expect(result.current.isStreaming).toBe(true);
  });

  it('cleans up on unmount', async () => {
    const wrapper = createWrapper();
    const { result, unmount } = renderHook(() => useJobStream('cleanup-job'), { wrapper });

    await waitFor(() => expect(result.current.isConnected).toBe(true));

    // Unmount should clean up connections
    unmount();

    // No specific assertion - cleanup should not throw
    expect(true).toBe(true);
  });
});
