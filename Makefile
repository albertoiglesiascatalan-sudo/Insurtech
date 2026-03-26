.PHONY: dev stop build seed ingest newsletter-send test lint install

# ── Dev ────────────────────────────────────────────────────────────────────────
dev:
	docker compose up --build

stop:
	docker compose down

build:
	docker compose build

# ── Database ───────────────────────────────────────────────────────────────────
migrate:
	docker compose exec api alembic upgrade head

seed:
	docker compose exec api python -m app.scripts.seed_sources

# Create first admin user
make-admin:
	@email=$${email:-admin@insurtech.news}; \
	docker compose exec api python -m app.scripts.make_admin --email=$$email

# ── Ingestion ──────────────────────────────────────────────────────────────────
ingest:
	docker compose exec api python -m app.scripts.run_ingestion

# ── Newsletter ─────────────────────────────────────────────────────────────────
newsletter-send:
	@profile=$${profile:-investor}; \
	frequency=$${frequency:-daily}; \
	docker compose exec api python -m app.scripts.send_newsletter --profile=$$profile --frequency=$$frequency

# ── Tests ──────────────────────────────────────────────────────────────────────
test:
	docker compose exec api pytest tests/ -v
	cd apps/web && pnpm test

test-api:
	docker compose exec api pytest tests/ -v

test-e2e:
	cd apps/web && pnpm exec playwright test

# ── Linting ────────────────────────────────────────────────────────────────────
lint:
	cd apps/api && ruff check . && mypy app/
	cd apps/web && pnpm lint

# ── Install ────────────────────────────────────────────────────────────────────
install:
	cd apps/web && pnpm install
	cd apps/api && pip install -r requirements.txt

# ── Local (without Docker) ─────────────────────────────────────────────────────
dev-api:
	cd apps/api && uvicorn app.main:app --reload --port 8000

dev-web:
	cd apps/web && pnpm dev
