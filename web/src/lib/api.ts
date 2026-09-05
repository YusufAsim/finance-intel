/** Typed client for the backend and the agentic service.
 *
 * Every call goes through one request helper so failures surface as a
 * single error type the pages can render instead of a blank screen.
 */

import { env } from "./env";
import type {
  Account,
  AccountList,
  AccountSummary,
  Anomaly,
  Category,
  ChatRequest,
  ChatResponse,
  Forecast,
  Merchant,
  Paginated,
  Subscription,
  Transaction,
} from "../types/api";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

type Query = Record<string, string | number | boolean | null | undefined>;

function buildUrl(base: string, path: string, query?: Query): string {
  const url = `${base}${path}`;
  if (!query) return url;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === null || value === undefined || value === "") continue;
    params.append(key, String(value));
  }
  const serialised = params.toString();
  return serialised ? `${url}?${serialised}` : url;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    // the service is down or unreachable, which is a normal state to render
    throw new ApiError("The service could not be reached.", 0);
  }

  if (!response.ok) {
    throw new ApiError(
      `Request failed with status ${response.status}.`,
      response.status,
    );
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

function api<T>(path: string, query?: Query): Promise<T> {
  return request<T>(buildUrl(env.apiBaseUrl, path, query));
}

export interface TransactionFilters {
  account?: string;
  category?: string;
  date_after?: string;
  date_before?: string;
  amount_min?: number | string;
  amount_max?: number | string;
  direction?: string;
  search?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export const backend = {
  listAccounts: (query?: Query) => api<Paginated<Account>>("/accounts/", query),

  listCategories: () =>
    api<Paginated<Category>>("/categories/", { page_size: 100 }),

  listMerchants: (query?: Query) => api<Paginated<Merchant>>("/merchants/", query),

  listTransactions: (filters: TransactionFilters = {}) =>
    api<Paginated<Transaction>>("/transactions/", filters as Query),

  accountSummary: (accountId: string) =>
    api<AccountSummary>(`/accounts/${accountId}/summary/`),

  accountSubscriptions: (accountId: string) =>
    api<AccountList<Subscription>>(`/accounts/${accountId}/subscriptions/`),

  accountAnomalies: (accountId: string) =>
    api<AccountList<Anomaly>>(`/accounts/${accountId}/anomalies/`),

  accountForecast: (accountId: string, horizonDays?: number) =>
    api<Forecast>(`/accounts/${accountId}/forecast/`, {
      horizon_days: horizonDays,
    }),
};

export const agent = {
  ask: (body: ChatRequest) =>
    request<ChatResponse>(buildUrl(env.agentBaseUrl, "/agent/chat"), {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
