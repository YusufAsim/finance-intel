/** Every page has to survive a failing backend without going blank. */

import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import Anomalies from "./Anomalies";
import Dashboard from "./Dashboard";
import Forecast from "./Forecast";
import Subscriptions from "./Subscriptions";
import Transactions from "./Transactions";
import { renderPage, TEST_ACCOUNT } from "../test/render";

const SUMMARY = {
  account_id: TEST_ACCOUNT,
  period: { start: "2024-01-01", end: "2025-12-29" },
  transaction_count: 825,
  total_income: "1255280.00",
  total_expense: "1267079.53",
  net: "-11799.53",
  categories: [{ category: "rent", total: "444000.00", count: 24, share: 0.3504 }],
};

const TRANSACTIONS = {
  count: 1,
  next: null,
  previous: null,
  results: [
    {
      id: "t1",
      external_id: "e1",
      account: TEST_ACCOUNT,
      date: "2025-12-31",
      amount: "141.79",
      signed_amount: "-141.79",
      direction: "out",
      raw_description: "BURGER KING ANKAMALL 8247",
      balance: "-142727.42",
      category: "c1",
      category_slug: "dining",
      merchant: "m1",
      merchant_name: "BURGER KING ANKAMALL",
      series_key: null,
    },
  ],
};

const SUBSCRIPTIONS = {
  account_id: TEST_ACCOUNT,
  count: 1,
  results: [
    {
      id: "s1",
      account: TEST_ACCOUNT,
      merchant: "m2",
      merchant_name: "NETFLIX INTERNATIONAL AMSTERDAM",
      series_key: "k1",
      cadence: "monthly",
      amount: "201.77",
      first_seen: "2024-01-28",
      last_seen: "2025-12-28",
      is_active: true,
    },
  ],
};

const ANOMALIES = {
  account_id: TEST_ACCOUNT,
  count: 1,
  results: [
    {
      id: "a1",
      transaction: "t9",
      transaction_date: "2025-03-27",
      transaction_amount: "8053.95",
      raw_description: "DOMINOS PIZZA CAYYOLU 1674",
      kind: "amount_spike",
      source: "ground_truth",
      score: null,
      note: null,
    },
  ],
};

const FORECAST = {
  account_id: TEST_ACCOUNT,
  horizon_days: 30,
  model_version: "stub-0.1.0",
  points: [
    {
      date: "2025-12-30",
      expected_balance: "-11815.73",
      expected_income: "1724.29",
      expected_expense: "1740.49",
    },
  ],
};

function mockFetch(handler: (url: string) => unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const payload = handler(String(url));
      return {
        ok: true,
        status: 200,
        json: async () => payload,
      } as Response;
    }),
  );
}

function failFetch(status: number) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({ ok: false, status, json: async () => ({}) }) as Response),
  );
}

afterEach(() => vi.unstubAllGlobals());

const PAGES = [
  { name: "Dashboard", element: <Dashboard /> },
  { name: "Transactions", element: <Transactions /> },
  { name: "Subscriptions", element: <Subscriptions /> },
  { name: "Anomalies", element: <Anomalies /> },
  { name: "Forecast", element: <Forecast /> },
];

describe("pages render real data", () => {
  function route(url: string) {
    if (url.includes("/summary/")) return SUMMARY;
    if (url.includes("/subscriptions/")) return SUBSCRIPTIONS;
    if (url.includes("/anomalies/")) return ANOMALIES;
    if (url.includes("/forecast/")) return FORECAST;
    if (url.includes("/categories/")) return { count: 0, next: null, previous: null, results: [] };
    return TRANSACTIONS;
  }

  it("dashboard shows the totals", async () => {
    mockFetch(route);
    renderPage(<Dashboard />);
    expect(await screen.findByText("Income")).toBeInTheDocument();
    expect(await screen.findByText(/1\.255\.280,00/)).toBeInTheDocument();
  });

  it("transactions shows a row", async () => {
    mockFetch(route);
    renderPage(<Transactions />);
    expect(
      await screen.findByText("BURGER KING ANKAMALL 8247"),
    ).toBeInTheDocument();
  });

  it("subscriptions shows a recurring charge", async () => {
    mockFetch(route);
    renderPage(<Subscriptions />);
    expect(
      await screen.findByText("NETFLIX INTERNATIONAL AMSTERDAM"),
    ).toBeInTheDocument();
  });

  it("anomalies shows a flagged transaction", async () => {
    mockFetch(route);
    renderPage(<Anomalies />);
    expect(
      await screen.findByText("DOMINOS PIZZA CAYYOLU 1674"),
    ).toBeInTheDocument();
  });

  it("forecast reports the model version", async () => {
    mockFetch(route);
    renderPage(<Forecast />);
    expect(await screen.findByText(/stub-0\.1\.0/)).toBeInTheDocument();
  });
});

describe("pages degrade when the backend is down", () => {
  it.each(PAGES)("$name shows an error instead of a blank screen", async ({ element }) => {
    failFetch(504);
    const { container } = renderPage(element);

    expect(
      await screen.findByText("This view could not be loaded."),
    ).toBeInTheDocument();
    await waitFor(() => expect(container.textContent?.trim()).not.toBe(""));
  });

  it.each(PAGES)("$name prompts for an account when none is selected", async ({ element }) => {
    mockFetch(() => ({}));
    const { container } = renderPage(element, null);
    await waitFor(() => expect(container.textContent?.trim()).not.toBe(""));
  });
});
