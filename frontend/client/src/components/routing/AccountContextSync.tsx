/**
 * AccountContextSync
 *
 * Syncs the React Router :accountId URL param to the Zustand account context store.
 * This ensures workspace components that read from the store stay in sync with the URL.
 */
import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { useAccountContextStore } from "@/stores/accountContextStore";

export function AccountContextSync() {
  const { accountId } = useParams<{ accountId: string }>();
  const setSelectedAccountId = useAccountContextStore(
    (state) => state.setSelectedAccountId
  );

  useEffect(() => {
    setSelectedAccountId(accountId ?? null);
  }, [accountId, setSelectedAccountId]);

  return null;
}
