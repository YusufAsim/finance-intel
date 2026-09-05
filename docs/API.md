# API

The platform exposes three HTTP surfaces: `backend` serves the domain
data, `ml` serves model output, `agentic` serves the natural language
endpoint. Addresses in the examples go through the nginx entry point.

Every money field travels as a string, so decimal precision is not lost
on the way through a float. Dates are `YYYY-MM-DD` and timestamps are
ISO 8601 UTC.

## Contents

- [Common behaviour](#common-behaviour)
- [backend](#backend)
  - [Health](#health)
  - [Accounts](#accounts)
  - [Transactions](#transactions)
  - [Categories](#categories)
  - [Merchants](#merchants)
  - [Subscriptions](#subscriptions)
  - [Budgets](#budgets)
  - [Anomaly flags](#anomaly-flags)
  - [Account summary](#account-summary)
  - [Account subscriptions](#account-subscriptions)
  - [Account anomalies](#account-anomalies)
  - [Account forecast](#account-forecast)
- [ml](#ml)
- [agentic](#agentic)

## Common behaviour

### Pagination

Every list endpoint returns the same envelope:

```json
{
  "count": 2354,
  "next": "http://localhost/api/transactions/?page=2",
  "previous": null,
  "results": []
}
```

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `page` | integer | no | 1 | Page number |
| `page_size` | integer | no | 50 | Page size, capped at 500 |

### Ordering and search

| Parameter | Type | Required | Description |
|---|---|---|---|
| `ordering` | string | no | Field name; prefix with `-` for descending |
| `search` | string | no | Searches the text fields specific to the resource |

The allowed `ordering` fields are listed in each resource's own section.

### Status codes

| Code | Meaning |
|---|---|
| 200 | Request succeeded |
| 201 | Record created |
| 204 | Record deleted, no body |
| 400 | Body or parameter failed validation |
| 404 | Resource does not exist |
| 422 | Body does not match the schema (ml and agentic) |
| 503 | Upstream service did not answer |

The error body is in DRF form:

```json
{ "detail": "Not found." }
```

## backend

Root: `http://localhost/api`

The `accounts`, `transactions`, `categories`, `merchants`,
`subscriptions` and `budgets` endpoints offer full CRUD: `GET` for the
list, `POST` to create, and `GET/PUT/PATCH/DELETE` on `/{id}/` for a
single record. `anomaly-flags` is read only.

### Health

```
GET /api/healthz
```

```json
{ "status": "ok" }
```

### Accounts

```
GET /api/accounts/
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `profile` | string | no | `employee`, `freelancer`, `student` |
| `currency` | string | no | Currency code |
| `search` | string | no | Searches the account name |
| `ordering` | string | no | `name`, `created_at` |

```bash
curl "http://localhost/api/accounts/?page_size=1"
```

```json
{
  "count": 3,
  "next": "http://localhost/api/accounts/?page=2&page_size=1",
  "previous": null,
  "results": [
    {
      "id": "f3378389-4158-4444-8c7c-7b3350dec380",
      "name": "employee account",
      "profile": "employee",
      "currency": "TRY",
      "opening_balance": "28500.00",
      "source_seed": 42,
      "transaction_count": 825,
      "created_at": "2026-08-15T10:10:06.364282Z",
      "updated_at": "2026-08-15T10:10:06.364282Z"
    }
  ]
}
```

### Transactions

```
GET /api/transactions/
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `account` | uuid | no | Account id |
| `direction` | string | no | `in` or `out` |
| `category` | string | no | Category slug |
| `merchant` | string | no | Text contained in the merchant name |
| `date_after` | date | no | This date and later |
| `date_before` | date | no | This date and earlier |
| `amount_min` | number | no | Lower amount bound |
| `amount_max` | number | no | Upper amount bound |
| `search` | string | no | Searches the description and merchant name |
| `ordering` | string | no | `date`, `amount`, `created_at`; defaults to `-date` |

```bash
curl "http://localhost/api/transactions/?category=dining&page_size=1"
```

```json
{
  "count": 900,
  "next": "http://localhost/api/transactions/?category=dining&page=2&page_size=1",
  "previous": null,
  "results": [
    {
      "id": "33405c93-3b6d-4880-a684-d34a377890df",
      "external_id": "8ebdf300-99c1-5856-ad11-61e472a43864",
      "account": "c9c57bc3-b90d-40dc-921d-4b4dc26da0c2",
      "date": "2025-12-31",
      "amount": "141.79",
      "signed_amount": "-141.79",
      "direction": "out",
      "raw_description": "BURGER KING ANKAMALL 8247",
      "balance": "-142727.42",
      "category": "788d7e5f-892f-40ab-b89b-8db6d43f6c32",
      "category_slug": "dining",
      "merchant": "58539551-1cee-4989-b79e-7c71f7bc61be",
      "merchant_name": "BURGER KING ANKAMALL",
      "series_key": null,
      "created_at": "2026-08-15T10:10:10.639049Z",
      "updated_at": "2026-08-15T10:10:10.639049Z"
    }
  ]
}
```

`amount` is always positive; the sign lives in `direction`.
`signed_amount` gives spending as negative and income as positive.

Creation body:

```json
{
  "account": "f3378389-4158-4444-8c7c-7b3350dec380",
  "external_id": "manual-0001",
  "date": "2026-01-15",
  "amount": "250.00",
  "direction": "out",
  "raw_description": "A101 YENIMAHALLE"
}
```

### Categories

```
GET /api/categories/
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `is_income` | boolean | no | Separates income categories |
| `search` | string | no | Searches `slug` and `name` |
| `ordering` | string | no | `slug`, `name`, `created_at` |

```json
{
  "id": "788d7e5f-892f-40ab-b89b-8db6d43f6c32",
  "slug": "dining",
  "name": "Dining",
  "is_income": false,
  "created_at": "2026-08-15T10:10:06.355353Z",
  "updated_at": "2026-08-15T10:10:06.355353Z"
}
```

### Merchants

```
GET /api/merchants/
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `category` | string | no | Category slug |
| `search` | string | no | Searches `name` and `display_name` |
| `ordering` | string | no | `name`, `created_at` |

```json
{
  "id": "7c2a76cb-2b00-4402-8957-430f699384b1",
  "name": "A101 YENIMAHALLE",
  "display_name": "A101 Yenimahalle",
  "category": "8534c69c-4520-4435-81e6-74b23b3e4537",
  "category_slug": "groceries",
  "created_at": "2026-08-15T10:10:06.399576Z",
  "updated_at": "2026-08-15T10:10:06.399576Z"
}
```

### Subscriptions

```
GET /api/subscriptions/
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `account` | uuid | no | Account id |
| `cadence` | string | no | `monthly` or `yearly` |
| `is_active` | boolean | no | Separates the series that are still running |
| `merchant` | string | no | Text contained in the merchant name |
| `ordering` | string | no | `amount`, `first_seen`, `last_seen` |

### Budgets

```
GET /api/budgets/
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `account` | uuid | no | Account id |
| `category` | string | no | Category slug |
| `ordering` | string | no | `monthly_limit`, `starts_on` |

### Anomaly flags

```
GET /api/anomaly-flags/
```

Read only.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `kind` | string | no | `amount_spike`, `duplicate`, `unusual_merchant`, `off_schedule` |
| `source` | string | no | `ground_truth` or `model` |
| `transaction__account` | uuid | no | Account id |
| `search` | string | no | Searches the description and the note |
| `ordering` | string | no | `created_at`; defaults to `-created_at` |

### Account summary

```
GET /api/accounts/{account_id}/summary/
```

The path parameter `account_id` is required. No query parameters.

```bash
curl "http://localhost/api/accounts/f3378389-4158-4444-8c7c-7b3350dec380/summary/"
```

```json
{
  "account_id": "f3378389-4158-4444-8c7c-7b3350dec380",
  "period": { "start": "2024-01-01", "end": "2025-12-29" },
  "transaction_count": 825,
  "total_income": "1255280.00",
  "total_expense": "1267079.53",
  "net": "-11799.53",
  "categories": [
    { "category": "rent", "total": "444000.00", "count": 24, "share": 0.3504 },
    { "category": "groceries", "total": "370176.28", "count": 271, "share": 0.2921 }
  ]
}
```

`share` gives the ratio to total spending, between 0 and 1. If the
account does not exist the endpoint returns 404.

### Account subscriptions

```
GET /api/accounts/{account_id}/subscriptions/
```

```json
{
  "account_id": "f3378389-4158-4444-8c7c-7b3350dec380",
  "count": 4,
  "results": [
    {
      "id": "d22df58c-4121-48d6-9d48-1d6ac5cb0bc5",
      "account": "f3378389-4158-4444-8c7c-7b3350dec380",
      "merchant": "4b49d013-5436-4352-90c1-c48e2ddd8f38",
      "merchant_name": "APPLE ICLOUD CORK",
      "series_key": "a219913c-508f-559e-bfd6-1eec87dfe6bb",
      "cadence": "monthly",
      "amount": "49.99",
      "first_seen": "2024-01-26",
      "last_seen": "2025-12-26",
      "is_active": true,
      "created_at": "2026-08-15T10:10:08.392372Z",
      "updated_at": "2026-08-15T10:10:08.392372Z"
    }
  ]
}
```

### Account anomalies

```
GET /api/accounts/{account_id}/anomalies/
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `kind` | string | no | Narrows to a single anomaly kind |

```json
{
  "account_id": "f3378389-4158-4444-8c7c-7b3350dec380",
  "count": 16,
  "results": [
    {
      "id": "00e92be3-42d7-4c83-b161-6bee129f0003",
      "transaction": "3c5cb5ba-5346-47a6-9bea-f4bb3c56bddb",
      "transaction_date": "2025-10-23",
      "transaction_amount": "71.99",
      "raw_description": "SPOTIFY AB STOCKHOLM",
      "kind": "off_schedule",
      "source": "ground_truth",
      "score": null,
      "note": "planted by the generator",
      "created_at": "2026-08-15T10:10:08.378372Z"
    }
  ]
}
```

The `source` field says where the flag came from: `ground_truth` is a
verified anomaly planted by the generator, `model` is a prediction from
the ml service. `score` is only filled in for model sourced flags.

### Account forecast

```
GET /api/accounts/{account_id}/forecast/
```

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `horizon_days` | integer | no | 30 | Length of the projection in days, 1-365 |

Values outside the range, or values that are not numbers, do not raise
an error; they are clamped to the bound or fall back to the default.

```json
{
  "account_id": "f3378389-4158-4444-8c7c-7b3350dec380",
  "horizon_days": 30,
  "model_version": "stub-0.1.0",
  "points": [
    {
      "date": "2025-12-30",
      "expected_balance": "-11815.73",
      "expected_income": "1724.29",
      "expected_expense": "1740.49"
    }
  ],
  "confidence": 0.897
}
```

This endpoint calls the ml service. If ml does not answer, the request
returns 503:

```json
{ "detail": "ml service is unreachable" }
```

## ml

Root: `http://localhost/ml`

All four endpoints take `POST` and expect a list of `TransactionIn`.
For now a rule based baseline runs in place of a model; the
`model_version` field reports this as `stub-0.1.0`. The schemas are the
production shape, so the contract does not change once a trained model
arrives.

`TransactionIn` fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | no | Echoed back in the response, for matching |
| `date` | date | yes | Transaction date |
| `amount` | decimal | yes | Must be greater than zero |
| `direction` | string | yes | `in` or `out` |
| `raw_description` | string | yes | 1-255 characters |

If the body does not match the schema the endpoint returns 422 and
points at the offending field.

### Health

```
GET /ml/healthz
```

```json
{ "status": "ok" }
```

### Categorization

```
POST /ml/categorize
```

```bash
curl -X POST http://localhost/ml/categorize \
  -H 'Content-Type: application/json' \
  -d '{"transactions":[{"id":"t1","date":"2025-12-31","amount":"141.79","direction":"out","raw_description":"BURGER KING ANKAMALL 8247"}]}'
```

```json
{
  "model_version": "stub-0.1.0",
  "predictions": [
    { "transaction_id": "t1", "category": "dining", "confidence": 0.9868 }
  ],
  "confidence": 0.9868
}
```

The category set is fixed: `salary`, `rent`, `subscription`,
`utilities`, `groceries`, `dining`, `electronics`, `travel`,
`health`, `other`.

### Recurring payments

```
POST /ml/recurring
```

```bash
curl -X POST http://localhost/ml/recurring \
  -H 'Content-Type: application/json' \
  -d '{"transactions":[{"id":"a","date":"2025-10-26","amount":"49.99","direction":"out","raw_description":"APPLE ICLOUD CORK"},{"id":"b","date":"2025-11-26","amount":"49.99","direction":"out","raw_description":"APPLE ICLOUD CORK"},{"id":"c","date":"2025-12-26","amount":"49.99","direction":"out","raw_description":"APPLE ICLOUD CORK"}]}'
```

```json
{
  "model_version": "stub-0.1.0",
  "series": [
    {
      "series_id": "5a7ecce44c66a9761e058aee9c7893de",
      "merchant": "APPLE ICLOUD CORK",
      "cadence": "monthly",
      "average_amount": "49.99",
      "occurrences": 3,
      "transaction_ids": ["a", "b", "c"],
      "next_expected_date": "2026-01-25",
      "confidence": 0.8025
    }
  ],
  "confidence": 0.8025
}
```

### Anomaly

```
POST /ml/anomaly
```

```bash
curl -X POST http://localhost/ml/anomaly \
  -H 'Content-Type: application/json' \
  -d '{"transactions":[{"id":"t1","date":"2025-12-31","amount":"141.79","direction":"out","raw_description":"BURGER KING ANKAMALL 8247"},{"id":"t2","date":"2025-12-30","amount":"8053.95","direction":"out","raw_description":"BURGER KING ANKAMALL 8247"}]}'
```

```json
{
  "model_version": "stub-0.1.0",
  "scores": [
    { "transaction_id": "t1", "score": 0.01, "kind": null, "is_anomaly": false },
    { "transaction_id": "t2", "score": 0.1207, "kind": null, "is_anomaly": false }
  ],
  "confidence": 0.0654
}
```

`score` is between 0 and 1. `kind` is only filled in when the kind can
be told apart, otherwise it stays `null`.

### Forecast

```
POST /ml/forecast
```

On top of the `TransactionBatch` fields the body takes:

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `horizon_days` | integer | no | 30 | Between 1 and 365 |

```bash
curl -X POST http://localhost/ml/forecast \
  -H 'Content-Type: application/json' \
  -d '{"horizon_days":3,"transactions":[{"id":"a","date":"2025-12-01","amount":"1000.00","direction":"in","raw_description":"SALARY"},{"id":"b","date":"2025-12-02","amount":"120.00","direction":"out","raw_description":"A101 YENIMAHALLE"}]}'
```

```json
{
  "model_version": "stub-0.1.0",
  "horizon_days": 3,
  "points": [
    {
      "date": "2025-12-03",
      "expected_balance": "1760.00",
      "expected_income": "1000.00",
      "expected_expense": "120.00"
    }
  ],
  "confidence": 0.897
}
```

## agentic

Root: `http://localhost/agent`

### Health

```
GET /healthz
```

Goes straight to the service: `http://localhost:8003/healthz`. It does
not touch a model provider and needs no key.

```json
{ "status": "ok" }
```

### Asking a question

```
POST /agent/chat
```

| Field | Type | Required | Description |
|---|---|---|---|
| `question` | string | yes | 1-1000 characters |
| `account_id` | uuid | no | Passed when the question is about one account |

The question is routed to an intent by keyword, a single tool matching
that intent is called through mcp, and the answer is produced from a
template. The intents are `subscriptions`, `anomalies`, `forecast`,
`summary`, `transactions`, `accounts` and `unknown`.

```bash
curl -X POST http://localhost/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"aboneliklerim neler","account_id":"f3378389-4158-4444-8c7c-7b3350dec380"}'
```

```json
{
  "question": "aboneliklerim neler",
  "intent": "subscriptions",
  "tool_name": "get_subscriptions",
  "answer": "4 recurring charges were found: APPLE ICLOUD CORK, MACFIT SPOR SALONU ANKARA, NETFLIX INTERNATIONAL AMSTERDAM, SPOTIFY AB STOCKHOLM.",
  "tool_results": { "account_id": "…", "count": 4, "results": [] },
  "error": null
}
```

A question that needs an account but arrives without `account_id` does
not fail; the intent is switched to `accounts` and the account list is
returned instead.

When no intent can be inferred, no tool is called:

```json
{
  "question": "hava nasıl",
  "intent": "unknown",
  "tool_name": null,
  "answer": "I could not tell what this question is about. Try asking about transactions, subscriptions, anomalies, totals or a forecast.",
  "tool_results": {},
  "error": null
}
```

If the tool call fails the request still returns 200; the problem is
carried in the `error` field and `answer` explains it to the user.

An empty `question` body returns 422.

### mcp tool surface

`agentic` reaches data only through `mcp`. The tools are not HTTP
endpoints; they are called over the mcp protocol and are not meant to
be consumed directly.

| Tool | Matching endpoint |
|---|---|
| `list_accounts` | `GET /api/accounts/` |
| `get_transactions` | `GET /api/transactions/` |
| `search_merchants` | `GET /api/merchants/` |
| `get_account_summary` | `GET /api/accounts/{id}/summary/` |
| `get_subscriptions` | `GET /api/accounts/{id}/subscriptions/` |
| `get_anomalies` | `GET /api/accounts/{id}/anomalies/` |
| `get_forecast` | `GET /api/accounts/{id}/forecast/` |

If the upstream does not answer, the tool does not raise; it returns a
payload with `error` filled in and `results` empty.
