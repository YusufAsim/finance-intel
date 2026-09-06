# finance-intel

A multi-service financial intelligence platform that works on bank
statements. Spending data is generated, categorised, modelled and then
queried through a dashboard and a natural language interface.

The platform answers five questions:

- Where is my money going, by category?
- Which recurring payments am I making without noticing?
- Is there anything unusual this month?
- Where does my balance land next month?
- Can I ask all of this in plain language?

## Status

The contract between the services and the end to end flow are in place:
the data generator, the domain models, the REST API, the tool surface,
the router and the dashboard all run. The model layer is the one piece
still missing.

| Layer | Status |
|---|---|
| Synthetic data generator | Labelled, deterministic, done |
| backend domain + REST API | Done |
| mcp tool surface | Done |
| agentic router | Rule based, done |
| web dashboard | Done |
| ml prediction layer | **Deterministic stub** |

The `ml` service does not host a trained model yet. The endpoints return
the real response schema, but the logic behind them is a rule based
placeholder in `ml/app/pipelines/stubs.py`; `MODEL_VERSION` reports this
as `stub-0.1.0`. The order is deliberate: the HTTP contract was fixed
first, so that none of the other services have to change when a model
arrives.

Models will be developed under `notebooks/`, saved into `ml/artifacts/`
and loaded through `ml/app/models/`. Because the generator hands over
its labels (category, series id, anomaly flag), scoring them is
measurable directly.

## Architecture

```
                            ┌──────────────────────────┐
                            │           web            │
                            │  React + TypeScript      │
                            │  Vite dashboard :5173    │
                            └────────────┬─────────────┘
                                         │ HTTP
                            ┌────────────▼─────────────┐
                            │          nginx           │
                            │    reverse proxy :80     │
                            └───┬──────────────────┬───┘
                                │                  │
                 /api/*         │                  │  /agent/*
                                │                  │
              ┌─────────────────▼──┐        ┌──────▼───────────────┐
              │      backend       │        │       agentic        │
              │  Django 5 + DRF    │        │  FastAPI + LangGraph │
              │  domain + REST     │        │  router + tool call  │
              └───┬────────────┬───┘        └──────────┬───────────┘
                  │            │                       │
                  │ SQL        │ HTTP                  │ HTTP
                  │            │                       │
        ┌─────────▼──────┐     │              ┌────────▼─────────┐
        │   postgres     │     │              │       mcp        │
        │   finance db   │     │              │     FastMCP      │
        └────────────────┘     │              │   tool surface   │
                               │              └───┬──────────┬───┘
                               │                  │          │
                               │        HTTP      │ HTTP     │ HTTP
                               │                  │          │
                        ┌──────▼──────────────────▼──┐       │
                        │            ml              │◄──────┘
                        │  FastAPI, model service    │
                        └────────────────────────────┘
```

Only `backend` writes to the database. `mcp` and `agentic` never reach
the database or another service's tables directly; everything goes over
the HTTP contract.

## Services

| Service | Container | Host port | Container port | Role |
|---|---|---|---|---|
| nginx | `fi-nginx` | 80 | 80 | Single entry point, reverse proxy |
| backend | `fi-backend` | 8000 | 8000 | Domain models and REST API |
| ml | `fi-ml` | 8001 | 8000 | Categorisation, anomalies, forecast |
| mcp | `fi-mcp` | 8002 | 8000 | Exposes endpoints as tools |
| agentic | `fi-agentic` | 8003 | 8000 | Question routing and tool calls |
| web | `fi-web` | 5173 | 5173 | Dashboard |
| postgres | `fi-postgres` | 5433 | 5432 | Database |

Postgres is published on 5433. If a local PostgreSQL is already
installed, 5432 collides; 5433 avoids it. Containers still reach each
other on 5432 over the compose network.

## Setup

Requirements: Docker and Docker Compose. To run the tests locally you
also need [uv](https://docs.astral.sh/uv/) and Node.js 20+.

### 1. Prepare the env files

Templates ship with an `.example` suffix, copy and edit them:

```bash
cd docker
for f in *.env.example; do cp "$f" "${f%.example}"; done
```

At the very least, replace the `change-me` values in `postgres.env` and
`backend.env`.

### 2. Bring the stack up

```bash
cd docker
docker compose up -d --build
docker compose ps
```

It is ready once all seven containers report `healthy`. The first start
takes a few minutes because the images are built.

### 3. Create the database schema

```bash
docker compose exec backend python manage.py migrate
```

### 4. Generate and load data

The generator writes one transaction file per profile, with a matching
label file next to it:

```bash
uv run --directory data python -m generator --seed 42 --profile all --months 24 --out out/
```

Output lands under `data/out/` and is mounted into the container as
`/data/out`. Load each profile in turn:

```bash
docker compose exec backend python manage.py seed_data --file /data/out/transactions_employee_42.json
docker compose exec backend python manage.py seed_data --file /data/out/transactions_freelancer_42.json
docker compose exec backend python manage.py seed_data --file /data/out/transactions_student_42.json
```

If the label file is not passed explicitly, the command finds its
counterpart in the same directory. The generator is deterministic: the
same seed always produces the same output. `seed_data` is idempotent,
running it twice does not duplicate records.

On Git Bash the container paths may be rewritten as Windows paths;
prefix the commands with `MSYS_NO_PATHCONV=1`.

### 5. Open it

| Address | Content |
|---|---|
| http://localhost:5173 | Dashboard |
| http://localhost/api/ | REST API root |
| http://localhost/admin/ | Django admin |
| http://localhost/agent/chat | Natural language endpoint |

The admin needs a user:

```bash
docker compose exec backend python manage.py createsuperuser
```

## Env fields

### `postgres.env`

| Field | Description |
|---|---|
| `POSTGRES_DB` | Database name |
| `POSTGRES_USER` | Database user |
| `POSTGRES_PASSWORD` | User password, consumed by the postgres image |

### `backend.env`

| Field | Description |
|---|---|
| `DJANGO_DEBUG` | 1 for development, 0 for production |
| `DJANGO_SECRET_KEY` | Session and signing key |
| `DJANGO_ALLOWED_HOSTS` | Comma separated list of allowed hosts |
| `DJANGO_LOG_LEVEL` | Log level |
| `DATABASE_URL` | Postgres connection string |
| `CORS_ALLOWED_ORIGINS` | Origins allowed to call from the browser |
| `ML_BASE_URL` | Address of the ml service |
| `ML_TIMEOUT_SECONDS` | Timeout for ml calls |
| `DATA_DIR` | Directory the generator output is mounted at |

### `ml.env`

| Field | Description |
|---|---|
| `ML_LOG_LEVEL` | Log level |
| `BACKEND_BASE_URL` | Backend the training data is pulled from |
| `BACKEND_TIMEOUT_SECONDS` | Timeout for backend calls |
| `ARTIFACTS_DIR` | Directory holding trained model files |

### `mcp.env`

| Field | Description |
|---|---|
| `MCP_LOG_LEVEL` | Log level |
| `BACKEND_BASE_URL` | Backend the tools call |
| `ML_BASE_URL` | ml service the tools call |
| `HTTP_TIMEOUT_SECONDS` | Timeout for upstream calls |

### `agentic.env`

| Field | Description |
|---|---|
| `AGENTIC_LOG_LEVEL` | Log level |
| `MCP_BASE_URL` | Address of mcp, the single data gateway |
| `HTTP_TIMEOUT_SECONDS` | Timeout for tool calls |
| `MAX_TOOL_CALLS` | Upper bound on tool calls for one question |

### `web.env`

| Field | Description |
|---|---|
| `VITE_API_BASE_URL` | REST API address used by the browser |
| `VITE_AGENT_BASE_URL` | agentic address used by the browser |

Both values run in the browser, so they point at the nginx entry point
rather than a container name.

## API summary

Full reference: [`docs/API.md`](docs/API.md).

### backend — `/api`

| Method | Path | Role |
|---|---|---|
| GET | `/api/accounts/` | Account list |
| GET | `/api/transactions/` | Transaction list, filtered and paginated |
| GET | `/api/categories/` | Category list |
| GET | `/api/merchants/` | Merchant list |
| GET | `/api/subscriptions/` | Recurring payments |
| GET | `/api/budgets/` | Budgets |
| GET | `/api/anomaly-flags/` | Anomaly flags |
| GET | `/api/accounts/{id}/summary/` | Income, spending, net, category breakdown |
| GET | `/api/accounts/{id}/subscriptions/` | Subscriptions of the account |
| GET | `/api/accounts/{id}/anomalies/` | Anomalies of the account |
| GET | `/api/accounts/{id}/forecast/` | Balance forecast |

List endpoints accept `page`, `page_size`, `ordering` and `search`.
Every resource has its own filters; `page_size` is capped at 500.

### ml — `/ml`

| Method | Path | Role |
|---|---|---|
| POST | `/ml/categorize` | Assigns a category to a list of transactions |
| POST | `/ml/recurring` | Marks recurring series |
| POST | `/ml/anomaly` | Scores unusual transactions |
| POST | `/ml/forecast` | Produces a balance forecast |

### agentic — `/agent`

| Method | Path | Role |
|---|---|---|
| POST | `/agent/chat` | Routes the question, calls a tool, returns an answer |

### Health endpoints

Every service answers `GET /healthz` with `{"status": "ok"}`.

| Address | Service |
|---|---|
| http://localhost/api/healthz | backend |
| http://localhost/ml/healthz | ml |
| http://localhost:8002/healthz | mcp |
| http://localhost:8003/healthz | agentic |

## Directory tree

```
finance-intel/
├── backend/          # Django 5 + DRF, domain and REST API
│   ├── config/       # settings, urls, middleware, pagination
│   ├── apps/
│   │   ├── accounts/
│   │   ├── transactions/
│   │   └── insights/ # derived metrics, ml client
│   └── tests/
├── ml/               # FastAPI model service
│   ├── app/
│   │   ├── routers/
│   │   ├── pipelines/
│   │   └── models/
│   ├── artifacts/
│   └── tests/
├── mcp/              # FastMCP tool surface
│   ├── app/
│   │   ├── tools/
│   │   └── clients/
│   └── tests/
├── agentic/          # FastAPI + LangGraph
│   ├── app/
│   │   ├── graph/    # nodes and router
│   │   └── tools/    # mcp bindings
│   └── tests/
├── web/              # React + TypeScript dashboard
│   └── src/
│       ├── pages/
│       ├── components/
│       ├── lib/      # api client, hooks, formatters
│       └── types/
├── data/
│   ├── generator/    # synthetic statement generator
│   └── out/          # generated csv/json
├── docker/           # compose, nginx, env templates
├── notebooks/        # model development
└── docs/
```

## Technology

| Layer | Choice |
|---|---|
| API | Django 5, Django REST Framework, django-filter |
| Database | PostgreSQL 16 |
| Model service | FastAPI, pydantic v2 |
| Tool surface | FastMCP |
| Flow | LangGraph |
| Interface | React 18, TypeScript, Vite 5, Tailwind 4, Recharts |
| Reverse proxy | nginx |
| Python packaging | uv |
| Tests | pytest, pytest-django, vitest, Testing Library |
| Format and lint | ruff, black, ESLint |

## Tests

```bash
uv run --directory data pytest
uv run --directory backend pytest
uv run --directory ml pytest
uv run --directory mcp pytest
uv run --directory agentic pytest

cd web && npm test
cd web && npm run lint
cd web && npm run build
```

End to end check while the stack is up:

```bash
curl localhost/api/healthz
curl localhost/ml/healthz
curl -X POST localhost/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"aboneliklerim neler","account_id":"<account-id>"}'
```

## Data generator

The generator produces a deterministic statement from a single seed and
writes the ground truth labels alongside it: the true category, the
subscription series id, the anomaly flag and the anomaly kind
(`amount_spike`, `duplicate`, `unusual_merchant`, `off_schedule`).

```bash
uv run --directory data python -m generator --seed 42 --months 24 --out out/
```

Because the labels come for free, model output is measurable: the gap
between prediction and truth is computed directly.

## License

MIT. See `LICENSE` for the full text.
