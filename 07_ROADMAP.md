# Build Roadmap
## AI-Based Business Report Generation and Analytics System

Phased for solo/small-team, AI-assisted ("vibe coding") development. Estimates assume you + an AI coding agent, not a full team — treat them as rough sizing, not commitments.

---

### Phase 0 — Foundation (≈2–3 days)
**Goal:** empty but running full-stack skeleton.
- Repo scaffolding per `02_TECH_ARCHITECTURE.md` folder structure.
- Docker Compose: Postgres, Redis, MinIO, backend, frontend all boot together.
- FastAPI app with health-check route; React app with routing shell + Tailwind/shadcn set up.
- Alembic migrations initialized.
- CI pipeline (lint + type-check) green on an empty project.
**Exit criteria:** `docker-compose up` gives a working "Hello World" full stack.

### Phase 1 — Auth & Org Foundation (≈3–4 days)
**Goal:** Epic 1 complete.
- `organizations`, `users` tables + migrations.
- Register/login/refresh/logout endpoints, JWT issuing + validation dependency.
- Frontend: login/register pages, auth context, protected routes.
**Exit criteria:** Can sign up, get redirected into an authenticated shell, log out and back in.

### Phase 2 — Data Ingestion (≈4–5 days)
**Goal:** Epic 2 complete.
- `datasets` table, S3/MinIO upload wiring, Celery task for parsing (pandas: type inference, row count, quality flags).
- Endpoints: upload, list, detail, preview, patch, delete.
- Frontend: Data Sources page, upload dropzone, dataset detail/preview page.
**Exit criteria:** Upload a real CSV, see correct schema inference and a data preview.

### Phase 3 — AI Report Generation (≈6–8 days, core phase)
**Goal:** Epic 3 complete — this is the product's primary value, budget the most time here.
- Stats computation service (deterministic aggregates, trend detection, outliers) — build and unit-test this *before* touching the LLM prompt.
- LLM provider abstraction + prompt template that narrates computed stats only.
- Chart-selection logic based on data shape.
- Celery task orchestrating the full pipeline; `reports` table.
- PDF/DOCX export (WeasyPrint/python-docx).
- Frontend: report config screen, generating/progress state, report viewer, export buttons.
**Exit criteria:** Generate a report from a real dataset, verify every number in the narrative matches `computed_stats_json`, export to PDF and DOCX successfully.

### Phase 4 — Chat With Data (≈5–7 days)
**Goal:** Epic 4 complete.
- Structured query DSL (whitelist of safe operations) + validator.
- LLM prompt constrained to emit the DSL, not free-form code.
- Execution engine (pandas, read-only, row/time limited) + NL answer phrasing.
- `chat_sessions`/`chat_messages` tables, endpoints.
- Frontend: chat UI with dataset selector, message thread, inline chart, visible query.
**Exit criteria:** Ask 10 varied real questions against a test dataset; verify no unsafe query ever gets a "silent wrong answer" — it either answers correctly or refuses clearly.

### Phase 5 — Forecasting (≈3–4 days)
**Goal:** Epic 5 complete.
- `forecast_jobs` table, Celery task wrapping Prophet/statsmodels.
- Endpoints: run, get result.
- Frontend: forecast config + chart with confidence band + summary text.
**Exit criteria:** Run a forecast on a seasonal test dataset, sanity-check the output visually.

### Phase 6 — Reports Library, Dashboard, Team Management (≈3–4 days)
**Goal:** Epics 6 & 7 complete.
- Dashboard summary endpoint + home screen.
- Reports library list/search.
- Org invite flow + role-based permission checks on all mutating endpoints.
**Exit criteria:** A second invited teammate can log in, see the org's data, and is correctly blocked from actions their role shouldn't allow.

### Phase 7 — Polish & Launch Readiness (≈4–5 days)
**Goal:** MVP is demo/launch-ready.
- Error states, empty states, loading states audited across every screen.
- Rate limiting on generation endpoints (protect LLM cost).
- Basic audit logging.
- Deploy to Railway/Render staging, smoke test end-to-end.
- (If time allows) scheduled reports (Epic 8) as a fast-follow, not a blocker.
**Exit criteria:** A brand-new user can sign up, upload data, get a report, chat, and forecast — end to end, with no dead ends.

---

## Post-MVP Backlog (do not build during MVP phases above)
- Live DB connectors (Postgres/MySQL/Snowflake/Google Sheets)
- Stripe billing integration
- Scheduled report emailing (beyond the data model already in place)
- White-labeling for agency use case
- Semantic search across past reports (pgvector)
- Mobile-optimized layouts
