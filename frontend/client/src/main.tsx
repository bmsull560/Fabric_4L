import { lazy, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import "./index.css";
import { I18nProvider } from "./i18n";
import { STALE_TIME } from "./hooks/useApiShared";

// ReactQueryDevtools is only included in development builds.
// Vite's tree-shaking drops this import entirely in production,
// preventing the ~40 kB devtools chunk from reaching end users.
const ReactQueryDevtools = import.meta.env.DEV
  ? lazy(() =>
      import("@tanstack/react-query-devtools").then((m) => ({
        default: m.ReactQueryDevtools,
      }))
    )
  : null;

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Global default — individual hooks override with a more specific STALE_TIME key
      staleTime: STALE_TIME.activity,
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <QueryClientProvider client={queryClient}>
    <I18nProvider>
      <App />
      {import.meta.env.DEV && ReactQueryDevtools && (
        <Suspense fallback={null}>
          <ReactQueryDevtools initialIsOpen={false} />
        </Suspense>
      )}
    </I18nProvider>
  </QueryClientProvider>
);
