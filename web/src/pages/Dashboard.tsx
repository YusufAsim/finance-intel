import { AsyncView, Empty } from "../components/States";
import { backend } from "../lib/api";
import { isNegative, money, percent, date } from "../lib/format";
import { useAccountId } from "../lib/useAccountId";
import { useAsync } from "../lib/useAsync";

function Card({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="rounded-lg border border-line bg-surface p-4">
      <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${tone ?? ""}`}>{value}</p>
    </div>
  );
}

export default function Dashboard() {
  const accountId = useAccountId();
  const state = useAsync(
    () =>
      accountId
        ? backend.accountSummary(accountId)
        : Promise.reject(new Error("no account")),
    [accountId],
  );

  if (!accountId) return <Empty label="Select an account to see its summary." />;

  return (
    <AsyncView state={state}>
      {(summary) => (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card label="Income" value={money(summary.total_income)} />
            <Card label="Expense" value={money(summary.total_expense)} />
            <Card
              label="Net"
              value={money(summary.net)}
              tone={isNegative(summary.net) ? "text-negative" : "text-positive"}
            />
            <Card label="Transactions" value={String(summary.transaction_count)} />
          </div>

          <p className="text-sm text-muted">
            Period {date(summary.period.start)} — {date(summary.period.end)}
          </p>

          <section className="rounded-lg border border-line bg-surface">
            <h2 className="border-b border-line px-4 py-3 text-sm font-medium">
              Spending by category
            </h2>
            {summary.categories.length === 0 ? (
              <p className="px-4 py-6 text-sm text-muted">No spending recorded.</p>
            ) : (
              <ul className="divide-y divide-line">
                {summary.categories.map((row) => (
                  <li
                    key={row.category}
                    className="flex items-center gap-4 px-4 py-3 text-sm"
                  >
                    <span className="w-32 shrink-0 capitalize">{row.category}</span>
                    <span className="h-2 flex-1 overflow-hidden rounded-full bg-canvas">
                      <span
                        className="block h-full rounded-full bg-ink"
                        style={{ width: percent(row.share) }}
                      />
                    </span>
                    <span className="w-16 shrink-0 text-right text-muted">
                      {percent(row.share)}
                    </span>
                    <span className="w-28 shrink-0 text-right tabular-nums">
                      {money(row.total)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </AsyncView>
  );
}
