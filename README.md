# InsurTech Intelligence

> The world's best insurtech newsletter platform — global news, AI-powered, personalised.

## What it is

A full-stack news aggregation + newsletter platform covering the global insurtech industry:
- **55+ verified sources** — trade press, VC/startup news, regulators, research firms (RSS + scraping)
- **AI pipeline** — automatic summaries (GPT-4o-mini), categorisation into 15 topics, semantic deduplication (pgvector), sentiment analysis
- **3 reader profiles** — Investor, Founder, General (personalised content + AI-generated newsletter tone)
- **15 topic categories** — Embedded Insurance, AI, Cyber, Health, Auto, P&C, Climate/Parametric, Regulatory, Funding/M&A, and more
- **6 regions** — US, EU, APAC, LATAM, MEA, Global
- **Email newsletter** — daily or weekly digest via Resend, AI-written editorial narrative

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router) + TailwindCSS |
| Backend | Python FastAPI (async) |
| Database | PostgreSQL 16 + pgvector |
| Cache/Queue | Redis 7 |
| AI | OpenAI GPT-4o-mini + text-embedding-3-small |
| Email | Resend |
| Infra | Docker Compose → Railway/Fly.io |

## Quick start

```bash
# 1. Configure
cp .env.example .env
# Edit .env with OPENAI_API_KEY and RESEND_API_KEY

# 2. Start everything
make dev

# 3. Migrate + seed
make migrate
make seed

# 4. First ingestion
make ingest

# 5. Open http://localhost:3000
```

## Make commands

| Command | Description |
|---|---|
| `make dev` | Start all services |
| `make migrate` | Run DB migrations |
| `make seed` | Seed 55+ sources |
| `make ingest` | Trigger manual ingestion |
| `make newsletter-send profile=investor frequency=daily` | Send newsletter |
| `make test` | Run tests |

## Sources

55+ verified global sources: trade press, VC/startup press, regulators (EIOPA, FCA, NAIC, FSB), research firms (Swiss Re, Munich Re, McKinsey), APAC, LATAM, MEA coverage.
