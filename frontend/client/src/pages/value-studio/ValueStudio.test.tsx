/**
 * Value Studio — Stage Component Test Suite
 *
 * Tests all 6 stages of the Value Studio pipeline:
 * 1. Discovery — Account & context capture
 * 2. Mapping — Needs-to-capability alignment
 * 3. Modeling — Value chain construction
 * 4. Validation — Quality gates & issue resolution
 * 5. Narrative — Business case assembly
 * 6. Tracking — Milestones & realization
 */

import * as React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { createWrapper } from '../../test-utils';

// ── Stage Component Tests ─────────────────────────────────────────────────────

// Mock the shell for stage tests - simplified mock
vi.mock('./ValueStudioShell', () => ({
  __esModule: true,
  default: vi.fn(({ children }: { children: React.ReactNode }) => (
    <div data-testid="value-studio-shell">{children}</div>
  )),
  buildStages: vi.fn(() => []),
  DEMO_DEAL: {
    accountName: 'Acme Corp',
    dealType: 'Enterprise',
    arr: '$1M',
    crmStage: 'Stage 3',
  },
}));

// Stage 1: Discovery
describe('Stage1Discovery', () => {
  it('renders without crashing', async () => {
    const Stage1Discovery = (await import('./Stage1Discovery')).default;
    const wrapper = createWrapper();
    render(<Stage1Discovery />, { wrapper });

    await waitFor(() => {
      expect(screen.getByTestId('value-studio-shell')).toBeInTheDocument();
    });
  });
});

// Stage 2: Mapping
describe('Stage2Mapping', () => {
  it('renders without crashing', async () => {
    const Stage2Mapping = (await import('./Stage2Mapping')).default;
    const wrapper = createWrapper();
    render(<Stage2Mapping />, { wrapper });

    await waitFor(() => {
      expect(screen.getByTestId('value-studio-shell')).toBeInTheDocument();
    });
  });
});

// Stage 3: Modeling
describe('Stage3Modeling', () => {
  it('renders without crashing', async () => {
    const Stage3Modeling = (await import('./Stage3Modeling')).default;
    const wrapper = createWrapper();
    render(<Stage3Modeling />, { wrapper });

    await waitFor(() => {
      expect(screen.getByTestId('value-studio-shell')).toBeInTheDocument();
    });
  });
});

// Stage 4: Validation
describe('Stage4Validation', () => {
  it('renders without crashing', async () => {
    const Stage4Validation = (await import('./Stage4Validation')).default;
    const wrapper = createWrapper();
    render(<Stage4Validation />, { wrapper });

    await waitFor(() => {
      expect(screen.getByTestId('value-studio-shell')).toBeInTheDocument();
    });
  });
});

// Stage 5: Narrative
describe('Stage5Narrative', () => {
  it('renders without crashing', async () => {
    const Stage5Narrative = (await import('./Stage5Narrative')).default;
    const wrapper = createWrapper();
    render(<Stage5Narrative />, { wrapper });

    await waitFor(() => {
      expect(screen.getByTestId('value-studio-shell')).toBeInTheDocument();
    });
  });
});

// Stage 6: Tracking
describe('Stage6Tracking', () => {
  it('renders without crashing', async () => {
    const Stage6Tracking = (await import('./Stage6Tracking')).default;
    const wrapper = createWrapper();
    render(<Stage6Tracking />, { wrapper });

    await waitFor(() => {
      expect(screen.getByTestId('value-studio-shell')).toBeInTheDocument();
    });
  });
});
