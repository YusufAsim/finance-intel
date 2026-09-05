import { AsyncView, Empty } from "../components/States";
import { backend } from "../lib/api";
import { date, money } from "../lib/format";
import { useAccountId } from "../lib/useAccountId";
import { useAsync } from "../lib/useAsync";

export default function Subscriptions() {
  const accountId = useAccountId();
  const state = useAsync(
    () =>
      accountId
        ? backend.accountSubscriptions(accountId)
        : Promise.reject(new Error("no account")),
    [accountId],
  );

  if (!accountId) return <Empty label="Select an account to see its subscriptions." />;

  return (
    <AsyncView
      state={state}
      isEmpty={(data) => data.results.length === 0}
      emptyLabel="No recurring charge was found on this account."
    >
      {(data) => (
        <div className="overflow-x-auto rounded-lg border border-line bg-surface">
          <table className="w-full text-sm">
            <thead className="border-b border-line text-left text-xs uppercase tracking-wide text-muted">
              <tr>
                <th className="px-4 py-3 font-medium">Merchant</th>
                <th className="px-4 py-3 font-medium">Cadence</th>
                <th className="px-4 py-3 font-medium">First seen</th>
                <th className="px-4 py-3 font-medium">Last seen</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 text-right font-medium">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {data.results.map((row) => (
                <tr key={row.id}>
                  <td className="px-4 py-2.5">{row.merchant_name}</td>
                  <td className="px-4 py-2.5 capitalize text-muted">{row.cadence}</td>
                  <td className="whitespace-nowrap px-4 py-2.5">{date(row.first_seen)}</td>
                  <td className="whitespace-nowrap px-4 py-2.5">{date(row.last_seen)}</td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${
                        row.is_active
                          ? "bg-positive/10 text-positive"
                          : "bg-canvas text-muted"
                      }`}
                    >
                      {row.is_active ? "active" : "ended"}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-4 py-2.5 text-right tabular-nums">
                    {money(row.amount)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AsyncView>
  );
}
