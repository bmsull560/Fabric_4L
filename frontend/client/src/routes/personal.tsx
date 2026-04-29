import { Route } from "wouter";
import type { ComponentType, ReactNode } from "react";
import type { RouteComposerContext } from "./types";

interface PersonalPages {
  Login: ComponentType;
  Signup: ComponentType;
  Home: ComponentType;
  CommandCenter: ComponentType;
  Accounts: ComponentType;
  NotFound: ComponentType;
  Layout: ComponentType<{ currentTier: "standard" | "advanced" | "admin"; effectiveTier: "standard" | "advanced" | "admin"; children: ReactNode }>;
  ErrorBoundary: ComponentType<{ children: ReactNode }>;
}

export function PersonalRoutes(context: RouteComposerContext, pages: PersonalPages, auth: { isLoading: boolean; isAuthenticated: boolean }) {
  const { tierProps, AuthenticatedRoute, Navigate } = context;
  const { Login, Signup, Home, CommandCenter, Accounts, NotFound, Layout, ErrorBoundary } = pages;

  return (
    <>
      <Route path="/">{auth.isLoading ? null : auth.isAuthenticated ? <Navigate to="/home" /> : <Navigate to="/login" />}</Route>
      <Route path="/login"><Login /></Route>
      <Route path="/login/callback"><Login /></Route>
      <Route path="/signup"><Signup /></Route>
      <Route path="/home"><AuthenticatedRoute {...tierProps}><Home /></AuthenticatedRoute></Route>
      <Route path="/command-center"><AuthenticatedRoute {...tierProps}><CommandCenter /></AuthenticatedRoute></Route>
      <Route path="/accounts"><AuthenticatedRoute {...tierProps}><Accounts /></AuthenticatedRoute></Route>
      <Route path="/accounts/:id"><AuthenticatedRoute {...tierProps}><Accounts /></AuthenticatedRoute></Route>
      <Route>
        <Layout currentTier={tierProps.currentTier} effectiveTier={tierProps.effectiveTier}>
          <ErrorBoundary><NotFound /></ErrorBoundary>
        </Layout>
      </Route>
    </>
  );
}
