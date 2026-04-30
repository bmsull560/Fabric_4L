import { RouterProvider } from "react-router-dom";
import { ErrorBoundary } from "@/components";
import { Toaster } from "@/components/ui/sonner";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { AuthProvider } from "@/contexts/AuthContext";
import { TooltipProvider } from "@/components/ui/tooltip";
import { router } from "./shell/router";
import { LegacyRouter } from "./shell/LegacyApp";

// Backward-compatible export for tests and consumers referencing the old wouter router
export const AppRouter = LegacyRouter;

export default function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="light" switchable>
        <AuthProvider>
          <TooltipProvider>
            <Toaster />
            <RouterProvider router={router} />
          </TooltipProvider>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
