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
import { createWrapper, renderWithRouter } from '../../test-utils';

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

vi.mock('@/hooks/useGovernance', () => ({
  useUsers: () => ({
    data: [
      {
        id: 'u-1',
        email: 'admin@example.com',
        display_name: 'Admin User',
        role: 'tenant_admin',
        status: 'active',
        tenant_id: 't-1',
        created_at: '2026-01-01T00:00:00Z',
        last_login_at: '2026-01-02T00:00:00Z',
      },
    ],
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useApiKeys: () => ({
    data: [
      {
        id: 'k-1',
        name: 'Primary Key',
        prefix: 'pk_live_',
        tenant_id: 't-1',
        is_enabled: true,
        created_at: '2026-01-01T00:00:00Z',
        last_used_at: '2026-01-03T00:00:00Z',
      },
    ],
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useRevokeApiKey: () => ({
    mutate: vi.fn(),
    isPending: false,
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
      expect(screen.getByText('Permissions & Access')).toBeInTheDocument();
    });
  });

  it('sets API Keys as the active tab for /settings/access/keys', async () => {
    const PermissionsAdmin = (await import('./PermissionsAdmin')).default;
    renderWithRouter(<PermissionsAdmin />, { path: '/settings/access/keys' });

    await waitFor(() => {
      const apiKeysTab = screen.getByRole('button', { name: /api keys/i });
      const usersTab = screen.getByRole('button', { name: /users/i });
      expect(apiKeysTab).toHaveClass('text-blue-700');
      expect(usersTab).not.toHaveClass('text-blue-700');
    });
  });

  it('keeps Users as the active tab for /settings/access/roles', async () => {
    const PermissionsAdmin = (await import('./PermissionsAdmin')).default;
    renderWithRouter(<PermissionsAdmin />, { path: '/settings/access/roles' });

    await waitFor(() => {
      const usersTab = screen.getByRole('button', { name: /users/i });
      const apiKeysTab = screen.getByRole('button', { name: /api keys/i });
      expect(usersTab).toHaveClass('text-blue-700');
      expect(apiKeysTab).not.toHaveClass('text-blue-700');
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
