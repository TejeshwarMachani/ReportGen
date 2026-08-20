# Product Requirements Document (PRD)
## AI-Based Business Report Generation and Analytics System

**Status:** Draft v1.0 · **Owner:** [you] · **Stage:** Pre-build / MVP

---

## 1. Vision

Most small and mid-sized businesses generate data (sales, inventory, marketing, ops) but can't afford a data analyst to turn it into decisions. This product lets a non-technical business user upload their data and, in minutes, get a readable report, ask it follow-up questions in plain English, and see where key metrics are headed — without touching a spreadsheet formula or hiring anyone.

## 2. Problem Statement

- Business owners have data scattered across spreadsheets/exports but no time or skill to analyze it.
- Existing BI tools (Power BI, Tableau, Looker) are built for analysts, not owners — steep learning curve, expensive seats, requires modeling work before you get value.
- Generic AI chatbots can't be trusted with a company's actual numbers, don't produce shareable reports, and don't do forecasting out of the box.

## 3. Target Users

| Persona | Description | Primary need |
|---|---|---|
| **Owner/Founder (Priya, 34)** | Runs a 15-person D2C brand. Not technical. | Weekly report she can read in 5 minutes and forward to investors. |
| **Ops/Finance lead (Raghav, 29)** | Handles reporting manually in Excel today. | Ask ad-hoc questions without waiting on IT or building a new pivot table. |
| **Small agency/consultant (Meera, 41)** | Reports on client performance monthly. | Fast, polished, white-label-able reports across multiple clients (multi-tenant). |

## 4. Goals & Success Metrics

| Goal | Metric | MVP Target |
|---|---|---|
| Prove core value loop works | % of new signups who generate at least 1 report in session 1 | ≥ 50% |
| Reports are actually useful | Report "helpful" rating (thumbs up/down) | ≥ 70% positive |
| Chat is trustworthy | % of chat answers with no user-flagged inaccuracy | ≥ 90% |
| Retention signal | Orgs that return and upload a 2nd dataset within 14 days | ≥ 30% |
| Monetization signal | Free → paid conversion (post-MVP paywall) | ≥ 5% |

## 5. Scope

### In scope (MVP)
1. Account/org signup, JWT auth, single-organization workspaces with team members.
2. Dataset upload: CSV and Excel (XLSX). Automatic schema/type detection.
3. AI-generated narrative business report from an uploaded dataset (summary + key metrics + 3–5 charts + insights/anomalies called out in plain language).
4. Report export to PDF and Word (.docx).
5. Chat-with-data: natural language questions answered against the uploaded dataset, with an inline chart when relevant, and a visible "here's the query I ran" for transparency/trust.
6. Basic forecasting: pick a numeric metric + a date column, get an N-period forecast chart (e.g., next 3 months of revenue).
7. Reports library (list, search, re-open past reports).
8. Basic org/team management (invite members, roles: owner/admin/member/viewer).

### Explicitly out of scope for MVP (post-MVP backlog)
- Live database connections (Postgres/MySQL/Snowflake) — start with file upload only.
- Scheduled/recurring reports emailed automatically.
- White-labeling / custom branding for agencies.
- Billing/Stripe integration (build the data model for it now; wire it up post-MVP).
- Mobile app (responsive web only).
- Real-time collaborative editing of reports.
- Fine-tuned/custom ML forecasting models (use off-the-shelf forecasting first — Prophet/statsmodels).

## 6. Core Features (detail)

**F1 — Data Ingestion**
Upload CSV/XLSX (≤ 25MB MVP limit). System parses, infers column types (numeric, categorical, date, text), flags obvious data quality issues (missing values, mixed types), and stores a schema summary. User can rename/confirm column types before proceeding.

**F2 — AI Report Generation**
User selects a dataset → picks a report intent (e.g., "Sales performance overview", "Monthly summary", "Custom prompt") → system computes real statistics (aggregates, trends, outliers) from the actual data, then uses an LLM to turn those computed facts into a narrative report with headline metrics, 3–5 auto-selected charts, and a short "what changed / what to watch" section. **The LLM narrates computed numbers — it does not invent numbers.** This distinction matters for both accuracy and is called out again in Architecture.

**F3 — Chat With Data**
Conversational interface scoped to one dataset at a time. User asks a question in plain English → system translates it into a safe, sandboxed query (pandas operation or parameterized SQL) → executes → returns a text answer + optional chart. The generated query is shown to the user for transparency. No arbitrary code execution from LLM output (see Architecture §8, Security).

**F4 — Forecasting**
User picks a numeric column + a date/time column + horizon (e.g., 3, 6, 12 periods) → background job runs a forecasting model (Prophet or statsmodels ETS as MVP default) → returns a forecast chart with confidence interval and a one-paragraph plain-language summary.

**F5 — Report Export & Library**
Every generated report is saved, versioned, and exportable to PDF/DOCX. Reports library supports search by title/dataset/date.

**F6 — Org & Team Management**
Org creation on signup, invite teammates by email, role-based permissions (owner/admin can manage data sources and billing; member can generate reports/chat; viewer can only view/export).

## 7. Key User Flows (high level)

1. **Onboarding:** Sign up → create org → upload first dataset → auto-generate first report → "aha moment."
2. **Report generation:** Dashboard → "New Report" → select dataset → select report type → wait (progress state) → view report → export.
3. **Chat:** Dashboard → select dataset → ask question → see answer + chart + underlying query → ask follow-up.
4. **Forecast:** Report or dataset page → "Forecast this metric" → pick column + horizon → view forecast chart.

## 8. Non-Functional Requirements

- **Performance:** Report generation for a dataset up to ~100k rows should complete in < 60s (background job with progress indicator, not a blocking request).
- **Security:** Per-org data isolation enforced at the query layer (every table scoped by `org_id`); uploaded files stored in isolated per-org storage paths; no LLM-generated code is ever executed directly — only whitelisted, parameterized operations.
- **Reliability:** Long-running jobs (report gen, forecasting) run via background workers with retry; user sees status, not a spinner that times out.
- **Privacy:** Business data is never used to train third-party models (must confirm this setting with whichever LLM API is chosen); data deletable by org admins on request.
- **Accessibility:** WCAG AA color contrast on charts and UI as a baseline.

## 9. Assumptions & Constraints

- MVP targets file-based data only; no live DB connectors yet.
- Single LLM provider integration at launch (see Architecture for pick), abstracted behind an interface so it can be swapped.
- English-language reports/chat only for MVP.
- Small team / solo-founder build — MVP must be buildable in weeks, not quarters, hence the phased roadmap and AI-assisted build approach.

## 10. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| LLM hallucinates numbers in reports | Compute all stats deterministically in code first; LLM only narrates pre-computed facts, never does arithmetic itself. |
| Chat-to-query lets a user (or malicious input) run unsafe operations | Whitelist of safe pandas/SQL operations only, executed in a sandboxed, read-only, resource-limited context; never `eval` raw LLM output. |
| Small/dirty datasets produce garbage reports | Data quality checks + minimum-row thresholds before generation; show warnings instead of silently producing a bad report. |
| LLM API costs scale badly with usage | Cache computed stats; limit report/chat frequency on free tier; monitor token usage per org. |

## 11. Monetization (model, not build target for MVP)

Freemium: free tier = 1 org, limited reports/month, 1 dataset. Paid tiers scale by report volume, dataset count, and team seats. Data model should anticipate this (see `organizations.plan`) even though Stripe integration itself is post-MVP.

## 12. Competitive Landscape (brief)

- **Traditional BI** (Power BI, Tableau, Looker): powerful but require analyst skill and setup time — this product's edge is zero-setup, plain-English interaction.
- **AI chat-with-data tools** (e.g., Julius, various "chat with your CSV" tools): close analog to the chat feature here, but usually lack polished narrative report generation and forecasting in one product.
- **Differentiation for this product:** the combination of (a) a real, exportable business report, not just a chat answer, plus (b) forecasting, plus (c) multi-tenant team use, in one MVP.
