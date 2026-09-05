/** The account the layout selected, read by each page. */

import { useOutletContext } from "react-router-dom";

export function useAccountId(): string | null {
  return useOutletContext<{ accountId: string | null }>().accountId;
}
