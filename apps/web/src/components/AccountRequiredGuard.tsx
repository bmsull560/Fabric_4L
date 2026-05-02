/**
 * AccountRequiredGuard — Wraps any account-dependent screen.
 *
 * If no account is selected, renders a centered message instead of the screen.
 * If an account is selected, renders children.
 */
import { Building2 } from "lucide-react";

interface AccountRequiredGuardProps {
  children?: React.ReactNode;
  accountId?: string | null;
}

export function AccountRequiredGuard({ children, accountId }: AccountRequiredGuardProps) {
  if (accountId) {
    return <>{children}</>;
  }

  return (
    <div className="flex h-full w-full items-center justify-center">
      <div className="flex flex-col items-center gap-3 text-center">
        <Building2 className="h-8 w-8 text-muted-foreground" />
        <div>
          <p className="text-sm font-semibold text-foreground">No account selected</p>
          <p className="text-xs text-muted-foreground mt-1">
            Select an account from the sidebar to view this page.
          </p>
        </div>
      </div>
    </div>
  );
}

export default AccountRequiredGuard;
