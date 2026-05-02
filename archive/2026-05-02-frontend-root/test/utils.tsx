/**
 * Test Utilities for React Testing Library + React Query
 */
import { renderHook, type RenderHookOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';

/**
 * Creates a test QueryClient with disabled retries and immediate garbage collection
 */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

/**
 * Wraps children with QueryClientProvider for hook testing
 */
export function createWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

/**
 * Renders a hook with React Query context
 */
export function renderHookWithQuery<TProps, TResult>(
  hook: (props: TProps) => TResult,
  options?: RenderHookOptions<TProps>
) {
  const queryClient = createTestQueryClient();
  return renderHook(hook, {
    wrapper: createWrapper(queryClient),
    ...options,
  });
}
