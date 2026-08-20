# Vibe-Coded Website — Pre-Launch QA & Security Checklist

A working checklist for reviewing a website that was built quickly with AI assistance (Claude Code or similar) before it ships. "Vibe coded" projects move fast and skip a lot of the manual scrutiny a hand-built app gets along the way — this list exists to catch what that speed usually misses.

**How to use this:** Work through each section top to bottom. For code-level checks, paste the relevant sub-section straight into Claude Code as a prompt ("go through this checklist and check off / fix each item"). Don't ship until Security and Error/Stability are fully clean — those two sections are non-negotiable even for a side project.

---

## 1. Frontend — Build & Rendering

- [ ] `npm run build` (or equivalent) completes with **zero errors and zero warnings**
- [ ] Every route/page renders — manually visit each one, not just the homepage
- [ ] No blank/white screen on any route (this usually means an uncaught render error — check the console)
- [ ] No infinite loading spinners (missing loading-state resolution)
- [ ] Browser console is clean on every page: no red errors, no unhandled promise rejections
- [ ] No React/Vue/Svelte key warnings, hydration mismatches, or prop-type warnings
- [ ] 404 page exists and renders correctly for unknown routes
- [ ] Refreshing the page on a non-root route works (no dead client-side routing)
- [ ] Back/forward browser navigation doesn't break state
- [ ] All images, icons, and fonts actually load (check Network tab for 404s on assets)
- [ ] No broken internal or external links
- [ ] Favicon and page `<title>` are set correctly per page (not all "React App")

## 2. Frontend — UI/UX Quality

- [ ] Layout doesn't break at common breakpoints: mobile (375px), tablet (768px), desktop (1440px)
- [ ] No overlapping elements, cut-off text, or horizontal scroll on mobile
- [ ] Forms show validation errors clearly and don't silently fail
- [ ] Buttons show a loading/disabled state during async actions (prevents double-submit)
- [ ] Empty states are handled (e.g., "no results found" instead of a blank list)
- [ ] Toasts/alerts/modals dismiss correctly and don't stack or trap focus
- [ ] Dark mode (if present) doesn't have unreadable text/contrast issues
- [ ] Basic accessibility: images have `alt` text, inputs have labels, interactive elements are keyboard-reachable
- [ ] Tested in at least two browsers (e.g., Chrome + Safari/Firefox)

## 3. Frontend — Modules & State

- [ ] All imported components/modules actually exist and resolve (no dangling imports from deleted files)
- [ ] No unused/dead code left over from iteration (stale components, commented-out blocks)
- [ ] Global state (Context/Redux/Zustand/etc.) initializes correctly on fresh load, not just after navigation
- [ ] No prop drilling bugs — check that data passed into deeply nested components is actually correct, not `undefined`
- [ ] Environment variables used in frontend code are prefixed correctly for the framework (e.g., `VITE_`, `NEXT_PUBLIC_`) and **contain no secrets**

## 4. Backend — API & Modules

- [ ] Every API route returns the expected response for valid input
- [ ] Every API route returns a sane error (not a stack trace or a 500 with no body) for invalid input
- [ ] Correct HTTP status codes used (200/201, 400, 401, 403, 404, 500 — not everything returning 200)
- [ ] All backend modules/routes are actually registered/mounted (easy to forget one after refactoring)
- [ ] Database connection is established with proper error handling if it fails on startup
- [ ] Database queries/models match the actual schema (no leftover fields from earlier iterations)
- [ ] Server starts cleanly with no unhandled exceptions in the logs
- [ ] Long-running or async operations (file processing, emails, webhooks) don't crash the server if they fail

## 5. Integration — Frontend ↔ Backend

- [ ] Every frontend API call points to the correct backend URL for the current environment (dev vs. prod)
- [ ] Request/response shapes match on both ends (rename a field on one side and it breaks silently — check for this)
- [ ] Loading, success, and error states are all handled for every API call, not just the happy path
- [ ] CORS is configured to allow the actual frontend origin (and **only** that origin in production — see Security)
- [ ] Auth tokens/sessions are correctly attached to requests that need them
- [ ] Third-party integrations (Stripe, auth providers, email services, analytics, maps, etc.) work end-to-end, not just in a mocked/sandbox state
- [ ] Webhooks (if any) are verified with a real test event, not just assumed to work
- [ ] File uploads (if any) complete and the file is retrievable afterward

## 6. Error Handling & Stability

- [ ] A global error boundary (frontend) catches component crashes instead of showing a blank page
- [ ] A global error handler (backend) catches unhandled exceptions instead of crashing the server
- [ ] Network failures (API down, timeout, offline) show a message instead of a blank/frozen UI
- [ ] No silent `catch (e) {}` blocks swallowing real errors — errors are logged somewhere
- [ ] App doesn't crash if the database, an env var, or a third-party service is temporarily unavailable
- [ ] Retesting after fixing a bug — confirm the fix didn't introduce a new blank-page or console error elsewhere

## 7. Security — Secrets & Config

- [ ] No API keys, database credentials, or tokens hardcoded in source files
- [ ] `.env` files are in `.gitignore` and were **never committed** (check git history, not just the current state)
- [ ] `.env.example` exists with placeholder values for anyone setting the project up
- [ ] Secrets are only referenced server-side, never bundled into frontend JS
- [ ] Production and development use separate credentials/keys (not the same Stripe/DB key everywhere)

## 8. Security — Input & Injection

- [ ] All user input is validated server-side (client-side validation alone is not security)
- [ ] Database queries use parameterized queries / an ORM — no raw string-concatenated SQL
- [ ] User-generated content is escaped/sanitized before rendering (prevents stored XSS)
- [ ] File uploads restrict file type and size, and uploaded files aren't executable
- [ ] No `eval()`, `dangerouslySetInnerHTML`, or `v-html` used on untrusted input

## 9. Security — Auth & Access Control

- [ ] Passwords are hashed (bcrypt/argon2), never stored in plain text
- [ ] Sessions/tokens use secure, httpOnly cookies where possible (or are otherwise stored safely, not in plain `localStorage` for sensitive tokens)
- [ ] Protected routes/pages check auth **on the server**, not just by hiding a button on the frontend
- [ ] Authorization is checked per-request (a logged-in user can't access another user's data by changing an ID in the URL — test this directly)
- [ ] Admin/internal routes are not reachable by regular users
- [ ] Rate limiting exists on login, signup, and password-reset endpoints (brute-force protection)
- [ ] Logout actually invalidates the session/token, not just clears local state

## 10. Security — Infra & Headers

- [ ] HTTPS is enforced in production (no mixed content)
- [ ] CORS allow-list is specific — not `*` — for any endpoint that handles authenticated requests
- [ ] Basic security headers are set: `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`
- [ ] Dependency audit run and high/critical issues addressed (`npm audit`, `pip-audit`, etc.)
- [ ] No verbose stack traces or debug info exposed to users in production error responses
- [ ] Sensitive data (passwords, tokens, PII) is never written to logs

## 11. Performance

- [ ] Images are compressed/optimized, not raw multi-MB uploads
- [ ] No obviously unnecessary re-renders or duplicate API calls on page load
- [ ] Bundle size is reasonable — check for accidentally-included large dependencies
- [ ] Caching is used where sensible (static assets, repeated API calls)

## 12. Deployment & Pre-Launch

- [ ] Production build tested locally with production environment variables before deploying
- [ ] All required environment variables are set in the hosting platform (not just locally)
- [ ] Custom domain and SSL certificate are working
- [ ] Error monitoring is wired up (Sentry or similar) so you find out about crashes before users tell you
- [ ] A rollback plan exists (previous deploy can be restored quickly)
- [ ] README is up to date with setup instructions for a fresh clone

## 13. Final Pass — Testing

- [ ] Walked through every critical user flow start to finish as a real user would (signup → core action → logout, checkout flow, etc.)
- [ ] Tried to break it: submitted empty forms, wrong data types, huge inputs, special characters, double-clicks on submit buttons
- [ ] Tested with a second, unprivileged account to confirm access control actually works
- [ ] Checked the site on a slow/throttled connection to see how loading states behave

---

### Common "vibe coding" red flags worth double-checking specifically
These show up disproportionately often in AI-assisted rapid builds:
- API keys pasted directly into frontend code "just to get it working"
- Auth checks that only exist in the UI (button hidden) and not on the server
- Copy-pasted boilerplate that still points at example.com or a template's default config
- Error handling that was never actually tested (the `catch` block was written but never triggered)
- CORS set to allow all origins because it was easier during development and never tightened
