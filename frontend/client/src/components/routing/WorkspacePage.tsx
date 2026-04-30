/**
 * WorkspacePage
 *
 * Wraps a wouter-based workspace component in a wouter Router that syncs
 * with React Router's location, plus a wouter <Route> so useParams() works.
 */
import { Route } from "wouter";
import { WouterAdapter } from "./WouterAdapter";

interface WorkspacePageProps {
  path: string;
  children: React.ReactNode;
}

export function WorkspacePage({ path, children }: WorkspacePageProps) {
  return (
    <WouterAdapter>
      <Route path={path}>{children}</Route>
    </WouterAdapter>
  );
}
