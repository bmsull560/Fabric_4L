import { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Router } from "wouter";

export const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

export function createWrapper() {
  return function Wrapper({ children }: { children: ReactNode }) {
    // Create fresh QueryClient for each test to prevent cache pollution
    const queryClient = createTestQueryClient();
    return (
      <Router>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </Router>
    );
  };
}

/** Create a wrapper with configurable retry behavior for error state testing */
export function createWrapperWithRetry(enableRetry: boolean) {
  return function Wrapper({ children }: { children: ReactNode }) {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: enableRetry,
          staleTime: 0,
        },
      },
    });
    return (
      <Router>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </Router>
    );
  };
}
