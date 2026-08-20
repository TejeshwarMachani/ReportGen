# Vibe Coding Guide
## How to actually build this with an AI coding agent

This doc is the operating manual for the other seven. It assumes you're using something like **Claude Code** or **Cursor** as your primary build tool.

---

## 1. One-time setup

1. Create the repo, add this entire `docs/` folder at the root.
2. Add a top-level `CLAUDE.md` (or `.cursorrules`) that points the agent at these docs and states your non-negotiables up front:

```markdown
# Project instructions for AI coding agent

This is "AI-Based Business Report Generation and Analytics System" — see /docs for full specs.
Read /docs/01_PRD.md, /docs/02_TECH_ARCHITECTURE.md, and /docs/03_DATABASE_SCHEMA.md before writing code.

Non-negotiables:
- Every DB-touching query must be scoped by org_id from the authenticated JWT — never trust a client-supplied org_id.
- Never execute LLM-generated code or raw LLM-generated SQL directly. Chat-to-data must go through the
  validated query DSL described in /docs/02_TECH_ARCHITECTURE.md §8.
- Report narratives may only reference numbers that exist in computed_stats_json — the LLM never does arithmetic.
- All schema changes go through an Alembic migration file, never a manual DB edit.
- Follow the folder structure in /docs/02_TECH_ARCHITECTURE.md §3 exactly.
- Build in the phase order defined in /docs/07_ROADMAP.md — don't jump ahead to a later phase's features.
```

This file is the single highest-leverage thing you can do — it prevents the agent from re-deriving (and getting wrong) your architecture decisions every session.

3. Do Phase 0 yourself with the agent in one focused session — get `docker-compose up` working before anything else. Don't let the agent write feature code against a stack that doesn't run yet.

---

## 2. How to prompt each phase

Work **one phase of `07_ROADMAP.md` at a time**, in a fresh-ish context each time. At the start of a phase's session:

> "We're starting Phase 3 (AI Report Generation) from /docs/07_ROADMAP.md. Re-read /docs/01_PRD.md §6 (F2), /docs/02_TECH_ARCHITECTURE.md §7, /docs/03_DATABASE_SCHEMA.md `reports` table, and /docs/04_API_SPECIFICATION.md Reports section. Then propose an implementation plan before writing code."

Making the agent **restate the plan before coding** catches misunderstandings while they're cheap to fix.

### Prompt templates you'll reuse constantly

**Scaffolding a backend resource:**
> "Implement the `datasets` resource: SQLAlchemy model per /docs/03_DATABASE_SCHEMA.md, Pydantic schemas, and the endpoints in /docs/04_API_SPECIFICATION.md 'Datasets' section, in `/backend/app/api/v1/routers/datasets.py`. Include an Alembic migration. Write pytest tests for the upload and list endpoints."

**Building a frontend page:**
> "Build the Dataset Detail screen per /docs/06_UI_UX_SPEC.md. Use the `<DataTable>`, `<StatusBadge>`, and `<UploadDropzone>` components — check if they already exist in `/frontend/src/components` before creating new ones. Wire it to `GET /datasets/{id}` and `GET /datasets/{id}/preview`."

**Debugging:**
> "This test is failing: [paste]. Don't just make the test pass — check whether the bug violates any rule in CLAUDE.md (especially org_id scoping) before proposing a fix."

**Reviewing security-sensitive code (always do this explicitly for chat + report generation):**
> "Review this chat query execution code against /docs/02_TECH_ARCHITECTURE.md §8. Confirm: (1) no raw LLM output is ever eval'd or passed to a SQL string directly, (2) every operation goes through the whitelist validator, (3) results are row-limited."

---

## 3. Session hygiene

- **Commit after every working increment**, not at the end of a whole phase. Small diffs are easier for both you and the agent to reason about on the next session.
- **Keep `/docs` in sync with reality.** If you deviate from the schema or API spec while building (you will, occasionally), update the doc in the same PR. Stale docs actively mislead the agent in future sessions.
- **Don't let context window pressure cause silent scope creep.** If a session starts proposing Phase 5 features while you're in Phase 2, redirect it back to the roadmap explicitly.
- **Write tests as you go, not at the end.** Ask the agent for tests alongside each endpoint/component, especially for: org_id isolation, the chat query whitelist validator, and the "narrative only references computed numbers" invariant.

---

## 4. The two things to personally review, always

AI agents move fast and will happily generate plausible-looking code in these two spots that's subtly unsafe — review these yourself line by line every time, don't just trust green tests:

1. **Anything that turns an LLM output into an executed query or code path** (chat-with-data). This is the project's biggest security surface.
2. **Anything that filters/joins data by `org_id`.** A missing filter here is a cross-tenant data leak, not just a bug.

---

## 5. Suggested session sequence (maps to `07_ROADMAP.md`)

1. Phase 0 — scaffolding (1 session, do it carefully, don't rush)
2. Phase 1 — auth (1–2 sessions)
3. Phase 2 — data ingestion (2 sessions: backend parsing, then frontend)
4. Phase 3 — report generation (3+ sessions: stats engine → LLM narration → export → frontend; this is the phase worth slowing down for)
5. Phase 4 — chat (2–3 sessions: query DSL + validator first, execution second, frontend third)
6. Phase 5 — forecasting (1–2 sessions)
7. Phase 6 — dashboard/library/team (1–2 sessions)
8. Phase 7 — polish + deploy (1–2 sessions)

Each session: restate plan → build → test → commit → update docs if anything changed.
