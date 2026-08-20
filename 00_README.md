# AI-Based Business Report Generation and Analytics System
### Documentation Package — v1.0

**Pitch:** A web platform where a business uploads data (CSV/Excel or a live DB connection) and gets three things an SMB normally can't afford a data team for: (1) auto-generated narrative business reports with charts, (2) a chat interface to ask questions about that data in plain English, and (3) simple forecasting on key metrics (revenue, sales, churn, etc.). Multi-tenant, subscription-based, MVP-scoped for a startup launch.

**Stack decision:** FastAPI (Python) backend + React (TypeScript/Vite) frontend + PostgreSQL + Celery/Redis for background jobs. Rationale is in `02_TECH_ARCHITECTURE.md`.

---

## How to use this package

These docs are written to be fed to an AI coding assistant (Claude Code, Cursor, etc.) as persistent context — not just for you to read once. Keep this whole `docs/` folder in the root of your repo. Start with **`08_VIBE_CODING_GUIDE.md`** — it tells you exactly how to sequence prompts against the other seven documents.

| # | Document | What it's for |
|---|----------|----------------|
| 01 | `01_PRD.md` | Product vision, users, features, scope, success metrics — the "why" and "what" |
| 02 | `02_TECH_ARCHITECTURE.md` | Stack, folder structure, env vars, security model — the "how" at a system level |
| 03 | `03_DATABASE_SCHEMA.md` | Every table, field, relationship, and the ER diagram |
| 04 | `04_API_SPECIFICATION.md` | Every REST endpoint, request/response shape |
| 05 | `05_FEATURES_USER_STORIES.md` | Epics broken into user stories with acceptance criteria, prioritized |
| 06 | `06_UI_UX_SPEC.md` | Screens, design tokens, component inventory, key flows |
| 07 | `07_ROADMAP.md` | Build order across 8 phases with exit criteria |
| 08 | `08_VIBE_CODING_GUIDE.md` | How to actually prompt an AI coding agent through all of this |

**Recommended reading order (for you):** 01 → 07 → 02 → 08, then dip into 03/04/05/06 as you build each phase.

**Recommended feeding order (for the AI agent):** whole folder up front, then re-point it at the specific doc section relevant to whatever phase you're in that session.
