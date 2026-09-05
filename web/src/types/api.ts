/** Response shapes returned by the backend and the agentic service. */

/** Money and other decimals arrive as strings so no precision is lost. */
export type Decimal = string;

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export type Direction = "in" | "out";

export interface Account {
  id: string;
  name: string;
  profile: string;
  currency: string;
  opening_balance: Decimal;
  source_seed: number;
  transaction_count: number;
  created_at: string;
  updated_at: string;
}

export interface Category {
  id: string;
  slug: string;
  name: string;
  is_income: boolean;
}

export interface Merchant {
  id: string;
  name: string;
  display_name: string;
  category: string | null;
  category_slug: string | null;
}

export interface Transaction {
  id: string;
  external_id: string;
  account: string;
  date: string;
  amount: Decimal;
  signed_amount: Decimal;
  direction: Direction;
  raw_description: string;
  balance: Decimal | null;
  category: string | null;
  category_slug: string | null;
  merchant: string | null;
  merchant_name: string | null;
  series_key: string | null;
}

export interface CategoryShare {
  category: string;
  total: Decimal;
  count: number;
  /** Fraction of total spending, between 0 and 1. */
  share: number;
}

export interface AccountSummary {
  account_id: string;
  period: { start: string; end: string };
  transaction_count: number;
  total_income: Decimal;
  total_expense: Decimal;
  net: Decimal;
  categories: CategoryShare[];
}

export interface Subscription {
  id: string;
  account: string;
  merchant: string;
  merchant_name: string;
  series_key: string;
  cadence: string;
  amount: Decimal;
  first_seen: string;
  last_seen: string;
  is_active: boolean;
}

export type AnomalyKind =
  | "amount_spike"
  | "duplicate"
  | "unusual_merchant"
  | "off_schedule";

export interface Anomaly {
  id: string;
  transaction: string;
  transaction_date: string;
  transaction_amount: Decimal;
  raw_description: string;
  kind: AnomalyKind;
  source: string;
  score: number | null;
  note: string | null;
}

export interface ForecastPoint {
  date: string;
  expected_balance: Decimal;
  expected_income: Decimal;
  expected_expense: Decimal;
}

export interface Forecast {
  account_id: string;
  horizon_days: number;
  model_version: string;
  points: ForecastPoint[];
}

/** Envelope shared by the account scoped insight endpoints. */
export interface AccountList<T> {
  account_id: string;
  count: number;
  results: T[];
}

export interface ChatRequest {
  question: string;
  account_id?: string | null;
}

export interface ChatResponse {
  question: string;
  intent: string;
  tool_name: string | null;
  answer: string;
  tool_results: Record<string, unknown>;
  error: string | null;
}
