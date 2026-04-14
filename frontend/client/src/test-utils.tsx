import { ReactElement, ReactNode, useState } from "react";
import { render, RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Router } from "wouter";

// Re-export for AuthContext tests (avoids circular dependency)
export type { UserInfo } from "./contexts/AuthContext";

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
    const [queryClient] = useState(() => createTestQueryClient());
    return (
      <Router>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </Router>
    );
  };
}

export function createWrapperWithRouterPath(path: string) {
  return function Wrapper({ children }: { children: ReactNode }) {
    const [queryClient] = useState(() => createTestQueryClient());
    if (typeof window !== "undefined") {
      const url = new URL(path, "http://localhost:3000");
      Object.defineProperty(window, "location", {
        configurable: true,
        writable: true,
        value: {
          ...window.location,
          href: url.toString(),
          pathname: url.pathname,
          search: url.search,
          hash: url.hash,
        },
      });
      window.history.replaceState({}, "", path);
    }
    return (
      <Router>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </Router>
    );
  };
}

type RenderWithRouterOptions = Omit<RenderOptions, "wrapper"> & {
  path?: string;
};

export function renderWithRouter(
  ui: ReactElement,
  { path = "/", ...renderOptions }: RenderWithRouterOptions = {}
) {
  const wrapper = createWrapperWithRouterPath(path);
  return render(ui, { wrapper, ...renderOptions });
}

/** Create a wrapper with configurable retry behavior for error state testing */
export function createWrapperWithRetry(enableRetry: boolean) {
  return function Wrapper({ children }: { children: ReactNode }) {
    const [queryClient] = useState(() =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: enableRetry,
            staleTime: 0,
            gcTime: 0,
          },
        },
      })
    );
    return (
      <Router>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </Router>
    );
  };
}
