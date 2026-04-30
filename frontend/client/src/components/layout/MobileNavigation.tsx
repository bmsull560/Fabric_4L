import { MobilePersistentSidebar } from "@/components/navigation/MobilePersistentSidebar";
import { NAV_SPINE } from "@/components/navigation/TieredNav";
import type { UserTier } from "@/navigation/navHelpers";
import { useAccountContextStore } from "@/stores/accountContextStore";
import { useAccounts } from "@/hooks";
import { useAuthContext } from "@/contexts/AuthContext";

interface MobileNavigationProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentTier: UserTier;
  onTierChange: (tier: UserTier) => void;
  isAdvancedModeEnabled?: boolean;
  onAdvancedModeToggle?: (enabled: boolean) => void;
}

export function MobileNavigation({
  open,
  onOpenChange,
  currentTier,
  onTierChange,
  isAdvancedModeEnabled = false,
  onAdvancedModeToggle = () => {},
}: MobileNavigationProps) {
  const selectedAccountId = useAccountContextStore(state => state.selectedAccountId);
  const setSelectedAccountId = useAccountContextStore(state => state.setSelectedAccountId);
  const { data: accountsData, isLoading: accountsLoading, error: accountsError } = useAccounts({ page_size: 100 });
  const accounts = accountsData?.items ?? [];
  const { user, logout } = useAuthContext();

  return (
    <div className="flex md:hidden">
      <MobilePersistentSidebar
        currentTier={currentTier}
        effectiveTier={currentTier === "standard" && isAdvancedModeEnabled ? "advanced" : currentTier}
        onTierChange={onTierChange}
        isAdvancedModeEnabled={isAdvancedModeEnabled}
        onAdvancedModeToggle={onAdvancedModeToggle}
        navItems={NAV_SPINE}
        accounts={accounts}
        selectedAccountId={selectedAccountId}
        onSelectAccount={setSelectedAccountId}
        isAccountsLoading={accountsLoading}
        accountsError={accountsError}
        user={user ? { email: user.email } : null}
        onSignOut={logout}
      />
    </div>
  );
}
