/**
 * Admin Pages — Test Suite
 *
 * Tests for all admin governance pages:
 * - FormulaGovernance
 * - BenchmarkPolicies
 * - VariableRegistry
 * - PackManagement
 * - PermissionsAdmin
 * - PlatformSettings
 * - HealthMonitor
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { createWrapper } from '../../test-utils';

// Mock the hooks to avoid backend dependencies
vi.mock('@/hooks/useFormulas', () => ({
  useFormulas: () => ({
    data: {
      formulas: [
        { id: '1', formula_id: 'f-001', name: 'Test Formula', version: '1.0.0', status: 'active' },
      ],
      total: 1,
    },
    isLoading: false,
    error: null,
  }),
  useFormulaApprovals: () => ({
    data: [],
    isLoading: false,
    error: null,
  }),
}));

vi.mock('@/hooks/useBenchmarks', () => ({
  useBenchmarkPolicies: () => ({
    data: [],
    isLoading: false,
    error: null,
  }),
}));

vi.mock('@/hooks/useValuePacks', () => ({
  useValuePacks: () => ({
    data: [],
    isLoading: false,
    error: null,
  }),
}));

// FormulaGovernance
describe('FormulaGovernance', () => {
  it('renders without crashing', async () => {
    const FormulaGovernance = (await import('./FormulaGovernance')).default;
    const wrapper = createWrapper();
    render(<FormulaGovernance />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Formula Governance')).toBeInTheDocument();
    });
  });
});

// BenchmarkPolicies
describe('BenchmarkPolicies', () => {
  it('renders without crashing', async () => {
    const BenchmarkPolicies = (await import('./BenchmarkPolicies')).default;
    const wrapper = createWrapper();
    render(<BenchmarkPolicies />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Benchmark Policies')).toBeInTheDocument();
    });
  });
});

// VariableRegistry
describe('VariableRegistry', () => {
  it('renders without crashing', async () => {
    const VariableRegistry = (await import('./VariableRegistry')).default;
    const wrapper = createWrapper();
    render(<VariableRegistry />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Variable Registry')).toBeInTheDocument();
    });
  });
});

// PackManagement
describe('PackManagement', () => {
  it('renders without crashing', async () => {
    const PackManagement = (await import('./PackManagement')).default;
    const wrapper = createWrapper();
    render(<PackManagement />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Pack Management')).toBeInTheDocument();
    });
  });
});

// PermissionsAdmin
describe('PermissionsAdmin', () => {
  it('renders without crashing', async () => {
    const PermissionsAdmin = (await import('./PermissionsAdmin')).default;
    const wrapper = createWrapper();
    render(<PermissionsAdmin />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Permissions')).toBeInTheDocument();
    });
  });
});

// PlatformSettings
describe('PlatformSettings', () => {
  it('renders without crashing', async () => {
    const PlatformSettings = (await import('./PlatformSettings')).default;
    const wrapper = createWrapper();
    render(<PlatformSettings />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Platform Settings')).toBeInTheDocument();
    });
  });
});

// HealthMonitor
describe('HealthMonitor', () => {
  it('renders without crashing', async () => {
    const HealthMonitor = (await import('./HealthMonitor')).default;
    const wrapper = createWrapper();
    render(<HealthMonitor />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Health Monitor')).toBeInTheDocument();
    });
  });
});
