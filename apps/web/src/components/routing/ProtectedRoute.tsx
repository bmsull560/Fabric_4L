import { Navigate, useLocation } from "react-router-dom";
import { useAuthContext } from "@/contexts/AuthContext";
import { useUserTierStore, type UserTier } from "@/hooks";
import { ErrorBoundary } from "@/components";
import { createFeatureLogger } from "@/lib/telemetry";

type RequiredUserTier = Exclude<UserTier, "unknown">;
const log = createFeatureLogger("protected-route");

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredTier?: RequiredUserTier;
}

export function ProtectedRoute({
  children,
  requiredTier = "standard",
}: ProtectedRouteProps) {
  const location = useLocation();
  const { isAuthenticated, isLoading } = useAuthContext();
  const canAccessRouteWithReason = useUserTierStore(
    (state) => state.canAccessRouteWithReason
  );
  const currentTier = useUserTierStore((state) => state.currentTier);

  if (isLoading) {
    return (
      <div className="flex h-full min-h-[400px] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-primary" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  let accessDecision;
  try {
    accessDecision = canAccessRouteWithReason(requiredTier);
  } catch (error) {
    log.error("Permission evaluation failed", {
      route: location.pathname,
      error: error instanceof Error ? error.message : String(error),
    });
    accessDecision = {
      allowed: false,
      reason: "PERMISSION_EVALUATION_EXCEPTION",
    };
  }

  if (!accessDecision.allowed) {
    log.warn("Access denied", {
      route: location.pathname,
      errorCode: accessDecision.reason,
      userId: null,
    });
    return <Navigate to="/home" replace />;
  }

  return <ErrorBoundary>{children}</ErrorBoundary>;
}
