/**
 * useJobStream.ts - Server-Sent Events hook for extraction job streaming
 * 
 * Provides real-time updates for extraction jobs from L2 API.
 * Falls back to polling if SSE is not available.
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { apiClient } from '@/api/client';
import { SSEBuilders, SSE_TIMEOUT_MS as SHARED_SSE_TIMEOUT_MS } from './useSSEUtils';
import { parseExtractionJob } from '@/types/api';
import { POLL_INTERVALS } from './usePolling';

export interface JobStreamEvent {
  type: 'progress' | 'status' | 'log' | 'entity' | 'complete' | 'error';
  timestamp?: string;
  data: unknown;
}

export interface JobStreamState {
  progress: number;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  logs: Array<{
    timestamp: string;
    level: string;
    message: string;
  }>;
  entities: Array<{
    type: string;
    name: string;
  }>;
}


function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function parseJobStreamEvent(eventPayload: unknown): JobStreamEvent | null {
  if (!isRecord(eventPayload)) return null;
  if (typeof eventPayload.type !== 'string') return null;
  return {
    type: eventPayload.type as JobStreamEvent['type'],
    timestamp: typeof eventPayload.timestamp === 'string' ? eventPayload.timestamp : undefined,
    data: eventPayload.data,
  };
}

/**
 * Subscribe to real-time job updates via SSE or polling fallback.
 * 
 * @param jobId - The extraction job ID to stream
 * @returns Job stream state and connection status
 */
export function useJobStream(jobId: string | null) {
  const [state, setState] = useState<JobStreamState>({
    progress: 0,
    status: 'pending',
    logs: [],
    entities: [],
  });
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const sseSupportedRef = useRef<boolean | null>(null);

  // Polling fallback when SSE is not available
  const pollJobStatus = useCallback(async () => {
    // Guard against stale callback executing after cleanup
    const currentJobId = jobId;
    if (!currentJobId) return;

    try {
      const response = await apiClient.get('l2', `/jobs/${currentJobId}`);
      const job = parseExtractionJob(response.data);
      
      setState(prev => ({
        progress: job.progress_percent_complete ?? prev.progress,
        status: mapJobStatus(job.status || ''),
        logs: (job.progress_logs || []).map((log) => ({
          timestamp: log.timestamp || '',
          level: log.level || 'INFO',
          message: log.message || '',
        })),
        entities: (job.extracted_entities || []).map((entity) => ({
          type: entity.type || 'unknown',
          name: entity.name || 'Unknown',
        })),
      }));
      
      setError(null);
      
      // Stop polling if job is complete
      if (['COMPLETED', 'FAILED', 'CANCELLED'].includes(job.status || '')) {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch job status'));
    }
  }, [jobId]);

  useEffect(() => {
    if (!jobId) {
      setState({ progress: 0, status: 'pending', logs: [], entities: [] });
      setIsConnected(false);
      setError(null);
      return;
    }

    // Try SSE first, fall back to polling
    const trySseConnection = () => {
      const url = SSEBuilders.l2(`/jobs/${jobId}/events`);

      // Close any existing connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      const es = new EventSource(url);
      eventSourceRef.current = es;
      setIsConnected(true);
      setError(null);

      // Set up timeout
      timeoutRef.current = setTimeout(() => {
        if (eventSourceRef.current === es) {
          es.close();
          eventSourceRef.current = null;
          sseSupportedRef.current = false;
          setIsConnected(false);
          // Fall back to polling
          startPolling();
        }
      }, SHARED_SSE_TIMEOUT_MS);

      es.onmessage = (event) => {
        try {
          // Clear timeout on any valid message to keep connection alive
          if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
            timeoutRef.current = null;
          }

          const parsed = parseJobStreamEvent(JSON.parse(event.data));
          if (!parsed) return;

          setState(prev => {
            switch (parsed.type) {
              case 'progress':
                return { ...prev, progress: typeof parsed.data === 'number' ? parsed.data : prev.progress };
              case 'status':
                return { ...prev, status: mapJobStatus(typeof parsed.data === 'string' ? parsed.data : '') };
              case 'log':
                if (!isRecord(parsed.data)) return prev;
                return {
                  ...prev,
                  logs: [
                    ...prev.logs,
                    {
                      timestamp: typeof parsed.data.timestamp === 'string' ? parsed.data.timestamp : '',
                      level: typeof parsed.data.level === 'string' ? parsed.data.level : 'INFO',
                      message: typeof parsed.data.message === 'string' ? parsed.data.message : '',
                    },
                  ],
                };
              case 'entity':
                if (!isRecord(parsed.data)) return prev;
                return {
                  ...prev,
                  entities: [
                    ...prev.entities,
                    {
                      type: typeof parsed.data.type === 'string' ? parsed.data.type : 'unknown',
                      name: typeof parsed.data.name === 'string' ? parsed.data.name : 'Unknown',
                    },
                  ],
                };
              case 'complete':
              case 'error':
                // Stop on completion or error
                if (timeoutRef.current) clearTimeout(timeoutRef.current);
                es.close();
                return prev;
              default:
                return prev;
            }
          });
        } catch (err) {
          // Log parse errors for debugging but don't break the connection
          console.warn('[useJobStream] Failed to parse SSE message:', err);
        }
      };

      es.onerror = () => {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        if (eventSourceRef.current === es) {
          setIsConnected(false);
          sseSupportedRef.current = false;
          // Fall back to polling
          startPolling();
        }
        es.close();
      };
    };

    const startPolling = () => {
      // Guard against duplicate polling intervals
      if (pollIntervalRef.current) return;
      // Immediate first poll
      pollJobStatus();
      // Set up interval polling
      pollIntervalRef.current = setInterval(pollJobStatus, POLL_INTERVALS.jobStream);
    };

    // Start with SSE, will fall back to polling if SSE fails
    try {
      trySseConnection();
    } catch {
      // SSE not supported, use polling
      startPolling();
    }

    // Cleanup
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      // Reset SSE support flag for next job
      sseSupportedRef.current = null;
    };
  }, [jobId, pollJobStatus]);

  return {
    ...state,
    isConnected,
    error,
    isStreaming: isConnected && ['pending', 'running'].includes(state.status),
  };
}

function mapJobStatus(status: string): JobStreamState['status'] {
  const statusMap: Record<string, JobStreamState['status']> = {
    'PENDING': 'pending',
    'QUEUED': 'pending',
    'VALIDATING': 'running',
    'BROWSER_ACQUIRING': 'running',
    'NAVIGATING': 'running',
    'EXTRACTING': 'running',
    'TRANSFORMING': 'running',
    'STORING': 'running',
    'COMPLETED': 'completed',
    'FAILED': 'failed',
    'CANCELLED': 'cancelled',
    'PARTIAL_SUCCESS': 'completed',
  };
  return statusMap[status] || 'pending';
}
