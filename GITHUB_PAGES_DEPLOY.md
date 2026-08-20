# GitHub Pages Deployment Guide — ReportGen

**Repo:** `TejeshwarMachani/ReportGen` → Pages URL: `https://tejeshwarmachani.github.io/ReportGen/`

---

## 1. The Hard Truth: GitHub Pages is Static-Only

GitHub Pages serves **static files only**. It cannot run Python, cannot execute a FastAPI process, cannot hold PostgreSQL/Redis, and cannot run the Celery worker. There is no server-side execution of any kind.

Your stack:

- **FastAPI** (backend API at `/api/v1`) — **must live elsewhere**.
- **PostgreSQL, Redis, MinIO, Celery worker** — **must live elsewhere**.
- **React + Vite SPA** — this is the *only* part that fits Pages.

So Pages is not a deployment target for this app's full architecture — it is a way to serve the **frontend** for free, while the API runs on a paid host. The frontend is a static bundle (HTML/JS/CSS); the runtime backend calls it makes over HTTP are fine, because browsers can talk cross-origin to any HTTPS API — that is just normal web traffic.

**Deployment topology:**

```
Browser
  │
  ├─ https://tejeshwarmachani.github.io/ReportGen/   (SPA, static, GitHub Pages)
  │        └─ fetches JSON via axios → VITE_API_BASE_URL
  │
  └─ https://reportgen-backend.onrender.com/api/v1   (FastAPI, Render)
           └─ PostgreSQL, Redis, Celery, MinIO
```

Two consequences you must handle, covered in section 4:

1. The API URL is **baked into the JS bundle at build time** (`VITE_API_BASE_URL`).
2. Pages has **no SPA fallback** — no nginx `try_files`, no `/index.html` rewrite. A refresh on `/ReportGen/dashboard` requests a real `dashboard` file that does not exist and returns **404**, unless you add a redirect file or switch to hash routing.

---

## 2. Step-by-Step: Deploy Backend (anywhere but Pages)

The backend MUST be deployed to a service that runs a process. This project already has a **Render Blueprint** (`/render.yaml` at repo root) covering PostgreSQL, Redis, backend API, Celery worker, and even a frontend service.

### 2a. Deploy the backend to Render

Short version (full details belong in `RENDER_DEPLOY.md` — create it if it does not exist yet):

1. Push this repo to GitHub.
2. In Render: **New → Blueprint**, connect the repo.
3. Render reads `render.yaml` and provisions:
   - `reportgen-postgres` (managed PostgreSQL)
   - `reportgen-redis` (managed Redis)
   - `reportgen-backend` (FastAPI, Docker, health check on `/health`)
   - `reportgen-worker` (Celery)
4. In the Render dashboard, set the secrets marked `sync: false` manually: `ANTHROPIC_API_KEY`, `SENTRY_DSN`.
5. Note the backend URL Render assigns, e.g. `https://reportgen-backend.onrender.com`. (The Blueprint also wires a frontend service at `https://reportgen-frontend.onrender.com` — see the note in section 7 about whether you still want it.)
6. Verify: open `https://<your-backend>.onrender.com/docs` and `/health`.

Alternative hosts (same idea, no Blueprint): **Railway** and **Fly.io** both deploy the `./backend` Dockerfile. You would recreate the same env vars (`DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `ANTHROPIC_API_KEY`, `ENVIRONMENT=production`) and attach managed Postgres/Redis.

> **CORS note (required):** the browser will call the API from origin `https://tejeshwarmachani.github.io`. The backend's CORS allow-list and `ALLOWED_HOSTS` must include that origin, or every request will be blocked. Add it in Render (the Blueprint currently sets `ALLOWED_HOSTS` to the on-Render frontend only), e.g. update `ALLOWED_HOSTS` to `https://reportgen-frontend.onrender.com,https://tejeshwarmachani.github.io` and add `https://tejeshwarmachani.github.io` to the CORS `allow_origins` in the backend middleware/settings.

### 2b. Deploy the frontend to Pages

1. Go to **repo → Settings → Pages**.
2. Under **Build and deployment → Source**, select **GitHub Actions** (do *not* pick "Deploy from a branch" — you want the workflow below, which uploads a build artifact).
3. Add the workflow file from section 3 and push to `main`. Every push rebuilds and republishes the SPA.
4. First deploy shows a yellow dot with a build spinner; a green check means live.
5. Visit `https://tejeshwarmachani.github.io/ReportGen/`.

---

## 3. The GitHub Actions Workflow (`.github/workflows/pages.yml`)

Create `.github/workflows/pages.yml` in the repo root:

```yaml
name: Deploy frontend to GitHub Pages

on:
  push:
    branches: [main]
    paths: ['frontend/**']        # only rebuild when the frontend changes
  workflow_dispatch:

permissions:
  contents: read
  pages: write                    # allow publishing to Pages
  id-token: write                 # required by deploy-pages

# Deploy only one build at a time
concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./frontend   # package.json lives here
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
          cache-dependency-path: ./frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build               # runs `tsc && vite build`

      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./frontend/dist          # upload the built bundle

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

Key pieces:

- **`permissions: pages: write` + `id-token: write`** — both are mandatory; without them the deploy step fails with a permissions error. These are GITHUB_TOKEN-scoped grants inside this workflow, not repo-wide settings.
- **`upload-pages-artifact`** packages `dist/` (relative to repo root, hence `./frontend/dist`) into the artifact Pages consumes.
- **`deploy-pages`** publishes that artifact with the `github-pages` environment, whose URL is surfaced in the workflow run and in Settings → Environments.
- **`working-directory: ./frontend`** — because `package.json` and `vite.config.ts` live under `frontend/`, not at repo root.

---

## 4. Issues You Must Solve Before It Works

### 4a. `VITE_API_BASE_URL` must point at the deployed backend

`Vite` inlines `import.meta.env.VITE_API_BASE_URL` into the JS bundle **at build time** (see `frontend/src/api/client.ts`). There is no "runtime config" — change the URL and rebuild.

Create `frontend/.env.production`:

```dotenv
# frontend/.env.production  — build-time, safe to commit (it is public in the bundle anyway)
VITE_API_BASE_URL=https://reportgen-backend.onrender.com/api/v1
```

Why this works with no workflow change: `npm run build` runs Vite in production mode, and Vite automatically loads `.env.production`. The workflow's `npm ci && npm run build` picks it up.

If you would rather not commit the URL, set it in the workflow instead (line 4a becomes its own step):

```yaml
      - name: Build
        run: npm run build
        env:
          VITE_API_BASE_URL: https://reportgen-backend.onrender.com/api/v1
```

Which to choose: on a **public** repo the URL is public either way, so commit `frontend/.env.production`. On a **private** repo, use the workflow `env` form so the URL stays out of git history. (GitHub Pages is public only whether your repo is public or not — that is just a visibility note.)

### 4b. BrowserRouter 404s on refresh for subroutes — use HashRouter

`App.tsx` uses `<BrowserRouter>`. On Pages, refreshing `https://tejeshwarmachani.github.io/ReportGen/dashboard` makes the server look for a file called `dashboard` — it does not exist — and Pages returns **404** even though the app is running. This does not affect in-app navigation (that is client-side); it only breaks hard refreshes, bookmarks, and pasted deep links.

Two fixes; **use HashRouter** for this project:

**Option A — HashRouter (recommended, one-line change, bulletproof).** URLs become `...#/dashboard`, the server never sees the route path after `#`, so Pages always serves `/index.html`. No 404.html, no basename, no repo-name coupling. Works on any subpath or a custom domain. The only cost: `#` in URLs.

Minimal change in `frontend/src/App.tsx`:

```tsx
// frontend/src/App.tsx  (line 2)
// before:
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
// after:
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
```

That is the whole change — every route in this app uses absolute paths (`/dashboard`, `/login`, ...) which HashRouter resolves identically after the `#`. `main.tsx` needs no change (it just renders `<App/>`).

One knock-on fix: `frontend/src/api/client.ts` line 46 does `window.location.href = '/login'` on expired auth. Under HashRouter that navigates to the *domain root* (`/login`, not `#/login`) and 404s. Change it to:

```ts
window.location.href = '#/login'
```

**Option B — keep BrowserRouter + clean URLs.** Needs TWO extra pieces:

1. A static **`404.html`** that Pages serves for any missing file and that instantly redirects the browser back to `/index.html` with the path preserved. Create `frontend/public/404.html` (it must be inside `public/` so Vite copies it into `dist/`):

```html
<!doctype html>
<script>
  // GitHub Pages SPA redirect: a request to /ReportGen/dashboard hits this file.
  // Re-enter the app by loading the real index.html, keeping the route so the app
  // can navigate there after mount (a bare "/" would land on /dashboard via the
  // app's own <Navigate> redirect).
  const route = location.pathname.replace('/ReportGen', '') || '/'
  window.location.replace('/ReportGen/' + '?redirect=' + route)
</script>
```

How it ties together with the app:

- Add a `?redirect=` → route hook: in `App.tsx`, after mount, `const params = new URLSearchParams(location.search); const r = params.get('redirect'); if (r) replace(r)`. This is a tiny router-agnostic snippet you own; the alternative is rewriting straight to `#` (HashRouter locale) — but the app uses BrowserRouter in Option B, so the browser must land on `index.html` first.
- **Router basename.** `BrowserRouter` must know it lives under `/ReportGen/`. Set `<Router basename={import.meta.env.BASE_URL}>` — it resolves to `/ReportGen/` because of the `base: './'` in 4c (with a relative base, part of the `BROWSER` page URL `/`). If you change `base` to a custom domain's `'/'`, switch the basename to `'/'` too.

This is strictly more moving parts than Option A and the redirect + hook + basename trio is easy to get subtly wrong (hard refresh, then paste a bookmark → still 404). **If you do not care about pretty URLs, skip Option B.**

### 4c. Project Pages URL has a `/repo-name/` prefix — set `vite base`

For a **project** Pages site (`https://USER.github.io/REPO/`), the app is served from a subpath. Vite's `base` (default `/`) controls where it expects its JS/CSS/assets. With the default `/` the built page requests `/assets/...`, which at the Pages domain root is the wrong place → blank page, fellow built assets.

Fix in `frontend/vite.config.ts` by adding a **relative** base, which is correct for any subpath and for a custom domain alike:

```ts
export default defineConfig({
  base: './',          // <-- assets resolve relative to the current path
  plugins: [react()],
  // ...rest unchanged
})
```

Combined with HashRouter (4b) this is fully correct on `https://USER.github.io/REPO/`. The `<link>`/`<script>` URLs become `./assets/...`, resolving against the directory the page is served from — which is always `/ReportGen/` (or `/` for a custom domain), because the route lives after the `#`.

If you go the BrowserRouter route instead, add the `basename={import.meta.env.BASE_URL}` to `<Router>` (or hardcode `/ReportGen`) and the `404.html` + redirect hook from 4b.

---

## 5. `.env.production` Example (complete file for Pages)

```dotenv
# frontend/.env.production
# The API host the SPA will talk to. Baked in at build time. Safe to commit (public data).
VITE_API_BASE_URL=https://reportgen-backend.onrender.com/api/v1
```

Everything else (auth keys, S3 secrets, DB URLs) is backend-only — those live in Render, never here, never in the bundle.

---

## 6. CNAME / Custom Domain

When you want `app.yourcompany.com` instead of `tejeshwarmachani.github.io/ReportGen/`:

1. **Buy/own the domain**, then at your DNS provider add:
   - `CNAME app → tejeshwarmachani.github.io` (root domains need `A` records to Pages' IPs instead — check the current IPs in the Pages settings page).
2. **GitHub repo → Settings → Pages → Custom domain:** enter `app.yourcompany.com`, save (GitHub verifies DNS and creates the cert automatically).
3. **Commit a `CNAME` file** containing `app.yourcompany.com` at the repo root. Git history shows it, but it must land in the deployed artifact for Pages to keep serving the custom domain — so include it in the build. Simplest: put it in `frontend/public/` so Vite copies it into `dist/` automatically:
   - `frontend/public/CNAME` → contents `app.yourcompany.com`
4. Once on a custom domain, the URL has no subpath. Everything keeps working because `base: './'` and HashRouter are prefix-agnostic. You may switch `base` to `'/'` if you want absolute asset URLs. You may *also* keep the repo URL working — Pages redirects `USER.github.io/REPO/` to the custom domain automatically.
5. Enforce HTTPS: after the first deploy, GitHub offers "Enforce HTTPS" — enable it. Renewal is automatic.

---

## 7. When Pages Makes Sense (and When It Does Not)

| Scenario | Pages? | Why |
|---|---|---|
| Public demo of the frontend (login screen, UI, read-only reports) | Yes | Free, fast CDN, no server to babysit. |
| Marketing / landing / docs site for the product | Yes | Static by nature. |
| Client-facing production app with real data + auth + uploads | No | API pays for itself; see below. |

**This exact project is a full multi-tenant product** (JWT auth, file uploads, LLM report generation, Celery jobs, per-org data). Running it on Pages means:

- The API still costs money on Render/Railway/Fly — Pages only removes the cost of hosting static files, which is already near-zero on any host.
- Download-size uploads and long LLM jobs go over the public internet to the API; fine, but there is no latency win.
- You split your origins: frontend on `*.github.io`, API on `*.onrender.com`. Works (Bearer tokens in `localStorage`, which the app already does), but you own the CORS config (section 2a).
- These `render.yaml` already deploys a frontend (nginx) alongside the API with a full SPA fallback and same-host static serving. **If you intend to run the real product, keep the Render frontend service and skip Pages entirely** — it is the least-friction, single-origin deployment. Use Pages only as a free, separate static surface (demo/docs) pointing at the same Render API.

**TL;DR:** Pages is great for a public demo or docs. For the actual product, Render already offers the whole app out of the box — Pages exists to show off the frontend, not to run the product.

---

## Files touched by this guide

- `.github/workflows/pages.yml` — new; Pages build/deploy workflow.
- `frontend/vite.config.ts` — add `base: './'`.
- `frontend/src/App.tsx` — swap `BrowserRouter` → `HashRouter` (one import line).
- `frontend/src/api/client.ts` — change `/login` redirect to `#/login`.
- `frontend/.env.production` — new; `VITE_API_BASE_URL` = your Render API.
- `frontend/public/404.html` — only needed if you want clean URLs (Option B).
- `frontend/public/CNAME` — only needed for a custom domain.
- Render dashboard — set `ANTHROPIC_API_KEY`, `SENTRY_DSN`; add the Pages origin to backend CORS/`ALLOWED_HOSTS`.