# Features & User Stories
## AI-Based Business Report Generation and Analytics System

Priority key: **P0** = must have for MVP launch · **P1** = fast-follow · **P2** = later

---

## Epic 1 — Auth & Onboarding (P0)

- As a new user, I want to sign up with email/password and automatically get an organization created, so I can start using the product immediately.
  - *AC:* Signup creates `organizations` + `users` row; user is `owner`; access + refresh tokens returned; redirected to onboarding.
- As a new user, I want a guided first step to upload my first dataset, so I reach value fast.
  - *AC:* Onboarding screen prompts upload before showing the main dashboard; skippable but discouraged.
- As a returning user, I want to log in and stay logged in across sessions, so I don't re-auth constantly.
  - *AC:* Refresh token flow works; access token auto-renews silently in the frontend.
- As an owner, I want to invite teammates by email with a role, so my team can collaborate.
  - *AC:* Invite generates a token/link; invited user signs up joins the existing org, not a new one.

## Epic 2 — Data Ingestion (P0)

- As a user, I want to upload a CSV or Excel file, so the system can analyze it.
  - *AC:* Accepts `.csv`, `.xlsx`; rejects other types with a clear error; 25MB limit enforced client- and server-side.
- As a user, I want to see a preview of my data and inferred column types before generating a report, so I can catch mistakes early.
  - *AC:* Preview table shows first 50 rows; each column shows inferred type (number/date/text/category); user can override a type.
- As a user, I want to be warned if my data has quality issues (missing values, mixed types), so I know the report might be limited.
  - *AC:* Dataset detail page shows a data-quality summary (e.g., "12% missing in `region` column").

## Epic 3 — AI Report Generation (P0 — core value prop)

- As a user, I want to generate a report from my dataset with one click, so I get an instant business overview.
  - *AC:* "Generate report" triggers background job; UI shows progress state; completes in < 60s for ≤100k rows.
- As a user, I want the report to include real numbers computed from my actual data, not made-up figures, so I can trust it.
  - *AC:* Every number in `narrative_text` traces back to a value present in `computed_stats_json`.
- As a user, I want charts auto-selected based on what's in my data, so I don't have to configure anything.
  - *AC:* Time-series columns → line chart; categorical breakdowns → bar chart; at least 3 charts per report where data supports it.
- As a user, I want the report to call out notable changes or anomalies in plain language, so I don't have to spot them myself.
  - *AC:* Narrative includes a "Highlights / Watch-outs" section referencing period-over-period change or outliers.
- As a user, I want to export my report as PDF or Word, so I can share it outside the platform.
  - *AC:* Export endpoint returns a correctly formatted PDF/DOCX matching the on-screen report.

## Epic 4 — Conversational Analytics / Chat With Data (P0)

- As a user, I want to ask a question about my dataset in plain English, so I don't need to know SQL or Excel formulas.
  - *AC:* Free-text input; response within a few seconds for typical aggregate questions.
- As a user, I want to see what query actually ran behind my answer, so I can trust and verify it.
  - *AC:* `query_executed` shown alongside every assistant answer, in plain readable form.
- As a user, I want a chart alongside a text answer when relevant, so I can visualize the result.
  - *AC:* Aggregate/grouped answers return `chart_data_json` when the result shape supports charting.
- As a user, I want the system to refuse gracefully if I ask something it can't safely answer, so I'm not misled by a wrong answer.
  - *AC:* Out-of-whitelist queries return a clear "I can't run that kind of query" message, not a silent failure or hallucinated answer.

## Epic 5 — Forecasting (P0)

- As a user, I want to pick a metric and see where it's headed, so I can plan ahead.
  - *AC:* User selects target column + date column + horizon; job runs; forecast chart with confidence band renders.
- As a user, I want a plain-language summary of the forecast, not just a chart, so I understand what it means.
  - *AC:* `result_json.summary_text` present and references the forecast direction/magnitude.

## Epic 6 — Report Management (P0)

- As a user, I want to see all my past reports in one place, so I can find and reuse them.
  - *AC:* Reports library lists title, dataset, date, status; searchable.
- As a user, I want to re-open a completed report exactly as it was generated, so historical reports stay accurate.
  - *AC:* Report detail page renders from stored `narrative_text`/`charts_json`, not re-computed live.

## Epic 7 — Team & Org Management (P1)

- As an owner, I want to control what each teammate can do, so I can limit access appropriately.
  - *AC:* Role-based permission checks enforced server-side on every mutating endpoint, not just hidden in the UI.

## Epic 8 — Scheduled Reports (P1/P2)

- As a user, I want a report to regenerate automatically every week/month and email to stakeholders, so I don't have to remember to run it.
  - *AC:* (Post-MVP) Celery beat schedule triggers `report.generate` job per `scheduled_reports` row; email sent with PDF attached or link.

## Epic 9 — Billing (P2)

- As an owner, I want to upgrade my plan when I hit free-tier limits, so I can keep using the product.
  - *AC:* (Post-MVP) Stripe checkout; `organizations.plan` updated via webhook.
