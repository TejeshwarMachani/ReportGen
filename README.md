# AI Business Report Generation System

A multi-tenant web platform for SMBs to upload data (CSV/Excel or live DB connections) and get:

1. **Auto-generated narrative business reports** with charts
2. **Chat interface** to ask questions about data in plain English
3. **Simple forecasting** on key metrics (revenue, sales, churn, etc.)

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI (Python 3.11) |
| Frontend | React 18 + TypeScript + Vite |
| Database | PostgreSQL 15 |
| Cache/Queue | Redis 7 + Celery |
| Object Storage | MinIO (S3-compatible) |
| Auth | JWT (access + refresh tokens) |
| LLM | Anthropic Claude (configurable) |
| Deployment | Docker Compose |

---

## Project Structure

```
ReportGen/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/v1/          # API routes
│   │   ├── core/            # Config, database, Celery
│   │   ├── middleware/      # Rate limiting, audit logging
│   │   ├── models/          # SQLAlchemy models
│   │   ├── services/        # Business logic
│   │   ├── workers/         # Celery tasks
│   │   └── llm/             # LLM prompt templates
│   ├── alembic/             # Database migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                # React application
│   ├── src/
│   │   ├── api/             # Axios client
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Page components
│   │   ├── store/           # Zustand state
│   │   └── lib/             # Utilities
│   ├── package.json
│   ├── Dockerfile
│   └── .env.example
├── docker-compose.yml       # Local development
├── docker-compose.prod.yml  # Production deployment
└── README.md                # This file
```

---

## Quick Start (Local Development)

### Prerequisites

- Docker & Docker Compose v2+
- Git
- (Optional) Anthropic API key for LLM features

### 1. Clone and Configure

```bash
git clone <your-repo-url>
cd ReportGen

# Backend environment
cp backend/.env.example backend/.env
# Edit backend/.env and add your ANTHROPIC_API_KEY

# Frontend environment
cp frontend/.env.example frontend/.env
```

### 2. Start Services

```bash
docker-compose up --build
```

This starts:
- **PostgreSQL** on `localhost:5432`
- **Redis** on `localhost:6379`
- **MinIO** on `localhost:9000` (console: `localhost:9001`)
- **Backend API** on `localhost:8000` (docs: `localhost:8000/docs`)
- **Frontend** on `localhost:3000`

### 3. Run Migrations

```bash
docker-compose exec backend alembic upgrade head
```

### 4. Create Initial User

The first user to register becomes the organization owner.

---

## Environment Variables

### Backend (`.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg2://user:pass@localhost:5432/reportgen` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT signing key (32+ chars) | **Required** |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `30` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `14` |
| `LLM_PROVIDER` | LLM provider | `anthropic` |
| `LLM_MODEL` | Model name | `claude-sonnet-4-6` |
| `ANTHROPIC_API_KEY` | **Required for LLM features** | - |
| `S3_ENDPOINT_URL` | MinIO/S3 endpoint | `http://localhost:9000` |
| `S3_BUCKET` | Upload bucket name | `reportgen-uploads` |
| `S3_ACCESS_KEY` | MinIO access key | `minioadmin` |
| `S3_SECRET_KEY` | MinIO secret key | `minioadmin` |
| `ENVIRONMENT` | `development` / `production` | `development` |
| `SENTRY_DSN` | Error tracking (optional) | - |

### Frontend (`.env`)

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8000/api/v1` |

---

## Production Deployment

### 1. Prepare Production Config

```bash
# Copy production compose file
cp docker-compose.prod.yml docker-compose.prod.yml

# Create production environment file
cp backend/.env.example backend/.env.prod
# Edit with production values (strong SECRET_KEY, real ANTHROPIC_API_KEY, etc.)

# Frontend production env
cp frontend/.env.example frontend/.env.prod
# Set VITE_API_BASE_URL to your production API URL
```

### 2. Key Production Changes

**docker-compose.prod.yml** includes:
- Resource limits (CPU/memory)
- Restart policies
- Health checks
- Non-root containers
- Production-grade PostgreSQL/Redis configs
- Nginx reverse proxy for frontend

### 3. Deploy

**Option A — Render (recommended, fully managed):**

See [`RENDER_DEPLOY.md`](RENDER_DEPLOY.md) for the step-by-step guide and the one-click Blueprint (`render.yaml` is included in the repo).

```bash
# Render Blueprint: push to GitHub → Render → New Blueprint Instance → select repo
```

**Option B — Docker Compose on your own server:**

```bash
# Using docker-compose (single server)
docker-compose -f docker-compose.prod.yml --env-file backend/.env.prod up -d --build

# Or use your preferred orchestrator (K8s, ECS, etc.)
```

**Option C — GitHub Pages (frontend demo):**

See [`GITHUB_PAGES_DEPLOY.md`](GITHUB_PAGES_DEPLOY.md). Note: GitHub Pages can only host the static frontend — the backend must run elsewhere (Render/Railway/Fly.io).

### 4. Required Production Checklist

- [ ] Generate strong `SECRET_KEY` (32+ random chars)
- [ ] Set real `ANTHROPIC_API_KEY`
- [ ] Configure `ALLOWED_HOSTS` in backend for CORS
- [ ] Use managed PostgreSQL (RDS, Cloud SQL, etc.)
- [ ] Use managed Redis (ElastiCache, etc.)
- [ ] Use real S3 (AWS S3, MinIO cluster, etc.)
- [ ] Enable HTTPS (terminate at load balancer / nginx)
- [ ] Configure `SENTRY_DSN` for error tracking
- [ ] Set up database backups
- [ ] Configure log aggregation
- [ ] Set up monitoring/alerting

---

## API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

Key endpoints:
| Feature | Endpoint |
|---------|----------|
| Auth | `POST /api/v1/auth/login`, `POST /api/v1/auth/register` |
| Datasets | `POST /api/v1/datasets/upload`, `GET /api/v1/datasets` |
| Reports | `POST /api/v1/reports/generate`, `GET /api/v1/reports` |
| Chat | `POST /api/v1/chat/message`, `GET /api/v1/chat/sessions` |
| Forecast | `POST /api/v1/forecast/generate`, `GET /api/v1/forecast/jobs` |

---

## Development

### Backend Commands

```bash
# Run tests
docker-compose exec backend pytest

# Run migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Open shell
docker-compose exec backend bash
```

### Frontend Commands

```bash
# Run dev server (outside Docker)
cd frontend && npm run dev

# Build for production
cd frontend && npm run build

# Lint
cd frontend && npm run lint
```

---

## Database Schema

See `03_DATABASE_SCHEMA.md` for full ER diagram and table definitions.

Key entities:
- **Organizations** - Multi-tenant root
- **Users** - Members of organizations
- **Datasets** - Uploaded data files
- **Reports** - Generated reports
- **Chat Sessions/Messages** - Conversation history
- **Forecast Jobs** - Forecasting tasks
- **Audit Logs** - Security/compliance trail

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- **Backend**: Black formatter, Ruff linter
- **Frontend**: ESLint + Prettier, TypeScript strict mode

---

## License

Proprietary - All rights reserved.

---

## Documentation

This project includes a full documentation package in the root:

| File | Description |
|------|-------------|
| `01_PRD.md` | Product requirements |
| `02_TECH_ARCHITECTURE.md` | Technical architecture |
| `03_DATABASE_SCHEMA.md` | Database schema & ER diagram |
| `04_API_SPECIFICATION.md` | API contracts |
| `05_FEATURES_USER_STORIES.md` | User stories & acceptance criteria |
| `06_UI_UX_SPEC.md` | UI/UX specifications |
| `07_ROADMAP.md` | Development roadmap |
| `08_VIBE_CODING_GUIDE.md` | AI-assisted development guide |

Start with `08_VIBE_CODING_GUIDE.md` if using an AI coding assistant.

## Deployment Guides

| Guide | When to use |
|-------|-------------|
| `RENDER_DEPLOY.md` | Deploy frontend + backend + DB + Redis to Render (one-click Blueprint) |
| `GITHUB_PAGES_DEPLOY.md` | Host the frontend demo on GitHub Pages (backend still needs a separate host) |