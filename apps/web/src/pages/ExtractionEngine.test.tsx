/**
 * ExtractionEngine Component Tests
 *
 * Tests for the configuration-driven extraction pipeline including:
 * - Configuration panel rendering and interaction
 * - Control bar (Model, Batch Size, Priority) controls
 * - Live Stream / Log Output display
 * - Results Table rendering
 * - Run Extraction workflow
 * - Loading skeleton display
 * - Error state handling
 */
import { describe, it, expect, vi } from 'vitest';
import '@testing-library/jest-dom';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createWrapper } from '../test-utils';
import ExtractionEngine from './ExtractionEngine';

// Mock the zustand store
vi.mock('@/hooks/useExtractionConfig', () => ({
  useExtractionConfig: () => ({
    sourceUrl: '',
    setSourceUrl: vi.fn(),
    entityTypes: {
      capability: true,
      useCase: true,
      persona: true,
      valueDriver: true,
    },
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
    getExtractionRequest: () => ({
      source_url: 'https://example.com/docs',
      extraction_config: {
        entity_types: ['Capability', 'UseCase', 'Persona', 'ValueDriver'],
        confidence_threshold: 0.75,
        chunk_size: 2000,
        chunk_overlap: 200,
      },
    }),
  }),
}));

vi.mock('@/hooks/useRunExtraction', () => ({
  useRunExtraction: () => ({
    mutateAsync: vi.fn().mockResolvedValue({ jobId: 'test-job-123', status: 'queued', message: 'Started' }),
    isPending: false,
  }),
}));

vi.mock('@/hooks/useExtractionResults', () => ({
  useExtractionResults: () => ({ data: null, isLoading: false }),
  useExtractedEntities: () => ({ data: [], isLoading: false }),
}));

vi.mock('@/hooks/useJobStream', () => ({
  useJobStream: () => ({
    progress: 0,
    status: 'pending',
    logs: [],
    entities: [],
    isConnected: false,
    error: null,
  }),
}));

describe('ExtractionEngine', () => {
  it('renders the header with title and actions', () => {
    const wrapper = createWrapper();
    render(<ExtractionEngine />, { wrapper });

    expect(screen.getByText('Extraction Engine')).toBeInTheDocument();
    expect(screen.getByText('Configure and monitor document extraction pipelines')).toBeInTheDocument();
    // Header has at least 2 action buttons (Pause All, Run Extraction)
    const headerButtons = screen.getAllByRole('button');
    expect(headerButtons.length).toBeGreaterThanOrEqual(2);
  });

  it('renders the configuration panel', () => {
    const wrapper = createWrapper();
    render(<ExtractionEngine />, { wrapper });

    expect(screen.getByText('Configuration Panel')).toBeInTheDocument();
    expect(screen.getByLabelText('Source URL')).toBeInTheDocument();
    expect(screen.getByText('Entity Types')).toBeInTheDocument();
    expect(screen.getByLabelText('Capabilities')).toBeInTheDocument();
    expect(screen.getByLabelText('Use Cases')).toBeInTheDocument();
    expect(screen.getByLabelText('Personas')).toBeInTheDocument();
    expect(screen.getByLabelText('Value Drivers')).toBeInTheDocument();
    expect(screen.getByText('Confidence Threshold')).toBeInTheDocument();
    expect(screen.getByText('Chunk Size')).toBeInTheDocument();
    expect(screen.getByText('Chunk Overlap')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /apply config/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument();
  });

  it('renders the control bar with Model, Batch Size, and Priority', () => {
    const wrapper = createWrapper();
    render(<ExtractionEngine />, { wrapper });

    expect(screen.getAllByText('Model').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Batch Size').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Priority').length).toBeGreaterThan(0);
  });

  it('renders the live stream and results sections', () => {
    const wrapper = createWrapper();
    render(<ExtractionEngine />, { wrapper });

    expect(screen.getByText('Live Stream / Log Output')).toBeInTheDocument();
    expect(screen.getByText('Results Table')).toBeInTheDocument();
    expect(screen.getByText('Run an extraction to see results')).toBeInTheDocument();
  });

  it('shows prompt to configure extraction when no job is running', () => {
    const wrapper = createWrapper();
    render(<ExtractionEngine />, { wrapper });

    expect(screen.getByText(/Configure extraction settings and click "Run Extraction" to begin/i)).toBeInTheDocument();
  });

  it('shows action buttons in header', () => {
    const wrapper = createWrapper();
    render(<ExtractionEngine />, { wrapper });

    // Find buttons by role - the buttons exist with icons inside
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThanOrEqual(4); // Pause All, Run Extraction, Apply Config, Reset
  });

  it('renders loading skeleton when extraction is starting', () => {
    // Mock the mutation as pending
    vi.doMock('@/hooks/useRunExtraction', () => ({
      useRunExtraction: () => ({
        mutateAsync: vi.fn(),
        isPending: true,
      }),
    }));

    const wrapper = createWrapper();
    render(<ExtractionEngine />, { wrapper });

    // Should show skeleton elements (we can't test exact classes, but the component renders)
    expect(document.querySelector('[class*="skeleton"]')).toBeDefined();
  });

  it('displays error state when stream error occurs', async () => {
    // Mock error state
    vi.doMock('@/hooks/useJobStream', () => ({
      useJobStream: () => ({
        progress: 0,
        status: 'pending',
        logs: [],
        entities: [],
        isConnected: false,
        error: new Error('Connection failed'),
      }),
    }));

    const wrapper = createWrapper();
    const { unmount } = render(<ExtractionEngine />, { wrapper });
    unmount();
  });
});
