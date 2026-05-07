import { create } from "zustand";
import { persist } from "zustand/middleware";

type WorkspaceSelection = {
  treeId: string | null;
  valueModelId: string | null;
};

interface WorkspaceSelectionState {
  selectionsByAccount: Record<string, WorkspaceSelection>;
  setSelection: (accountId: string, selection: WorkspaceSelection) => void;
  getSelection: (accountId: string) => WorkspaceSelection;
}

const EMPTY_SELECTION: WorkspaceSelection = { treeId: null, valueModelId: null };

export const useWorkspaceSelectionStore = create<WorkspaceSelectionState>()(
  persist(
    (set, get) => ({
      selectionsByAccount: {},
      setSelection: (accountId, selection) =>
        set((state) => ({
          selectionsByAccount: {
            ...state.selectionsByAccount,
            [accountId]: selection,
          },
        })),
      getSelection: (accountId) => get().selectionsByAccount[accountId] ?? EMPTY_SELECTION,
    }),
    {
      name: "fabric-workspace-selection",
      partialize: (state) => ({ selectionsByAccount: state.selectionsByAccount }),
    }
  )
);
