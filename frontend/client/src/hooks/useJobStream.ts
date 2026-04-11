/**
 * useJobStream.ts - Server-Sent Events hook for extraction job streaming
 * 
 * Provides real-time updates for extraction jobs from L2 API.
 * Falls back to polling if SSE is not available.
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { apiClient } from '@/api/client';

export interface JobStreamEvent {
  type: 'progress' | 'status' | 'log' | 'entity' | 'complete' | 'error';
  timestamp: string;
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

const SSE_TIMEOUT_MS = 30 * 1000;
const POLL_INTERVAL_MS = 2000;

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
    if (!jobId) return;
    
    try {
      const response = await apiClient.get('l2', `/extract/status/${jobId}`);
      const job = response.data;
      
      setState(prev => ({
        progress: job.progress_percent_complete ?? prev.progress,
        status: mapJobStatus(job.status),
        logs: job.progress_logs?.map((log: any) => ({
          timestamp: log.timestamp,
          level: log.level,
          message: log.message,
        })) ?? prev.logs,
        entities: job.extracted_entities?.map((e: any) => ({
          type: e.type,
          name: e.name,
        })) ?? prev.entities,
      }));
      
      setError(null);
      
      // Stop polling if job is complete
      if (['COMPLETED', 'FAILED', 'CANCELLED'].includes(job.status)) {
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
      const baseUrl = import.meta.env.VITE_API_BASE || '/api/v1';
      const l2Prefix = import.meta.env.VITE_L2_PREFIX || '/extract';
      const url = `${baseUrl}${l2Prefix}/jobs/${jobId}/events`;

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
      }, SSE_TIMEOUT_MS);

      es.onmessage = (event) => {
        try {
          // Clear timeout on any valid message to keep connection alive
          if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
            timeoutRef.current = null;
          }

          const data = JSON.parse(event.data) as JobStreamEvent;

          setState(prev => {
            switch (data.type) {
              case 'progress':
                return { ...prev, progress: data.data as number };
              case 'status':
                return { ...prev, status: mapJobStatus(data.data as string) };
              case 'log':
                return { ...prev, logs: [...prev.logs, data.data as JobStreamState['logs'][0]] };
              case 'entity':
                return { ...prev, entities: [...prev.entities, data.data as JobStreamState['entities'][0]] };
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
        } catch {
          // Ignore invalid JSON
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
      // Immediate first poll
      pollJobStatus();
      // Set up interval polling
      pollIntervalRef.current = setInterval(pollJobStatus, POLL_INTERVAL_MS);
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
