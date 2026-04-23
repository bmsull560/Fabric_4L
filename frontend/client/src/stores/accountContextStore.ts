import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AccountContextState {
  selectedAccountId: string | null;
  setSelectedAccountId: (accountId: string | null) => void;
  clearSelectedAccountId: () => void;
}

export const useAccountContextStore = create<AccountContextState>()(
  persist(
    set => ({
      selectedAccountId: null,
      setSelectedAccountId: accountId => set({ selectedAccountId: accountId }),
      clearSelectedAccountId: () => set({ selectedAccountId: null }),
    }),
    {
      name: "fabric-account-context",
      partialize: state => ({ selectedAccountId: state.selectedAccountId }),
    }
  )
);
