import { AsyncView, Empty } from "../components/States";
import { backend } from "../lib/api";
import { date, money } from "../lib/format";
import { useAccountId } from "../lib/useAccountId";
import { useAsync } from "../lib/useAsync";
import type { AnomalyKind } from "../types/api";

const KIND_LABELS: Record<AnomalyKind, string> = {
  amount_spike: "amount spike",
  duplicate: "duplicate",
  unusual_merchant: "unusual merchant",
  off_schedule: "off schedule",
};

export default function Anomalies() {
  const accountId = useAccountId();
  const state = useAsync(
    () =>
      accountId
        ? backend.accountAnomalies(accountId)
        : Promise.reject(new Error("no account")),
    [accountId],
  );

  if (!accountId) return <Empty label="Select an account to review its anomalies." />;

  return (
    <AsyncView
      state={state}
      isEmpty={(data) => data.results.length === 0}
      emptyLabel="Nothing on this account looks unusual."
    >
      {(data) => (
        <ul className="space-y-2">
          {data.results.map((row) => (
            <li
              key={row.id}
              className="flex flex-wrap items-center gap-3 rounded-lg border border-line bg-surface px-4 py-3 text-sm"
            >
              <span className="rounded-full bg-canvas px-2 py-0.5 text-xs text-muted">
                {KIND_LABELS[row.kind] ?? row.kind}
              </span>
              <span className="font-medium">{row.raw_description}</span>
              <span className="text-muted">{date(row.transaction_date)}</span>
              {row.score !== null && (
                <span className="text-xs text-muted">score {row.score.toFixed(2)}</span>
              )}
              <span className="ml-auto tabular-nums">
                {money(row.transaction_amount)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </AsyncView>
  );
}
