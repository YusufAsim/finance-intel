/** Account list plus the currently selected account.
 *
 * The selection lives at the top of the tree because every page is
 * scoped to one account.
 */

import { useEffect, useMemo, useState } from "react";

import { backend } from "./api";
import { useAsync } from "./useAsync";
import type { Account } from "../types/api";

export function useAccounts() {
  const state = useAsync(() => backend.listAccounts({ page_size: 50 }), []);
  const [accountId, setAccountId] = useState<string | null>(null);

  // memoised so the effect below does not re-run on every render
  const accounts: Account[] = useMemo(
    () => state.data?.results ?? [],
    [state.data],
  );

  useEffect(() => {
    if (!accountId && accounts.length > 0) setAccountId(accounts[0].id);
  }, [accountId, accounts]);

  return {
    accounts,
    accountId,
    setAccountId,
    loading: state.loading,
    error: state.error,
  };
}
