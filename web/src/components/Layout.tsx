/** Application shell: navigation plus the account picker every page reads. */

import { NavLink, Outlet } from "react-router-dom";

import { useAccounts } from "../lib/useAccounts";

const LINKS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/transactions", label: "Transactions" },
  { to: "/subscriptions", label: "Subscriptions" },
  { to: "/anomalies", label: "Anomalies" },
  { to: "/forecast", label: "Forecast" },
];

export default function Layout() {
  const { accounts, accountId, setAccountId, loading, error } = useAccounts();

  return (
    <div className="min-h-full">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-4 px-6 py-4">
          <span className="text-lg font-semibold">finance-intel</span>

          <nav className="flex flex-wrap gap-1">
            {LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) =>
                  `rounded-md px-3 py-1.5 text-sm ${
                    isActive ? "bg-ink text-white" : "text-muted hover:bg-canvas"
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto">
            {error ? (
              <span className="text-sm text-negative">accounts unavailable</span>
            ) : (
              <select
                value={accountId ?? ""}
                onChange={(event) => setAccountId(event.target.value)}
                disabled={loading || accounts.length === 0}
                className="rounded-md border border-line bg-surface px-2 py-1.5 text-sm"
              >
                {loading && <option>Loading…</option>}
                {!loading && accounts.length === 0 && <option>No accounts</option>}
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet context={{ accountId }} />
      </main>
    </div>
  );
}
