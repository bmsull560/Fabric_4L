import {
  useAccountContextStore,
  type AccountContextState,
  type StoreSelector,
} from "@fabric/platform-contract/stores";

const selector: StoreSelector<AccountContextState, string | null> = (state) =>
  state.selectedAccountId;

useAccountContextStore.getState().setSelectedAccountId("acc-1");
useAccountContextStore.getState().clearSelectedAccountId();

void selector;
