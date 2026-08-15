SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c

COMPOSE := docker compose -f docker/docker-compose.yml
PY_SERVICES := data backend ml mcp agentic

.PHONY: up down reset seed test logs lint fmt

up:
	$(COMPOSE) up -d --build
	$(COMPOSE) ps

down:
	$(COMPOSE) down

reset:
	$(COMPOSE) down -v
	$(COMPOSE) up -d --build
	$(COMPOSE) ps

seed:
	uv run --directory data python -m generator --seed 42 --profile employee --months 24 --out out
	$(COMPOSE) exec backend python manage.py seed_data \
		--file /data/out/transactions_employee_42.json \
		--labels /data/out/labels_employee_42.json

# services without a tests directory are skipped, so the target stays
# usable while the project is still being filled in
test:
	@for service in $(PY_SERVICES); do \
		if [ -d "$$service/tests" ]; then \
			echo "--- $$service"; \
			uv run --directory $$service pytest -q; \
		fi; \
	done
	@if [ -d web/node_modules ]; then npm --prefix web run build; fi

logs:
	$(COMPOSE) logs -f --tail 100

lint:
	@for service in $(PY_SERVICES); do \
		if [ -f "$$service/pyproject.toml" ]; then \
			echo "--- $$service"; \
			uv run --directory $$service ruff check .; \
			uv run --directory $$service black --check .; \
		fi; \
	done
	@if [ -d web/node_modules ]; then npm --prefix web run lint; fi

fmt:
	@for service in $(PY_SERVICES); do \
		if [ -f "$$service/pyproject.toml" ]; then \
			uv run --directory $$service ruff check --fix .; \
			uv run --directory $$service black .; \
		fi; \
	done
