import { backend } from "./lib/api";
import { useAsync } from "./lib/useAsync";

export default function App() {
  const accounts = useAsync(() => backend.listAccounts({ page_size: 50 }), []);

  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="text-2xl font-semibold">finance-intel</h1>
      <p className="mt-1 text-sm text-muted">
        Dashboard pages are not wired up yet.
      </p>

      <section className="mt-6 rounded-lg border border-line bg-surface p-4">
        {accounts.loading && <p className="text-sm text-muted">Loading…</p>}
        {accounts.error && (
          <p className="text-sm text-negative">{accounts.error}</p>
        )}
        {accounts.data && (
          <ul className="space-y-1 text-sm">
            {accounts.data.results.map((account) => (
              <li key={account.id}>
                {account.name} — {account.transaction_count} transactions
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
