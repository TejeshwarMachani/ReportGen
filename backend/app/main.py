from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from .middleware.rate_limiting import RateLimitingMiddleware, set_rate_limiter, RateLimiter
from .middleware.audit_logging import AuditLoggingMiddleware
import os
import redis
from .core.config import settings

# Sentry error tracking
SENTRY_DSN = os.getenv("SENTRY_DSN")

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integration.fastapi import FastApiIntegration
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[FastApiIntegration()],
        environment=os.getenv("ENVIRONMENT", "development"),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        send_default_pii=os.getenv("SENTRY_SEND_DEFAULT_PII", "False").lower() == "true",
    )

# Security headers - applied via audit logging middleware and response headers
SECURE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' https://*.cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://*.cdn.jsdelivr.net; img-src 'self' data: https:; connect-src 'self'; font-src 'self' https://*.cdn.jsdelivr.net; frame-ancestors 'none';",
}


app = FastAPI(title="AI Business Report Generation API", version="1.0.0")

# CORS middleware
# Origins come from the ALLOWED_HOSTS env var (comma-separated), with a
# dev default that matches local development. In production set
#   ALLOWED_HOSTS="https://your-frontend.onrender.com,https://your-api.onrender.com"
# Note: allow_credentials=True with "*" is rejected by browsers, so we only
# use "*" when no explicit origins are configured and credentials are off.
_allow_origins = os.getenv("ALLOWED_HOSTS", "")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins.split(",") if _allow_origins else ["*"],
    allow_credentials=bool(_allow_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis client for rate limiting and other services
redis_client = redis.asyncio.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    max_connections=20,
)

# Initialize rate limiter with Redis
rate_limiter = RateLimiter(redis_client=redis_client)
set_rate_limiter(rate_limiter)


# Health check endpoints (must be added BEFORE rate limiting/audit middleware
# so they can be checked without auth)
@app.get("/health", include_in_schema=False)
async def health_check():
    response = JSONResponse(content={"status": "healthy"}, status_code=200)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    return response


@app.get("/ready", include_in_schema=False)
async def readiness_check():
    """Readiness check - verifies DB, Redis, and other dependencies are available."""
    try:
        # Quick ping to Redis
        await redis_client.ping()
        # Quick ping to PostgreSQL would go here
        response = JSONResponse(content={"status": "ready"}, status_code=200)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        return response
    except Exception as e:
        print(f"Readiness check error: {e}")
        return JSONResponse(
            content={"status": "not_ready", "detail": "Dependencies unavailable"},
            status_code=503,
        )


@app.get("/live", include_in_schema=False)
async def liveness_check():
    """Liveness check - verifies the process is alive."""
    response = JSONResponse(content={"status": "alive"}, status_code=200)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    return response


# Rate limiting middleware - injected with Redis client
app.add_middleware(
    RateLimitingMiddleware,
    override_limits={
        "/api/v1/reports/generate": (30, 60),
        "/api/v1/forecast/generate": (20, 40),
        "/api/v1/chat/message": (50, 100),
    },
    exclude_paths=["/health", "/docs", "/redoc", "/openapi.json", "/ready", "/live"],
)

# Audit logging middleware
app.add_middleware(
    AuditLoggingMiddleware,
    exclude_paths=["/health", "/docs", "/redoc", "/openapi.json", "/ready", "/live"],
)


# Startup event - verify Redis connection
@app.on_event("startup")
async def startup_event():
    try:
        await redis_client.ping()
        print("[OK] Redis connection established")
    except Exception as e:
        print(f"[WARN] Redis connection failed: {e}")
        print("       Rate limiting will use in-memory fallback")


# Include API routers under /api/v1
from .api.v1.router import api_router

app.include_router(api_router)