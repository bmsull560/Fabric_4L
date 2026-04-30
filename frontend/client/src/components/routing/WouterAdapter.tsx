/**
 * WouterAdapter
 *
 * Bridges React Router location to wouter's Router context.
 * This allows legacy wouter-based components (workspace shells, tabs,
 * navigation) to work unchanged inside React Router routes.
 */
import { useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Router as WouterRouter } from "wouter";
import type { BaseLocationHook } from "wouter";

function useReactRouterLocation(): ReturnType<BaseLocationHook> {
  const { pathname } = useLocation();
  const navigate = useNavigate();

  const setLocation = useCallback(
    (to: string, options?: { replace?: boolean }) => {
      navigate(to, { replace: options?.replace });
    },
    [navigate]
  );

  return [pathname, setLocation];
}

interface WouterAdapterProps {
  children: React.ReactNode;
}

export function WouterAdapter({ children }: WouterAdapterProps) {
  return (
    <WouterRouter hook={useReactRouterLocation}>{children}</WouterRouter>
  );
}
