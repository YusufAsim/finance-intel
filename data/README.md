# data

Synthetic bank statement generator. Produces 24 months of transaction
history for three different profiles, along with the ground truth labels
for that history.

The generator is deterministic: the same seed always produces
byte-identical output. History starts from a fixed date (2024-01-01), so
the output does not drift with today's date.

## Running

```bash
uv sync
uv run python -m generator --seed 42 --profile employee --months 24 --out out
```

To generate every profile in one pass:

```bash
uv run python -m generator --seed 42 --profile all --months 24 --out out
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `--seed` | int | required | Seed driving every random draw |
| `--profile` | `student` / `employee` / `freelancer` / `all` | `employee` | Profile to generate |
| `--months` | int | `24` | Length of the history in months |
| `--out` | path | `out` | Directory the JSON files are written to |
| `--start` | ISO date | `2024-01-01` | First month of the history |

Output files:

```
out/transactions_<profile>_<seed>.json
out/labels_<profile>_<seed>.json
```

## Transaction schema

`transactions_<profile>_<seed>.json` is a list of transactions, sorted by
date in ascending order.

| Field | Type | Description | Example |
|---|---|---|---|
| `id` | string (UUID) | Transaction id. Derived from the profile, the seed and the sequence number, so it is reproducible. | `7ce55050-66cc-520f-9b49-68cc0bb950f9` |
| `date` | string (ISO date) | Day the transaction was recorded by the bank | `2024-01-01` |
| `amount` | string (decimal) | Transaction amount, always positive. The sign lives in `direction`. Two decimal places. | `"18500.00"` |
| `raw_description` | string | Raw description as it appears on the statement, in POS format | `"MIGROS MMM ANKARA 4527"` |
| `direction` | string | `in` for income, `out` for spending | `"out"` |
| `balance` | string (decimal) | Account balance after the transaction | `"10000.00"` |

Amounts are written as strings rather than floats. This avoids floating
point loss and keeps the file byte-identical between two runs. Consumers
should read them as `Decimal`.

The balance starts from the profile's opening balance and moves with each
transaction according to its direction, so
`balance[n] = balance[n-1] ± amount[n]`.

## Ground truth schema

`labels_<profile>_<seed>.json` has exactly the same length and ordering as
the transaction file. It carries the label the generator itself knows to
be correct; no detection algorithm runs here.

| Field | Type | Description |
|---|---|---|
| `transaction_id` | string (UUID) | The `id` of the matching transaction |
| `category` | string | True category label |
| `series_id` | string (UUID) or `null` | Id of the series, when the transaction is part of a recurring one |
| `is_anomaly` | bool | Whether the transaction was deliberately planted as an anomaly |
| `anomaly_kind` | string or `null` | Kind of anomaly, `null` when `is_anomaly` is false |

### Categories

`salary`, `rent`, `subscription`, `utilities`, `groceries`, `dining`,
`electronics`, `travel`, `health`, `other`.

`other` is only used for the unusual merchant anomaly.

### Series

Monthly recurring flows are grouped under a `series_id`: salary/income,
rent, every subscription and every utility line is its own series. In a
24 month history a monthly series holds 24 transactions. Groceries,
dining and one-off large purchases have a `null` `series_id`.

### Anomaly kinds

| Kind | What happens |
|---|---|
| `amount_spike` | The amount of a groceries or dining transaction is multiplied by 5-9 |
| `duplicate` | An existing transaction is written a second time on the same day, with the same amount and description |
| `unusual_merchant` | A transaction is added for a merchant that never appears in the normal spending pattern |
| `off_schedule` | A subscription is shifted off its fixed monthly day |

Anomalies make up roughly 2% of all transactions and their count is
deterministic with respect to the seed.

## Profiles

| Profile | Income | Rent | Subscriptions | Character |
|---|---|---|---|---|
| `student` | Monthly family support + part time wage | Low, shared | 2 | Small amounts, frequent minor spending |
| `employee` | Single salary, 5th of the month ±2 days | High | 4 | Steady flow, seasonal utility bills |
| `freelancer` | 1-3 irregular client payments a month, amounts spread wide | Medium | 3 | Volatile income, steady spending |

In every profile income is raised once over the 24 months, each
subscription is raised once or twice, and utility bills follow the
seasons (natural gas and electricity climb in winter).

## Tests

```bash
uv run pytest
```

The tests verify determinism, transaction count ranges, balance
consistency, ground truth alignment and the anomaly ratio. They need
neither network nor database.
