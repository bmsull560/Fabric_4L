/**
 * useFormulaDependents Hook Tests
 *
 * Tests for formula dependency tracking:
 * - useFormulaDependents: Fetch assets that depend on this formula
 * - useFormulaDependencies: Fetch formulas this formula depends on
 */
import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/mocks/server';
import {
  useFormulaDependents,
  useFormulaDependencies,
  type FormulaDependency,
  type DependentAsset,
} from './useFormulaDependents';

const mockIncomingDeps: FormulaDependency[] = [
  {
    source_formula_id: 'formula-child-1',
    target_formula_id: 'formula-parent',
    dependency_type: 'uses',
  },
  {
    source_formula_id: 'formula-child-2',
    target_formula_id: 'formula-parent',
    dependency_type: 'uses',
  },
  {
    source_formula_id: 'business-case-1',
    target_formula_id: 'formula-parent',
    dependency_type: 'references',
  },
];

const mockOutgoingDeps: FormulaDependency[] = [
  {
    source_formula_id: 'formula-parent',
    target_formula_id: 'formula-base-1',
    dependency_type: 'uses',
  },
  {
    source_formula_id: 'formula-parent',
    target_formula_id: 'formula-base-2',
    dependency_type: 'extends',
  },
  {
    source_formula_id: 'formula-child',
    target_formula_id: 'formula-parent',
    dependency_type: 'uses',
  },
  {
    source_formula_id: 'formula-child',
    target_formula_id: 'formula-helper',
    dependency_type: 'extends',
  },
];

describe('useFormulaDependents', () => {
  it('fetches formulas that depend on this formula', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/formula-parent/dependencies', ({ request }) => {
        const url = new URL(request.url);
        const direction = url.searchParams.get('direction');
        if (direction === 'incoming' || direction === 'both') {
          return HttpResponse.json(mockIncomingDeps.filter(d => 
            d.target_formula_id === 'formula-parent'
          ));
        }
        return HttpResponse.json([]);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaDependents('formula-parent'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(3);
    expect(result.current.data?.[0].type).toBe('Formula');
  });

  it('handles formula with no dependents', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/isolated-formula/dependencies', () => {
        return HttpResponse.json([]);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaDependents('isolated-formula'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([]);
  });

  it('does not fetch when formulaId is null', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaDependents(null), { wrapper });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isSuccess).toBe(false);
    expect(result.current.data).toBeUndefined();
  });

  it('handles different dependency types', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/formula-parent/dependencies', () => {
        return HttpResponse.json([
          { source_formula_id: 'child-1', target_formula_id: 'formula-parent', dependency_type: 'uses' },
          { source_formula_id: 'child-2', target_formula_id: 'formula-parent', dependency_type: 'extends' },
          { source_formula_id: 'child-3', target_formula_id: 'formula-parent', dependency_type: 'references' },
        ]);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaDependents('formula-parent'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const types = result.current.data?.map((d: DependentAsset) => d.dependency_type);
    expect(types).toContain('uses');
    expect(types).toContain('extends');
    expect(types).toContain('references');
  });

  it('handles error fetching dependents', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/invalid-id/dependencies', () => {
        return HttpResponse.json(
          { error: 'Formula not found' },
          { status: 404 }
        );
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaDependents('invalid-id'), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.statusCode).toBe(404);
  });
});

describe('useFormulaDependencies', () => {
  it('fetches formulas this formula depends on', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/formula-child/dependencies', ({ request }) => {
        const url = new URL(request.url);
        const direction = url.searchParams.get('direction');
        if (direction === 'outgoing' || direction === 'both') {
          return HttpResponse.json(mockOutgoingDeps.filter(d => 
            d.source_formula_id === 'formula-child'
          ));
        }
        return HttpResponse.json([]);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaDependencies('formula-child'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(2);
    expect(result.current.data?.[0].type).toBe('Formula');
  });

  it('handles formula with no dependencies', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/base-formula/dependencies', () => {
        return HttpResponse.json([]);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaDependencies('base-formula'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([]);
  });

  it('does not fetch when formulaId is null', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaDependencies(null), { wrapper });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isSuccess).toBe(false);
    expect(result.current.data).toBeUndefined();
  });

  it('identifies dependency chain', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/formula-a/dependencies', () => {
        return HttpResponse.json([
          { source_formula_id: 'formula-a', target_formula_id: 'formula-b', dependency_type: 'uses' },
          { source_formula_id: 'formula-a', target_formula_id: 'formula-c', dependency_type: 'uses' },
        ]);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaDependencies('formula-a'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const targetIds = result.current.data?.map((d: DependentAsset) => d.id);
    expect(targetIds).toContain('formula-b');
    expect(targetIds).toContain('formula-c');
  });

  it('handles error fetching dependencies', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/error-formula/dependencies', () => {
        return HttpResponse.json(
          { error: 'Failed to fetch dependencies' },
          { status: 500 }
        );
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaDependencies('error-formula'), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.statusCode).toBe(500);
  });
});
