# Render Deployment Guide — ReportGen

Step-by-step guide to deploying this repo (FastAPI + gunicorn, React+Vite served by nginx, PostgreSQL 15/16, Redis 7, MinIO S3, Celery workers for reports/forecasts) on [Render](https://render.com). Everything is verified against this repo: `backend/Dockerfile.prod`, `frontend/Dockerfile.prod`, `backend/app/core/config.py`, `backend/app/main.py`, `backend/alembic/env.py`, `docker-compose.prod.yml`.

**How the pieces map to Render services**

| Local (compose) | Render service | Notes |
|---|---|---|
| `nginx` (host proxy) | — (not needed) | Internal networking replaces it |
| `frontend` | Static Site | `$0`, serves `frontend/dist` |
| `backend` (gunicorn :8000) | Web Service (Docker) | `healthCheckPath: /health` |
| `worker` (celery worker) | Background Worker (Docker) | same image, `dockerCommand` override |
| `beat` (celery beat) | Background Worker (Docker) | free tier is fine |
| `postgres:15` | Managed PostgreSQL | user/password/db via blueprint |
| `redis:7` | Managed Redis (Key Value) | `maxmemoryPolicy: allkeys-lru` |
| `minio` | Web Service (Docker) + disk | Render has no managed S3 — see cost notes |

---

## 1. Render Blueprint (`render.yaml`)

A complete `render.yaml` for the whole stack is included in this repo root (see **`E:\ReportGen\render.yaml`**). Key facts it relies on (verified in code):

- `backend/Dockerfile.prod` exposes port **8000** and runs `gunicorn app.main:app` with uvicorn workers. The `HEALTHCHECK` inside the Dockerfile is ignored by Render (Render uses its own health check), but the file already curls `/health` — keep it, it's correct.
- `frontend/Dockerfile.prod` is a multi-stage build (node → nginx) exposing port **80** — but the simpler and **free** option is a Static Site that runs `npm run build` and serves `frontend/dist`. Use the Docker web-service alternative only if you need nginx features beyond static file serving (your `nginx.conf` proxies `/api` to `backend:8000` — see §7, that proxy does **not** work on Render as-is because it uses the compose service hostname).
- `backend/app/core/config.py` reads these env vars (defaults in parens): `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (30), `JWT_REFRESH_TOKEN_EXPIRE_DAYS` (14), `LLM_PROVIDER` (anthropic), `LLM_MODEL` (claude-sonnet-4-6), `S3_ENDPOINT_URL` (http://localhost:9000), `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`.
- `backend/app/main.py` exposes `GET /health` (no auth, 200), plus `/ready` and `/live`. Health check path: **`/health`**.
- `backend/alembic/env.py` falls back to `settings.DATABASE_URL` when no `sqlalchemy.url` — so migrations pick up the `DATABASE_URL` env var automatically. `script_location = ./alembic` and `prepend_sys_path = .` assume you run alembic from inside `/app` (the image WORKDIR) — true for the `cd backend && alembic upgrade head` start command.
- Celery app: `app.core.celery_app` — `celery -A app.core.celery_app worker` / `... beat` (as in `docker-compose.prod.yml`).

### Full blueprint

```yaml
# render.yaml — ReportGen (see repo root: E:\ReportGen\render.yaml)
services:
  # ---------- Backend API ----------
  - name: api
    type: web
    runtime: docker
    repo: https://github.com/USERNAME/reportgen   # your repo
    branch: main
    plan: starter
    region: oregon
    dockerfilePath: ./backend/Dockerfile.prod
    dockerContext: ./backend
    healthCheckPath: /health
    # renderSubdomainPolicy: disabled     # keep private; frontend hits it internally
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: postgres
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: redis
          type: keyvalue
          property: connectionString
      - key: SECRET_KEY
        generateValue: true               # or sync: false and paste one yourself
      - key: JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        value: "30"
      - key: JWT_REFRESH_TOKEN_EXPIRE_DAYS
        value: "14"
      - key: LLM_PROVIDER
        value: anthropic
      - key: LLM_MODEL
        value: claude-sonnet-4-6
      - key: ANTHROPIC_API_KEY
        sync: false                       # set manually in dashboard (never in git)
      - key: S3_ENDPOINT_URL
        fromService:
          name: minio
          type: web
          property: hostport              # http://minio:9000 on the private network
      - key: S3_BUCKET
        value: reportgen-uploads
      - key: S3_ACCESS_KEY
        sync: false                       # must match MINIO_ROOT_USER
      - key: S3_SECRET_KEY
        sync: false                       # must match MINIO_ROOT_PASSWORD
      - key: ENVIRONMENT
        value: production
      - key: ALLOWED_HOSTS
        value: https://reportgen.onrender.com

  # ---------- Celery worker ----------
  - name: worker
    type: worker
    runtime: docker
    repo: https://github.com/USERNAME/reportgen
    branch: main
    plan: starter
    region: oregon
    dockerfilePath: ./backend/Dockerfile.prod
    dockerContext: ./backend
    dockerCommand: celery -A app.core.celery_app worker --loglevel=info --concurrency=2
    envVars:
      - key: DATABASE_URL
        fromDatabase: { name: postgres, property: connectionString }
      - key: REDIS_URL
        fromService: { name: redis, type: keyvalue, property: connectionString }
      - key: SECRET_KEY
        sync: false                       # set same value as api
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: LLM_PROVIDER
        value: anthropic
      - key: LLM_MODEL
        value: claude-sonnet-4-6
      - key: S3_ENDPOINT_URL
        fromService: { name: minio, type: web, property: hostport }
      - key: S3_BUCKET
        value: reportgen-uploads
      - key: S3_ACCESS_KEY
        sync: false
      - key: S3_SECRET_KEY
        sync: false
      - key: ENVIRONMENT
        value: production

  # ---------- Celery beat ----------
  - name: beat
    type: worker
    runtime: docker
    repo: https://github.com/USERNAME/reportgen
    branch: main
    plan: free
    region: oregon
    dockerfilePath: ./backend/Dockerfile.prod
    dockerContext: ./backend
    dockerCommand: celery -A app.core.celery_app beat --loglevel=info
    envVars:
      - key: DATABASE_URL
        fromDatabase: { name: postgres, property: connectionString }
      - key: REDIS_URL
        fromService: { name: redis, type: keyvalue, property: connectionString }
      - key: ENVIRONMENT
        value: production

  # ---------- MinIO (S3-compatible object storage) ----------
  - name: minio
    type: web
    runtime: docker
    repo: https://github.com/USERNAME/reportgen
    branch: main
    plan: starter
    region: oregon
    dockerfilePath: ./backend/Dockerfile.prod
    dockerContext: ./backend
    dockerCommand: minio server /data --console-address ":9001"
    healthCheckPath: /minio/health/live     # standard MinIO-on-Render workaround
    disk:
      name: minio-data
      mountPath: /data
      sizeGB: 10
    envVars:
      - key: MINIO_ROOT_USER
        sync: false                         # e.g. minioadmin
      - key: MINIO_ROOT_PASSWORD
        sync: false

  # ---------- Frontend (static site, free) ----------
  - name: frontend
    type: static
    repo: https://github.com/USERNAME/reportgen
    branch: main
    buildCommand: cd frontend && npm install && npm run build
    publishPath: frontend/dist
    envVars:
      # Vite bakes this into the bundle at build time (frontend/src/api/client.ts reads
      # import.meta.env.VITE_API_BASE_URL). Point it at the api's PUBLIC url.
      - key: VITE_API_BASE_URL
        value: https://api.onrender.com/api/v1   # your api's public URL — see §7

databases:
  - name: postgres
    plan: starter
    region: oregon
    postgresMajorVersion: "16"      # closest managed major to your postgres:15 image; minor patched by Render
    databaseName: reportgen
    user: reportgen

services-extra:
  - name: redis
    type: keyvalue
    plan: starter
    region: oregon
    maxmemoryPolicy: allkeys-lru            # matches docker-compose redis args
    ipAllowList:
      - source: 0.0.0.0/0                   # tighten to "private network only" if Render offers it
```

Notes on the blueprint:

- `fromDatabase`/`fromService` inject connection strings **without ever putting credentials in git**. All three of api/worker/beat get working `DATABASE_URL` / `REDIS_URL` automatically.
- `generateValue: true` for `SECRET_KEY` creates a random value; you can regenerate it in the dashboard. For the worker, copy the same value into its `SECRET_KEY` (signed JWTs must match between api and worker). Simplest: set `SECRET_KEY` manually (`sync: false`) on all three with one strong value, e.g. `openssl rand -hex 32`.
- This file uses the `runtime: docker` form (blueprint spec). If your Blueprint UI shows the older "Dockerfile" runtime, the deploy still just loads `Dockerfile.prod` via `dockerfilePath`/`dockerContext` as shown.
- `minio` reuses `backend/Dockerfile.prod` (whatever image, the `dockerCommand` decides the process). It works because the image ships `curl` and the entrypoint is overridden.

---

## 2. One-click deploy with the blueprint

1. Commit `render.yaml` at the **repo root** and push (the repo needs no `Dockerfile` at root — the blueprint points at the real ones).
2. Sign up at [render.com](https://render.com) (free tier available) and connect GitHub/GitLab.
3. Dashboard → **New +** → **Blueprint** → pick the repo.
4. Render parses `render.yaml` and shows every service with its plan. Review, then **Apply**.
5. While the services provision, set the `sync: false` secrets in each service's **Environment** tab:
   - api: `ANTHROPIC_API_KEY`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `SECRET_KEY` (same on worker)
   - worker: `SECRET_KEY`, `ANTHROPIC_API_KEY`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`
   - minio: `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` (must match the S3_ACCESS_KEY/S3_SECRET_KEY pair)
   - (optional) `SENTRY_DSN` on api/worker
6. Each service **saves → restarts** itself, then auto-deploys from the connected branch on every push.

---

## 3. Alternative — manual service setup (no blueprint)

Create each service via **New + → Web Service / Background Worker / PostgreSQL / Redis**, selecting the **Docker** runtime for api/worker (choose "Dockerfile" and set root directory `backend` — Render uses `Dockerfile.prod` only if you set it; you can also name the file `Dockerfile` for the manual path). What to fill:

| Service | Type | Root dir / Dockerfile | Port | Health path |
|---|---|---|---|---|
| api | Web Service | `backend/Dockerfile.prod` (or root dir `backend`) | 8000 | `/health` |
| worker | Background Worker | same, then **Start Command** override: `celery -A app.core.celery_app worker --loglevel=info --concurrency=2` | — | none (workers don't support health checks) |
| beat | Background Worker (free) | same, Start Command: `celery -A app.core.celery_app beat --loglevel=info` | — | none |
| minio | Web Service Docker | `backend/Dockerfile.prod`, Start Command: `minio server /data --console-address ":9001"` | 9000 | `/minio/health/live` |
| frontend | Static Site | build: `cd frontend && npm install && npm run build` | — | — |
| postgres | PostgreSQL (New +) | plan, region | — | — |
| redis | Redis (New +) | plan, `maxmemoryPolicy: allkeys-lru` | — | — |

Every service you create manually belongs to the **same private network** (same workspace/environment), so `fromDatabase`/`fromService` values from the dashboard's "Environment" quick-add are equivalent: pick **PostgreSQL → Connection String**, **Redis → Connection String**, and for minio use **Internal Hostname/Port** (`http://minio:9000`).

---

## 4. Environment variables per service

Cheat sheet — copy-paste into each service's Environment tab.

**api (Web Service)**

```
DATABASE_URL        = <from PostgreSQL service: connection string>
REDIS_URL           = <from Redis service: connection string>
SECRET_KEY          = <openssl rand -hex 32>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS   = 14
LLM_PROVIDER        = anthropic
LLM_MODEL           = claude-sonnet-4-6
ANTHROPIC_API_KEY   = <your Anthropic key>          ← secret
S3_ENDPOINT_URL     = http://minio:9000             ← internal host:port
S3_BUCKET           = reportgen-uploads
S3_ACCESS_KEY       = <matches MINIO_ROOT_USER>     ← secret
S3_SECRET_KEY       = <matches MINIO_ROOT_PASSWORD> ← secret
ENVIRONMENT         = production
ALLOWED_HOSTS       = https://reportgen.onrender.com
```

**worker (Background Worker)** — subset: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `ANTHROPIC_API_KEY`, `LLM_PROVIDER`, `LLM_MODEL`, `S3_ENDPOINT_URL`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `ENVIRONMENT=production`. (Worker creates/updates reports; give it the same S3 creds as api.)

**beat (Background Worker)** — only `DATABASE_URL`, `REDIS_URL`, `ENVIRONMENT=production` (schedule lives in Redis).

**minio (Web Service)** — `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` (keep these in sync with the S3 keys above; `minioadmin`/a strong password works).

**frontend (Static Site)** — `VITE_API_BASE_URL`: **build-time** var, baked into the JS bundle. Must be a publicly reachable URL (see §7) — e.g. `https://api.onrender.com/api/v1` or `https://reportgen.onrender.com/api/v1` (with a Proxy Integration).

**postgres** — nothing to set; the connection string carries user/password/db (`reportgen`/`reportgen`).

**redis** — nothing to set beyond plan + `maxmemoryPolicy`; if Render shows an internal auth toggle, leave it off or mirror the URL into `REDIS_URL` (api code just uses `redis://user:pass@host:6379/0`).

---

## 5. Health check path

Render uses its own health checks (the `HEALTHCHECK` line inside your Dockerfiles is ignored for restart decisions).

- **api**: set `healthCheckPath: /health` (or `Health Check Path: /health` in the dashboard). The app serves `GET /health` → 200 with no auth, registered **before** rate-limiting/audit middleware — correct. `/ready` also exists (pings Redis) if you prefer a stricter check, but `/health` is the recommended default.
- **minio**: `healthCheckPath: /minio/health/live` (MinIO serves no HTTP on `/`; this is the documented workaround).
- **worker/beat**: background workers have **no** health check support on Render. If you want a signal, add a log line the worker prints on boot and watch logs; for scheduled jobs this matters less because Redis/Postgres are hosted.
- Render restarts a service when the health check fails 3 times (your Dockerfile's interval/timeout/retries are overridden by Render's own probe).

---

## 6. Migrations (Alembic)

Your `backend/alembic/env.py` already falls back to `settings.DATABASE_URL`, so migrations just run in the container:

- **Blueprint**: add to the `api` service:

```yaml
    preDeployCommand: cd backend && alembic upgrade head
```

(Valid only in the blueprint — the manual dashboard has no equivalent; use the start-command approach below.)

- **Manual dashboard**: place it at the **front of the api Start Command** —

```
cd backend && alembic upgrade head && gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 120 --access-logfile - --error-logfile -
```

Notes:

- Alembic must run **from the image's WORKDIR (`/app`)** because `script_location = ./alembic` and `prepend_sys_path = .` are relative. `cd backend` inside the container is harmless (there is no `backend/` dir in the image — the `backend` folder is the build context, so contents land at `/app`). If you prefer, just `alembic upgrade head && gunicorn …`.
- Only **one** of api/worker should run migrations (`preDeployCommand` runs before every deploy, so an api instance is enough; the worker's start command doesn't migrate).
- Schema changes only happen on deploy; new dev branches touching migrations should run `alembic upgrade head` in a Preview Environment first.
- If you need your docker-compose `postgres/init.sql` (extension grants, seed roles), run it once against the managed DB: `psql "$DATABASE_URL" -f postgres/init.sql` from your laptop after provisioning — Alembic will then manage everything else.

---

## 7. Frontend ↔ API wiring, custom domain + SSL

### How the frontend talks to the api (IMPORTANT)

The static site is a **public client**; the api is on Render's private network. Your `frontend/nginx.conf` proxies `/api → backend:8000` — that hostname only exists in docker-compose, so it **will not work as-is on Render**. Three options:

1. **Public api + static frontend (recommended, zero extra cost).** Don't disable the api's `renderSubdomainPolicy`; set `VITE_API_BASE_URL=https://api.onrender.com/api/v1`. Because the frontend runs on `https://reportgen.onrender.com`, ensure CORS allows it (see §8). Note `ALLOWED_HOSTS` is not read by the app (the env is set but unused for CORS — see the hard-coded CORS block in `backend/app/main.py`: it currently uses `allow_origins=["*"]`).
2. **Proxy Integration (`/api` route).** Render can route `https://reportgen.onrender.com/api/*` to the api service; set `VITE_API_BASE_URL=https://reportgen.onrender.com/api/v1`. Same origin → CORS is a non-issue. Look up "Proxy Integration" in Render docs; it's the cleanest for SPA + API on one domain.
3. **Docker web service for frontend.** Build `frontend/Dockerfile.prod` (nginx on :80) with `dockerCommand: nginx -g 'daemon off;'`, `healthCheckPath: /` — but this **requires a paid plan** since free web services don't support Docker, and you'd still need to fix the `/api` proxy (nginx can `proxy_pass` to `http://api:8000` **over internal networking** — that part does work on Render, only the `backend` hostname from compose doesn't). Choose this only if you need nginx-level control (gzip/caching headers) beyond what a static site offers.

### Custom domain + SSL

- **Certificate**: Render gives `*.onrender.com` subdomains with automatic Let's Encrypt TLS on all web services/static sites — no action needed.
- **Custom domain** (e.g. `app.reportgen.io`): Service → **Settings → Custom Domains → Add**. Render shows CNAME records; add them at your DNS provider. Verification takes ~minutes; SSL is issued and auto-renewed by Render (no certbot, no 80/443 juggling like your certificate setup).
- Static sites and web services each carry their own domain list; put the main app domain on the **frontend** service, and `api.reportgen.io` (optionally) on the api.
- Make sure `VITE_API_BASE_URL` uses the final https URL before your first production build — it's baked into the bundle.

---

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| api deploy fails/hangs at health check | Wrong health path | Confirm `healthCheckPath: /health`; the endpoint exists and returns 200 pre-middleware. `curl https://api.onrender.com/health` from your laptop. |
| `sqlalchemy.exc.ArgumentError: Could not parse rfc1738 URL from string 'postgres://…'` | Render's managed Postgres `connectionString` sometimes uses `postgres://`; your `DATABASE_URL` default is `postgresql+psycopg2://` and alembic just passes the env value through | Set `DATABASE_URL` env to `postgresql+psycopg2://…` (or `postgresql://` works too — SQLAlchemy accepts it; only the `postgres` scheme without a driver fails). Easiest: quick-add the connection string from the Postgres dashboard and prefix `postgresql+psycopg2` if not already there. |
| Worker restarts/OOM with `concurrency=4` | 4 Celery processes × ~150MB > 512MB starter limit | Lower to `--concurrency=2`, or upgrade api/worker to `plan: standard` (1GB). |
| CORS errors in browser console | Api CORS block is hard-coded `allow_origins=["*"]` with `allow_credentials=True` (invalid combo for credentialed requests), and `ALLOWED_HOSTS` env is **not read** anywhere | Edit `backend/app/main.py`: `allow_origins=os.getenv("ALLOWED_HOSTS", "https://reportgen.onrender.com")`.split(",")` (there's a commented template at line 38), or set `allow_origins=["*"]` without `allow_credentials=True`, or use a Proxy Integration (§7) so requests are same-origin. |
| Frontend loads but API calls 404/502 | Static site can't reach api: `VITE_API_BASE_URL` wrong (defaults to `http://localhost:8000/api/v1` in `client.ts`), or api's render subdomain disabled | Fix `VITE_API_BASE_URL` env (build-time!) and redeploy the static site; rebuild needed because the URL is baked in. Check `curl https://api.onrender.com/health`. |
| `404 Page Not Found` on SPA deep links (e.g. `/reports/12`) | Static-site/nginx has no SPA fallback | Static sites: add a route rewrite `source: /(.*)` → `/index.html` (or `try_files` in nginx). |
| 502 on `/api/*` through Proxy Integration | Proxy destination wrong, or api still initializing | Verify the proxy target service name + port 8000; confirm api health first. |
| S3 uploads fail (`ServiceUnavailable` / `InvalidAccessKeyId`) | `S3_ENDPOINT_URL` default `http://localhost:9000` never overridden, or keys don't match `MINIO_ROOT_USER/PASSWORD` | Set `S3_ENDPOINT_URL=http://minio:9000` (internal) on api+worker; match keys exactly; check bucket exists (`mc mb` or MinIO console :9001 if exposed). |
| celery worker boots but tasks never run | Worker & api Redis URLs differ (two different Redis services), or `beat` not deployed | Both run on the **same** `REDIS_URL` (fromService quick-add); ensure `beat` is up if you use `scheduled_report` features. |
| DB connection refused from worker | `DATABASE_URL` missing on worker | Worker env must carry the same `fromDatabase` connection string. |
| Render "Deploy failed: Dockerfile not found" | `dockerfilePath`/root dir mismatch | With the blueprint, `dockerfilePath: ./backend/Dockerfile.prod` + `dockerContext: ./backend`. Manual: root directory `backend`. |
| Gunicorn binding errors | Port mismatched with Render's expected port | Render injects `PORT`; the image binds `0.0.0.0:8000` explicitly. Keep 8000 (the blueprint sets it) or change the build to bind `$PORT`. If you see `Address already in use`, check you aren't running the Dockerfile CMD **and** an override. |
| Rate limit errors on first load | `RateLimitingMiddleware` default 100/min on `/api/v1/chat/message` etc. | Normal under bursty dev traffic; raise in `main.py` overrides if needed. |

---

## 9. Cost notes (as of 2026, US regions)

| Item | Plan | Monthly cost | Notes |
|---|---|---|---|
| api (web, Docker) | starter | ~$7 | 512MB/0.5CPU; ~750 instance-hrs. **Pay-per-use**: free tier gives 750 hrs before billing starts |
| worker | starter | ~$7 | same |
| beat | free | $0 | 0.1 CPU, sleeps when idle — fine for a heartbeat schedule |
| minio (web + disk) | starter + 10GB disk | ~$7 + ~$1.5 | disk is the only persistent MinIO storage |
| postgres | starter | ~$19 | 1GB RAM, 15GB disk included; minor versions auto-patched |
| redis | starter | ~$7 | 128MB maxmemory |
| frontend | static | $0 | free static site; **$0 but requires a paid account** (Render free account exclusion) |
| **Blueprint total** | | **≈ $48/mo** | swap minio for S3/R2/B2 (pay-per-use, often < $5/mo) → ≈ $40/mo |

**Cheaper alternatives**

- **Drop MinIO → managed S3-compatible object storage.** Render has no hosted S3. Use AWS S3, Cloudflare R2, or Backblaze B2: keep the same `S3_*` env vars (`S3_ENDPOINT_URL` = `https://<account-id>.r2.cloudflarestorage.com` for R2, or omit for AWS SigV4 defaults), delete the minio service (≈ −$8/mo), and remove the disk entirely. This also removes the single-point-of-failure of a single-instance MinIO.
- **Merge worker + beat into one service**: run both commands via `dockerCommand` (e.g. a small script) or use `celery worker -B` for the scheduler — saves the free-slot usage and simplifies env (though `-B` is discouraged at scale).
- **Downsize postgres** to `plan: free` only during development; production data needs the starter disk guarantee.
- The 750 free instance-hrs **do not cover** a second web service running 24/7 — a full-time web API on the free tier gets sleep-woken cycles; plan for starter from day one if you want reliability.
- **Business/pro** plans unlock: more RAM on postgres, zero-downtime deploys, and priority infrastructure. Move to pro only when you have paying traffic; starter is plenty for a first production launch. When you scale, swap `plan:` in the blueprint and re-apply — no code changes.

---

## Checklist before you hit deploy

- [ ] `render.yaml` committed at repo root; `dockerfilePath`/`dockerContext` point at the real `Dockerfile.prod` files
- [ ] `SECRET_KEY` generated (or `generateValue`) — identical on api and worker
- [ ] `ANTHROPIC_API_KEY`, `S3_ACCESS_KEY`/`S3_SECRET_KEY` set as secrets, matching `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD`
- [ ] `VITE_API_BASE_URL` = final https API URL (build-time — set **before** the first build)
- [ ] CORS tightened: either the `ALLOWED_HOSTS`-driven snippet from §8 or a Proxy Integration
- [ ] Migrations wired: `preDeployCommand` (blueprint) or start-command prefix (dashboard)
- [ ] Health paths: api `/health`, minio `/minio/health/live`
- [ ] Custom domain CNAMEs added; SSL auto-issued by Render