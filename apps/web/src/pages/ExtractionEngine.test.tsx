import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import '@testing-library/jest-dom';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createWrapper } from '../test-utils';
import { toast } from 'sonner';
import ExtractionEngine from './ExtractionEngine';

const mockRun = vi.fn();
const mockPauseAll = vi.fn();

let streamStatus: 'pending' | 'running' | 'completed' = 'pending';
let pausePending = false;

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

vi.mock('@/hooks/useExtractionConfig', () => ({
  useExtractionConfig: () => ({
    sourceUrl: 'https://example.com/docs',
    setSourceUrl: vi.fn(),
    entityTypes: { capability: true, useCase: true, persona: true, valueDriver: true },
    setEntityType: vi.fn(),
    confidenceThreshold: 0.75,
    setConfidenceThreshold: vi.fn(),
    chunkSize: 2000,
    setChunkSize: vi.fn(),
    chunkOverlap: 200,
    setChunkOverlap: vi.fn(),
    model: 'gpt-4o',
    setModel: vi.fn(),
    batchSize: 10,
    setBatchSize: vi.fn(),
    priority: 'normal',
    setPriority: vi.fn(),
    resetToDefaults: vi.fn(),
    getExtractionRequest: () => ({ source_url: 'https://example.com/docs', extraction_config: { entity_types: ['Capability'], confidence_threshold: 0.75, chunk_size: 2000, chunk_overlap: 200 } }),
  }),
}));

vi.mock('@/hooks/useRunExtraction', () => ({
  useRunExtraction: () => ({ mutateAsync: mockRun, isPending: false }),
}));

vi.mock('@/hooks/usePauseAllExtractions', () => ({
  usePauseAllExtractions: () => ({ mutateAsync: mockPauseAll, isPending: pausePending }),
}));

vi.mock('@/hooks/useExtractionResults', () => ({
  useExtractionResults: () => ({ data: null, isLoading: false }),
  useExtractedEntities: () => ({ data: [], isLoading: false }),
}));

vi.mock('@/hooks/useJobStream', () => ({
  useJobStream: () => ({ progress: 0, status: streamStatus, logs: [], entities: [], isConnected: false, error: null }),
}));

const originalEnv = import.meta.env.VITE_ENABLE_EXTRACTION_PAUSE_ALL;

describe('ExtractionEngine Pause All', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    streamStatus = 'pending';
    pausePending = false;
  });

  it('hides pause button when feature flag is disabled', () => {
    import.meta.env.VITE_ENABLE_EXTRACTION_PAUSE_ALL = 'false';
    render(<ExtractionEngine />, { wrapper: createWrapper() });
    expect(screen.queryByRole('button', { name: /pause all/i })).not.toBeInTheDocument();
  });

  it('shows disabled pause button when not running', () => {
    import.meta.env.VITE_ENABLE_EXTRACTION_PAUSE_ALL = 'true';
    streamStatus = 'completed';
    render(<ExtractionEngine />, { wrapper: createWrapper() });
    expect(screen.getByRole('button', { name: /pause all/i })).toBeDisabled();
  });

  it('invokes pause mutation when running', async () => {
    import.meta.env.VITE_ENABLE_EXTRACTION_PAUSE_ALL = 'true';
    streamStatus = 'running';
    mockPauseAll.mockResolvedValueOnce({ message: 'Paused jobs' });

    render(<ExtractionEngine />, { wrapper: createWrapper() });
    await userEvent.click(screen.getByRole('button', { name: /pause all/i }));

    await waitFor(() => expect(mockPauseAll).toHaveBeenCalledTimes(1));
    expect(toast.success).toHaveBeenCalledWith('Paused jobs');
  });

  it('shows error toast when pause fails', async () => {
    import.meta.env.VITE_ENABLE_EXTRACTION_PAUSE_ALL = 'true';
    streamStatus = 'running';
    mockPauseAll.mockRejectedValueOnce(new Error('Pause failed'));

    render(<ExtractionEngine />, { wrapper: createWrapper() });
    await userEvent.click(screen.getByRole('button', { name: /pause all/i }));

    await waitFor(() => expect(toast.error).toHaveBeenCalledWith('Pause failed'));
  });
});

afterAll(() => {
  import.meta.env.VITE_ENABLE_EXTRACTION_PAUSE_ALL = originalEnv;
});
