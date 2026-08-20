# Technical Architecture
## AI-Based Business Report Generation and Analytics System

---

## 1. Stack Summary

| Layer | Technology | Why |
|---|---|---|
| Backend framework | **FastAPI** (Python 3.11+) | Async-native (good for LLM streaming + I/O-bound jobs), auto-generated OpenAPI docs, strong typing via Pydantic — pairs well with an AI coding agent because contracts are explicit. |
| Frontend | **React 18 + TypeScript + Vite** | Fast dev loop, huge ecosystem, easy to pair with Tailwind + shadcn/ui for a professional-looking dashboard fast. |
| Styling | **Tailwind CSS + shadcn/ui** | Consistent design system without hand-rolling components. |
| Charts | **Recharts** | Good React ergonomics for the dashboard/report charts. |
| Database | **PostgreSQL 15+** | Relational integrity for multi-tenant data; `pgvector` extension available later if you add semantic search over reports. |
| Background jobs | **Celery + Redis** | Report generation and forecasting are slow — must not block the request/response cycle. |
| File storage | **S3-compatible object storage** (AWS S3 in prod, MinIO locally) | Uploaded CSV/XLSX and generated PDFs live here, not in the DB. |
| Auth | **JWT (access + refresh tokens)**, passwords hashed with `bcrypt`/`argon2` | Standard, stateless, easy to reason about for a multi-tenant SaaS. |
| LLM provider | **Anthropic Claude API** (or OpenAI as alternative) via a thin provider-abstraction layer | Used for report narration and NL→query translation — never for raw arithmetic (see §7). |
| Forecasting | **Prophet** or **statsmodels (ETS/ARIMA)** | Off-the-shelf time series forecasting, no custom ML needed for MVP. |
| Data parsing | **pandas** | CSV/XLSX parsing, schema inference, aggregate computation. |
| PDF/DOCX export | **WeasyPrint** (PDF from HTML) + **python-docx** | Standard, well-documented libraries. |
| Containerization | **Docker + Docker Compose** (local), target host **Railway/Render** for MVP, migrate to AWS ECS/Fargate later if needed | Keep MVP hosting simple and cheap. |
| CI | **GitHub Actions** | Lint, type-check, test on every PR. |

---

## 2. High-Level Architecture

```
┌─────────────────┐      HTTPS/JSON       ┌──────────────────────┐
│  React SPA       │ ───────────────────▶ │  FastAPI (API layer) │
│  (Vite, TS)       │ ◀─────────────────── │  /api/v1/*            │
└─────────────────┘                       └──────────┬────────────┘
                                                        │
                        ┌───────────────────────────────┼───────────────────────────────┐
                        │                                │                                │
                 ┌──────▼──────┐               ┌─────────▼─────────┐            ┌─────────▼─────────┐
                 │ PostgreSQL   │               │ Redis + Celery     │            │ S3 / MinIO          │
                 │ (all core    │               │ workers             │            │ (uploaded files,    │
                 │ tables)      │               │ - report generation │            │ generated PDFs)     │
                 └──────────────┘               │ - forecasting jobs  │            └──────────────────────┘
                                                  │ - file processing   │
                                                  └──────────┬──────────┘
                                                              │
                                                    ┌─────────▼─────────┐
                                                    │ LLM Provider API   │
                                                    │ (Claude/OpenAI)    │
                                                    └────────────────────┘
```

Key principle: the **API layer stays fast and synchronous-feeling** for the user; anything slow (report generation, forecasting, large file parsing) is handed off to a Celery worker, and the frontend polls or uses a websocket/SSE channel for status updates.

---

## 3. Repo Structure (monorepo)

```
/repo-root
  /backend
    /app
      /api/v1/routers        # one file per resource: auth.py, datasets.py, reports.py, chat.py, forecasts.py, orgs.py
      /core                  # config, security (JWT), dependencies
      /models                # SQLAlchemy models
      /schemas                # Pydantic request/response schemas
      /services               # business logic (report_service.py, chat_service.py, forecast_service.py)
      /workers                 # Celery tasks
      /db                       # session, migrations (Alembic)
      /llm                       # provider abstraction, prompt templates
      main.py
    /tests
    Dockerfile
    requirements.txt / pyproject.toml
  /frontend
    /src
      /pages                  # route-level components
      /components              # shared UI (shadcn-based)
      /features                 # feature-scoped components+hooks (reports/, chat/, forecast/, datasets/)
      /api                       # typed API client functions
      /lib                        # utils
      /hooks
    Dockerfile
    package.json
  /docs                        # this documentation package
  docker-compose.yml
  .github/workflows/ci.yml
```

---

## 4. Environment Variables (`.env.example`)

```
# App
ENVIRONMENT=development
SECRET_KEY=changeme
API_BASE_URL=http://localhost:8000

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/reportgen

# Redis / Celery
REDIS_URL=redis://localhost:6379/0

# Storage
S3_ENDPOINT_URL=http://localhost:9000   # MinIO locally
S3_BUCKET=reportgen-uploads
S3_ACCESS_KEY=...
S3_SECRET_KEY=...

# Auth
JWT_SECRET=changeme
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=14

# LLM
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=...
LLM_MODEL=claude-sonnet-4-6

# Email (invites, post-MVP scheduled reports)
SMTP_HOST=...
SMTP_USER=...
SMTP_PASSWORD=...
```

---

## 5. Third-Party Services to Set Up Before Building

1. LLM API key (Anthropic or OpenAI).
2. Object storage — start with local MinIO via Docker Compose, no account needed to start building.
3. Postgres — local via Docker Compose to start.
4. (Post-MVP) Stripe account for billing, transactional email provider (Postmark/Resend) for invites.

---

## 6. Security Considerations (non-negotiable, read before Phase 2)

1. **Multi-tenant isolation:** every query-bearing table has `org_id`; every service-layer query filters by the authenticated user's `org_id`. Never trust an `org_id` passed from the client — always derive it from the JWT.
2. **No LLM-generated code execution.** For chat-with-data, the LLM's job is to select from a whitelisted set of safe operations (e.g., "filter, group_by, aggregate, sort, limit" on a pre-validated dataframe/table) — never to produce arbitrary Python/SQL that gets `eval`'d or executed directly. Build a small internal query DSL the LLM outputs as structured JSON, validate it, then execute it yourself.
3. **Report numbers are computed, not generated.** All statistics (totals, averages, growth %, outliers) are computed in Python from the actual data first. The LLM call receives those computed numbers and writes narrative text around them — it is never asked to "calculate" anything itself. This is the single most important integrity rule in the system.
4. **File upload validation:** enforce file type, size limit, and row/column sanity checks before processing; scan for formula-injection risks in CSV (cells starting with `=`, `+`, `-`, `@`) before any export back to Excel.
5. **Secrets never in the repo** — `.env` gitignored, secrets injected via host/CI environment.

---

## 7. Report Generation Pipeline (detail — this is the core AI flow)

```
1. Load dataset (pandas) → validate schema
2. Compute deterministic stats: totals, trends, period-over-period change,
   top/bottom performers, simple outlier detection (z-score or IQR)
3. Select 3-5 chart candidates based on data shape (time series → line chart,
   categorical breakdown → bar chart, etc.)
4. Build an LLM prompt containing ONLY the computed stats (as structured JSON)
   + report intent → LLM returns narrative text sections (summary, highlights,
   watch-outs) referencing those exact numbers
5. Assemble narrative + charts into report record → render to PDF/DOCX on export
```

## 8. Chat-With-Data Pipeline (detail)

```
1. User question (NL) + dataset schema → LLM call constrained to output a
   structured query object (JSON: operation, columns, filters, group_by, agg)
2. Validate the structured query against the whitelist + dataset schema
3. Execute the validated query against pandas/SQL (read-only, row-limited)
4. Result → optionally pass back through LLM to phrase a natural-language
   answer ("Revenue grew 12% in Q2, driven mainly by...")
5. Return answer + chart (if applicable) + the human-readable query that ran
```

## 9. Deployment (MVP)

- **Local dev:** `docker-compose up` — Postgres, Redis, MinIO, backend, frontend, one Celery worker.
- **Staging/Prod (MVP):** Railway or Render (managed Postgres + Redis + easy container deploys) to avoid AWS setup overhead pre-revenue. Migrate to AWS (ECS/Fargate + RDS + S3) once there's usage to justify the complexity.
- **CI:** GitHub Actions — lint (ruff/eslint), type-check (mypy/tsc), run backend + frontend tests on every PR.
