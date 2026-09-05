/** Display helpers. Amounts stay strings until the moment they are shown. */

const MONEY = new Intl.NumberFormat("tr-TR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const DATE = new Intl.DateTimeFormat("tr-TR", {
  year: "numeric",
  month: "short",
  day: "2-digit",
});

export function money(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") return "—";
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isNaN(parsed) ? "—" : MONEY.format(parsed);
}

export function date(value: string | null | undefined): string {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : DATE.format(parsed);
}

export function percent(share: number): string {
  return `${(share * 100).toFixed(1)}%`;
}

/** Amounts are signed strings, so the sign decides the colour. */
export function isNegative(value: string | number): boolean {
  return Number(value) < 0;
}
