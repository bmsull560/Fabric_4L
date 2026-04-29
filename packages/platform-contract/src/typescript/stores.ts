/**
 * Canonical Zustand store patterns for Fabric 4L frontend.
 *
 * Rules:
 * - All stores are typed with interfaces.
 * - Server state lives in React Query, NOT Zustand.
 * - persist() is used only for client-side UI state.
 * - No 'any' in store definitions.
 */

import { create } from "zustand";
import { persist, PersistOptions } from "zustand/middleware";

/** Example: Account context store (canonical pattern) */
export interface AccountContextState {
  selectedAccountId: string | null;
  setSelectedAccountId: (id: string) => void;
  clearSelectedAccountId: () => void;
}

export const useAccountContextStore = create<AccountContextState>()(
  persist(
    (set) => ({
      selectedAccountId: null,
      setSelectedAccountId: (id) => set({ selectedAccountId: id }),
      clearSelectedAccountId: () => set({ selectedAccountId: null }),
    }),
    {
      name: "fabric-account-context",
      partialize: (state) => ({ selectedAccountId: state.selectedAccountId }),
    } as PersistOptions<AccountContextState>
  )
);

/** Helper type for typed store selectors */
export type StoreSelector<T, R> = (state: T) => R;
