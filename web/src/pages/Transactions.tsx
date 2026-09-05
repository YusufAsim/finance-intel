import { useState } from "react";

import { AsyncView, Empty } from "../components/States";
import { backend, type TransactionFilters } from "../lib/api";
import { date, isNegative, money } from "../lib/format";
import { useAccountId } from "../lib/useAccountId";
import { useAsync } from "../lib/useAsync";

const PAGE_SIZE = 25;

interface FilterForm {
  date_after: string;
  date_before: string;
  category: string;
  amount_min: string;
  amount_max: string;
}

const EMPTY_FILTERS: FilterForm = {
  date_after: "",
  date_before: "",
  category: "",
  amount_min: "",
  amount_max: "",
};

export default function Transactions() {
  const accountId = useAccountId();
  const [filters, setFilters] = useState<FilterForm>(EMPTY_FILTERS);
  const [page, setPage] = useState(1);

  const categories = useAsync(() => backend.listCategories(), []);

  const state = useAsync(() => {
    if (!accountId) return Promise.reject(new Error("no account"));
    const query: TransactionFilters = {
      account: accountId,
      page,
      page_size: PAGE_SIZE,
      ordering: "-date",
    };
    if (filters.date_after) query.date_after = filters.date_after;
    if (filters.date_before) query.date_before = filters.date_before;
    if (filters.category) query.category = filters.category;
    if (filters.amount_min) query.amount_min = filters.amount_min;
    if (filters.amount_max) query.amount_max = filters.amount_max;
    return backend.listTransactions(query);
  }, [accountId, page, JSON.stringify(filters)]);

  function update(field: keyof FilterForm, value: string) {
    setPage(1);
    setFilters((current) => ({ ...current, [field]: value }));
  }

  if (!accountId) return <Empty label="Select an account to list its transactions." />;

  const input = "rounded-md border border-line bg-surface px-2 py-1.5 text-sm";

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3 rounded-lg border border-line bg-surface p-4">
        <label className="flex flex-col gap-1 text-xs text-muted">
          From
          <input
            type="date"
            className={input}
            value={filters.date_after}
            onChange={(event) => update("date_after", event.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted">
          To
          <input
            type="date"
            className={input}
            value={filters.date_before}
            onChange={(event) => update("date_before", event.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted">
          Category
          <select
            className={input}
            value={filters.category}
            onChange={(event) => update("category", event.target.value)}
          >
            <option value="">All</option>
            {categories.data?.results.map((category) => (
              <option key={category.id} value={category.slug}>
                {category.name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted">
          Min amount
          <input
            type="number"
            className={`${input} w-28`}
            value={filters.amount_min}
            onChange={(event) => update("amount_min", event.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-muted">
          Max amount
          <input
            type="number"
            className={`${input} w-28`}
            value={filters.amount_max}
            onChange={(event) => update("amount_max", event.target.value)}
          />
        </label>
        <button
          type="button"
          onClick={() => {
            setFilters(EMPTY_FILTERS);
            setPage(1);
          }}
          className="rounded-md border border-line px-3 py-1.5 text-sm hover:bg-canvas"
        >
          Reset
        </button>
      </div>

      <AsyncView
        state={state}
        isEmpty={(data) => data.results.length === 0}
        emptyLabel="No transaction matches these filters."
      >
        {(data) => (
          <>
            <div className="overflow-x-auto rounded-lg border border-line bg-surface">
              <table className="w-full text-sm">
                <thead className="border-b border-line text-left text-xs uppercase tracking-wide text-muted">
                  <tr>
                    <th className="px-4 py-3 font-medium">Date</th>
                    <th className="px-4 py-3 font-medium">Description</th>
                    <th className="px-4 py-3 font-medium">Category</th>
                    <th className="px-4 py-3 text-right font-medium">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {data.results.map((row) => (
                    <tr key={row.id}>
                      <td className="whitespace-nowrap px-4 py-2.5">{date(row.date)}</td>
                      <td className="px-4 py-2.5">{row.raw_description}</td>
                      <td className="px-4 py-2.5 capitalize text-muted">
                        {row.category_slug ?? "—"}
                      </td>
                      <td
                        className={`whitespace-nowrap px-4 py-2.5 text-right tabular-nums ${
                          isNegative(row.signed_amount)
                            ? "text-negative"
                            : "text-positive"
                        }`}
                      >
                        {money(row.signed_amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex items-center justify-between text-sm">
              <span className="text-muted">
                {data.count} transactions, page {page} of{" "}
                {Math.max(1, Math.ceil(data.count / PAGE_SIZE))}
              </span>
              <span className="flex gap-2">
                <button
                  type="button"
                  disabled={!data.previous}
                  onClick={() => setPage((value) => Math.max(1, value - 1))}
                  className="rounded-md border border-line px-3 py-1.5 disabled:opacity-40"
                >
                  Previous
                </button>
                <button
                  type="button"
                  disabled={!data.next}
                  onClick={() => setPage((value) => value + 1)}
                  className="rounded-md border border-line px-3 py-1.5 disabled:opacity-40"
                >
                  Next
                </button>
              </span>
            </div>
          </>
        )}
      </AsyncView>
    </div>
  );
}
